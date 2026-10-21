# sourced by tests/test.sh: the file finder.
#
#   t_frecency, t_fuzzy, t_picker   unit checks (decay and state files, path ranking, the picker, hints)
#   finder_pty.py                   the pty property: over a tree of hostile names and files (wide, combining,
#                                   tabs, control bytes, ESC sequences, CRLF, binary, huge lines) the screen
#                                   the diff renderer produced equals a from-scratch redraw after every key,
#                                   the box keeps its frame, resizes included; ranking, the score column,
#                                   frecency and the clean run; skips cleanly when pyte is missing
#   finder_variants_pty.py          the same typing sequence on terminals that measure text differently (Terminal.app's
#                                   code point sum, wide ambiguous or private use glyphs, narrow new emoji): every
#                                   step against that terminal's own repaint
#   width_pty.py                    the start-up width probe through the real m3 on an emulator that answers cursor
#                                   position reports: borders in ASCII where box drawing is wide, TUI_WIDTH_PROBE, TUI_BORDERS
#   bench/finder_bench.m31          the scorer on 100,000 paths; here only that it runs and that narrowing from
#                                   the previous matches finds what a full rescore finds
if [ ! -x "$WORK/m3" ]; then
    build m3 m3.m31
fi
if [ -x "$WORK/m3" ]; then
    if out=$(python3 tests/finder_variants_pty.py "$WORK/m3" 2>&1); then
        note "finder_variants_pty: $(printf '%s\n' "$out" | tail -1)"
    else
        bad "finder_variants_pty" "$(printf '%s\n' "$out" | tail -25)"
    fi
    if out=$(python3 tests/width_pty.py "$WORK/m3" "$WORK/width_pty" 2>&1); then
        note "width_pty: $(printf '%s\n' "$out" | tail -1)"
    else
        bad "width_pty" "$(printf '%s\n' "$out" | tail -25)"
    fi
    if out=$(python3 tests/finder_pty.py "$WORK/m3" 2>&1); then
        note "finder_pty: $(printf '%s\n' "$out" | tail -1)"
    else
        bad "finder_pty" "$(printf '%s\n' "$out" | tail -25)"
    fi
fi
if build finder_bench bench/finder_bench.m31; then
    out=$("$WORK/finder_bench" 2>&1)
    if printf '%s\n' "$out" | grep -q MISMATCH || ! printf '%s\n' "$out" | grep -q 'typing'; then
        bad "finder_bench" "$(printf '%s\n' "$out" | tail -12)"
    else
        note "finder_bench: $(printf '%s\n' "$out" | grep 'full rescore  pom' | sed 's/^ *//')"
    fi
fi
