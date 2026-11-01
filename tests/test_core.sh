# sourced by tests/test.sh: core behaviour checked on the real binary (tests/core_pty.py; docs/CORE-STATUS.md).
if [ ! -x "$WORK/m3" ]; then
    build m3 m3.m31
fi
if [ -x "$WORK/m3" ]; then
    if out=$(python3 tests/core_pty.py "$WORK/m3" 2>&1); then
        note "core_pty: $(printf '%s\n' "$out" | tail -1)"
    else
        bad "core_pty" "$(printf '%s\n' "$out" | tail -15)"
    fi
fi
