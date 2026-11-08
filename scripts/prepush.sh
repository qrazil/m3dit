#!/usr/bin/env bash
# The gate every change passes before it is pushed or handed back.
#
#   M31_ROOT=... LANGC=... bash scripts/prepush.sh [--quick]
#
#   1. regenerates every generated file: ext/MED_ext_enabled.m31 (the default profile's plugin registry), docs/KEYMAP.md,
#      docs/OPTIONS.md and the divergences table of docs/CORE-STATUS.md
#   2. runs the plugin checks, `m31c -lint .` and `m31c -fmt --check --recursive .`
#   3. fails when `git status` is not clean afterwards: a generated file changed (commit it) or work is uncommitted
#   4. clones HEAD into a temporary directory and runs the whole tests/test.sh there, so that what was tested is
#      exactly what is committed (no local files, no stale generated files)
#
# --quick stops after step 3 (a minute instead of about an hour); a hand-back is never done on --quick.
# Needs python3 and git; tests/test.sh needs pyte and nvim for the pty and oracle parts (it says what it skips).
set -euo pipefail
cd "$(dirname "$0")/.."

is_quick=0
if [ "${1:-}" = "--quick" ]; then
    is_quick=1
elif [ $# -gt 0 ]; then
    echo "usage: bash scripts/prepush.sh [--quick]" >&2
    exit 2
fi
if [ -z "${M31_ROOT:-}" ]; then
    echo "prepush: M31_ROOT is not set -- point it at a checkout of github.com/qrazil/m31" >&2
    exit 1
fi
LANGC=${LANGC:-./m31c}
step() { printf '\n== %s\n' "$1"; }
fail() { printf 'prepush: FAILED: %s\n' "$1" >&2; exit 1; }

step "generated files"
bash scripts/plugins.sh gen $(bash scripts/plugins.sh resolve) > ext/MED_ext_enabled.m31
bash scripts/gen_keymap.sh > /dev/null 2>&1 || fail "scripts/gen_keymap.sh failed"
python3 scripts/options_doc.py > /dev/null
python3 scripts/divergences.py --write docs/CORE-STATUS.md

step "plugin rules, lint, format"
bash scripts/check_plugins.sh
lint=$("$LANGC" -lint . 2>&1 | tail -1)
echo "$lint"
case "$lint" in
    "0 finding(s)"*) ;;
    *) "$LANGC" -lint . 2>&1 | head -20; fail "m31c -lint . reports findings" ;;
esac
fmt=$("$LANGC" -fmt --check --recursive . 2>&1 | grep -v '^warning' || true)
if [ -n "$fmt" ]; then
    printf '%s\n' "$fmt" | head -20
    fail "m31c -fmt --check --recursive . reports files to format"
fi

step "git status"
if [ -n "$(git status --porcelain)" ]; then
    git status --short
    fail "the tree is not clean: commit what was regenerated or changed (a generated file is out of date, or work is uncommitted)"
fi
echo "clean at $(git rev-parse --short HEAD)"

if [ "$is_quick" = 1 ]; then
    echo
    echo "prepush --quick: ok (the full suite was NOT run)"
    exit 0
fi

step "full tests/test.sh from a clean clone of $(git rev-parse --short HEAD)"
work=$(mktemp -d "${TMPDIR:-/tmp}/m3-prepush.XXXXXX")
trap 'rm -rf "$work"' EXIT
git clone -q . "$work/clone"
head=$(git rev-parse HEAD)
[ "$(git -C "$work/clone" rev-parse HEAD)" = "$head" ] || fail "the clone is not at HEAD"
log="$work/test.log"
set +e
(cd "$work/clone" && bash tests/test.sh) 2>&1 | tee "$log" | tail -40
status=${PIPESTATUS[0]}
set -e
summary=$(grep -E '^[0-9]+ passed, [0-9]+ failed' "$log" | tail -1 || true)
echo
echo "prepush: $summary (commit $(git rev-parse --short HEAD), clean clone)"
[ "$status" = 0 ] || fail "tests/test.sh failed: $summary"
echo "prepush: ok"
