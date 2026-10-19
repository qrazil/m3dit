# medit design

`medit` (working codename, trivially renamable) is a terminal text editor with
Vim key bindings, written entirely in m31 on top of the `tui` library. It is an
IDE-lite: no toolbar, no menu chrome, keyboard first, discoverable through a
which-key popup, a command palette and `?`.

Goal for v0.1.0: at least as capable as Helix, with Vim bindings. Section 9
defines that concretely and says honestly which parts are impossible in m31
today.

Rules that shape everything below:

* Everything is written in m31. If m31 cannot do something, we stop and record
  a gap (section 11); we do not add Rust or work around it with a shell.
* nvim 0.11 is the oracle for the editing engine (section 7). Behaviour is
  whatever `nvim --headless -u NONE` does, defaults included.
* Naming follows the m31 naming decision. The project prefix is `MED_`.

## 1. What the user actually runs (plugin audit)

Read from `~/.vimrc` (vim-plug era), `~/.config/nvim/init.lua`,
`lua/config/keymaps.lua`, `lua/plugins/*.lua` and `lazy-lock.json`.

Core settings the editor must make default or one-line configurable: leader is
Space, 4-space expandtab, `number` + `relativenumber`, `ignorecase` +
`smartcase`, `scrolloff=8`, `nowrap`, `undofile`, `mouse=a`, `hlsearch` +
`incsearch`, `cursorline`, `signcolumn=yes`, `splitright`/`splitbelow`,
`clipboard=unnamedplus`. Keymaps in use: `jk` as Escape in insert mode,
`<leader>w` write, `<leader>z` close, `<leader>n` new file, `<leader>o` only,
`<leader>R` reload all buffers, `<leader>sv/sh/se/sc` split/balance/close,
`<leader>b` buffer manager, `<leader>e` explorer, `<leader>?` which-key,
`<leader>ha/he/hp/hn/1..n` harpoon, `<leader>h*` git hunks, `<leader>xx...`
trouble, `<leader>a` aerial, `<leader>ll`/`]]`/`[[` diagnostics.

### Decision table

Legend: **v0.1** = built in and required for the v0.1.0 tag. **later** = wanted,
after v0.1.0, with the reason it waits. **never** = out of scope, with the
reason. "Milestone" is the build phase that delivers it (M1 engine, M2 tui,
M3 picker; M4 is the stretch work between M3 and the tag).

| Plugin(s) | What the user does with it | Decision | Reasoning |
|---|---|---|---|
| fzf-lua, fzf.vim, mini.pick, mini.extra | files, live grep, buffers, git files, oldfiles, quickfix, git branches/commits | **v0.1** (M3): files, buffers, grep, oldfiles, command palette, jumplist. Branch/commit pickers later | This is the feature Helix is most loved for and the one the user reaches for most. The picker is one widget, reused by every list. Git pickers need the git library: later |
| mini.files, neo-tree, NERDTree | `<leader>e` explorer | **v0.1** (M4): directory picker with `-` to go up and a plain read-only directory buffer (`:Explore`). Editable (oil-style rename/delete by editing) later | Helix ships exactly a picker-based explorer. A persistent sidebar tree needs splits plus a tree view and buys little over the picker; the directory buffer gets all Vim motions for free |
| which-key (vim-which-key) | `<leader>?`, leader popup | **v0.1** (M3) | Core promise (no chrome, still discoverable). The tui crate already ships `TUI_menu.WhichKey` |
| nvim-autopairs, auto-pairs | insert-mode pairing | **v0.1** (M4), default on, one option to disable | Insert-mode only, small, and Helix has it on by default |
| comment (vim-commentary), Comment.nvim | `gc`, `gcc` | **v0.1** (M4): `gc{motion}`, `gcc`, visual `gc`; comment string chosen by file extension | Oracle-testable: nvim 0.11 has native `gc` |
| mini.surround, vim-surround | `<leader>sa/sd/sr/sf/sh`; `ys/ds/cs` | **v0.1** (M4): vim-surround keys `ys{motion}{char}`, `ds{char}`, `cs{old}{new}`, visual `S`; the user's `<leader>s*` aliases are keymap data on top | Helix has `ms/md/mr`; this is the Vim-shaped equivalent. Pure text transform on the engine, no new machinery |
| built-in marks + marks.nvim | named marks | **v0.1**: marks `a-z A-Z ' \` [ ] < >` are engine features (M1). Sign-column marks later | Marks are part of Vim grammar, oracle-testable |
| harpoon2 | pinned file list, `<leader>1..n` | **later** | Needs a persisted per-project list and a small menu; the buffer picker, `'A` global marks and the jumplist cover the need until then |
| buffer_manager | `<leader>b` | **v0.1** (M3): it is the buffer picker | Folded into the picker |
| splits (`<leader>s*`, `<C-w>`) | vsplit/split/balance/close/only | **v0.1** (M4): window tree with `:split`, `:vsplit`, `<C-w>hjkl`, close, only, equalise | The user's keymaps show splits are used daily, and Helix has them. The engine models `Window` (cursor, scroll, jumplist) separately from `Buffer` from day one so splits are a UI feature, not a redesign. Phases 0-3 render a single window |
| gitsigns, vim-gitgutter | gutter signs, hunk nav, stage/reset hunk, blame, `ih` | **v0.1** gutter signs and `]c`/`[c` (M4), via the stdlib `diff` module against the HEAD blob read through the gitui git modules. Stage/reset/undo hunk, blame, `ih` / `ah`, `:Git log|show|diff|blame`: **0.12.0** (ROADMAP items 12 to 14), in process over the pinned `m31git` library (`ui/MED_gitlib.m31`), with the `git` binary only as the fallback for a repository the library cannot read | Helix has a diff gutter, so the tag needs one. It depends on gitui's `GIT_*` modules as a dependency |
| fugitive, neogit, diffview, git-conflict | full git UI | **never** in medit | The user has gitui. `<leader>g` suspends medit and runs gitui through `os.run` (inherits the terminal): later |
| LSP: vim-lsp, nvim-lspconfig, mason, asyncomplete, blink.cmp, nvim-cmp, nvim-java, trouble, aerial | diagnostics, completion, goto, hover, rename, symbols | **later, blocked**: needs a child process with piped stdin/stdout. `os.run` only inherits stdio. Gap G1 | Not workable by shelling out through temp files without being a hack; per the rules this is a stop-and-report item |
| conform (rustfmt, ruff, stylua, prettier) | format on save | **later, blocked** by G1 for filters; running `rustfmt <file>` in place and reloading is possible with `os.run` alone but is deferred until G1 is decided | Same family as filters (`!`, `:r !`) |
| nvim-dap | debugger | **never** (v0.x) | Needs LSP-class process plumbing plus a UI; far outside IDE-lite |
| treesitter, vim-polyglot, markview, nvim-highlight-colors, colorizer | highlight, indent | **later**: a hand-written lexical highlighter (per-language token rules, no parse tree) for Rust, Python, C, Lua, m31, Markdown, JSON, shell. Tree-sitter itself is impossible (G3) | Gives colours without a parser runtime. Not v0.1.0-blocking, but listed in the Helix gap in section 9 |
| nvim-ufo, folds | `zR`, `zM`, folds | **later**: indent-based folds only | Needs fold state in the view layer; not core to editing correctness |
| todo-comments | highlight TODO | **later** (a highlighter rule) | Cosmetic |
| mini.move | move line/selection | **v0.1** (M4): `<M-j>`/`<M-k>` line move, visual too | Tiny, uses ordinary edits |
| mini.bracketed | `]b [b ]c ...` | **v0.1** for `]b [b` (buffers), `]c [c` (hunks), `]d [d` once diagnostics exist | Keymap data |
| editorconfig | indent/charset per file | **later** (v0.1.x) | Easy, but not needed to be capable |
| vim-repeat | `.` for plugins | **v0.1**, built in: every command goes through the dot-repeat recorder | The grammar design makes plugins a non-issue |
| incsearch / hlsearch | search UX | **v0.1** (M2/M3) | Built in |
| lualine, vim-airline | statusline | **v0.1** (M2): built-in statusline with mode, file, modified flag, position | Plain widget |
| themes (tokyonight, nightfox, gruvbox-material) | colours | **Done (0.5.0)**: theme as data in Helix's TOML format, 14 built-in (the owner's three included), user themes, `:theme`, picker with live preview (section 3) | Was a hard-wired 16-colour mapping in 0.1.0 to 0.4.0 |
| mini.indentscope, indent-blankline, indentLine | indent guides | **later** | Cosmetic |
| neoscroll | smooth scroll | **never** | Animation through a polling loop is the wrong trade |
| nvim-notify | popup notifications | **v0.1**: messages go to the command-line area; a `:messages` history | No popups |
| LuaSnip, ultisnips | snippets | **later** (static templates with tab stops) | Without LSP the snippet source is a file we would also ship |
| floaterm, `:terminal` | embedded shell | **never** (G4: no pty) | Cannot be built without a pty |
| vim-startify | start screen | **later**; `<leader>fo` oldfiles picker covers it | |
| markdown-preview | browser preview | **never** | Needs a browser and a server; out of IDE-lite |
| nvim-devicons | glyphs | **never** by default (font dependent); optional later | |
| no-neck-pain | centred layout | **never** | |
| Copilot, CopilotChat, codecompanion, avante, minuet, claude-code | AI | **never** inside the editor | Needs network + process plumbing and is not an editor concern. Claude Code runs in the neighbouring terminal pane |
| neotest | test runner | **never** (disabled in the user's config) | |

Everything marked **v0.1** has an owner phase. The ones that are not in the
three phases of this build (M1-M3) are the M4 list: splits, explorer,
surround, comment, autopairs, mini.move, git gutter. They are designed for now
(window model, command registry, keymap data) so they do not require rework.

## 2. Architecture

Flat layout like gitui: library modules at the repo root, `MED_` prefix on
library file names, a lowercase entry file `medit.m31`.

### 2.1 Layers

```
 term / tui          (from the tui dependency, not ours)
   |
 MED_view, MED_status, MED_picker_ui, MED_help     UI: draw state into TUI buffers
   |
 MED_editor                                        session: buffers, windows, mode machine
   |
 MED_command + MED_keymap                          named commands; keymaps as data
   |
 MED_operator, MED_motion, MED_textobj, MED_search, MED_ex     the Vim engine
   |
 MED_buffer, MED_edit, MED_undo, MED_register, MED_text, MED_key  text model
```

The bottom three layers import no terminal code. The engine is driven by one
function, `Editor.feed(key)`, plus accessors. That is also the whole oracle
harness API.

### 2.2 Text model

* **Buffer**: a `List<str>` of lines, no line terminators stored, plus
  `final_newline`/`line_ending` flags for load and save. The narrow interface
  is `line_count()`, `line(row)`, `text(range)` and one mutator,
  `splice(range, replacement) -> Edit`. Nothing outside `MED_buffer` indexes the
  list. A rope can replace it behind that interface if benchmarks demand it.
  Why a line array: m31 `str` is immutable UTF-8, `List.insert` is a memmove
  (spike: 1000 insert/remove pairs at the middle of a 100,000-line list is
  immeasurable), every Vim operation is line-oriented, and a rope in m31 would be
  a tree of refcounted nodes we would have to write and tune first.
  Known cost: editing one very long line is O(line length) per keystroke;
  benchmarks (section 8) will quantify.
* **Positions** are `(row, col)` with `col` a byte offset into the line, always
  on a grapheme cluster boundary. nvim reports byte columns, so oracle
  comparison needs no translation. Display columns exist only in the view and in
  `curswant`.
* **Grapheme awareness**: `MED_text` wraps `unicode.graphemes`/`unicode.width`
  with an ASCII fast path (a line whose bytes are all `< 0x80` never calls
  unicode). `l`, `h`, `x`, `~`, `r` etc. move by cluster; nvim 0.11 does too.
* **Edit** = `(start, removed_text, inserted_text)`; **Transaction** = ordered
  `List<Edit>` plus cursor before and after. A transaction is the unit of undo.
  Applying a transaction runs its edits in order; inverting it reverses the list
  and swaps removed/inserted. Positions in each edit are relative to the buffer
  at the moment that edit is applied (sequential semantics), which is simpler
  than Helix's offset ChangeSet and enough with a line array.
* **Undo tree**: nodes `{seq, parent, children, transaction, time}`; `u`/`<C-r>`
  walk parent / latest child; `g-`/`g+` walk by `seq` through the tree;
  `:earlier`/`:later` by count first, time later. One undo block per normal-mode
  command, per insert session (from `i`/`a`/`o`/`c...` to Escape), per `:s`, per
  `:g`, per macro-level undo exactly as nvim blocks them. `undofile` persistence
  is a later serialisation of the tree.
* **Registers**: `"` unnamed, `0`, `1-9` (shifting on large/linewise deletes
  exactly as Vim), `-` small delete, `a-z` and `A-Z` (append), `_` black hole,
  `/` last search, `:` last command, `.` last inserted text, `%` file name. Each
  value is `{text lines, kind: Char | Line | Block(width)}`. `+`/`*` map to the
  system clipboard through OSC 52 (write only, see G5).
* **Marks**: per-buffer `a-z`, `'`, `` ` ``, `[`, `]`, `<`, `>`, `.`, `^`, `"`;
  global `A-Z`. Marks track edits (adjusted by transactions).
* **Window**: `{buffer, cursor, curswant, scroll_top, scroll_left, jumplist,
  changelist, visual anchor/kind}`. Buffer ≠ window so splits are free later.

### 2.3 Commands and keymaps as data

Every action is a named command: `move.word_forward`, `op.delete`,
`edit.join_lines`, `mode.insert`, `file.write`, `picker.files`, ... A command has
a **kind**: `Motion`, `Operator`, `TextObject`, `Action`, `Ex`, `Insert`,
`Visual`, `Picker`, `Window`. The registry is a `Map<str, CommandId>` onto an
`enum CommandId`; a single exhaustive `match` in `MED_command` dispatches
(m31 has no function values and `match` works only on enums, so an enum with one
dispatch function gives compile-time exhaustiveness and no per-command type
boilerplate).

Keymaps are **data**: `MED_defaults` is a list of
`(mode, key notation, command name, args, description)` rows, e.g.
`("n", "gg", "move.file_start", "", "go to first line")`,
`("n", "<leader>ff", "picker.files", "", "find files")`. At start they are
compiled into one trie per mode. `description` feeds which-key and `?`. A user
keymap file can override rows. As built, the user layer is Vim's own: the file
is a list of ex lines (`~/.config/m3/keymap.vim`, or `$M3_KEYMAP`, or
`-u FILE`) using the `:map` / `:noremap` family for n, x, o, i and c modes,
`:unmap`, `:mapclear`, `let mapleader`, `<nowait>` and `:source`. The engine
resolves them (`MED_map`, `MED_ex.pump`) and the mapping behaviour is checked
against nvim (corpus 60 and 61). Limits: no `<buffer>` or `<expr>` maps
(E474), no select mode, mappings do not apply inside macros, dot repeat or
`:normal`, and a macro register holds the keys after mapping (nvim records the
typed keys). A user map starting with `<Space>` (or with `j` in Insert mode)
takes over from the front end's built-in leader menu (or `jk`).

Modes: `Normal`, `OperatorPending`, `Visual` (kind Char/Line/Block), `Insert`,
`Replace`, `Cmdline` (`:` `/` `?`), `Picker`, `Help`. Insert mode keymaps resolve
the longest-match with a timeout (`jk`), using the 250 ms-class tick in the
tui loop (configurable `timeoutlen`).

### 2.4 Vim grammar onto commands

Input arrives as keys (`int`: code point, control codes as themselves, special
keys in a private range, modifier bits above bit 24). The normal-mode machine
keeps a **pending key list** and after each key asks the parser:

```
command := ["x] [count] ( action
                        | operator [count] motion_or_object
                        | operator operator          (dd, yy, >>, gUU, g??)
                        | motion )
```

`parse(pending) -> Complete(Parsed) | NeedMore | Invalid`. Reparsing the pending
list on every key is stateless, obviously correct and cheap (pending lists are
at most a handful of keys). Operator-pending lookups use the OperatorPending
trie (motions and text objects); counts multiply (`2d3w` is 6 words). Forced
motion types `dv` `dV` `d<C-v>` are parsed there.

* **Motions** return a `MotionResult {target position, kind: Charwise | Linewise,
  inclusive, jump?}`; as plain cursor moves they set the cursor and `curswant`.
* **Text objects** return a range (start, end, kind) given count and
  inner/around.
* **Operators** take `(range, kind, register)`, build one Transaction, set cursor
  and registers. The special cases (`cw` acts like `ce`, `dw` at end of line, the
  `d` linewise-promotion rule for multi-line exclusive motions) are implemented
  where Vim implements them and are what the oracle exists to check.
* **Comment toggle** `gc` is an ordinary operator (`gcc`, `gcip`, visual `gc`) that
  follows Neovim 0.11's `vim._comment`: the leader goes at the minimum indent, blank
  lines get the bare leader, and a range is uncommented only if every non-blank line
  is commented. `commentstring` is a string option, set per file type by the app.
* **Count** is carried as `Option<int>`; `.` substitutes a new count for the
  original one as Vim does.
* **Dot repeat**: the editor records the full key list of the last *change*
  (prefix, register, operator, motion/object, and for insert-starting changes all
  typed keys through Escape). `.` replays that list with the count replaced. This
  is also why autopairs/surround/comment need nothing special: they are ordinary
  key sequences. Replay is guarded against recursion.
* **Macros**: `q{reg}` appends typed keys to a recording; stopping stores them in
  the register as text (special keys as private-range code points), `@{reg}`/`@@`
  feeds them through `feed` with the count, aborting the rest of a macro on the
  first failing motion or search as Vim does.
* **Visual modes**: anchor + cursor in the window; `v`, `V`, `<C-v>`, `o`, `O`,
  `gv`, `$` in block mode, then operator keys applied immediately to
  `'<,'>`-style ranges, `I`/`A`/`c` block insert replicating to every line.
* **Ex**: `:` parses a command line (`range`, `command`, `bang`, `args`) for
  `:s`, `:g`/`:v`, `:d`, `:y`, `:m`, `:t`, `:>`/`:<`, `:j`, `:normal`, `:w`, `:q`,
  `:wq`, `:x`, `:e`, `:b`, `:set`, `:noh`, `:sp`/`:vsp`, `:!` (inherit-terminal
  run only). Regex: Vim regex are translated (magic, `\v`, `\<`/`\>`, `\{n,m}`,
  `\zs` ...) onto the stdlib `regex` module (Pike VM, no backreferences or
  lookaround). Gaps against Vim regex are listed in the known divergences
  (section 7).

## 3. Rendering

`MED_view` is a `TUI_widget.Widget`. It draws the text window, line numbers
(absolute, relative, hybrid), signs column, cursorline, visual selection,
search highlights, statusline, and the command/message line into a
`TUI_buffer.Buffer`; `TUI_diff` does the minimal-update. Cells are graphemes
(wide characters take two). Tabs expand with `tabstop`. `nowrap` + horizontal
scroll is the default (the user's setting); soft wrap is later.

**Colour (0.5.0).** Nothing in the renderer names a colour. `ui/MED_theme.m31` parses Helix-format themes
(`[palette]`, `"scope" = { fg, bg, underline, modifiers }`, `inherits`; only the TOML subset that needs: strings,
arrays, inline tables, `#` comments) and answers `theme.look(scope)`: the scope's style laid over a base of
`ui.background` and `ui.text`, so a theme without `ui.background` stays transparent and one with it paints every cell
(`App.render` fills the screen with the base first, and every style the renderer builds already carries it, so no
post-pass over the buffer is needed). Lookup tries the scope, the names Helix themes use for the scopes m3 adds
(`FALLBACKS`), then dotted prefixes. The 25 `SYN_class` values map to scopes in `CLASS_SCOPES` (PROPERTY and MEMBER
share `variable.other.member`); per-class styles and their cursor-line / colour-column variants are precomputed when a
theme loads, so drawing a byte costs two list indexings. Colours are `TUI_style.Colour.Rgb` / `Indexed` and `tui`
writes them at the terminal's depth (truecolor, the 256 cube, nearest of 16); on a 16-colour terminal `default` is
swapped for `term16-dark` / `term16-light`, which use ANSI names only. The built-in themes are `themes/*.toml`,
embedded as string lists in `ui/MED_theme_data.m31` by `scripts/gen_themes.sh` (m31 has no multi-line literals and no
runtime file may be needed). `MED_theme` sits in `ui/` because it imports `TUI_style`; the engine only gets theme
names for completion (`Editor.theme_names`).

The loop is the tui `Loop` pattern (read with timeout, `Action.Redraw`), with the
gitui-style idle `Ticker` for timeouts (`jk`), message expiry and picker results
streaming in. Resize is detected by polling `term.size()` each tick (there is no
SIGWINCH, G2).

### 3.1 Frames

One pass of the loop: wait for input (or the next tick), handle every event that has
already arrived (up to a budget, with one event of look-ahead so a callback can ask
`Loop.is_input_queued`), give the ticker its turn, then draw **once**. The frame is the
view rendered into a cell buffer, diffed against the previous one (`TUI_diff`), and written
as one `write()`:

* `CSI ? 2026 h` ... `l` around it when the terminal answered the DECRQM question
  (`CSI ? 2026 $ p`, sent at start-up, the reply consumed by the loop); a terminal that does
  not answer gets plain frames. No clear-screen, ever; a resize writes every cell over the old
  ones inside one synchronized frame.
* A view that scrolled by a few lines: `diff_scrolled` finds a vertical shift (candidate shifts
  from three anchor rows, counted over the changed rows) and emits a scroll region
  (`CSI t;b r`, line feeds on the last row or reverse indices on the first, `CSI r`), then diffs
  against the picture of the screen the scroll leaves. It only matches whole identical rows, so
  splits and sidebars that did not move fall back to the plain diff with no special casing.
  Plain `LF`/`RI` rather than `CSI S`/`T` because every terminal, screen and tmux has them.
* The terminal's own cursor is hidden while a frame is drawn and shown afterwards only when the
  view asked (`Loop.cursor`: position and DECSCUSR shape); the editor draws a block cell for
  Normal and Visual and uses the real cursor, shaped, for Insert, Replace and the command line.

### 3.2 Motion (`ui/MED_anim.m31`, `ui/MED_glide.m31`)

The rule: an animation is a path to a state the engine already computed. `MED_view.update` still
settles `view_top` as it always did; `MED_glide.shift` is called right after it while the active
window is drawn and, when the top moved by two or more lines, draws from an intermediate top
(restoring the engine's value before the status line and input handling see it). So
macros, tests and `M3_NO_ANIM` follow the same code with the same result, and the last frame is
the engine's.

* `Scroll` (pure, given a clock): each frame closes `1 - exp(-dt/tau)` of the remaining distance
  (`tau` from `animatetime`), which is frame-rate independent and needs no restart when the goal
  moves (wheel bursts, repeated `<C-d>`); a hard cap lands it exactly; a jump of more than a
  screen and a quarter starts a screen and a quarter away. Frames are the monotonic clock's
  (`timer.monotonic_ns`), never counted.
* The cursor row drawn is the engine's row clamped into the window with `scrolloff` (`clamp_row`).
* Not animated: a one-line move; a different window or buffer; a text change since the last frame;
  a frame after a macro, `.`, `:normal` or `:g` (the engine counts replays); while input is queued;
  while unfocused; when `Pacer` says the terminal is too slow (smoothed frame time: 16 ms ticks
  under 8 ms, 33 under 16, 66 under 30, none above).
* Ticks: `Loop.animate_ms` is read each pass and set by the front end: 16 ms (or the pacer's) while
  something moves, 50 ms while the editor is in use or has timers, 250 ms after 1.5 s of quiet.
* Effects over the finished frame: the yank flash (`engine.yank_serial`; a blend of the cell's own
  background in gamma-2 space, a reverse flash without truecolor) and the popup fade (`fade_in`
  against a copy of the frame as it was before the popup, only cells the popup changed).

## 4. Picker

One `Picker` widget serves files, buffers, grep, oldfiles, jumplist, commands
(palette), help topics, explorer. It is: a prompt line, a list (`TUI_list_table`
`ListView`), a preview pane (file head or grep context), and a source that
produces items asynchronously.

* **Sources** run in a `spawn`ed green thread and push batches over a channel;
  the loop drains it each tick, so a 100k-file walk never blocks input.
* **Files**: `fs.walk` from the project root (nearest ancestor with `.git`, else
  cwd) honouring `.gitignore`, `.git/info/exclude` and a hidden-file toggle
  (`<C-h>`), `<C-i>` toggles ignore (the user's fzf-lua `ctrl-i`). The gitui
  `GIT_ignore` matcher is the reference for the rules.
* **Grep** ("ripgrep-like, in m31"): walk with the same ignore rules, skip files
  that contain NUL in their first 8 KiB, split into lines, match either with a
  literal search (`str.index_of` after smart-case folding, the fast path when the
  query has no regex metacharacters) or with `regex.compile` (fixed-string toggle
  `<C-f>`). Each file is searched in its own task; results stream as
  `path:line:col:text`. `<C-q>` sends all to a quickfix-style list. A literal
  scan over a few hundred MB is memory-bandwidth bound in this runtime; the
  benchmark plan includes it against `rg` honestly.
* **File ranking** (0.10.0): paths are ranked by what the query is to the file name before the score below
  matters (exact name, stem, prefix, run, tight subsequence, path subsequence, scattered), with a relevance
  percentage and a frecency boost that cannot cross a tier; see `docs/FINDER.md`. The generic scorer below stays
  what grep, symbols and the palette use, and what highlights.
* **Fuzzy scoring** (the scorer is a pure module, `MED_fuzzy`): an fzf-v2
  style Smith-Waterman-like dynamic program, chosen because it is the algorithm
  users already have intuition for (fzf, fzf-lua, Helix's nucleo are all this
  family) and it is well specified:
  1. Smart-case (case-insensitive unless the query has an uppercase letter),
     ASCII fold fast path, Unicode fold for the rest.
  2. Subsequence prefilter: cheap `O(n)` reject (the vast majority of items).
  3. For survivors, a DP over `query × candidate` filling a best-score matrix
     with: match `+16`; consecutive matches `+4` (carry); boundary bonus `+8` after
     `/`, `+7` after `_ - . space`, `+7` camelCase lower→upper, `+8` first char
     of the string; first query char bonus ×2; gap open `-3`, gap extend `-1`.
     Backtrack for highlight positions only for the visible rows.
  4. Extended syntax: space-separated terms are ANDed; `^abc` prefix; `abc$`
     suffix; `'abc` exact substring; `!abc` negation.
  5. Ranking: score desc, then shorter candidate, then earlier match start, then
     original order (the stdlib `sort` is stable).
  Incremental: extending the query rescans only the previous survivors.
  Scoring runs in chunks (e.g. 4k items per tick) so typing stays responsive on
  large sets; the list always shows the best results found so far.
* **Palette**: `:` with an empty line or `<leader>:` opens the command picker
  over the registry (name + description + bound keys).
* `?` opens a searchable keymap help (same data), which-key shows the next-key
  popup after the leader (or any prefix) times out.

## 5. File explorer

Decision: **no persistent sidebar**. `<leader>e` opens a picker rooted at the
directory of the current file (directories first, `-` goes up, Enter opens or
descends, `<C-d>` shows hidden files). `:Explore` opens a directory as a normal
read-only buffer (netrw-lite) so `j/k//`, `gg` etc. work. Editable rename/delete
(oil / mini.files style) is a later feature built on the same buffer plus a
diff-the-listing-on-write step.

## 6. Module list (v0.1)

The tree is grouped (m3 0.0.x, see RENAMES.md): `engine/` is the editing core with no
terminal dependency, `ui/` is everything that draws, picks or lays out; `m3.m31` is the entry
at the root. Modules are imported by path (`import engine.MED_buffer;`); names keep the `MED_`
prefix. The rows below are the original plan, including modules not written yet.

```
engine/MED_key.m31  key codes, notation <Esc> <C-v> <leader> <CR> <Tab> ...
engine/MED_text.m31  cluster boundaries, widths, word/WORD/blank classes
engine/MED_buffer.m31  line array, splice, load/save, line endings
MED_edit.m31       Edit, Transaction, apply/invert
MED_undo.m31       undo tree
engine/MED_register.m31  register file
engine/MED_motion.m31  w b e ge W B E gE 0 ^ $ g_ | f F t T ; , % ( ) { } H M L gg G ...
engine/MED_textobj.m31  iw aw iW aW is as ip ap i( a( i[ i{ i< i" i' i` it at ...
MED_operator.m31   d c y > < = gu gU g~ g? gq J gJ ~ r ...
engine/MED_search.m31  / ? n N * # g* g#, Vim-regex translation
engine/MED_nrfmt.m31  <C-a> <C-x> g<C-a> g<C-x>: decimal/0x/0b numbers (64-bit signed; Vim's are unsigned 64-bit, so a decimal of 2^63 or more is left alone)
engine/MED_ex.m31  ex-command parser and executor: ranges (patterns, marks, offsets, `;`), `:s` (flags, `&&`, `~`, `\r`, `\u`/`\U`/`\e`, multi-line patterns), `:g`/`:v`, `:d :y :pu :m :t/:co :j :> :< :k :normal :undo :redo :earlier :later :sort :z :registers`, `:set` of the supported options, `|` chains, `@:` and cmdline history (Up/Down); an ex line is one undo block. `:earlier Nf` / `:later Nf` follow file writes (the editor records the undo node of every write in `saved_nodes`). A whole `@a` (with a count) is one undo block. Insert-mode `<C-o>` runs one Normal command and restarts the insert (cursor, `Insstart` and `<C-w>`/`<C-u>` limits follow nvim; `:normal` keeps the pending restart). `{Visual}@a` is `:'<,'>normal @a` for linewise Visual and runs inside Visual for `v`/`<C-v>`. Not supported: the command-line window (`q:`, `q/`), `.` repeating directly after an insert `<C-o>` (nvim replays the half-finished insert in an order we do not model), `<C-o>` combined with `.`/`g;`/`` `. `` marks (those need the changelist), the nvim K_SPECIAL artifact that a macro recorded with `r`/`f`/`t` + a char picks up when more commands follow, `:s///c`, `\=` replacement expressions, `:!`, `:r`, `:a`/`:i`/`:c`, time-based `:earlier 10s`, an operator followed by `:` (`d:cmd<CR>`), the `.`/`(`/`)` marks, jumplist/changelist. Corpus 52 keeps only the insert-`<C-o>` cases that match nvim; the rest (a column off by one after a `<C-o>` motion from an `A` insert at the end of a line, a block insert inside `<C-o>`, the ``` `` ``` mark, registers or `@a` inside `<C-o>`) are known gaps. `:sort` and `:z` match nvim for the cursor, not the printed text
ui/MED_keymap.m31  leader table (rows: keys, label, action), prefix/leaf lookup, which-key timeout
MED_command.m31    command registry and dispatch
engine/MED_editor.m31  modes, pending keys, dot, macros, jumplist
ui/MED_fuzzy.m31  scorer: smart-case, fzf-style DP, extended syntax (^ $ ' !), highlight positions; tests/t_fuzzy.m31
ui/MED_ignore.m31  .gitignore / .git/info/exclude matcher; tests/t_ignore.m31
ui/MED_files.m31  project root, file walk with ignore and hidden toggles, directory listing
ui/MED_grep.m31  corpus + search (literal fast path, regex, smart-case); tests/t_grep.m31
ui/MED_picker.m31  picker state machine (prompt, ranking, selection, keys); tests/t_picker.m31
ui/MED_picker_view.m31  picker drawing: list, highlights, preview pane
ui/MED_window.m31  window layout tree with nvim's frame sizes (win_split_ins, win_equal, frame_setheight / width, frame_new_height / width, win_exchange / win_rotate / win_totop), placement into screen rectangles, directional neighbours, the tab page record; tests/t_window.m31, tests/oracles/oracle_windows.py
engine/MED_view.m31  drawing
ui/MED_window.m31  window layout tree with nvim's frame sizes (win_split_ins, win_equal, frame_setheight / width, frame_new_height / width, win_exchange / win_rotate / win_totop), placement into screen rectangles, directional neighbours, the tab page record; tests/t_window.m31, tests/oracles/oracle_windows.py
MED_help.m31       ? and which-key content from keymap data
m3.m31        entry: args, terminal check, tui loop
ui/MED_app.m31  front end (v0.5.0 tui): key translation, render, buffers (:e :ls :b :bn :bp :bd, CTRL-^, `:wa`), mouse (press, drag, wheel), :w/:q, ZZ; tests/t_app.m31
```

## 7. Oracle test plan

Oracle: `nvim --headless -u NONE -i NONE -n -l <driver.lua>`; the driver sets the
buffer lines and cursor, runs `nvim_feedkeys(keys, 'xt', false)` (`x` executes
until the typeahead is empty and ends a pending Insert as if Escape were
typed), then writes JSON: lines, cursor (1-based row, 0-based byte col), mode,
registers `" 0-9 - a-z / : . %` (text + type), marks, the undo sequence number,
and `v:errmsg`. One nvim process per case (about 40 ms) run in a thread pool, so
no state (registers, last search, `.`, jumplist) can leak between cases. nvim's
defaults are part of the contract: `autoindent`, `nostartofline`,
`nojoinspaces`, `shiftwidth=8`, `tabstop=8`, `noexpandtab`, `whichwrap=b,s`,
`iskeyword=@,48-57,_,192-255`, `backspace=indent,eol,nostop`,
`nrformats=bin,hex`, `wrapscan`, `matchpairs=(:),{:},[:]`.

The m31 side is `tests/t_oracle_run.m31`: reads a case file (one case per line
of escaped fields), builds an `Editor`, feeds the key notation, prints the same
fields. Python (`tests/oracles/oracle_nvim.py`) owns case generation, the nvim
run, the m31 run and the comparison, so neither side compares itself with itself.

Compared per case: buffer text, cursor, mode, every register's text and type,
and (corpus level, phase 1.5) marks and undo position. Cursor is compared as byte
column; `curswant` is compared where nvim exposes it (`winsaveview().curswant`).

Layers of cases:

1. **Hand corpus** (`tests/oracles/corpus/*.txt`): grouped by feature
   (motions, operators, text objects, registers, counts, dot, undo/redo, visual,
   ex, search, unicode), every case a `name | text | keys` row. It grows with
   every bug found.
2. **Fuzzer**: deterministic (`--seed N`, `--cases M`); a grammar-aware
   generator picks small texts (1-5 lines from an alphabet of ASCII words,
   punctuation, tabs, blanks, empty lines, and Unicode: accents with combining
   marks, CJK wide characters, emoji ZWJ sequences, RTL), then 1-8 commands from
   the supported feature set (counts, registers, operators with motions and
   objects, visual selections, `u`/`<C-r>`/`.`/macros, `:s` with a
   small pattern set). Only commands the engine claims to support are generated;
   the feature set widens as the engine does.
3. **Shrinker**: on a mismatch, drop keys and text lines while the mismatch
   persists, and print the minimal repro as a corpus row.
4. **Known divergences**: `tests/oracles/known_divergences.txt`, each row names a
   case (or fuzz seed + index), the reason and the nvim behaviour. A listed
   divergence is reported but does not fail; an unlisted one fails; a listed one
   that now matches also fails (stale entry), so the list cannot rot.

The shell side (`tests/test_engine.sh`, sourced by `tests/test.sh`) prints
`N cases, M matched, K known divergences, F failed`.

Also: pure unit tests (`t_*.m31`) for text, keys, fuzzy, undo, and `fmt --check`.

## 8. Benchmark plan (against nvim and hx)

Harness `bench/bench.py` drives each editor in a real pty (python `pty`), with a
scripted key stream and a sentinel to find completion, so all three are measured
the same way. Fixtures are generated deterministically (seeded): 1k-line, 100k-line
and 1M-line source-like files, one 20 MB single-line file, and a large git repo
checkout for the picker.

| Measurement | How | Compared |
|---|---|---|
| startup | spawn → first full frame bytes, 20 runs, median/p95 | nvim `-u NONE`, hx, medit |
| open large file | spawn with 1M-line file → first frame; peak RSS (`VmHWM`) | all |
| search | `/needle<CR>` (rare and common) on 1M lines, time to cursor placed (sentinel `:echo`-equivalent) | nvim, hx (`/`) |
| replace-all | `:%s/a/b/g` on 1M lines (hx has no direct equivalent: `s` + `r`; reported separately) | nvim, medit |
| scroll / redraw | hold `<C-d>`/`<C-f>` 2000 times with a 200 col × 60 row pty; bytes emitted and wall time | all |
| typing | 10k inserted characters in one line and in a 100k-line file | all |
| memory | RSS after load and after 1000 edits with undo history | all |
| picker | files over a 100k-file tree: time to first result, time to settle after each keystroke; fzf as a reference | nvim+fzf-lua if present, hx, medit |

Results go in the benchmark repo (not here); this repo holds the harness. No
numbers are claimed before they are measured. Expectation recorded up front so it
can be checked: medit will lose on large-file load and single-line edits (refcounted
`str` lines, no rope) and should be competitive on small files and the picker.

## 9. v0.1.0 acceptance: "at least as capable as Helix, with Vim bindings"

Helix 25.01 feature inventory and the v0.1.0 verdict. **Yes** = in the tag,
**Partial** = in the tag but narrower, **Later** = after the tag, **Impossible**
= cannot be built in m31 today.

| Helix feature | v0.1.0 | Note |
|---|---|---|
| Modal editing, motions, text objects, counts, registers, macros | Yes | Vim grammar, oracle-tested against nvim |
| Undo tree (`u`, `U`, earlier/later) | Yes | Undo tree with `g-`/`g+`; Vim `u`/`<C-r>` |
| Multiple selections / multi-cursor | **Partial** | Not Helix's selection-first model. Covered by visual block `I`/`A`/`c`, `:s`, `:g`, `:normal`, macros and dot repeat, and (later) `gn`/`cgn` |
| Fuzzy file picker, buffer picker, global search, jumplist picker, last picker | Yes | M3 |
| Command palette | Yes | M3 |
| File explorer | Yes | A neo-tree style sidebar (`<Space>e`, `:Neotree`: expand/collapse, add/delete/rename/copy/move/paste, filter, git status letters, follow current file), the picker explorer (`<Space>fe`) and a netrw-style directory buffer (`:Explore`, `:e dir`) |
| Which-key style popups for prefixes | Yes | M3 |
| Splits | Yes | M4 |
| Buffers (list, switch, close) | Yes | |
| Git diff gutter | Yes | M4, HEAD vs buffer, `]c` `[c` |
| Auto pairs, comment toggle, surround | Yes | M4 |
| Mouse (click, scroll, drag-select) | Partial | Click/scroll first; drag-select later |
| Clipboard | Yes | `"+` `"*` and `clipboard=unnamedplus` through pbcopy / pbpaste, wl-clipboard, xclip or xsel (spawned through `sh` with a file in between: no pipes needed); without a tool the registers are the unnamed one, as in nvim |
| Themes | **Yes** (0.5.0) | Helix-format TOML themes with `[palette]`, `inherits` and dotted scope fallback; 14 built in, user themes in `~/.config/m3/themes`, `:theme` / `:colorscheme`, picker with live preview, truecolor / 256 / 16-colour output. Gaps: no underline colour or curl (the `tui` style has no bits for them), no blink / hidden, no diagnostic underlines in the text, one markdown heading class (no `markup.heading.N`), no theme saved from the picker |
| Syntax highlighting | **Partial** | The shared `syntax` library (lexical, no parse tree; 77 languages, see section 14); `:syntax on/off`, `:set syntax=`. Multi-line comments, strings and code fences carry across lines |
| Tree-sitter textobjects (`maf`, `mic`), indentation, selection expansion | **Impossible** (G3) | No tree-sitter runtime in m31 and the rule forbids Rust/FFI work |
| LSP: diagnostics, completion, hover, goto, rename, code actions, signature help, inlay hints | **Partial** (0.1.0) | Section 13: diagnostics, hover, definition, references, rename, code action, format over `proc` pipes, tested with real servers. Completion is a picker on CTRL-Space (section 13); no signature help or inlay hints |
| Formatting via external formatter, shell pipe (`!`, `\|`, `:pipe`), `:sh`-capture, `:r !cmd` | **Yes** (0.1.0) | `:!cmd`, `:{range}!cmd`, `:r !cmd`, `!{motion}` through `proc.run`; nvim oracle corpus 103. `:!cmd` captures output (no tty): use `:terminal` for interactive programs |
| Debug adapter (DAP) | **Later** | The pipes exist now; the UI does not |
| Embedded terminal | **Partial** (0.1.0) | `:terminal` over `proc.start_pty`; a line-oriented screen model (`ui/MED_vt.m31`), not a full VT emulator |
| Soft wrap, rulers, indent guides, whitespace rendering | Partial | Soft wrap (with nvim's scrolling), `list` + `listchars`, `number`, `relativenumber`, `colorcolumn`, `cursorline`, `cursorcolumn`, `scrolloff`, `sidescroll(off)` and `nowrap` scrolling, indent guides (0.1.0, `:set noindentguides`), `linebreak`, `breakat`, `showbreak`, `breakindent` and `breakindentopt` (`shift`, `min`, `sbr`; `list` is not done) done |
| Snippets | **Done** (0.8.0) | `engine/MED_snippet.m31` (grammar, expansion, transforms, tabstop ranges with extmark gravity), `engine/MED_snipops.m31` (session on an Editor), Select mode in `MED_vim`; user snippets in `snippets.json`; LSP snippet completions use it. Checked against nvim's `vim.snippet` where that can parse the snippet |
| Auto-reload on external change, auto-save | Partial | Poll `fs.stat` mtimes on idle tick; auto-save later |
| Persistent undo, session restore | Yes (0.7.0) | Undo files under the state directory, buffers and cursors of a project restored, and (next release) the tab pages and window layout |
| Increment/decrement (`<C-a>`/`<C-x>`) | Yes | Engine feature, oracle-tested |
| Search (`/`, `?`, `*`, `#`), `:s`, `:g` | Yes | Vim regex with backreferences and lookaround (engine/MED_regex.m31) |
| Config file | Yes (minimal) | `~/.config/m3/keymap.vim`: `:map` family, `let mapleader`, `:set`; no scripting |
| Command-line completion and history | Yes | Tab / Shift-Tab complete ex commands (nvim's own list and order), option names (long and short), files, directories and buffers; `<Up>`/`<Down>` history with prefix, `<C-p>`/`<C-n>` |
| Folds | Partial | Manual, indent and marker methods (marker jump levels as nvim builds them), foldlevel, foldlevelstart, zm zr zx; no expr or syntax methods |

Honest summary: with Vim bindings, medit can match or exceed Helix on
editing, navigation, picker and window features. It cannot match Helix on the
three things built on external-process or parser infrastructure: LSP, tree-sitter
and shell pipes, and it will not until the runtime supplies process pipes and
(for tree-sitter) a parser strategy. A v0.1.0 that omits those is "capable
as Helix without its language intelligence", and the tag description must say so.

## 10. Milestones

The queue after 0.4.x (0.7.0 to 1.0.0, the 1.0 acceptance bar, what is never in scope and the decisions that need the
owner) is in [docs/ROADMAP.md](docs/ROADMAP.md).

* M0 (this commit): design and scaffolding.
* M1: engine + oracle harness + fuzzer, with a stated divergence list.
* M2 (started: `m3 <file>` opens, renders with gutter and status line, edits, `:w`, `:q`, `ZZ`; build with `scripts/build.sh`): tui integration: render, scroll, numbers, statusline, command line, insert
  entry, open/save, grapheme width.
* M3 (done): pickers (files, buffers, grep, commands, help, explorer), which-key, keymap help.
  Deviations from section 4: sources run synchronously on the loop (the file list
  and grep corpus are cached; grep is debounced 120 ms by the ticker), not on a
  spawned thread; `?` stays Vim's backward search, so the keymap help is
  `<Space>?` / `:help`; Space is the leader in Normal mode (it no longer moves
  right); which-key only exists for the leader, not for `g`/`z`; no `<C-q>`
  quickfix list yet; the buffers picker is in buffer order, not MRU. There is no
  nvim oracle for buffers and pickers, so they are covered by unit tests and
  manual runs only.
* M4 (in progress): splits are done (`:split :vsplit :new :vnew :close :only :wincmd`, `<C-w>` s v n c q o w W p t b h j k l, `<Space>sv/sh/se/sc/o/n`, mouse click focuses a window). Window sizes: see the 0.4.0 window model (nvim's frame sizes, equalising after a split or close, `:resize`, `<C-w> + - < > _ | =`, `H J K L r R x T`, counts); each has its own status line and shows its own cursor and view of a shared buffer; closing a window keeps its buffer loaded (hidden), so `:q` of a modified buffer in a window never prompts, and E162 reports it at the final quit. Edits made through one window do not move the cursor of another window on the same buffer (it is only clamped). Tab pages arrived in 0.4.0 (`:tabnew` and friends, `gt` / `gT`, `<C-w>T`): a page is a window list, a layout and the active window.
* M4 explorer: done. `<Space>e` / `<Space>fe` is the picker explorer (`-` up on an empty prompt). `:Explore [dir]`, `:Sexplore`, `:Vexplore` and `:e dir` open a read-only directory buffer (`../`, folders, files; cursor on the file we came from): Enter opens the entry (the listing buffer is dropped when a file replaces it), `-` goes up, and any edit is undone at once by re-reading the directory with Vim's E21; `:w` gives E382. Not done: netrw's rename/delete/create keys, `gh` hidden toggle (dotfiles are always shown, `.git` never). In every picker CTRL-S / CTRL-V accept a file, buffer or grep hit into a new window below / beside.
* M4 keymap file: done. `:map` family (see 2.3), `:source`, startup file, `-u`.
* M4 (done): git gutter (`MED_git`, signs and `]c` `[c`, HEAD read through `git show`, diff by LCS
  with a size limit), surround (`MED_surround`, a port of surround.vim run on the engine and checked against
  the plugin: corpora 88 to 90), auto pairs (`MED_autopair`, a port of auto-pairs 2.0.0's decisions, corpora
  91 and 92), marks UI (sign letters, `:marks`, `:registers`, `:jumps`, `:changes`, `<Space>fm`), system
  clipboard (`MED_clip`), `:resize` and the `<C-w>` size and move keys, soft wrap with nvim's scrolling
  rules (corpus 87), `bench/bench.py`. The oracle runner knows which vim plugins a case names; the
  corpora that need a plugin are skipped where the plugin is missing (CI), so `tests/t_surround.m31`
  and `tests/t_git.m31` hold the checks that run everywhere.
* Known divergences from nvim after M4 (see `tests/oracles/known_divergences.txt` and `pending/`): manual
  folds; the command-line window; `=` is a reduced C indenter (it matters for the line a closing bracket
  gets after `<CR>` between a pair); `:s///c` inside `:g`; `CTRL-D` with the cursor on a tall wrapped
  line; the `.` register after `<BS>` runs into the buffer start in Replace mode; insert-mode
  completion is keyword completion (`CTRL-N`, `CTRL-P`, `CTRL-X CTRL-N`, `CTRL-X CTRL-P`) only;
  options that only store a value ('foldmethod', 'spell', 'smoothscroll', 'cindent' ...).

* 0.1.0 (default plugins, this branch): the plugin framework and keymap table (section 12), fuzzy finder sources over
  `proc` streams (files, grep, recent, lines, quickfix, options, symbols, todos, git branches / commits / changed),
  git hunk stage / reset / preview / blame, statusline and bufferline, harpoon, bracketed pairs, Alt-hjkl move, label
  jump, indent guides, TODO highlighting, position restore, `:!` / `:r !` / `!` filters (oracle corpus 103), terminal
  pane and a minimal LSP client (section 13). Skipped on purpose: undo files, a full terminal emulator, LSP completion,
  third-party plugins (no process boundary yet), `<Space><Space>` as jump (it stays find-files; jump is `<Space>j`).
  Deviations from section 4: picker sources run on the tick (a child process read with an expired deadline), not on
  spawned green threads, because m31 has no non-blocking channel receive; scoring is still the section 4 scorer.

## 11. m31 gaps (stop-and-report items, not worked around)

| # | Gap | Effect |
|---|---|---|
| G1 | **Resolved in m31 0.4.3** (`proc`: pipes, `run`, `start`). Was: `os.run` inherits stdio | LSP, filters, `:r !cmd` and the finder's rg / fd / git streams are built on it (0.1.0) |
| G2 | No SIGWINCH / signals | Resize is polled each tick (works; slightly delayed) |
| G3 | No tree-sitter or foreign-library binding | No parse-tree features |
| G4 | **Resolved in m31 0.4.3** (`proc.start_pty`) | `:terminal` (0.1.0) |
| G5 | No clipboard read, no process pipe to `wl-copy`/`xclip` | OSC 52 yank only |
| G6 | The stdlib `regex` has no backreferences/lookaround, `\d \w \s` ASCII-only | Not an effect any more: `engine/MED_regex.m31` is the editor's own backtracking Vim regex engine (`\1`, `\@=`, `\zs`, multi-line) |
| G7 | `str` immutable, no function values, `match` only on enums | Design choices above (line array, enum dispatch); not blockers |
| G8 | **Miscompile** (m31c 0.3.3 `--emit-c`, -O2): when both arms of an `if`/`else` start with the same assignment, that assignment is dropped. Repro: `int b(int x, bool open) { int i = x; int f = 0; if (open) { f = i; i = 1; } else { f = i; i = 2; } return f * 1000 + i; } print(b(40, true).to_str());` prints `1`, expected `40001` | Worked around by hoisting the shared assignment above the `if` (MED_search.findmatch). Needs a compiler fix |

## 12. Built-in plugins

Decision (0.1.0, taken without the owner: it is reversible): the "default
plugins" are **ordinary modules of the program behind one small internal
interface**, not scripts and not out-of-process extensions.

A built-in plugin is:

* a **name** and a one-line summary (`ui/MED_plugin.m31`, `MED_plugin.all()`),
* **keymap rows**: `MED_keymap.Binding` rows carry the plugin name, a
  description (the which-key label), a mode (Normal or Visual) and a source
  (`vim`, `config` = mirrors the owner's nvim config, `m3`),
* **ex commands** (`:Files`, `:Plugins` ... routed through `MED_ex.is_ui_command`
  to the front end) and
* **UI** it draws or loads (statusline segments, signs, guides, pickers).

Switching: `:PluginDisable NAME` / `:PluginEnable NAME` (also lines of the
keymap file) and `:Plugins` to list. A disabled plugin's rows leave the leader
tree, which-key, the palette, `:Keys` and the help picker, and its UI is not
drawn. Plugins that are engine features (surround, autopairs, comment, git
signs) are switched through their `:set` option (`surround`, `autopairs`,
`comment`, `gitsigns`), so both spellings are one switch. `core` (the keymap
tree itself) cannot be disabled. Replacing a plugin is done the Vim way: disable
it and `:nnoremap` your own keys; user maps under `<Space>` are merged into the
leader tree and win over a built-in row with the same keys.

Why not out-of-process JSON-RPC (yet): the editor's value is a 0.02 s start and
a single static binary. A process boundary costs a spawn per plugin, a
protocol, and a second implementation of every picker/list widget. None of the
built-ins needs it. The seam is kept narrow enough that it can be added later:
a plugin is rows plus ex commands plus a UI hook, which is exactly what a
JSON-RPC plugin could declare. Third-party plugins remain "later"; the keymap
file and `:map` are the extension point today.

Rules that keep the core fast: nothing a plugin owns runs at startup except
building its (small) rows when they are asked for; sources (file lists, grep,
git) are started on demand by the first picker use, never at launch; the
statusline reads `.git/HEAD` once per refresh interval, not per frame.

### 12.1 Where the keys come from

One table, `ui/MED_keymap.m31`: the leader tree (`defaults()`), the prefix help
for `g z [ ] CTRL-W " ' m q @` and the operators (`prefixes()`, `motion_rows`),
the palette commands and notes. The leader menu, the which-key popup, the
`<Space>?` / `:Keys` browser and `docs/KEYMAP.md` (generated by
`scripts/gen_keymap.sh`, checked by `tests/t_keymap.m31`) are all views of it,
so they cannot disagree with what the keys do. The engine is not changed by
any of this: the oracle (section 7) keeps checking the Vim keys; the front end
only decides when a pending prefix shows a popup (after `WHICH_KEY_MS`, 400 ms).

Collision rule: the leader tree is a prefix tree in which no key is both a leaf
and a prefix (a test enforces it). The owner's nvim config used `<Space>s` both
for splits (`sv sh se sc`) and for mini.surround (`sa sd sf sF sh sr`), where
`sh` meant two things. The built-in surround is `ys ds cs` and Visual `S`;
`<Space>sa/sd/sr` are aliases for those, and `sf sF sh` are not mapped.

## 13. Language server client

`ui/MED_lsp.m31` is the protocol (framing, JSON-RPC over the child's pipes with `encoding.json`, URIs, UTF-16
columns, text edits, a `Server` that is polled); `ui/MED_app.m31` holds the editor side. No threads: the tick reads
whatever a server wrote (a read with a deadline that has already passed fails at once when the pipe is empty).

* Servers by language, first one on `$PATH` wins: rust-analyzer; gopls; pyright-langserver --stdio, pylsp,
  jedi-language-server; clangd; typescript-language-server --stdio; lua-language-server; marksman server;
  bash-language-server start. `:Lsp server LANGUAGE COMMAND...` overrides one (a keymap file line).
* Started on demand when the active buffer's language has one, never at launch. Root is the project root.
* Sync: `didOpen` when the server is ready, `didChange` on the next tick after a change while the buffer is not in
  Insert mode (so diagnostics refresh when Insert mode ends), `didSave` on `:w`. Full text by default; incremental
  only when the server announced change kind 2 (or registered it dynamically): `Server.did_change` compares the text
  it sent last (a copy of the lines, kept per document) with the buffer and sends one ranged change, `MED_lsp.change_of`.
  Positions are converted between UTF-16 columns and bytes with the buffer text.
* Features: `publishDiagnostics` (signs `E W I`, `E:n W:n` in the statusline, `]d [d`, `<Space>ll`, `<Space>]]`
  `<Space>[[`, the diagnostics picker `<Space>xx fx`), `K` hover, `gd` definition, `grr` references (picker),
  `grn` / `:Lsp rename NAME`, `gra` / `:Lsp action` (picker of edit-carrying actions), `:Lsp format`. WorkspaceEdits
  from the server (`workspace/applyEdit`) are applied. Edits go in as one undoable change per file.
* Code actions: an action with an `edit` is applied; one with only `data` is sent through `codeAction/resolve`
  first; a `command` goes out as `workspace/executeCommand` (servers answer with `workspace/applyEdit`). The
  diagnostics of the cursor line are part of the request context, so quick fixes are offered for them.
* Server-initiated requests are all answered (a server that is not answered waits for ever): `workspace/applyEdit`
  (applied), `workspace/configuration` (one `null` per item), `workspace/workspaceFolders`,
  `window/workDoneProgress/create`, `client/registerCapability`, `window/showMessageRequest`, anything else with
  `null`. Ids may be numbers or strings and are echoed as sent. `$/progress` drives the `LSP: ...` status text.
* Capabilities from the `initialize` answer gate the commands ("does not support rename" instead of an
  `Unhandled method` from the server). `publishDiagnostics` carrying a `version` older than the text last sent is
  dropped (stale). `languageId` follows the file (`typescript`, `typescriptreact`, `javascriptreact`, `shellscript`).
* The server's stderr is drained on every tick and its tail kept (`:Lsp info` shows it when the server died); it is
  never closed, because a closed stderr kills servers that log (clangd). `workspaceFolders` is deliberately not
  declared: pyright then never analyses. Quit sends `shutdown`/`exit`, waits briefly for the server to exit by
  itself (so tsserver and proc-macro servers go with it), then kills it.
* Completion: CTRL-Space in Insert mode (or `:Lsp complete`) syncs the buffer, sends `textDocument/completion` and
  lists the items in the picker, ordered by `sortText`, pre-filtered by the typed word; Enter accepts (its
  `textEdit` or `insertText`, snippets through the snippet engine, `additionalTextEdits` such as clangd's
  includes), the cursor lands after the text (past edits made above it: `MED_lsp.map_point`).
* The completion popup (`ui/MED_pum.m31`, `:set lspcomplete=auto`; `manual` is the default until it has soaked):
  `Pum` holds the items of one answer, the typed text after the anchor (the start of the word, or of the first item's
  own edit range), the ranked rows and the selection (-1 none). A request is sent 25 ms after the last typed
  identifier or trigger character and flushes the buffer first (Insert mode holds `didChange` back); the answer is
  dropped when the cursor left the word. Filtering is ours: a prefix that only grew narrows the rows already shown,
  anything else rescans; `isIncomplete` lists are requested again (triggerKind 3). Ranking tiers: same-case prefix,
  prefix, word-start substring, substring, in-order letters (two typed characters at least), then the server's
  `sortText`. Selection does not change the text (nvim's `noinsert`); `<CR>` on no selection is a line break. The
  selected item's documentation comes from `completionItem/resolve` after 80 ms of rest; accepting waits up to 300 ms
  for a resolve it still needs (`additionalTextEdits`). Placement: under the cursor row when it fits, else above;
  the documentation panel on the right of the list when 24 cells fit, else on the left. Cells only get text through
  `MED_pum.clean`. `Server.cancel` sends `$/cancelRequest` for a request that was overtaken. Divergences from nvim:
  nvim inserts the selected text live and `<C-e>` restores it; here nothing is inserted until accept.
* Tests: `tests/t_pum.m31` and `tests/lsp_pty.py` (the popup), `tests/t_lsp.m31` (framing, decoding, URIs, columns, edits, ids, a round trip with a scripted server);
  the `lsp_client` pty scenario of `tests/e2e.py` against `tests/fake_lsp.py` (server requests with string ids,
  an stderr flood, lazy and command code actions); and `lsp_real_*` pty scenarios against real servers (skipped
  when a binary is missing). Each of the latter waits for diagnostics, then hover, definition, references and
  rename, and requires that no process of the server survives the quit.

Tested with real servers on 2026-10-13 (Linux x86-64):

| server | diagnostics | hover | definition | references | rename | code action | format | notes |
|---|---|---|---|---|---|---|---|---|
| pyright-langserver 1.1.407 | yes | yes | yes | yes | yes | none offered on the probe | not supported (message) | needs `workspaceFolders` undeclared |
| clangd 21.1.8 | yes | yes | yes | yes | yes | none on the probe | yes | dies if stderr is closed |
| typescript-language-server | yes | yes | yes | yes | yes | yes (refactors) | yes | `.ts` is sent as `typescript` |
| lua-language-server | yes | yes | yes | yes | yes | yes | yes | no highlighting for lua (server only) |
| rust-analyzer (mason build) | yes | yes | yes | yes | yes | not exercised | not exercised | diagnostics arrive while indexing; hover waits for it, shown as `LSP: Indexing` |
| gopls, marksman, bash-language-server | not installed here | | | | | | | configured, untested |

## 14. Syntax highlighting: the `syntax` library

Since 0.2.0 the editor has no tokenizer of its own. `engine/MED_syntax.m31`
(a 1000-line hand-written lexer for twelve languages) is gone; highlighting,
language detection and comment forms come from
[`github.com/qrazil/syntax`](https://github.com/qrazil/syntax), pinned in `deps`
(v0.4.2, commit `e49e01c`), the same library `tui` and `gitui` use.

- `engine/MED_hl.m31` is the adapter. `language(editor)` answers `:set
  syntax=NAME` (through `SYN_detect.alias_of`, so `py`, `bash`, `md`, `ts` work)
  or else `SYN_detect.language_of(path, first_line)` (extension, file name,
  modeline, shebang). `classes_of(editor, row, lang)` answers one class per byte.
- Each `Editor` holds a `SYN_highlight.Highlighter` (`editor.syn`) over the
  buffer's own line list. `Buffer.dirty_row` (the first row any splice touched)
  is handed to `Highlighter.update`, which re-tokenizes from that row and stops
  at the first later line whose start state is unchanged; typing in a line that
  opens or closes nothing costs one line. Inserted and removed lines shift the
  cached states with them. Code that replaces `buffer.lines` wholesale sets
  `dirty_row = 0`.
- The library has 25 classes; since 0.5.0 the editor draws all 25 (each has a theme scope, section 3);
  `SYN_class.legacy`, the fold onto twelve, is no longer used by the renderer. Markdown
  fences are the library's: a fence in any known language (`rust`, `py`, `sh`,
  ...) is highlighted in that language, states carried line to line.
- `commentstring` defaults (`gc`) come from `SYN_structure.comment_forms` of the
  detected language (`// %s`, `# %s`, `<!-- %s -->`, `/* %s */`, ...).
- Not taken from the library: `%` (`MED_motion.match_pair`) stays Vim's, because
  it is checked against the nvim oracle (Vim does not skip brackets in strings
  or comments, `SYN_structure.match_bracket` does); `gc` stays the engine's
  commentstring toggle (checked against nvim, with `commentstring` an option).
- LSP: a TypeScript file is served as `javascript` (one server for both), as before.

Tests: `tests/t_syntax.m31` (detection, options, classes, markdown fences,
incremental edits, 17 file types, and a 20k-line speed check: a cold pass
under 10 s and 1000 edits each followed by a 50-line redraw under 5 s; measured
about 0.1 s and 1.4 s).
