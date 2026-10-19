# sourced by tests/test.sh: the language server popups.
#
#   t_pum         unit checks of the completion popup (matching, ranking, selection, placement, drawing)
#   lsp_pty.py    the popup through a pty against a scripted server (tests/fake_lsp_complete.py): as-you-type
#                 filtering, trigger characters, resolve, documentation panel, snippets, additionalTextEdits,
#                 hostile labels, placement, cancel; the screen the diff renderer produced equals a from-scratch
#                 redraw after every step and the popup keeps its rectangle. M3_LSP_REAL=1 adds the scenarios
#                 against real servers (pyright, clangd; skipped when missing) and the nvim cross-check.
if [ ! -x "$WORK/m3" ]; then
    build m3 m3.m31
fi
if [ -x "$WORK/m3" ]; then
    if out=$(python3 tests/lsp_pty.py "$WORK/m3" 2>&1); then
        note "lsp_pty: $(printf '%s\n' "$out" | tail -1)"
    else
        bad "lsp_pty" "$(printf '%s\n' "$out" | tail -25)"
    fi
fi
