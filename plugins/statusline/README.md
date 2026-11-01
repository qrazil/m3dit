# statusline

The status line beyond the core's minimal one, and the buffer line.

The core draws the mode, the file name, the filetype and the position. This plugin adds, between the name and the
filetype, `main +1 ~2 -0  E:1 W:0  LSP: indexing`: the git branch with the hunk counts against HEAD, the language server's
errors and warnings for the file, and what the server is busy with. It also gives the buffer line: one row of
` 1 name + ` labels above the windows from two open buffers (`+` marks unsaved changes; the active one in
`ui.bufferline.active`); `:set nobufferline` hides it. The line of tab pages is the core's and shows from two pages.

API used (0.3.0): `Ctx.status()` (the host answers with the branch, hunk counts, diagnostics and server activity),
`Ctx.set_segment` (the text, refreshed on every `Tick` and at `BufferOpen`, so a change shows within 250 ms) and
`Registry.did_bar` (the labels of the buffer line; the host draws them). It is eager.

Turn it off: `:PluginDisable statusline` (no extras, no buffer line), `--without statusline`, `--no-plugins`.

Tests: `tests/t_statusline.m31`, the golden screens `bufferline` and `start`, `tests/transparent_pty.py` (statusline and
tab line on transparent terminals), the e2e scenario `statusline_tabline_guides`.
