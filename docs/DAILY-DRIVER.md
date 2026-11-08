# m3 as a daily driver: what is there, what is missing

> Written at 0.17.0/0.18.0. Several rows moved since: explorer, git, statusline and (on a branch) terminal are plugins; the quickfix list is the generic list; `:cdo`/`:cfdo` are `:ldo`/`:lfdo`; miller columns and `:diffthis` are planned, no longer declined. [NORTH-STAR.md](NORTH-STAR.md) has the current state and the order of the work.

Status: audit of m3 0.17.0 plus the plugin work of 0.18.0, written 2026-11-01. Sources: README, `docs/KEYMAP.md` (generated),
`docs/ROADMAP.md`, the command table in `engine/MED_ex.m31`, `~/homelab/apps/nox/VIM_PARITY.md` for what the owner's earlier
editor was held to, and the code. A row says where the feature lives: **core** (always built), a **plugin** (default profile;
`--without NAME` removes it), **missing** or **declined** (the roadmap says no). "Vim commands behave exactly like nvim" is the
rule for anything below that is a Vim command: nothing here is proposed as a look-alike with other behaviour.

## What a day of work needs

| need | state | where | notes |
|---|---|---|---|
| Modal editing, ex subset, registers, macros, marks, folds, undo files | core | engine | checked against `nvim --headless` on 40,887 cases (20 listed divergences) |
| Fuzzy find files, live grep, recent files, buffers, lines of the buffer, quickfix, commands, keys, options, marks, themes | core | finder (picker primitive and its sources) | `<Space>ff fg fr fb fd fq fc fk fo fm`; async, ripgrep/fd when present, built-in walker and grep otherwise; frecency |
| Symbols (this file), diagnostics list, TODO list, word under cursor | core + plugin | finder sources; `todo` for the TODO list | `<Space>fs fx fw ft`; symbols are line patterns or LSP |
| File tree | core | `ui/MED_tree.m31`, `:Neotree`, `:Explore` | `<Space>e`, `<Space>E`; git letters; planned plugin `explorer` (step 12) |
| Buffers: next, previous, alternate, delete, list, buffer line | core + plugin | core commands; `bracketed` keys; `statusline` buffer line | |
| Windows, tab pages, session of the open files | core + plugin | window model, `:Session`; `session` (cursor positions, recent files, frecency) | cursor, layout and tab pages; sizes are shared out again |
| LSP: hover, definition, references, rename, code action, format, signature, inlay hints, semantic tokens, completion popup, snippets | core | `ui/MED_lsp.m31` | `K gd grr grn gra`, `<Space>cr ca cf ck ch`; `:Lsp ...`; servers found on `$PATH` |
| Diagnostics: signs, list, next and previous, float at cursor | core + plugin | LSP client; `bracketed` (`[d ]d`) | `<Space>ll xx xX`; toast for server messages via `notify` |
| Git gutter, hunk stage/reset/undo/preview, blame line and list, diff, log, branches, commits, checkout | core | `ui/MED_git*.m31` over m31git (in process) | `<Space>g...`, `:Git`, `:Hunk`; `]h [h ]c [c` are `bracketed`; planned plugin `git` (step 10) |
| Terminal pane | core | `:terminal`, `<Space>t` | `<C-\><C-n>` leaves; planned plugin `terminal` (step 13) |
| Surround, auto pairs, comment toggle | core | engine options `surround`, `autopairs`, `comment` | `ys ds cs S`, `gc gcc`; entangled with the engine, see CORE-AND-PLUGINS section 10 |
| which-key (leader and prefix popup) | core (0.22.0; it was a plugin) | `:set whichkey` | 400 ms; on by default, off in a bare build |
| Pinned files (harpoon) | plugin | `harpoon` | `<Space>ha he hn hp hd 1..9` |
| Notifications | plugin | `notify` | toasts for LSP `window/showMessage` and plugins; `:Notifications` history; `:messages` is the core ring |
| Statusline extras, buffer line | plugin | `statusline` | branch, hunk counts, E/W, server activity |
| Move lines, label jump, indent guides | plugin / core | `move`; `jump`, `guides` in core | |
| Project settings | core | `.editorconfig`, `.m3.toml` | tabstop, formatting, per-project options |
| Themes, transparent terminals, truecolor with fallbacks | core | theme engine (14 themes) | decision: stays in core |
| Clipboard, mouse, bracketed paste | core | | OSC 52 / wl-copy / xclip / pbcopy detected |
| Multi-buffer / project search and replace | core (0.19.0), partial | `:ldo` `:lfdo` `:bufdo` in `MED_app.run_do` | the finder sends hits to quickfix (`<C-q>`), then `:cdo s/old/new/ \| update`; stops at the first failing line. `:windo`, `:argdo`, `:tabdo`, `:vimgrep`, `:grep`, `:make` exist since 0.20.0 (docs/VI-CORE.md); 'errorformat' is not read |
| Diff mode (`:diffthis`, `]c` between two windows) | **missing** | | `:Git diff` and hunk preview exist; two-window diff does not |
| `:make` and the quickfix errorformat | **missing** | | quickfix is fed by the finder and LSP only |
| Spell checking | **declined** | ROADMAP | not before 1.x |
| Debugger (DAP) | **declined** | ROADMAP item 18 | post 1.0 |
| Full git UI (fugitive, lazygit), miller columns | **declined** | ROADMAP, owner | use `mgit`, `gitui` |
| Tree-sitter text objects and folds | **declined** | ROADMAP | the `syntax` library highlights; no parse tree |
| Remote files (netrw protocols) | **declined** | ROADMAP | |

## Gaps, in the order they hurt a daily user

1. **Project-wide replace: done in 0.19.0 for `:ldo`, `:lfdo` and `:bufdo` (named `:cdo` and `:cfdo` until 0.26.0)** (core, `App.run_do`: an ex line at each quickfix
   entry, once per file, in each listed buffer; the first failing line ends the run; nothing is written, add `| update`).
   The plugin API still has no buffer handle (it reads and edits the active buffer only), so this had to be core code in
   the App, which owns the buffers. Left: `:windo` and `:argdo` (rarely used), and checking `:cdo` against nvim in the oracle
   with files on disk (the unit test `t_cdo` covers the semantics, not the corner cases of `:cnext` at the end of the list).
2. **`:grep`, `:vimgrep`, `:make`** feeding the quickfix list, with `:cwindow`. The pieces exist (quickfix list, grep sources);
   the commands do not. Same owner: the App.
3. **Restore the session on `m3` with no arguments** in a project directory (what `persistence.nvim` does). `session` (0.19.0)
   restores cursors and keeps the recent files; the named `:Session` and the project session saved on exit are core and
   explicit.
4. **Two-window diff** (`:diffthis`, `:diffoff`, `]c [c` in diff windows, `do`/`dp`). Large (a diff algorithm in the
   renderer, scroll binding, fold of equal runs); the hunk preview covers the common case of "what did I change".
5. **Entangled core features that stay core for now:** surround, autopairs, comment (engine options with oracle
   coverage), git (the gutter is drawn by the renderer), finder, explorer, terminal. CORE-AND-PLUGINS section 10 records the
   seam each needs; none is a blocker for daily use.
6. **Polish nobody asked for yet:** icons and colour swatches (optional plugins), a startup dashboard (declined by the owner).

## What changed in 0.18.0 to get here

Six features left the core and became plugins on API 0.3.0 (and `session` on 0.4.0 in 0.19.0), each with `plugin.txt`, a module, a README and tests, in the
default profile and switched off by `--without NAME`: `bracketed`, `harpoon`, `todo`, `notify` (new) and
`statusline`. The core keeps a minimal status line (mode, file, filetype, position) and the tab-page line, so
`--no-plugins` is a working editor. No daily feature was removed. Comment toggle was not missing (it is `gc` in the engine,
checked against nvim 0.11), so there is no `comment` plugin.
