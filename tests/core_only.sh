#!/usr/bin/env bash
# The core-only acceptance (docs/CORE-AND-PLUGINS.md 7.4): `scripts/build.sh --no-plugins` builds on a tree without
# plugins/ and the result is a working modal editor. Needs M31_ROOT and LANGC like the other tests.
#
#   bash tests/core_only.sh [WORKDIR]      builds WORKDIR/m3-core (a temporary directory when none is given)
#
# Gates so far (0.18.0: the absence checks cover move, harpoon, bracketed, notify, todo, statusline; whichkey is core since 0.22.0): 1 build (no plugins/ reachable), 2 --version and --list-plugins name no plugin, 3 behaviour (a
# pty session: the golden screens of the scenarios that need no plugin), 5 absence (Alt-j does not move a line, :Plugins
# has no move row).
# Gates 2 (units) and 3 (oracle) of 7.4 are the ordinary suites, which do not depend on the plugin selection
# until a step moves a feature out; the core corpora are listed here when one does. While no feature has left
# the core, minimal and default are the same program and the golden file is the same.
set -uo pipefail
cd "$(dirname "$0")/.."
work=${1:-$(mktemp -d)}
mkdir -p "$work"
bin="$work/m3-core"
fail=0
say() { printf '%s\n' "$*"; }
bad() { say "FAIL $*"; fail=1; }

if ! LANGC="${LANGC:-./m31c}" bash scripts/build.sh --no-plugins -o "$bin" >"$work/m3-core.log" 2>&1; then
    bad "build --no-plugins"; grep -v '^warning' "$work/m3-core.log" | tail -8; exit 1
fi
grep -q '^plugins: none' "$work/m3-core.log" || bad "the build did not report 'plugins: none'"
version=$("$bin" --version 2>&1)
case "$version" in *"(api 0.8.0; plugins: none)") ;; *) bad "--version says: $version" ;; esac
[ -z "$("$bin" --list-plugins 2>&1)" ] || bad "--list-plugins prints something"

if python3 -c 'import pyte' 2>/dev/null; then
    scenarios=start,open_markdown_wide,insert_typing,visual_block,search_highlight,explore_directory,wrap_long_lines,number_options,scroll_half_page,indent_guides,error_message
    if ! out=$(python3 tests/screen_pty.py "$bin" --only "$scenarios" --scratch "$work/core-screens" 2>&1); then
        bad "golden screens on the core build"; say "$out" | tail -15
    fi
    # absence gate: what lives in a default plugin is not there (the golden screens are those of the default build); a bare build starts with :set nowhichkey, so the which_key_* popups are absent too
    for absent in move_line harpoon_pin bufferline which_key_leader which_key_g which_key_bracket notify_toast; do
        if python3 tests/screen_pty.py "$bin" --only "$absent" --scratch "$work/core-absent" >/dev/null 2>&1; then
            bad "scenario $absent is the same in the --no-plugins build: its plugin is still in the core"
        fi
    done
    # and the TODO badge: main.py has TODO and FIXME comments, drawn as plain comments without the todo plugin
    if python3 tests/screen_pty.py "$bin" --only open_python --scratch "$work/core-absent" >/dev/null 2>&1; then
        bad "open_python is the same in the --no-plugins build: the TODO badge is still in the core"
    fi
    listing=$(python3 tests/screen_pty.py "$bin" --only plugins_list --scratch "$work/core-absent" 2>&1)
    if printf '%s\n' "$listing" | grep -q "move  move a line"; then
        :
    else
        bad ":Plugins in the core build does not differ from the default one by the plugin rows"
    fi
else
    say "skip golden screens: pyte is not installed"
fi
[ "$fail" -eq 0 ] && say "core_only: build, version, absence and golden screens ok"
exit "$fail"
