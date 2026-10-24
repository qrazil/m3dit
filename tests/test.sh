#!/usr/bin/env bash
# Every check for this repo.
#
#   M31_ROOT=/path/to/m31 LANGC=/path/to/m31c bash tests/test.sh
#
# The editing engine is checked against an oracle that is not this program:
# `nvim --headless -u NONE` (see tests/test_engine.sh and DESIGN.md section 7).
# The other tests are unit programs (tests/t_*.m31) that print a final
# "... N failed" line, which this script greps.
set -uo pipefail
cd "$(dirname "$0")/.."

if [ -z "${M31_ROOT:-}" ]; then
    echo "M31_ROOT is not set -- point it at a checkout of github.com/qrazil/m31" \
         "(or an extracted release's runtime SDK)." >&2
    exit 1
fi
if [ ! -f "$M31_ROOT/config.sh" ] || [ ! -d "$M31_ROOT/runtime" ]; then
    echo "M31_ROOT=$M31_ROOT does not look like an m31 checkout" >&2
    exit 1
fi

. "$M31_ROOT/runtime/arch.sh"

LANGC=${LANGC:-./m31c}
WORK=$(mktemp -d)
# unit programs that need scratch files (t_theme) put them here, not in /tmp
export M3_TEST_TMP=$WORK
trap 'rm -rf "$WORK"' EXIT
pass=0
fail=0

note() { printf '\033[32mok\033[0m   %s\n' "$1"; pass=$((pass + 1)); }
bad()  { printf '\033[31mFAIL\033[0m %s\n' "$1"; shift; printf '%s\n' "$@" | sed 's/^/     /'; fail=$((fail + 1)); }

# build NAME [SOURCE]: compile tests/NAME.m31 (or SOURCE) to $WORK/NAME
build() {
    local name=$1
    local src=${2:-tests/$name.m31}
    if ! "$LANGC" --emit-c "$src" -o "$WORK/$name.c" 2>"$WORK/$name.diag"; then
        bad "compile $name" "$(head -8 "$WORK/$name.diag")"
        return 1
    fi
    if ! cc -O2 -Wall -Wextra -I "$M31_ROOT/runtime" -pthread -o "$WORK/$name" "$WORK/$name.c" \
           "$M31_ROOT/runtime/rt.c" "$M31_ROOT/runtime/scheduler.c" "$M31_ROOT/$RT_REACTOR_C" "$M31_ROOT/$RT_CTX_ASM" \
           2>"$WORK/$name.cc"; then
        bad "cc $name" "$(head -5 "$WORK/$name.cc")"
        return 1
    fi
    return 0
}

# unit NAME [SOURCE]: build tests/NAME.m31 (or SOURCE), run it, require its last line to end "0 failed"
unit() {
    local name=$1
    build "$name" ${2:+"$2"} || return
    local out
    out=$("$WORK/$name" 2>&1)
    local last
    last=$(printf '%s\n' "$out" | tail -1)
    if printf '%s' "$last" | grep -q ' 0 failed$'; then
        note "$name: $last"
    else
        bad "$name" "$(printf '%s\n' "$out" | tail -15)"
    fi
}

# --- house style ---------------------------------------------------------------

if out=$("$LANGC" fmt --check -r . 2>&1); then
    note "source is formatted"
else
    bad "source is not formatted (run: m31c fmt -r .)" "$out"
fi

if out=$("$LANGC" lint . 2>&1); then
    note "naming lint is clean"
else
    bad "m31c lint reports findings" "$(printf '%s\n' "$out" | tail -15)"
fi

for part in tests/test_*.sh; do
    [ -f "$part" ] && . "$part"
done

# a plugin owns its tests: plugins/NAME/tests/test.sh is sourced when the plugin is in the default profile
for plugin in $(bash scripts/plugins.sh resolve 2>/dev/null); do
    [ -f "plugins/$plugin/tests/test.sh" ] && . "plugins/$plugin/tests/test.sh"
done

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
