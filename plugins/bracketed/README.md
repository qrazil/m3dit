# bracketed

`[` and `]` pairs that walk through lists, one key letter for each kind of list.

| keys | does |
|---|---|
| `[b` `]b` / `[B` `]B` | previous, next / first, last buffer (`:bprevious` `:bnext` `:bfirst` `:blast`) |
| `[l` `]l` / `[L` `]L` | previous, next / first, last entry of the default list (`:lprev` `:lnext` `:lfirst` `:llast`; docs/LIST.md). `[q` `]q` `[Q` `]Q` are gone: there is no separate quickfix list |
| `[t` `]t` | previous, next TODO comment in the buffer (`:Todo prev`, `:Todo next`; the `todo` plugin) |
| `[h` `]h`, `[c` `]c` | previous, next git hunk (`:Hunk prev`, `:Hunk next`; wraps) |
| `[d` `]d` | previous, next diagnostic (`:Lsp prev_diag`, `:Lsp next_diag`) |

Options: none. Events and commands used: none; it is sixteen Normal-mode `MapSpec`s that run an ex command, and nothing runs
when it activates. A count typed before the key is ignored (as before). It was `App.did_bracketed` and two special cases in
`App.handle`; the core gained `:Hunk next|prev` and `:Lsp next_diag|prev_diag` so that the keys are plain commands you can map
yourself. `wants: todo`: `[t` needs `:Todo`.

Turn it off: `:PluginDisable bracketed`, `bash scripts/build.sh --without bracketed`, `--no-plugins`. Without it `[b` and
friends fall through to the engine's own `[`/`]` motions (`[(`, `[{`, `]]` ...), which are untouched.

Tests: `tests/t_bracketed.m31` (buffers, the keys go with `:PluginDisable`, the which-key labels), the e2e scenario
`bracketed_and_move`, the golden screen `which_key_bracket`.
