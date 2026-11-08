# North Star

Written 2026-11-07, updated 2026-11-09 at m3 0.31.1. This is the one page that says where m3 is going and how far it is.
It is a summary: the details are in `docs/DAILY-DRIVER.md` (what a working day needs), `docs/CORE-AND-PLUGINS.md` (what is core and what is a plugin),
`docs/DIVERGENCE-AUDIT.md` and `docs/CORE-STATUS.md` (where m3 differs from vim and why), `docs/KEYMAP.md` and `docs/ROADMAP.md`.

## 1. The goal

m3 is a new terminal editor, built on vim and nvim, that **replaces nvim as the owner's daily driver**. It is fast (start-up and per-key cost are budgets,
not hopes: docs/UX-PERF.md), it has a batteries-included core with the extras as plugins, and it **diverges from nvim wherever that is better**:
nvim and helix are sources of ideas, not specifications, and m3 does not copy their mistakes or their unwanted features.

## 2. The laws in force

| law | in practice |
|---|---|
| Parity is a means, not a goal | the vi core (motions, operators, text objects, registers, marks, macros, ex basics) stays compatible and is checked against `nvim --headless` on about 42,000 cases; every deliberate difference is a row of `tests/oracles/divergences.tsv`, shown in docs/CORE-STATUS.md |
| Toggles and combined keys over paired keys | one key flips a state (`ghs` stages or unstages); `[`/`]` pairs stay as they are; the keymap audit applies this to the default maps |
| Hunks live under `gh*` | `ghs ghr ghS ghR ghd ghD ghb ghl`, `]h [h`, plus the operators `gh{motion}` already built; no `gS`/`gD` |
| One generic list instead of quickfix | `:l`, `:lnext`, `[l ]l`; the finder's `<C-q>`, `:grep`, LSP references, tag matches and hunks all fill it; there are no `:c*` commands |
| The system clipboard is the default register | `'clipboard'` is `unnamedplus`; no tool falls back to OSC 52, then the internal register; it never errors |
| which-key, surround and autopairs are core | on by default, each with an option to switch it off (`whichkey`, `surround`, `autopairs`) |
| Everything else is a plugin through the extension API | `plugins/NAME`, built in by default, removable with `--without NAME`; the API grows additively and a plugin may not touch the editor's internals |
| Refuse out loud | something m3 dropped answers with what to write instead (`E492: ... write ':lnext'`, `E518: ... (reason)`), in the manner of the command line's own refusals |
| Defaults stay overridable | a user keymap or `:set` line overrides any default key or option |

## 3. Non-goals (unless the owner changes them)

A debugger (DAP) before 1.0; spell checking; remote files;
a startup dashboard; a Vimscript or Lua interpreter (the extension language is m31); full-screen programs in the terminal pane (it is line oriented). Tree-sitter used to be on this list; it is a requirement now.

## 4. Distance to the goal

| need | state |
|---|---|
| Vi core, ex, registers, macros, folds, undo files | done (oracle-checked) |
| Fuzzy finder, live grep, pickers with preview | done |
| Generic list (`:l`, `]l`) | done (0.25.0) |
| File tree | done (plugin `explorer`, 0.24.0); miller columns on `<Space>E`: queued |
| Git: gutter, `:Git` log/show/diff/blame, hunk stage/reset/diff/blame/list | done (plugin `git`, 0.21 to 0.31; the `gh*` chords: `ghs ghr ghS ghR ghd ghD ghb ghl`; `ghD` becomes a two-window diff with `:diffthis`) |
| LSP: diagnostics, hover, definition, references, rename, code action, format, completion, signature, inlay hints, semantic tokens | done (core) |
| LSP navigation (more than the above) and a server installer | queued; the installer is a requirement |
| Virtual text API (one decorator for diagnostics, blame and plugins) | queued |
| Terminal | done (plugin `terminal`, 0.29.0; API 0.8.0 ptys and panes) |
| Surround, autopairs, comment, which-key, harpoon, jump, move, guides, TODO, notifications, statusline, bufferline, session | done |
| Clipboard, mouse, bracketed paste, OSC 52 | done (0.28.x) |
| Themes, transparency, truecolor fallbacks | done |
| Two-window diff (`:diffthis`) | queued |
| Text-object registry (user text objects through the API) | queued |
| Project search and replace | partly done (`:ldo`, `:lfdo`, `:bufdo` on the list); a finder-based flow on the same list: queued |
| The keymap audit (merged duplicate keys, toggles) | done (0.30.0, docs/KEYMAP-AUDIT.md) |
| The owner's own nvim keymap and plugin list | owner input pending: the `nvim` profile follows his config once it is supplied |
| Tree-sitter: highlights, structural text objects, indent, folds, injections, incremental selection, with no server | **required before 1.0** (owner decision): spike done (docs/TREE-SITTER.md), design and questions pending, 0.34 and 0.35 |
| Debugger, spell, remote files, dashboard | not planned |

## 5. Milestones (an order, not dates)

Done: 0.29 terminal plugin, 0.30 keymap audit, 0.31 the `gh*` hunk keys. The LSP navigation and installer work (0.33) is written and parked on a branch while the toolkit and the terminal come first.

| version | content |
|---|---|
| 0.32 | the plugin toolkit (floats, popup, prompt, select, layout, timing helpers) and an excellent terminal (float, split, sessions, smooth under flood). **The owner dogfoods m3 for real work from here on** |
| 0.33 | LSP navigation and the server installer |
| 0.34 | tree-sitter core: the parser (helper process or in-process glue, docs/TREE-SITTER.md), incremental re-parse, highlights with injections, the large-file fallback to the lexical `syntax` library, a build option to leave it out |
| 0.35 | tree-sitter text objects, indent, folds and incremental selection, with the text-object registry. Sources in this order: tree-sitter, LSP ranges (`documentSymbol`, `foldingRange`, `selectionRange`, semantic tokens), the lexical fallback (the `syntax` library plus bracket and indent rules), then user-defined objects |
| 0.36 | project search and replace (the finder plus the generic list) |
| 0.37 | virtual text API (one decorator for diagnostics, blame and plugins) |
| 0.38 | miller columns on `<Space>E` |
| 0.39 | `:diffthis` (two-window diff; `ghD` moves onto it) |
| 0.40 and on | the owner's nvim keymap and plugin list, then 1.0 hardening |

**Dogfood from 0.32.** Every gap the owner hits while working in m3 goes to the front of the queue, ahead of the list above. The CHANGELOG and its one-line migration notes are kept tidy so that
he can follow what changes under him. Before anything is pushed or handed back, `bash scripts/prepush.sh` regenerates the generated files, runs lint and format, and runs the full `tests/test.sh` from
a clean clone of the commit; work only ever goes on top of `origin/master`.

**Done enough to switch** means: the owner uses m3 for a full working day, editing, searching, using git and the language servers he works with, without opening nvim once. The first honest test is
the dogfooding that starts at 0.32; whatever he reaches for and does not find becomes the next item.
