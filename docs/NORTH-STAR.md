# North Star

Written 2026-11-07, at m3 0.28.1 with the terminal plugin (0.29.0) built on a branch. This is the one page that says where m3 is going and how far it is.
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

A debugger (DAP) before 1.0; spell checking; remote files; tree-sitter and tree-sitter text objects (the `syntax` library highlights, there is no parse tree);
a startup dashboard; a Vimscript or Lua interpreter (the extension language is m31); full-screen programs in the terminal pane (it is line oriented).

## 4. Distance to the goal

| need | state |
|---|---|
| Vi core, ex, registers, macros, folds, undo files | done (oracle-checked) |
| Fuzzy finder, live grep, pickers with preview | done |
| Generic list (`:l`, `]l`) | done (0.25.0) |
| File tree | done (plugin `explorer`, 0.24.0); miller columns on `<Space>E`: queued |
| Git: gutter, `:Git` log/show/diff/blame, hunk stage/reset/preview, `gh{motion}` | done (plugin `git`, 0.21 to 0.23); the final `gh*` key set (toggle stage, reset, buffer, diff, blame, list): queued |
| LSP: diagnostics, hover, definition, references, rename, code action, format, completion, signature, inlay hints, semantic tokens | done (core) |
| LSP navigation (more than the above) and a server installer | queued; the installer is a requirement |
| Virtual text API (one decorator for diagnostics, blame and plugins) | queued |
| Terminal | in progress: plugin `terminal`, API 0.8.0, built and tested on a branch (0.29.0), not released |
| Surround, autopairs, comment, which-key, harpoon, jump, move, guides, TODO, notifications, statusline, bufferline, session | done |
| Clipboard, mouse, bracketed paste, OSC 52 | done (0.28.x) |
| Themes, transparency, truecolor fallbacks | done |
| Two-window diff (`:diffthis`) | queued |
| Text-object registry (user text objects through the API) | queued |
| Project search and replace | partly done (`:ldo`, `:lfdo`, `:bufdo` on the list); a finder-based flow on the same list: queued |
| The keymap audit (toggles for option switches, one key per panel) | queued (docs/KEYMAP-AUDIT.md) |
| The owner's own nvim keymap and plugin list | owner input pending: the `nvim` profile follows his config once it is supplied |
| Debugger, spell, remote files, tree-sitter, dashboard | not planned |

## 5. Milestones (an order, not dates)

| version | content |
|---|---|
| 0.29 | terminal plugin (ptys and panes in the API) |
| 0.30 | the keymap audit: toggles, merged keys, `docs/KEYMAP-AUDIT.md` |
| 0.31 | git write ops under `gh*` |
| 0.32 | LSP navigation and the installer |
| 0.33 | virtual text API (shared with diagnostics and blame) |
| 0.34 | miller columns and `:diffthis` |
| 0.35 | text-object registry |
| 0.36 | project search and replace on the finder and the list |
| 0.37 and on | the owner's nvim keymap and plugin list, gaps found by using it; then 1.0 hardening |

**Done enough to switch** means: the owner uses m3 for a full working day, editing, searching, using git and the language servers he works with, without
opening nvim once. The first honest test is after 0.36, with the nvim profile filled in from his config; whatever he reaches for and does not find becomes the
next item, ahead of everything else on this page.
