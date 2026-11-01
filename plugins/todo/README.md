# todo

TODO FIXME HACK XXX NOTE WARN PERF BUG in a comment are drawn as a badge, listed, and jumped between.

| what | how |
|---|---|
| highlight | the word as a whole word inside a comment, in theme scope `ui.todo`; `:set notodohl` turns it off |
| `:Todo` / `<Space>ft` | the TODO comments of the project in the finder (ripgrep, or the built-in grep without it) |
| `:Todo next` `:Todo prev` | the next, previous TODO line of the buffer, wrapping, as a jump (`<C-o>` returns); `]t` `[t` of `bracketed` |

API used (0.3.0): `Registry.did_decorate` (the badge is a `Decorator` that the renderer asks for each drawn line, only
while the plugin is on and `todohl` is), `Ctx.open_picker("todos", ...)` (the finder source stays in the core with the other
sources), `Ctx.set_jump_mark`. It activates at start-up (one registered decorator and one command). The list of words
exists three times (here, the finder's `grep` pattern and its built-in fallback); it is not an option.

Turn it off: `:PluginDisable todo`, `--without todo`, `--no-plugins` (then `:Todo` and `<Space>ft` do not exist, the
words are plain comments). The finder's `todos` source remains for `:Finder`-style use by other plugins.

Tests: `tests/t_todo.m31` (`]t` `[t`, wrap, jump list, `:Todo`, the spans, `todohl`, `:PluginDisable`), the golden screens
that draw a TODO line (`start`, `open_python`).
