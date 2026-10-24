# move

Move a line or the Visual selection with Alt-j and Alt-k, shift it with Alt-h and Alt-l.

| keys | mode | does |
|---|---|---|
| `<A-j>` / `<A-k>` | Normal | `:m +1` / `:m -2`: the line one down / up |
| `<A-j>` / `<A-k>` | Visual | `:m '>+1` / `:m '<-2`, then `gv`: the selection one down / up, still selected |
| `<A-h>` / `<A-l>` | Normal | `<<` / `>>`: shift the line |
| `<A-h>` / `<A-l>` | Visual | `<gv` / `>gv`: shift the selection, still selected |

Options: none. Events and commands used: none; it is eight `MapSpec`s (`Action.Keys`) and registers nothing when it
activates. The App feeds an Alt key as the single key `<M-x>` when a map of the mode starts with it, and as Escape plus the
key otherwise (so in Insert mode `Alt-j` is still `<Esc>j`).

Turn it off: `:PluginDisable move` (the keys are unmapped; `:PluginEnable move` maps them again), `bash scripts/build.sh
--without move` (not compiled in), `--no-plugins` (core only).

Tests: `tests/t_move.m31` (through the App: Alt-j/k/h/l, Visual, the first and last line, `:PluginDisable`), the e2e scenario
`bracketed_and_move` and the golden screen `move_line`. It was `App.did_alt_move` in the core (docs/CORE-AND-PLUGINS.md,
step S2).
