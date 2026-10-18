# sourced by tests/test.sh: the extension API.
#
#   t_ext        unit checks (registry, dispatch, error isolation, edits, the App's hooks); in test_units.sh
#   ext_pty.py   m3 built with the sample extension (scripts/build.sh --ext MEDX_trim_whitespace) in a pty:
#                trim on write, the :TrimTrailing command, undo as one step, dot unchanged; and the default
#                build, which must leave the file alone
if [ ! -x "$WORK/m3" ]; then
    build m3 m3.m31
fi
if [ -x "$WORK/m3" ]; then
    if LANGC="$LANGC" bash scripts/build.sh --ext MEDX_trim_whitespace -o "$WORK/m3_ext" >"$WORK/m3_ext.log" 2>&1; then
        if out=$(python3 tests/ext_pty.py "$WORK/m3_ext" "$WORK/m3" 2>&1); then
            note "ext_pty: $(printf '%s\n' "$out" | tail -1)"
        else
            bad "ext_pty" "$(printf '%s\n' "$out" | tail -25)"
        fi
    else
        bad "build m3 with --ext MEDX_trim_whitespace" "$(grep -v '^warning' "$WORK/m3_ext.log" | tail -8)"
    fi
fi
