#!/usr/bin/env bash
# Build the engine half of the oracle and run it against nvim.
#
#   M31_ROOT=/path/to/m31 scripts/oracle.sh [oracle_nvim.py args]
#
# With no arguments: the corpus. Examples:
#   scripts/oracle.sh --fuzz --seed 7 --cases 500
#   scripts/oracle.sh --corpus --only 'ciw' -v
set -euo pipefail
cd "$(dirname "$0")/.."
: "${M31_ROOT:?set M31_ROOT to an m31 checkout}"
. "$M31_ROOT/runtime/arch.sh"
LANGC=${LANGC:-$M31_ROOT/m31c}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
"$LANGC" -emit-c tests/t_oracle_run.m31 --out "$WORK/run.c"
cc -O2 -I "$M31_ROOT/runtime" -pthread -o "$WORK/run" "$WORK/run.c" \
   "$M31_ROOT/runtime/rt.c" "$M31_ROOT/runtime/scheduler.c" "$M31_ROOT/$RT_REACTOR_C" "$M31_ROOT/$RT_CTX_ASM"
python3 tests/oracles/oracle_nvim.py --runner "$WORK/run" "$@"
