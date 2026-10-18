# Changelog

## Unreleased

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
