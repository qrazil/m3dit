#!/usr/bin/env bash
# Which plugins an m3 build contains, and the registry module that compiles them in
# (docs/CORE-AND-PLUGINS.md 5.2). Used by scripts/build.sh and the tests; bash 3.2 and BSD tools only.
#
#   bash scripts/plugins.sh resolve [SELECTION]     the plugins to build, one per line, `requires` and `wants` first
#   bash scripts/plugins.sh gen [--ext A,B] NAME... the text of ext/MED_ext_enabled.m31 for these plugins
#   bash scripts/plugins.sh dir NAME [SELECTION]    the directory that holds plugin NAME
#   bash scripts/plugins.sh check-files [SELECTION] the plugin.txt files of the selection are well formed
#   bash scripts/plugins.sh table [SELECTION]       what `m3 --list-plugins` must print for that build (from plugin.txt)
#
# SELECTION (each also has an environment variable; the flag wins):
#   --profile NAME      plugins/profiles/NAME.txt (`include OTHER` lines allowed)   $M3_PROFILE   (default: default)
#   --no-plugins        none: the core only                             $M3_NO_PLUGINS=1
#   --plugins A,B       exactly these (their `requires` are added and reported)   $M3_PLUGINS
#   --without A,B       the selection minus these (refused when a kept plugin requires one)   $M3_WITHOUT
#   --plugin-dir DIR    one more place to look for plugins/NAME/plugin.txt (DIR/NAME/plugin.txt)   $M3_PLUGIN_DIR
#
# A plugin lives in plugins/NAME/ with a plugin.txt of `key: value` lines (name, summary, requires, wants) and
# a module MEDX_NAME.m31 that exports `register`. tests/test_plugins.sh checks plugin.txt against the Spec.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)

die() { echo "plugins: $*" >&2; exit 1; }
note() { echo "plugins: $*" >&2; }

# has_word "a b c" b
has_word() {
    case " $1 " in *" $2 "*) return 0 ;; *) return 1 ;; esac
}

split_list() { printf '%s' "$1" | tr ',' ' ' | tr -s '[:space:]' ' ' | sed 's/^ //; s/ $//'; }

# ---------------------------------------------------------------- selection

profile=${M3_PROFILE:-}
no_plugins=${M3_NO_PLUGINS:-}
only=${M3_PLUGINS:-}
without=${M3_WITHOUT:-}
plugin_dir=${M3_PLUGIN_DIR:-}
[ "$no_plugins" = 1 ] || no_plugins=""
is_given_profile=""
[ -n "$profile" ] && is_given_profile=1

parse_selection() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --profile) profile=${2:?--profile needs a name}; is_given_profile=1; shift 2 ;;
            --no-plugins) no_plugins=1; shift ;;
            --plugins) only=${2:?--plugins needs a list}; shift 2 ;;
            --without) without=${2:?--without needs a list}; shift 2 ;;
            --plugin-dir) plugin_dir=${2:?--plugin-dir needs a directory}; shift 2 ;;
            *) die "unknown argument: $1" ;;
        esac
    done
    [ -n "$profile" ] || profile=default
    if [ -n "$no_plugins" ] && [ -n "$only" ]; then die "--no-plugins and --plugins exclude each other"; fi
    if [ -n "$no_plugins" ] && [ -n "$without" ]; then die "--no-plugins and --without exclude each other"; fi
    if [ -n "$only" ] && [ -n "$is_given_profile" ]; then die "--plugins and --profile exclude each other"; fi
    return 0
}

# the directory of plugin $1 (its plugin.txt inside), or nothing
plugin_dir_of() {
    local name=$1 found="" candidate
    if [ -f "$ROOT/plugins/$name/plugin.txt" ]; then found="$ROOT/plugins/$name"; fi
    if [ -n "$plugin_dir" ] && [ -f "$plugin_dir/$name/plugin.txt" ]; then
        candidate=$(cd "$plugin_dir/$name" && pwd)
        if [ -n "$found" ] && [ "$found" != "$candidate" ]; then die "plugin $name is in $found and in $candidate"; fi
        found=$candidate
    fi
    printf '%s' "$found"
}

# field KEY of plugin NAME from its plugin.txt, as written
plugin_field() {
    local dir
    dir=$(plugin_dir_of "$1")
    [ -n "$dir" ] || die "no plugin called $1 (no plugins/$1/plugin.txt${plugin_dir:+ and none in $plugin_dir})"
    sed -n "s/^$2:[[:space:]]*//p" "$dir/plugin.txt" | head -1 | sed 's/[[:space:]]*$//'
}

# a list field (requires, wants): comma or space separated, printed space separated
plugin_list() {
    plugin_field "$1" "$2" | tr ',' ' ' | tr -s '[:space:]' ' ' | sed 's/^ //; s/ $//'
}

# the names in plugins/profiles/$1.txt; a line `include NAME` brings in another profile first (at most 4 deep)
profile_names() {
    local file="$ROOT/plugins/profiles/$1.txt" depth=${2:-0} line included names=""
    [ -f "$file" ] || die "no such profile: $1 (plugins/profiles/$1.txt)"
    [ "$depth" -lt 4 ] || die "profile $1: includes are nested too deep"
    while IFS= read -r line; do
        case "$line" in
            ''|'#'*) ;;
            include\ *)
                included=$(profile_names "$(printf '%s' "${line#include }" | tr -d '[:space:]')" $((depth + 1)))
                names="$names $included" ;;
            *) names="$names $(printf '%s' "$line" | tr ',' ' ')" ;;
        esac
    done < "$file"
    printf '%s' "$names" | tr -s '[:space:]' ' ' | sed 's/^ //; s/ $//'
}

# The ordered list: selection, without, closure of requires, then dependency order.
resolve() {
    parse_selection "$@"
    local base="" name dep want kept=""
    if [ -n "$no_plugins" ]; then
        base=""
    elif [ -n "$only" ]; then
        base=$(split_list "$only")
    else
        base=$(profile_names "$profile")
    fi
    # every name must be a plugin
    for name in $base; do
        plugin_field "$name" name >/dev/null
    done
    if [ -n "$without" ]; then
        for name in $(split_list "$without"); do
            has_word "$base" "$name" || note "--without $name: not in the selection"
        done
        for name in $base; do
            has_word "$(split_list "$without")" "$name" || kept="$kept $name"
        done
        kept=${kept# }
        for name in $kept; do
            for dep in $(plugin_list "$name" requires); do
                if has_word "$(split_list "$without")" "$dep" && ! has_word "$kept" "$dep"; then
                    die "plugin $name requires $dep: drop $name too, or keep $dep"
                fi
            done
        done
        base=$kept
    fi
    # closure of requires
    local set=$base changed=1
    while [ "$changed" = 1 ]; do
        changed=0
        for name in $set; do
            for dep in $(plugin_list "$name" requires); do
                if ! has_word "$set" "$dep"; then
                    plugin_field "$dep" name >/dev/null
                    note "added $dep (required by $name)"
                    set="$set $dep"
                    changed=1
                fi
            done
        done
    done
    # dependency order: requires and wants first, ties in selection order; a cycle of wants is broken
    local emitted="" remaining=$set next progress ok use_wants=1
    while [ -n "$remaining" ]; do
        next=""
        progress=0
        for name in $remaining; do
            ok=1
            for dep in $(plugin_list "$name" requires); do
                has_word "$emitted" "$dep" || ok=0
            done
            if [ "$use_wants" = 1 ]; then
                for want in $(plugin_list "$name" wants); do
                    if has_word "$set" "$want" && ! has_word "$emitted" "$want"; then ok=0; fi
                done
            fi
            if [ "$ok" = 1 ]; then
                emitted="$emitted $name"
                progress=1
            else
                next="$next $name"
            fi
        done
        remaining=${next# }
        if [ "$progress" = 0 ]; then
            if [ "$use_wants" = 1 ]; then
                note "a cycle among wants ($remaining): registered in selection order"
                use_wants=0
            else
                die "a cycle among requires: $remaining"
            fi
        fi
    done
    for name in $emitted; do
        printf '%s\n' "$name"
    done
}

# ---------------------------------------------------------------- generator

gen() {
    local ext_names="" name
    if [ "${1:-}" = "--ext" ]; then ext_names=$(split_list "${2:-}"); shift 2; fi
    printf '// The plugins and extensions built into this m3 (generated by scripts/plugins.sh gen; do not edit).\n//\n'
    printf '// scripts/build.sh resolves the profile (plugins/profiles/default.txt), --plugins, --without and --ext into\n'
    printf '// this list, in dependency order (`requires` and `wants` first), and compiles m3 against a copy of this file.\n'
    printf '// The checked-in version is the default profile, so a bare `m31c m3.m31` equals the release; tests/test_plugins.sh\n'
    printf '// checks that it equals the generator. docs/CORE-AND-PLUGINS.md 5.2, docs/EXTENSIONS.md.\n\n'
    printf 'import ext.MED_ext;\n'
    for name in "$@"; do
        printf 'import plugins.%s.MEDX_%s;\n' "$name" "$name"
    done
    for name in $ext_names; do
        printf 'import ext.%s;\n' "$name"
    done
    printf '\npub void install(MED_ext.Registry api) {\n'
    for name in "$@"; do
        printf '    MEDX_%s.register(api);\n' "$name"
    done
    for name in $ext_names; do
        printf '    %s.register(api);\n' "$name"
    done
    printf '}\n'
}

check_files() {
    local name dir
    parse_selection "$@"
    for name in $(resolve "$@" 2>/dev/null); do
        dir=$(plugin_dir_of "$name")
        [ "$(plugin_field "$name" name)" = "$name" ] || die "plugins/$name/plugin.txt: name must be $name"
        [ -n "$(plugin_field "$name" summary)" ] || die "plugins/$name/plugin.txt: summary is empty"
        [ -f "$dir/MEDX_$name.m31" ] || die "plugins/$name has no MEDX_$name.m31"
        while IFS= read -r line; do
            case "$line" in
                ''|'#'*) ;;
                name:*|summary:*|requires:*|wants:*) ;;
                *) die "plugins/$name/plugin.txt: unknown line: $line" ;;
            esac
        done < "$dir/plugin.txt"
    done
}

# name, summary, requires and wants (comma separated) of each resolved plugin, tab separated
table() {
    local name
    parse_selection "$@"
    for name in $(resolve "$@" 2>/dev/null); do
        printf '%s\t%s\t%s\t%s\n' "$name" "$(plugin_field "$name" summary)" "$(plugin_list "$name" requires | tr ' ' ',')" "$(plugin_list "$name" wants | tr ' ' ',')"
    done
}

cmd=${1:-}
[ $# -gt 0 ] && shift
case "$cmd" in
    resolve) resolve "$@" ;;
    gen) gen "$@" ;;
    dir) name=${1:?dir needs a plugin name}; shift; parse_selection "$@"; plugin_dir_of "$name"; echo ;;
    check-files) check_files "$@" ;;
    table) table "$@" ;;
    *) die "usage: plugins.sh resolve|gen|dir|check-files ..." ;;
esac
