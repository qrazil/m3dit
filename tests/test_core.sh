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

if command -v python3 >/dev/null 2>&1; then
    if out=$(python3 scripts/options_doc.py --check 2>&1); then
        note "docs/OPTIONS.md is generated from the option table"
    else
        bad "docs/OPTIONS.md" "$out"
    fi
    if out=$(python3 scripts/divergences.py --check docs/CORE-STATUS.md 2>&1); then
        note "docs/CORE-STATUS.md divergences table is generated from tests/oracles/divergences.tsv"
    else
        bad "docs/CORE-STATUS.md divergences" "$out"
    fi
fi
