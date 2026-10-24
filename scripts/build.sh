#!/usr/bin/env bash
# Build m3 (`m3.m31`) into a real executable.
#
#   M31_ROOT=/path/to/m31 bash scripts/build.sh            -> ./m3
#   M31_ROOT=/path/to/m31 bash scripts/build.sh -o name    -> ./name
#   ... bash scripts/build.sh --ext MEDX_trim_whitespace   -> m3 with that extension compiled in
#   ... bash scripts/build.sh --ext A,B --ext-dir ~/m3ext  -> extensions A and B (A may live in ~/m3ext)
#
# Plugins (docs/CORE-AND-PLUGINS.md 5.2). The plugins built in are chosen at build time (there is no runtime
# loading); the default is the profile in plugins/profiles/default.txt, which is also what the checked-in
# ext/MED_ext_enabled.m31 holds, so a bare `m31c m3.m31` equals the release.
#
#   ... bash scripts/build.sh --profile full              plugins/profiles/full.txt
#   ... bash scripts/build.sh --no-plugins                the core only: plugins/ is not linked into the build
#   ... bash scripts/build.sh --plugins git,finder        exactly these; their `requires` are added and reported
#   ... bash scripts/build.sh --without terminal,jump     the profile minus these (refused if a kept one requires one)
#   ... bash scripts/build.sh --plugin-dir DIR            also look for plugins in DIR/NAME/plugin.txt
#   $M3_PROFILE, $M3_NO_PLUGINS=1, $M3_PLUGINS, $M3_WITHOUT and $M3_PLUGIN_DIR say the same; a flag wins.
# The resolved list is printed on standard error (`plugins: a b c`). scripts/plugins.sh does the work.
#
# Extensions (docs/EXTENSIONS.md): `--ext NAME[,NAME]`, else $M3_EXT, else the names in ext/enabled.txt. NAME is
# the module's file name without `.m31`, found in ext/ or in `--ext-dir DIR` (or $M3_EXT_DIR). With none named
# and the default plugins the build is exactly the default one. With some, or with another selection of plugins,
# the build runs on a scratch tree of symlinks in which ext/MED_ext_enabled.m31 is generated; the checkout is not
# modified. It needs the m31 toolchain, as every build does.
#
# `m3.m31` and `ui/MED_app.m31` import github.com/qrazil/tui as `import tui.app.TUI_app;`. The
# `deps` file names the exact commit; the first compile fetches it into
# `.m31-deps/` and records it in `deps.lock`.
#
# Needs LANGC (the m31c compiler binary, v0.4.3 or later (the proc module)) and M31_ROOT (a
# checkout of github.com/qrazil/m31, or an extracted release's runtime SDK
# containing config.sh and runtime/). There is no pre-built runtime library.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -z "${M31_ROOT:-}" ]; then
    echo "M31_ROOT is not set -- point it at a checkout of github.com/qrazil/m31" \
         "(or an extracted release's runtime SDK). See this script's header." >&2
    exit 1
fi
if [ ! -f "$M31_ROOT/config.sh" ] || [ ! -d "$M31_ROOT/runtime" ]; then
    echo "M31_ROOT=$M31_ROOT does not look like an m31 checkout" \
         "(expected $M31_ROOT/config.sh and $M31_ROOT/runtime/)" >&2
    exit 1
fi
. "$M31_ROOT/config.sh"
. "$M31_ROOT/runtime/arch.sh"

out=m3
ext_names=${M3_EXT:-}
ext_dir=${M3_EXT_DIR:-}
selection=()
while [ $# -gt 0 ]; do
    case "$1" in
        -o) out=${2:?-o needs a name}; shift 2 ;;
        --ext) ext_names=${2:?--ext needs a name}; shift 2 ;;
        --ext-dir) ext_dir=${2:?--ext-dir needs a directory}; shift 2 ;;
        --profile|--plugins|--without|--plugin-dir)
            selection+=("$1" "${2:?$1 needs a value}"); shift 2 ;;
        --no-plugins) selection+=("$1"); shift ;;
        *) echo "unknown argument: $1" >&2; exit 1 ;;
    esac
done
plugin_list=$(bash scripts/plugins.sh resolve ${selection[@]+"${selection[@]}"}) || exit 1
plugin_list=$(printf '%s' "$plugin_list" | tr '\n' ' ' | sed 's/ $//')
is_no_plugins=${M3_NO_PLUGINS:-}
plugin_dir=${M3_PLUGIN_DIR:-}
position=0
while [ "$position" -lt "${#selection[@]}" ]; do
    case "${selection[$position]}" in
        --no-plugins) is_no_plugins=1 ;;
        --plugin-dir) plugin_dir=${selection[$((position + 1))]} ;;
    esac
    position=$((position + 1))
done
if [ -z "$ext_names" ] && [ -f ext/enabled.txt ]; then
    ext_names=$(grep -v '^[[:space:]]*#' ext/enabled.txt | tr -s '[:space:]' ',')
fi
ext_names=$(printf '%s' "$ext_names" | tr -s ', ' ',,' | sed 's/^,//; s/,$//')

LANGC=${LANGC:-./m31c}
CC=${CC:-cc}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

if [ ! -x "$LANGC" ]; then
    echo "compiler not found or not executable: $LANGC" >&2
    exit 1
fi

LANGC_ABS=$(cd "$(dirname "$LANGC")" && pwd)/$(basename "$LANGC")
src=.
# the registry this build needs: the plugins, then the extensions
if [ -n "$plugin_list" ]; then
    wanted=$(bash scripts/plugins.sh gen --ext "$ext_names" $plugin_list)
else
    wanted=$(bash scripts/plugins.sh gen --ext "$ext_names")
fi
if [ -n "$is_no_plugins" ] || [ "$wanted" != "$(cat ext/MED_ext_enabled.m31)" ] || [ -n "$plugin_dir" ]; then
    src=$tmp/tree
    mkdir -p "$src/ext"
    for entry in .m31-deps deps deps.lock engine ui themes m3.m31; do
        [ -e "$entry" ] && ln -s "$PWD/$entry" "$src/$entry"
    done
    for file in ext/*.m31; do
        [ "$(basename "$file")" = MED_ext_enabled.m31 ] || ln -s "$PWD/$file" "$src/ext/$(basename "$file")"
    done
    if [ -n "$plugin_list" ]; then
        mkdir -p "$src/plugins"
        for name in $plugin_list; do
            ln -s "$(bash scripts/plugins.sh dir "$name" ${plugin_dir:+--plugin-dir "$plugin_dir"})" "$src/plugins/$name"
        done
    fi
    for name in $(printf '%s' "$ext_names" | tr ',' ' '); do
        if [ -f "ext/$name.m31" ]; then
            :
        elif [ -n "$ext_dir" ] && [ -f "$ext_dir/$name.m31" ]; then
            ln -s "$(cd "$ext_dir" && pwd)/$name.m31" "$src/ext/$name.m31"
        else
            echo "extension $name not found (ext/$name.m31${ext_dir:+ or $ext_dir/$name.m31})" >&2
            exit 1
        fi
    done
    printf '%s\n' "$wanted" > "$src/ext/MED_ext_enabled.m31"
    echo "plugins: ${plugin_list:-none}" >&2
    [ -z "$ext_names" ] || echo "extensions: $ext_names" >&2
fi
(cd "$src" && "$LANGC_ABS" --emit-c m3.m31 -o "$tmp/m3.c")
"$CC" -O2 -pthread -I "$M31_ROOT/runtime" -o "$out" "$tmp/m3.c" \
    "$M31_ROOT/runtime/rt.c" "$M31_ROOT/runtime/scheduler.c" \
    "$M31_ROOT/$RT_REACTOR_C" "$M31_ROOT/$RT_CTX_ASM"
echo "$out"
