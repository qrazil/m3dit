# Changelog

## Unreleased

Language intelligence completion: docs/ROADMAP.md items 15 to 17 (item 18, DAP, is not started).

- Completion popup that follows the cursor (item 15): `:set lspcomplete=auto` (default `manual`: CTRL-Space keeps
  opening the picker) shows the server's items under the word being typed, asked for after trigger characters and
  identifier characters (a 25 ms pause after the last key, so typing never waits for a server) and narrowed on every
  further key by `filterText` (same-case prefix, prefix, word start, substring, in-order letters; ties by the server's
  `sortText`; matched letters highlighted). `<Tab> <C-n> <Down>` and `<S-Tab> <C-p> <Up>` select (past the end nothing is
  selected, as in nvim's menu), `<C-y>` and `<CR>` on a selected row accept (`<CR>` on none is a line break), `<C-e>`
  closes, `<Esc>` closes and leaves Insert mode, a commit character accepts the selected row and is then typed.
  A documentation side panel (on the right, else on the left) shows `detail` and `documentation` of the selected item,
  fetched with `completionItem/resolve` after an 80 ms pause; accepting resolves first when it must (auto-import
  `additionalTextEdits`), applies the item's `textEdit` or `insertText`, and moves the cursor past edits made above it.
  Snippet items go through the snippet engine (tabstops, placeholders, choices). An outdated request is cancelled with
  `$/cancelRequest`; an `isIncomplete` list is asked for again as you type. Drawn with `ui.menu` / `ui.menu.selected` /
  `ui.picker.match` / `ui.popup`; every string is cleaned of control characters before it reaches a cell. New module
  `ui/MED_pum.m31`; `ui/MED_app.m31` has one delimited section. The client now declares completion capabilities
  (snippets, markdown documentation, resolve properties, label details, commit characters) at `initialize`.
- LSP client: `Server.await` (a response within a deadline, other messages kept for `poll`), `Server.cancel`,
  `map_point`, trigger and commit characters.
- Tests: `tests/t_pum.m31` (parsing, matching tiers, ranking, narrowing, selection, placement, drawing of hostile
  labels), `tests/lsp_pty.py` against `tests/fake_lsp_complete.py` (frame integrity against a from-scratch redraw,
  control characters, placement above the cursor, resize, cancel, resolve, snippets, additional edits) and, with
  `M3_LSP_REAL=1`, against real clangd and pyright with an nvim cross-check (`tests/oracle_lsp.py`).

## 0.12.0

Git in process: docs/ROADMAP.md items 12 to 14, decision D3 (m3 depends on `m31git`, github.com/qrazil/m31git, as a
pinned git dependency, v0.27.0). The git gutter, blame, hunk staging and the new `:Git` read commands no longer start a
`git` process; a repository the library cannot read goes to `git` as before.

- Dependencies: `deps` and `deps.lock` pin `m31git` v0.27.1 (`41be583`), `tui` v0.11.0 (`e156723`) and `syntax`
  (`e49e01c`), one source per name (m31 allows no more). Build cost of the library, measured with m31 v0.6.0 on tui
  v0.11.0 (clean `scripts/build.sh`, two runs each): binary 3,210,960 to 3,770,976 bytes (+17.4 percent; stripped
  2,703,232 to 3,174,336), build 54.5 / 54.2 s to 64.2 / 68.8 s (+12.2 s on the means). Under the thresholds set with
  D3 (30 percent size, 40 s), so the library is the default and there is no build switch. The tui change itself is
  from `0b132ce` (what 0.11.0 pinned) to v0.11.0, with no change in m3 beyond the pin.
- Gutter and `<Space>gB`: the base text (index, else HEAD) and the blame of a line are read from the object store
  (`ui/MED_gitlib.m31`: loose and packed objects, linked worktrees, SHA-256 repositories). A version 4 index, a missing
  object (partial clone) or a non-UTF-8 file falls back to `git show` / `git blame`. A line the buffer changed says
  "Not committed yet".
- `:Git log [FILE|%] [-L A,B]`, `:Git show [REV]`, `:Git diff [working|index|head]`, `:Git blame`: lists in the finder
  (with a `git show` preview from the library) for log and blame, scratch buffers for show and diff. `-L` follows first
  parents (`git log --first-parent -L`). Read only; the preview of every commit list, and `git:show`, use the library too.
  Keys: `<Space>gl` (log of the file), `gd`, `gm` (blame list), `gu` (unstage hunk).
- `:Hunk stage|reset|undo|preview`: `stage` writes the index in process (a new blob and an index entry with zeroed stat
  fields, so `git status` compares content), `undo` unstages the staged hunk under the cursor, `reset` and `preview` are
  the `<Space>gr` / `gp` actions. Staging no longer uses `git apply --unidiff-zero`, which put a pure addition in the wrong
  place when an earlier hunk had changed the line count (the patch's new-side line numbers are only a hint to git).
- Text objects `ih` (the rows of the hunk) and `ah` (the same plus the blank rows after it) in operator-pending and
  Visual mode. A removal-only hunk has no rows, so there is nothing to select.
- Fixed: resetting a hunk of lines appended at the end of the file trapped (`index out of range`) with the cursor past
  the last row.
- Tests: `tests/t_gitlib.m31` (60 checks of the pure parts), `tests/oracles/oracle_git.py` over `tests/t_gitlib_run.m31`
  (329 checks against real `git`: gutter base, blame, `log`, `log -L`, `show`, `diff` in three forms, twin repositories
  for hunk stage / reset / undo compared with `git add|restore|reset -p` on index, work tree, refs and status, `fsck`,
  a linked worktree, SHA-256, a version 4 index, a 100,000-line timing check), `tests/git_pty.py` (the commands in the
  real binary).
- Known limits: the index is rewritten without its extensions (`TREE`, `UNTR`; an index that needs one, such as a split
  index, is left to `git`), under `index.lock`; a locked or concurrently changed index is reported by `:Hunk stage`
  and nothing is written; a hunk is staged from the buffer, so a buffer that dropped
  its final newline stages the file's line ends as the index had them; `:Git show` of a merge shows the first-parent
  diff, not git's combined diff.

## 0.11.0

Editing depth: the 0.8.0 group of docs/ROADMAP.md (items 7 to 11) and the part of item 6 that 0.7.0 left, each checked
against `nvim --headless -u NONE` where nvim can answer. Nothing here changes a default except that `<S-Tab>` in Insert
mode types a Tab (as nvim) and that Tab can expand a snippet when you have written some.

- Session restore: the tab pages and the window layout come back (`m3` with no arguments, `:Session load`): the shape
  of each page, which file each window shows and where its cursor was, the page and window that were current. Session
  files are version 2 (version 1 files still load); sizes are shared out equally again.
- Folds: `foldmethod=marker` builds the same tree as nvim, jump levels (`{{{3`, `}}}2`) included (`foldnestmax` does not
  apply to markers); a fold's open or closed state survives an edit that moves its end; `3dd`, `2yy`, `3>>` over a closed
  fold count it as one line; `:set foldlevel=N` re-levels the folds even when N did not change; `foldlevelstart` sets
  `foldlevel` when a buffer is first shown. The cursor goes to the first line of a closed fold that ends the buffer only
  when lines were deleted. Corpus 110, 111, 113; `tests/oracles/oracle_folds.py` (the whole fold tree of random marker
  texts), `tests/t_autofold.m31`, `tests/t_foldstart.m31`.
- Soft wrap: `linebreak`, `breakat`, `showbreak`, `breakindent` and `breakindentopt` (`shift`, `min`, `sbr`) lay a wrapped
  line out as nvim does (`engine/MED_wrapmap.m31`), in scrolling, `gj gk g0 gm gM g$`, `j k |`, the mouse and the drawing;
  a double-width character that leaves the last cell empty gets nvim's `>` also without these options. `g0`, `gm` and
  `gM` leave the column they asked for as the wanted one. Corpus 112; `tests/t_wrapmap.m31` holds nvim's virtcol() tables
  and screen rows. New options `breakat`, `breakindentopt`.
- Snippets: the LSP / VS Code grammar with tabstops, placeholders (nested too), mirrors, choices, transforms and the
  variables (`engine/MED_snippet.m31`, `MED_snipops.m31`). `<Tab>` / `<S-Tab>` jump while a snippet is active, a
  placeholder is selected in Select mode (`SELECT` in the status line; a typed character replaces it); `snippets.json` and
  `snippets/LANGUAGE.json` next to the keymap file hold your own, expanded with `<Tab>` after the prefix; LSP completion
  items with snippets expand through the engine. `tests/oracles/oracle_snippet.py` (450 cases against nvim's
  `vim.snippet`), `tests/t_snippet.m31`, a pty scenario.
- `cgn` / `dgn` with `.`, counts and `nowrapscan` match nvim (corpus 109, nothing needed fixing).
- Tab pages: `:[N]tab split|vsplit|new|vnew [file]`; a count on `:tabnew`, `:tabedit`, `:tabnext`, `:tabclose`, `:tabonly`
  and `:tabmove` is a tab page number (`:0tabnew`, `:2tabnew`, `:$tab split`, `.`, `+N`, `-N`), where it was a line
  number; a click on a tab label shows that page. The window oracle skipped every case with a second tab page since
  nvim 0.11 (a check of the command line height was off by the tab line): fixed, 78 cases added, all match.
- Known differences from nvim are listed in `tests/oracles/known_divergences.txt`.

Extension API 0.1.0 (docs/EXTENSIONS.md). Off by default: with no extension built in the editor behaves as before.
Per decision D2 an extension is an m31 module compiled into the binary; there is no runtime loading.

- `ext/MED_ext.m31`: the API (events, commands, key mappings, statusline segments, buffer edits through
  `editor.change`, finder lists, background jobs, version check), its own semantic version (API 0.1.0, separate
  from the editor's), and the registry with dispatch and error isolation (`Err` is reported, three in a row switch
  an extension off; a trap is still fatal).
- `scripts/build.sh --ext NAME[,NAME] [--ext-dir DIR]` (or `$M3_EXT`, `ext/enabled.txt`) builds m3 with extensions;
  no name, no change to the build. `ext/MED_ext_enabled.m31` is the (empty) installer it replaces in a scratch tree.
- Sample extension `ext/MEDX_trim_whitespace.m31` (trim trailing blanks on write, `:TrimTrailing`); not built by default.
- Hooks in the editor: `Editor.user_commands` and `MED_ex.is_builtin_command` (engine), event dispatch in
  `ui/MED_app.m31` and three calls in `m3.m31`; each returns at once when nothing is registered.
- Tests: `tests/t_ext.m31`, `tests/ext_pty.py` (builds with and without the sample, `tests/test_ext.sh`).

## 0.10.0

The file finder: no corrupted borders, hints on the bottom edge, name-first ranking with a relevance and
frecency. The design, numbers and knobs are in docs/FINDER.md; needs tui 0.9.1.

- Drawing: a control character in a file name or in a previewed file (a tab, the CR of a CRLF file, an ESC
  sequence) was written to the terminal as it was and shifted or cleared whatever followed, the right border
  included; the library now draws its picture instead (tui `Buffer`). Emoji ZWJ sequences, flags and
  variation-selector emoji, which terminals draw at different widths, no longer move the rest of the row (tui
  `TUI_diff`: the cursor is placed again after one, the two columns after it are written again). Names are
  drawn one grapheme cluster at a time, so combining marks and flags survive. The preview expands tabs to the
  next stop of four, drops the CR of CRLF lines, cuts very long lines when the file is read, and reads the file
  again when it changes on disk. CTRL-L in a picker (and a focus-in report) writes the whole screen again.
- Key hints sit in the bottom border of the box as one dim row, by picker, cut to fit.
- Ranking (`ui/MED_fuzzy.m31`): the file name first: exact name, name without extension, name prefix, run in
  the name, tight subsequence of the name (or an initialism), subsequence of the path, scattered; inside a
  tier the fzf-style placement score, then the shorter path. `pom` lists `pom.xml`, `parent/pom.xml`, then
  `poxm.txt`, then `pxxxxxxoxxxxxxxx_fbdjdk_m`. A relevance percentage per row (`:set nofinderscore` hides it).
- Frecency (`ui/MED_frecency.m31`): per file a heat with a 14 day half life (`:set finderhalflife=N`),
  `$XDG_STATE_HOME/m3/frecency`, 2000 files at most, written atomically, nothing with `--keymap NONE`. It lifts
  a match inside its tier (a dim `*` marks frecent files) and orders the empty prompt.
- Speed: 100,000 paths rank in 25 to 50 ms for the first keystroke and less after it (a longer prompt only looks
  at what the shorter one matched); typing is ranked once per batch of keys.
- Tests: `tests/finder_pty.py` (hostile names and files, diff renderer against a full redraw after every key,
  resizes, ranking, frecency, clean run; skipped without pyte), `t_frecency.m31`, new cases in `t_fuzzy.m31` and
  `t_picker.m31`, renderer tests in tui; `bench/finder_bench.m31`.

## 0.8.0

Smooth, polished, never abrupt (docs/UX-PERF.md has the numbers; needs tui with the `feat/render` changes,
tui 0.9.0).

- Measurement first: `bench/uxperf.py` drives the real binary in a pty and reports key-to-first-byte and
  key-to-frame latency, bytes per frame, frames per second for a held key, the cost of a full redraw, 1 MB pastes
  and key storms, idle wakeups and a wrapped file. `tests/test.sh` runs it with `--check` (gross regressions only).
- Output: synchronized output (mode 2026, asked with DECRQM, silent when unsupported), one write per frame, scroll
  regions instead of rewriting a scrolled view, the cursor hidden while a frame is drawn.
- Animation (`:set animate`, `animatetime`, `animatescroll`, `animatefade`, `animateflash`; `--no-anim`,
  `$M3_NO_ANIM`, `TERM=dumb`): scrolling glides (`<C-d> <C-u> <C-f> <C-b> zt zz zb gg G`, search and distant jumps,
  the mouse wheel), a yank flashes, which-key and the pickers fade in. Never animated: one-line moves, macros, `.`,
  `:normal`, `:g`, pastes, queued input, an unfocused terminal, a slow terminal. A 16 ms ticker runs only while
  something moves; idle ticks drop to 4 a second.
- Polish: the terminal cursor takes a bar in Insert and the command line and an underline in Replace
  (`:set nocursorshape`), restored on exit; focus reports; `:set scrollbar` with click and drag; drag-select
  autoscroll with a speed ramp; the gutter only grows; the sign column is reserved while a language server runs; the
  picker's preview pane keeps its place.
- Tests: `tests/t_anim.m31` (scheduler, pacer, blends), `tests/anim_pty.py` (an animation never changes the final
  screen over 19 motion sequences, intermediate frames are consistent, kill switches), renderer golden-byte tests in tui.
- Engine: `replay_runs`, `yank_serial` and friends on the editor, for the front end only; new options.

## 0.7.0

Persistence, project settings and folds. The queue is in docs/ROADMAP.md.

- `undofile`: the undo tree is written to `~/.local/state/m3/undo/` on `:w` and read back when the file still holds
  the text it was saved for (a fingerprint of the buffer; a changed file drops the history). On by default in a normal
  run; `:set noundofile` in the keymap file turns it off. Own text format, tests/t_undofile.m31.
- `gq` and `gw` leave the `.` mark where nvim's format_lines does (corpus 107).
- `.editorconfig` (globs, indent_style, indent_size, tab_width, max_line_length, insert_final_newline,
  trim_trailing_whitespace) and `.m3.toml` (`[options]` and `[language.NAME]` tables of `:set` values) per buffer;
  new option `trimtrailing`. `end_of_line` and `charset` are read but not applied.
- Disk watch: an outside change to the unmodified active buffer is read again within a second (`autoread`),
  a modified one gets W12 once, a vanished file E211; `:checktime`. `autowriteall` writes modified buffers before
  `:e`, `:q` and closing, `autowrite` before CTRL-^; `autosave` N writes after N quiet seconds in Normal mode. `:e!`
  keeps the cursor line.
- Sessions: plain `m3` reopens the files the directory had at its last exit, with their cursors (`--no-session` and
  `-u NONE` start empty); `:Session save|load|delete|list NAME`. Window layout and tab pages are not restored yet.
- Folds: `foldmethod=indent` and `marker`, `foldlevel`, `foldminlines`, `foldnestmax`, `foldignore`, `foldmarker`,
  `zm zr zx zX`, `zR`/`zM` through `foldlevel`, `zc`/`za` turn `foldenable` on, `zj zk` and the new `[z ]z` as nvim's
  foldMoveTo, `{` and `}` skip closed folds, the cursor leaves a closed fold that ends the buffer. Corpus 108 (400
  cases against nvim); five marker cases with jump levels (`{{{3`) are in tests/oracles/pending.
  `zf zd zD zE` under indent and marker give an error instead of editing markers.

Known gaps and what is blocked: see the roadmap (snippets, linebreak, tab `:split`, m31git as a library).

## 0.5.0

Themes. The hard-wired mapping onto the terminal's 16 colours is gone; every colour the renderer draws now comes from a
theme, a Helix-format TOML file (`[palette]`, scope to style, `inherits`).

- Fourteen built-in themes compiled into the binary: `default` (a new dark theme, truecolor, transparent background),
  `default-light`, `term16-dark` / `term16-light` (the terminal's own 16 colours, used instead of the defaults on
  16-colour terminals), and the Helix ports of `tokyonight` (night), `nightfox`, `gruvbox-material` (dark, medium) and
  `-soft`, `gruvbox`, `catppuccin-mocha`, `onedark`, `nord`, `dracula`, `github-light`. Sources are `themes/*.toml`;
  `scripts/gen_themes.sh` embeds them in `ui/MED_theme_data.m31`.
- `:theme` (shows the current theme), `:theme NAME` and `:colorscheme NAME` switch at once; Tab completes names;
  `<Space>fC` is a picker that previews each theme as the selection moves and goes back on Esc; `--theme NAME`;
  `colorscheme NAME` in the startup file (`keymap.vim`). `:set background=light|dark` still moves between `default` and
  `default-light`. A bad theme is a message and the old theme stays.
- User themes: `~/.config/m3/themes/NAME.toml` (`$XDG_CONFIG_HOME`), shadowing or inheriting built-ins. All 154 themes
  of Helix 25.01 load.
- Scope lookup falls back by dotted prefix as in Helix, then through the names Helix themes do have for the scopes m3
  adds (`ui.statusline.visual`, `ui.which-key`, `ui.picker.*`, `search.match`, ...). All 25 `syntax` classes have a
  scope (`SYN_class.legacy`, the fold onto 12, is no longer used by the renderer). Statusline mode colours, git gutter,
  signs, which-key, picker, tab line, indent guides, cursor line, colour columns, selection, search, TODO highlight and
  the tree all go through scopes; a theme with `ui.background` paints the whole screen, one without leaves the
  terminal's background alone.
- Colours are written at the terminal's depth (truecolor, the 256 cube, or the nearest of 16).
- `m3 --dump-sample [--theme NAME] [--colors 16|256|true]` draws sample code in six languages, the theme picker and the
  which-key popup through the real renderer as ANSI text.
- `:source` now runs requests that a sourced file queues (`:theme` lines) before the next key.
- Tests: `tests/t_theme.m31` (parser, palettes, inheritance, fallback, depth, every built-in, user themes in a temporary
  XDG directory, bad themes, the commands, the picker, `--dump-sample`; it reads the renderer's source and fails when a
  built-in lacks a scope the renderer asks for), a pty scenario `themes` in `tests/e2e.py`.

Not done: underline colour and curl (the `tui` style has six attribute bits and no underline colour), blink and hidden
modifiers, diagnostic underlines in the text (only the sign column shows diagnostics), per-heading-level markdown
colours (the lexical highlighter has one heading class), a theme setting saved from the picker.

## 0.4.0

A round of queue items, each probed against nvim where the repo can.

- Tab pages: `:tabnew :tabedit :tabnext :tabprev :tabNext :tabfirst :tablast :tabclose :tabonly :tabmove :tabs`,
  `gt` / `gT`, `<C-w>T`, a tab line, a layout per page. `:q`, `:close` and `<C-w>c` on the last window of a page close
  the page.
- Command-line abbreviations (`:cabbrev :cnoreabbrev :cunabbrev :cabclear`); `:ab` is now Insert and command line;
  `:unabbreviate` arguments are not expanded; end-id and non-id left-hand sides are not recognised straight after
  punctuation (Insert mode too); `:ab` lists in nvim's format. Corpus 105.
- Windows follow nvim's frame model (see the README): halves, equalising after a split or close, 'winwidth',
  `:resize` and `<C-w> + - < > _ |` taking rows from the next windows first, terminal resizes shrinking the last
  window first, counts after `<C-w>`, `<C-w>x r R H J K L` as `win_exchange` / `win_rotate` / `win_totop`.
  `tests/oracles/oracle_windows.py` (115 cases plus random sequences) is part of `tests/test.sh`.
- LSP: signature help, inlay hints, `textDocument/didClose`; the scripted fake server grew the three methods.
- Marks, registers and macros, from a probe of 480 cases (corpus 106): `]'` `['` `` ]` `` `` [` ``, `]p [p ]P [P`,
  the expression register `"=` and `:put =`, `:let @A=`, `:let @"=`, the unnamed register reading register 0 before
  anything is written, the `.` mark and change list after put, join, linewise delete, shift, `:copy`, `:move`,
  `:s` over several lines, a character-wise multi-line delete, a block delete or insert and undo / redo (`g;` and
  `` `. `` land where nvim's do), the `<` and `>` marks after their lines are deleted, `E19` for a mark below the end.
- Git gutter: already in place (an in-repo diff against the index or HEAD blob; no `gitui` dependency needed); tests added
  for `]c` / `[c`, no repository and a 100000-line file.

- File-name completion sorts a directory by its name, not by the `/` after it (`next` before `next-2`).

Known gaps: text typed in one burst leaves `.` at its last character, nvim at its first (nvim's typeahead
batching); `gq` leaves `.` one line higher; resizing the only window, or a column that is the whole screen, does not
grow the command line as nvim does;
`:tab` as a modifier (`:tab split`), `:{N}tabnew` placement; inlay hints are drawn at the end of the line, not inline.

## 0.3.0

Chosen from probing the engine against nvim for gaps (a batch of 110 ad hoc daily-use cases; the failures became this
release) and from the 0.2.0 note that the renderer still folded the library's classes onto twelve.

- Insert-mode abbreviations (`:ab :iab :noreab :inoreab :unab :iunab :abc :iabc`), checked against nvim (corpus 104).
- `:let` variables (`g:` scope, `+= -= *= .=`) usable in `\=` and `:echo`; `\=` with a variable matched nvim.
- Richer highlighting: the renderer draws every class of the `syntax` library instead of folding onto twelve.
- `gw` keeps the cursor on blank text through a join and when nothing changes (it moved one column).
- A command that changes nothing (`x` on an empty line) no longer enters the change list or sets the `.` mark, so
  `g;` and `` `. `` match nvim.

Known gaps: abbreviations in the command line, non-id abbreviations expand only on `<Esc>`/`<CR>`/`CTRL-]`,
tab pages (`:tabnew`), `:ab` listing format, `gw` cursor after a re-wrap that moves it to another line.

## 0.2.0

Highlighting by the shared `syntax` library (see RENAMES.md).
