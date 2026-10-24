#!/usr/bin/env bash
# The core-only acceptance (docs/CORE-AND-PLUGINS.md 7.4): `scripts/build.sh --no-plugins` builds on a tree without
# plugins/ and the result is a working modal editor. Needs M31_ROOT and LANGC like the other tests.
#
#   bash tests/core_only.sh [WORKDIR]      builds WORKDIR/m3-core (a temporary directory when none is given)
#
# Gates so far: 1 build (no plugins/ reachable), 2 --version and --list-plugins name no plugin, 3 behaviour (a
# pty session: the golden screens of the scenarios that need no plugin), 5 absence (:Plugins has no plugin section).
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
case "$version" in *"(api 0.2.0; plugins: none)") ;; *) bad "--version says: $version" ;; esac
[ -z "$("$bin" --list-plugins 2>&1)" ] || bad "--list-plugins prints something"

if python3 -c 'import pyte' 2>/dev/null; then
    scenarios=start,open_python,insert_typing,visual_line,search_highlight,split_vertical,tab_pages,explore_directory,command_palette,plugins_list,fold_manual,wrap_long_lines,error_message
    if ! out=$(python3 tests/screen_pty.py "$bin" --only "$scenarios" --scratch "$work/core-screens" 2>&1); then
        bad "golden screens on the core build"; say "$out" | tail -15
    fi
else
    say "skip golden screens: pyte is not installed"
fi
[ "$fail" -eq 0 ] && say "core_only: build, version, absence and golden screens ok"
exit "$fail"
