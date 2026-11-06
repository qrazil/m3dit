#!/usr/bin/env bash
# Regenerate docs/KEYMAP.md from ui/MED_keymap.m31.
#
#   M31_ROOT=/path/to/m31 LANGC=/path/to/m31c bash scripts/gen_keymap.sh
set -euo pipefail
cd "$(dirname "$0")/.."
. "$M31_ROOT/runtime/arch.sh"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
"${LANGC:-./m31c}" -emit-c scripts/gen_keymap.m31 --out "$tmp/gen.c"
cc -O2 -pthread -I "$M31_ROOT/runtime" -o "$tmp/gen" "$tmp/gen.c" \
    "$M31_ROOT/runtime/rt.c" "$M31_ROOT/runtime/scheduler.c" \
    "$M31_ROOT/$RT_REACTOR_C" "$M31_ROOT/$RT_CTX_ASM"
mkdir -p docs
"$tmp/gen" > docs/KEYMAP.md
echo docs/KEYMAP.md
