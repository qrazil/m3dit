# m3

A terminal text editor with Vim key bindings, written in
[m31](https://github.com/qrazil/m31) on the [tui](https://github.com/qrazil/tui)
library. IDE-lite: keyboard first, no toolbar or menu chrome, discoverable
through which-key, a command palette and a keymap help picker. (`medit` is the
design codename that `DESIGN.md` still uses.)

**Status: v0.8.0.** The Vim engine is checked against `nvim --headless` on
more than 38,500 generated and hand-written cases (20 known divergences, listed in
`tests/oracles/known_divergences.txt`); on top of it sit the built-in plugins that make it a daily editor:
a fuzzy finder with async sources (rg / fd / git when installed, a built-in walker and grep when not), which-key for
every prefix, a keymap table that mirrors the owner's Neovim leader keys, git signs with hunk stage / reset /
preview / blame, a statusline and bufferline, harpoon-style pinned files, quickfix, a terminal pane, `:!` `:r !` and
`!{motion}` filters, label jump, line move, indent guides, TODO highlighting, last-position restore and a minimal
language server client. Every built-in can be switched off (`:PluginDisable NAME`, `:Plugins`). See
[docs/ROADMAP.md](docs/ROADMAP.md) for the queue from 0.7.0 to 1.0.0 and [docs/KEYMAP.md](docs/KEYMAP.md) for every default key (generated from the same table the editor uses) and DESIGN
section 12 and 13 for the plugin framework and the LSP client.

Options that change behaviour are checked against nvim one by one: `scrolloff`, `sidescroll`,
`sidescrolloff`, `wrap`/`nowrap` scrolling, `whichwrap`, `iskeyword`, `textwidth`
with `formatoptions` (auto-wrap, `gq`, comment leaders), `tabstop`, `shiftwidth`,
`softtabstop`, `expandtab`, `smarttab`, `autoindent`, `ignorecase`, `smartcase`,
`wrapscan`, `startofline`, `smartindent`, `list`/`listchars`, `cursorline`,
`cursorcolumn`, `colorcolumn`, `linebreak`/`breakat`/`showbreak`/`breakindent`/`breakindentopt`. Known limits: no command-line window, fold methods manual, indent and marker only,
a reduced `=` indent (`cindent` is not implemented; `smartindent` is), `formatoptions` `a` and `n`, many
options are stored but do not change behaviour yet, no tree-sitter, and the terminal pane is
line oriented (no full-screen programs). `m3 --version` prints the version.

## Command line

    m3 [options] [FILE...]

The grammar is Oro's `args` (`lib/args`, m31's
[`docs/cli-conventions.md`](https://github.com/qrazil/m31/blob/master/docs/cli-conventions.md)):
`--keymap FILE`, `--keymap=FILE`, `--k FILE`; a short option is two dashes and one
letter; `-word` would be a command (there are none), so an unknown `-x` is an error
instead of a file called `-x` (pass it as `./-x`); `--help` is the only help; a
mistyped option names the closest one. A bad command line is an error on standard
error with the usage line and exit 2; `m3` needs a terminal on standard input and
output (exit 1).

| option | | default | |
|---|---|---|---|
| `--keymap FILE\|NONE`, `--k` | path, or the word `NONE` | `$M3_KEYMAP`, else `$XDG_CONFIG_HOME/m3/keymap.vim` | `NONE` reads no keymap and keeps no state files (this was vim's `-u`) |
| `--theme NAME` | theme name | the default theme | start with that colour theme |
| `--colors DEPTH` | `16`, `256`, `true` | the terminal's | the depth `--dump-sample` writes at |
| `--dump-sample` | switch | off | print the theme(s) on sample code as ANSI text and exit |
| `--no-mouse` | switch | mouse on, unless `M3_NO_MOUSE` is non-empty | do not ask the terminal for mouse reports |
| `--version` | | | `m3 0.5.0` |
| `--completions SHELL` | `bash`, `zsh`, `fish` | | prints a completion script |
| `FILE...` | paths | an empty buffer | a new buffer when a file does not exist yet |

`-u`, `-v` and `-h` (the old spellings) still work for this one release and print a
warning; then they go.

    m3 --completions bash > ~/.local/share/bash-completion/completions/m3
    m3 --completions fish > ~/.config/fish/completions/m3.fish
    m3 --completions zsh  > "${fpath[1]}/_m3"

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/qrazil/m3dit/master/install.sh | sh
```

Picks the release for your OS and CPU, unpacks it under `~/.local/opt/m3dit/<version>` and links the programs into `~/.local/bin`. `--release v1.2.3` (or `VERSION=v1.2.3`) pins a release, `--prefix DIR` (or `PREFIX=...`) moves the install, `--libc gnu|musl` (or `LIBC=`) overrides detection, `-uninstall` removes it, `--help` lists them; piped from curl, pass them after `-s --`: `curl -fsSL <url> | sh -s -- --prefix /usr/local`. The grammar is Oro's: a mistyped option is an error naming the closest one (exit 2).

On Alpine (musl) the installer picks the `-musl` Linux asset built by `scripts/ci-musl.sh`; `LIBC=gnu|musl` overrides detection, and a release without a musl asset falls back to the glibc one.

## Features

- Modal editing with Vim grammar: motions, operators, text objects, counts,
  registers, macros, dot repeat, marks, visual modes (char, line, block), `<C-a>` / `<C-x>`.
- Undo tree (`u`, `<C-r>`, `g-`, `g+`, `:earlier`, `:later`).
- Search (`/ ? n N * #`), `:s`, `:g`, `:v`, `:normal`, `:sort` and the rest of the
  ex subset in DESIGN section 2. A purpose-built Vim-regex engine (no
  backreferences or lookaround).
- Buffers and windows: `:e :ls :b :bn :bp :bd`, `:split :vsplit :close :only`,
  `<C-w>` commands (with counts: `<C-w>5_`, `3<C-w>w`), mouse click, drag and wheel. Sizes follow nvim's
  frame model: a split halves the window and shares the space out again only when needed, closing gives the
  space to the neighbour, `:resize` takes rows from the windows below and then above, and a terminal resize
  shrinks the last window first (checked against nvim by `tests/oracles/oracle_windows.py`).
- Tab pages: `:tabnew :tabedit :tabnext :tabprev :tabNext :tabfirst :tablast :tabclose :tabonly :tabmove :tabs`,
  `gt` / `gT` (and `3gt`), `<C-w>T`; a tab line shows the window count, `+` and the name; each page keeps its own
  windows; `:q` / `:close` on the last window of a page closes the page. `:[N]tab split|vsplit|new|vnew [file]` opens the
  window in a new page, and a count on `:tabnew`, `:tabedit`, `:tabnext`, `:tabclose`, `:tabonly` and `:tabmove` is a tab
  page number (`:0tabnew` first, `:2tabnew` after page 2, `:$tab split` last; `.`, `$`, `+N`, `-N` as in nvim); a left click
  on a tab label shows that page.
- Pickers: files, buffers, live grep, commands, keymap help, explorer; `.gitignore` aware.
- Syntax highlighting for 77 languages (c, cpp, go, javascript/typescript, json, m31, markdown,
  python, rust, sh, toml, yaml, html, css, sql, java, ruby, lua, ...), by the shared
  [`syntax`](https://github.com/qrazil/syntax) library (`:syntax on|off`, `:set syntax=NAME`); the
  colours come from the theme (see Themes below).
  Markdown: headings, emphasis, strong, strikethrough, code spans, links, lists and task boxes, quotes, rules,
  tables, and fenced blocks highlighted in the fence's language (```` ```rust ````, `py`, `sh`, `m31`, ...;
  unknown language = plain code colour).
- Command-line completion: `<Tab>` / `<C-n>` and `<S-Tab>` / `<C-p>` complete ex
  commands, option names (long and short), file and directory names and buffers.
- Folds: manual (`zf` `zF` `:fold`, `zd zD zE`) and `:set foldmethod=indent|marker` (marker levels such as `{{{3` and `}}}2` as nvim builds them); `zo zO zc zC za zA zv zR zM zm zr zx zX zn zN zi zj zk [z ]z`, `foldlevel`, `foldlevelstart`.
- Persistence and project settings: undo files, `.editorconfig` and `.m3.toml`, outside-change reload, `autowriteall`, `autosave`, `:Session` (the buffers, their cursors, the tab pages and the window layout: sizes are shared out equally again).
- File tree sidebar (neo-tree style): `<Space>e` toggles it, `<Space>E` reveals the
  current file, `:Neotree [toggle|show|focus|close|reveal|refresh|DIR]`. Rows are
  folders first, git status letters (M A D R ? !) sit at the right and folders
  carry the worst status of what is inside; the tree follows the buffer.
  `:Explore` and `:e DIR` still open the netrw-style listing in a window.
- Abbreviations: `:abbreviate` (Insert and command line), `:iabbrev`, `:cabbrev` (and the `nore` forms),
  `:unabbreviate` `:iunabbrev` `:cunabbrev`, `:abclear` `:iabclear` `:cabclear`, listed as nvim does. Full-id,
  end-id and non-id forms; expansion on a non-keyword character, `<Esc>`, `<CR>` or `CTRL-]`, repeated by `.` and counts
  as in Vim; in the command line (also `/` and `?`) on a non-keyword character, `<CR>` or `CTRL-]`.
- Snippets (LSP / VS Code grammar): `$1`, `${1:default}`, mirrors, nested placeholders, `${1|a,b|}` choices (the first
  is the text), `${1/re/fmt/opts}` transforms, variables (`TM_FILENAME`, `TM_LINE_INDEX`, `TM_SELECTED_TEXT`, `CLIPBOARD`,
  `CURRENT_YEAR` ...; an unknown name is a tabstop that holds it). `<Tab>` / `<S-Tab>` jump while one is active, a
  placeholder is selected in Select mode (typing replaces it). Your own: `snippets.json` (VS Code format) and
  `snippets/LANGUAGE.json` next to the keymap file, expanded with `<Tab>` after the prefix; LSP completion items that
  are snippets use the same engine. Expansion and jumping follow nvim's `vim.snippet` and are checked against it by
  `tests/oracles/oracle_snippet.py`.
- Variables: `:let x = 1`, `g:x`, `+= -= *= .=`, read by `\=` in `:s` and shown by `:echo`.
- Syntax: all 25 token classes of the `syntax` library are drawn (properties, tags, attributes, calls, links, emphasis,
  strong, raw text, diff added / removed, builtin variables).
- Which-key popup for the leader sequences.
- Comment toggle `gc` / `gcc` / visual `gc`, with the comment string chosen by file type
  (`:set commentstring=`), matching Neovim 0.11's built-in `gc`.
- A keymap file in Vim syntax: `:map` / `:noremap` for n, x, o, i, c modes, `:unmap`,
  `:mapclear`, `let mapleader`, `:source` (see below).
- Themes: `:theme` / `:colorscheme`, a live-preview picker, truecolor with 256 and 16-colour fallback, Helix-format theme
  files (see Themes below).

The editing engine is tested differentially against `nvim --headless` (31k+ cases): motions, operators, text objects,
counts, dot repeat, registers, undo, visual modes, macros, marks, search, ex commands, insert-mode keys (including
`<C-r>` forms, `<C-n>`/`<C-p>` completion, `<C-t>`/`<C-d>`, `gR`), `:set` options, soft wrap and screen-line motions.

Display: soft wrap (`:set nowrap` for horizontal scrolling), `gj gk g0 g^ g$ gm`, `:set number relativenumber list`,
`hlsearch` highlighting (`:noh`).

More

- Surround as in vim-surround: `ys{motion}{char}`, `yss`, `yS`, `ySS`, `ds{char}`, `cs{old}{new}`, `cS`, and `S` / `gS` in
  Visual mode (`)`/`b`, `(`, `]`/`r`, `}`/`B`, `>`/`a`, quotes, `t` and `<` for tags with attributes kept by `cs`, `f` and `F` for
  function calls, `l` for LaTeX, `p`, `s`, a space prefix). The engine is checked against the plugin itself.
- Auto pairs as in auto-pairs: `(` `[` `{` `'` `"` `` ` `` and the triples, a closing key steps over, `<BS>` in an empty pair deletes
  both, `<Space>` pads, `<CR>` between brackets opens a line. `:set noautopairs` turns it off.
- Git gutter: `+` added, `~` changed, `_` removed lines against HEAD in a sign column, `]c` / `[c` to jump between changes
  (`:set nogitsigns` turns it off). Lower-case marks show as letters in the same column; `:marks`, `:registers`, `:jumps`,
  `:changes` list as Vim does and `<Space>fm` is a marks picker.
- Git in process (`m31git`): the gutter's base text, `<Space>gB` blame, hunk staging and the `:Git` read commands read and
  write the repository themselves (loose and packed objects, linked worktrees, SHA-256); a repository the library cannot
  read (a version 4 index, a partial clone) falls back to `git`. `:Git log [FILE|%] [-L A,B]` and `:Git blame` are lists in
  the finder with a commit preview (`Enter` on a blame row jumps to the line), `:Git show [REV]` and `:Git diff
  [working|index|head]` open scratch buffers. `:Hunk stage|reset|undo|preview` act on the hunk under the cursor
  (`undo` unstages it); `ih` / `ah` select the hunk (`ah` adds the blank rows after it), as in `dih`, `yah`, `vih`.
- System clipboard: `"+` and `"*` use pbcopy / pbpaste (macOS), wl-clipboard, xclip or xsel; `:set clipboard=unnamedplus` makes
  every yank and put use it.
- Windows: `:resize`, `:vertical resize`, `<C-w>` `+ - < > _ | =` `H J K L` `r R x T`; closing a modified buffer's last window is E37.
- Language servers: diagnostics, hover (`K`), definition, references, rename, code actions, format, completion,
  signature help (`:Lsp signature`, `<C-s>` in Insert mode, `<Space>ck`, and after the server's trigger characters),
  inlay hints (`:Lsp hints`, `<Space>ch`; drawn dimmed after the end of the line) and `textDocument/didClose`
  when a buffer is deleted.
- Registers: `"=` (the expression register, `"=5*5<CR>p`), `:put =expr`, `:let @a=` / `@A=` / `@"=`, `]p [p ]P [P`;
  marks: `]'` `['` `` ]` `` `` [` ``, `.` and `^` as nvim sets them after put, join, delete, shift, :copy, :move, :s and undo.
- Display: soft wrap, `incsearch`, `hlsearch`, `number`, `relativenumber`, `list`; `gj gk g0 g^ g$ gm`.
- Directory listings (`:Explore`): `R` rename, `D` delete, `%` new file, `d` new directory, `gh` toggle dotfiles.

## Smoothness

The editor decides every result exactly as it always did; what changed in 0.8.0 is
what you see on the way there. Nothing is ever animated into a different final state:
an animation is a path to the screen the engine already computed, and the last frame is
always that screen.

What moves (all of it terminal-native: cells, not pixels):

* **Scrolling.** `<C-d> <C-u> <C-f> <C-b> zt zz zb gg G`, search jumps, `{n}G`, `%`,
  marks and the mouse wheel glide to their target in about 100 ms: the window's top line
  closes a fixed share of the remaining distance each frame (an ease-out), the cursor line
  slides with the text and `scrolloff` holds at every frame, a long jump arrives from a
  screen away instead of sweeping 10,000 lines, and a wheel burst accumulates into one
  movement. `j`, `k`, `<C-e>`, `<C-y>` (one line) stay instant. Any key is handled before
  the next frame, and a key that is not itself a scroll shows the final state at once.
* **Yank flash.** The yanked text lights up for 200 ms.
* **Popups fade in** (which-key, the pickers) over about 90 ms, in 24-bit colour.
* **Cursor shape.** Insert mode shows a bar, Replace an underline, the command line a
  bar; the terminal's own shape is put back when m3 quits. Without focus (`CSI ? 1004`)
  the cursor cell becomes an underline.
* **Scrollbar** (`:set scrollbar`, off by default): a thin dim thumb on each window's
  right edge; click or drag it to jump. Dragging a selection to the top or bottom edge
  autoscrolls, faster the longer it stays.
* **No layout jumps.** The line-number gutter only grows (deleting lines does not pull
  the text back), a running language server reserves the sign column before its first
  diagnostic, and the picker keeps its preview pane's place when a query matches nothing.

The output side: every frame is written once, wrapped in synchronized output (DEC mode
2026) when the terminal says it supports it, and a view that scrolled by a few lines is
moved with a terminal scroll region instead of being rewritten (a held `j` writes ~140
bytes a frame instead of ~2000). Idle, the editor wakes four times a second to notice a
resize, and not at all otherwise for the animation.

Switching it off: `:set noanimate` (everything), `:set noanimatescroll`,
`:set noanimatefade`, `:set noanimateflash`, `:set animatetime=60` (shorter or longer
scrolls), `:set nocursorshape`; `m3 --no-anim`, `M3_NO_ANIM=1` or `TERM=dumb` for a whole
run. Colour fades need 24-bit colour (`COLORTERM=truecolor`) and are skipped without it;
scrolling still glides. Nothing animates during a macro, `.`, `:normal`, `:g`, a paste or
while more input is waiting, while the terminal is not focused, or when frames take too
long to write (then fewer steps, then none). Numbers and budgets: [docs/UX-PERF.md](docs/UX-PERF.md).

## Keys

Normal-mode `<Space>` is the leader; a pending sequence shows which-key after a short delay.

| keys | action |
|---|---|
| `jk` | Insert mode: back to Normal |
| `<Space>ff` / `<Space><Space>` | find files |
| `<Space>fr` `fd` `fq` | recent files, lines of the buffer, quickfix |
| `<Space>fb` / `<Space>,` | buffers |
| `<Space>fg` / `<Space>/` | live grep |
| `<Space>fc` / `<Space>:` | command palette |
| `<Space>?` / `<Space>fh` | keymap help |
| `<Space>e` / `<Space>fe` | file explorer (`-` goes up) |
| `<Space>bn` `bp` `ba` `bd` `bl` | next, previous, alternate, delete, list buffers |
| `<Space>sv` `sh` `se` `sc` `z` `o` | split right, split below, equalise, close, close, only this window |
| `<Space>n` | new buffer |
| `<Space>w` / `<Space>qq` / `<Space>qa` | write, quit, quit all |
| `<C-w>` `s v n c q o w W p t b h j k l x r R H J K L = + - < > _ \| T` | window commands |
| `gt` `gT` `:tabnew` | next / previous tab page, new tab page |
| `<C-^>` | alternate buffer |
| `:w` `:q` `:q!` `:wq` `ZZ` | write and quit |

In a picker, `<C-s>` / `<C-v>` open the hit in a split below / beside.

## Built-in plugins

| plugin | default keys | what it does |
|---|---|---|
| finder | `<Space>ff fg fr fb fd fq fh fc fk fo fm fx fs ft fw` | files, live grep, recent, buffers, lines of the buffer, quickfix, keys, commands, options, marks, diagnostics, symbols, TODOs, word under cursor; `<C-t>` marks, `<C-q>` sends to quickfix |
| whichkey | after 400 ms of any pending prefix | `<Space>`, `g`, `z`, `[`, `]`, `<C-w>`, `"`, `'`, operators |
| explorer | `<Space>e` | file tree sidebar (see below) |
| git | `<Space>gg gf gb gc gC gs gr gp gu gB gl gd gm gt`, `]c [c ]h [h`, `ih ah`, `:Git`, `:Hunk` | changed files, branch checkout, remote branches, commit log with preview, hunk stage / unstage / reset / preview, blame line and list, file log, diff, signs; the reads and the staging run in process (see below) |
| surround | `ys ds cs`, Visual `S`, `<Space>sa sd sr` | vim-surround |
| comment | `gc` `gcc` | language-aware toggle |
| autopairs | insert mode | bracket and quote pairing |
| statusline | | mode, file, git branch and hunk counts, E/W counts, filetype, position; bufferline with two or more buffers |
| bracketed | `[b ]b [q ]q [d ]d [h ]h [t ]t` | buffers, quickfix, diagnostics, hunks, TODO comments |
| harpoon | `<Space>ha he hn hp hd`, `<Space>1`..`9` | pinned files per project (`~/.local/state/m3`) |
| move | `<A-j> <A-k> <A-h> <A-l>` | move or shift the line or the Visual selection |
| jump | `<Space>j` | type a character, then a label |
| guides | | indent guides (`:set noindentguides`) |
| todo | `<Space>ft`, `]t` | highlight and list TODO FIXME HACK XXX NOTE WARN PERF BUG |
| terminal | `<Space>t`, `:terminal [cmd]` | a shell on a pty; `<C-\><C-n>` leaves to Normal mode, `i` goes back |
| session | | last cursor position of each file, recent files |
| lsp | `K gd grr grn gra`, `<Space>cr ca cf ll xx`, `:Lsp ...` | diagnostics, hover, definition, references, rename, code action, format |

`:Plugins` lists them, `:PluginDisable NAME` / `:PluginEnable NAME` switch one (put the lines in the keymap file).
`:Keys` or `<Space>?` browses every key. `:set nojk_escape` turns the Insert-mode `jk` off.

Shell: `:!cmd` shows the output, `:{range}!cmd` filters lines, `:r !cmd` and `:r file` read, `!{motion}` and
Visual `!` start the filter command line; `%` is the file name and `!` the previous command. They match nvim
(corpus 103) for commands that do not need a terminal; use `:terminal` for interactive programs.

LSP: servers are found on `$PATH` by file type (rust-analyzer, gopls, pyright-langserver or pylsp, clangd,
typescript-language-server, lua-language-server, marksman, bash-language-server) and started on demand;
`:Lsp server LANGUAGE COMMAND...` sets one, `:Lsp info|start|stop|hover|definition|references|rename NAME|format|action`.
Servers that are not on `$PATH` are also looked for in Neovim's mason directory
(`~/.local/share/nvim/mason/bin`). Tested against real servers (pty scenarios in `tests/e2e.py`, skipped when a
server is not installed): pyright, clangd, typescript-language-server, lua-language-server, rust-analyzer;
the per-server table is in DESIGN.md section 13. The status line shows `LSP: ...` while a server reports progress
(indexing). CTRL-Space in Insert mode completes from the server (a picker; Enter accepts). `:set lspcomplete=auto`
turns on the completion popup that follows the cursor: it opens as you type (trigger and identifier characters), narrows
with every key, shows documentation beside the list; `<Tab>`/`<C-n>` and `<S-Tab>`/`<C-p>` select, `<C-y>` (or `<CR>` on a
selected row) accepts, `<C-e>` closes. Snippet items expand through the snippet engine. `:set lspformat` formats a
buffer with its server before every write. Servers that announce incremental sync get ranged `didChange`s; servers that
register capabilities dynamically are supported.

## Themes

Colours are data, in Helix's model: a theme is a TOML file with a `[palette]` and a table from scope names to styles.
Fourteen are built in (no files needed at run time): `default` and `default-light` (original to m3, no background colour
of their own so the terminal's shows through), `term16-dark` and `term16-light` (only the terminal's 16 ANSI colours;
what `default` becomes on a 16-colour terminal), `tokyonight` (night), `nightfox`, `gruvbox-material` (dark, medium)
and `gruvbox-material-soft`, `gruvbox`, `catppuccin-mocha`, `onedark`, `nord`, `dracula`, `github-light`.
The last nine are the Helix ports of those schemes, unchanged (see the header of `themes/*.toml` for the authors).

```
:theme                   show the theme in use
:theme tokyonight        switch now (Tab completes names); :colorscheme NAME is the same
<Space>fC                pick one: the text beside the list is redrawn as the selection moves, Esc goes back
m3 --theme nord FILE     start with it
m3 --dump-sample         every built-in theme drawn on sample code as ANSI text (--theme X, --colors 16|256|true)
```

`:set background=light|dark` switches between `default` and `default-light` (and only while one of them is in use).
To keep a theme, put `colorscheme tokyonight` (or `theme tokyonight`) in `~/.config/m3/keymap.vim`; `--theme` wins over it.
An unknown or broken theme is a message on the command line and the theme in use stays.

Colour depth: truecolor when `COLORTERM` says so (or the terminal is iTerm2, WezTerm, VS Code, ghostty, kitty,
alacritty), else the 256-colour cube for a `*256color` `TERM`, else the nearest of the 16 ANSI colours. Hex colours
are rounded down to what the terminal has; `default` becomes `term16-dark` / `term16-light` at 16 colours.

**Your own themes** are `~/.config/m3/themes/NAME.toml` (`$XDG_CONFIG_HOME/m3/themes`; macOS uses `~/.config` too).
They show up in the picker and in completion, shadow a built-in of the same name, and can start from one:

```toml
inherits = "tokyonight"                 # a built-in or another user theme; the parent's palette is visible too
"comment" = { fg = "gray", modifiers = ["italic"] }
"ui.statusline.normal" = { fg = "bg", bg = "blue", modifiers = ["bold"] }
"keyword" = "#ff79c6"                   # a bare colour is a foreground
"ui.background" = { bg = "bg" }         # optional: without it the terminal's own background shows

[palette]
gray = "#565f89"
bg = "#1a1b26"
blue = "#7aa2f7"
```

Format: colours are `#rrggbb` (`#rgb`, and `#rrggbbaa` with the alpha ignored), a palette name, one of `black red green
yellow blue magenta cyan gray light-red .. light-cyan light-gray white` (`gray` is bright black, `light-gray` plain white),
`default`, or a number 0..255. A style has `fg`, `bg`, `modifiers` (`bold dim italic underlined reversed crossed_out`;
`slow_blink`, `rapid_blink` and `hidden` are accepted and ignored) and `underline = { color, style }` (draws a plain
underline: the terminal layer has no underline colour or curl). Only the TOML the format needs is read: comments,
`[palette]`, `key = value`, strings, arrays and inline tables (which may span lines). A syntax error fails the theme
with the file and line; an entry that cannot be read (an unknown colour, modifier or key) is left out and reported,
as Helix does. Every theme in Helix's `runtime/themes` loads (checked against Helix 25.01).

Scope lookup is Helix's: `keyword.control.return`, then `keyword.control`, then `keyword`. Scopes Helix themes do
not have fall back to ones they do (`ui.statusline.visual` to `ui.statusline.select`, `ui.cursorline` to
`ui.cursorline.primary`, `markup.heading` to `markup.heading.1`, ...: `FALLBACKS` in `ui/MED_theme.m31`), so a
Helix theme works unchanged and looks right. What is drawn, and the scope for it:

| area | scopes |
|---|---|
| text | `ui.background` (optional), `ui.text`, `ui.text.inactive`, `ui.gutter`, `ui.linenr`, `ui.linenr.selected` |
| cursor and selection | `ui.cursor` (and `ui.cursor.primary.normal`/`insert`/`select`; reversed when absent), `ui.cursorline`, `ui.selection`, `search.match` (hlsearch), `search.current` (incsearch preview), `ui.todo` (TODO / FIXME) |
| statusline | `ui.statusline`, `.inactive`, and the mode segment `.normal .insert .visual .replace .command .terminal` |
| buffer / tab line | `ui.bufferline`, `ui.bufferline.active` |
| popups | `ui.popup` (listings), `ui.which-key` (+ `.title`), `ui.menu`, `ui.menu.selected` (command-line completion row), `ui.picker` (+ `.title`, `.match`, `.selected`), `ui.prompt` |
| editing area | `ui.virtual.indent-guide`, `ui.virtual.whitespace` (`:set list`, `~`, `<<<`), `ui.virtual.ruler` (`colorcolumn`), `ui.virtual.inlay-hint`, `ui.window` (split borders) |
| file tree | `ui.tree.directory`, `ui.tree.hidden` |
| signs | `error` `warning` `info` (diagnostics), `special` (marks), `diff.plus` `diff.delta` `diff.minus` (git gutter, tree status letters) |
| messages | `error` |
| syntax | the 25 `syntax` classes: `variable` (plain code), `comment`, `string`, `constant.numeric`, `keyword`, `type`, `function`, `keyword.directive`, `constant`, `operator`, `string.special`, `markup.heading`, `variable.other.member` (properties and members), `tag`, `attribute`, `punctuation.special`, `function.call`, `diff.plus`, `diff.minus`, `markup.link.url`, `markup.italic`, `markup.bold`, `markup.raw`, `variable.builtin` |

A theme file that lacks a scope gets the fallbacks above, then plain text. Built-in themes must resolve every scope the
renderer asks for: `tests/t_theme.m31` reads the renderer's source for the scopes it uses and fails when a built-in omits one.
`diagnostic.*` is accepted (themes have it) but not drawn: diagnostics show in the sign column only.
`scripts/gen_themes.sh` turns `themes/*.toml` into `ui/MED_theme_data.m31`; edit the `.toml`, then run it.

## Keymap file

`~/.config/m3/keymap.vim` (or `$XDG_CONFIG_HOME/m3/keymap.vim`, or the file
named by `$M3_KEYMAP`, or `m3 --keymap FILE`; `--keymap NONE` reads none) is a list of ex lines:

    let mapleader = " "
    nnoremap <leader>w :w<CR>
    inoremap jj <Esc>
    xnoremap < <gv

`"` starts a comment line. A map on `<Space>` replaces the built-in leader menu, and a
map starting with `j` in Insert mode replaces the built-in `jk`. Behaviour follows nvim
(checked in the oracle corpus); `<buffer>` and `<expr>` maps are refused (E474), and maps do
not apply inside macros, `.` or `:normal`.

## macOS (Apple silicon) in three lines

    curl -fsSL https://github.com/qrazil/m31/releases/download/v0.4.3/m31-macos-arm64.tar.gz | tar -xz -C /tmp && export M31_ROOT=/tmp LANGC=/tmp/m31c   # the m31 compiler and runtime
    git clone https://github.com/qrazil/m3dit && cd m3dit && bash scripts/build.sh      # needs Xcode command line tools (cc); first run fetches tui
    ./m3 FILE   # Terminal.app (256 colours) and iTerm2 / kitty / WezTerm (truecolor) work; --no-mouse turns mouse reports off

Colour depth follows `COLORTERM` / `TERM`; `--no-mouse` (or `M3_NO_MOUSE=1`) leaves the mouse to the terminal.

## Build

    export M31_ROOT=/path/to/m31          # a checkout or an extracted release (config.sh + runtime/)
    export LANGC=$M31_ROOT/target/release/m31c
    bash scripts/build.sh                 # -> ./m3   (bash scripts/build.sh -o NAME to rename)
    ./m3 FILE...

Needs m31 v0.4.3 or later (the `proc` module); the first compile fetches the pinned `tui`, `syntax` and `m31git`
into `.m31-deps/` (the commits are in `deps`, recorded in `deps.lock`). `m31git` (github.com/qrazil/m31git) is the
git library the editor reads repositories with; its `deps` pins the same `tui` and `syntax` commits as ours (m31 allows
one source per dependency, so bump them together).

## Test

    M31_ROOT=... LANGC=... bash tests/test.sh

`tests/test.sh` is the single entry point: `m31c fmt --check -r .`, `m31c lint .`,
the unit programs (`tests/test_units.sh`), the git oracle (`tests/oracles/oracle_git.py`: the in-process git against real
`git` on twin repositories, and `tests/git_pty.py`), the nvim oracles
(`tests/test_engine.sh`, skipped with a note when `nvim` is missing) and pty end-to-end
runs of the real binary (`tests/e2e.py`, which needs `pyte`: `pip install pyte`; skipped with a note
otherwise). The oracles need `nvim` 0.11 and `python3`. `bash scripts/oracle.sh --fuzz --seed 7 --cases 500`
runs the engine oracle on its own.

## File tree keys

With the tree focused (`<C-w>h` from the leftmost window, `<Space>e`, a click):

| keys | action |
|---|---|
| `j k gg G <C-d> <C-u> <C-f> <C-b>` | move |
| `l` `<CR>` `o` | open the file / expand the folder |
| `h` | collapse the folder, or go to the parent |
| `s` `v` `t` | open in a split / vertical split / vertical split (there are no tab pages) |
| `a` | add: `:Neotree add DIR/` is typed for you, a trailing `/` makes a folder |
| `d` | delete: `:Neotree delete PATH` is shown, Enter confirms, Esc cancels |
| `r` `m` `c` | rename / move / copy to: the command line holds the old path |
| `y` `x` `p` | copy, cut, paste into the folder under the cursor |
| `H` | toggle hidden files |
| `/` | filter (fuzzy; Esc clears it) |
| `z` | collapse all |
| `R` | refresh git status |
| `P` `i` | preview / info |
| `.` `u` `<BS>` | make the folder the root / go up a folder |
| `?` | help |
| `q` | close the tree |
| `<C-w>l` `<C-w>w` `<Esc>` | back to the editor window |
| `:` `<Space>` | the command line and leader keys work as everywhere |

Options: `:set treeglyphs` (Nerd Font icons), `:set treewidth=40`, `:set treehidden`.

## Layout

    m3.m31        entry point: arguments, terminal check, tui loop
    engine/            editing core, no terminal dependency
                       buffer text charclass case key parse num nrfmt motion textobj
                       register regex search editor ex vim view
    ui/                drawing, input and navigation
                       app keymap plugin window picker picker_view fuzzy files grep ignore tree git gitlib gitcmd
                       clip sources state vt lsp shell theme theme_data sample
    themes/            the built-in themes as .toml (scripts/gen_themes.sh embeds them in ui/MED_theme_data.m31)
    tests/             test.sh (entry), t_*.m31 unit programs, MED_check.m31, oracles/
    scripts/           build.sh, oracle.sh, gen_keymap.sh (docs/KEYMAP.md from the keymap table), gen_themes.sh
    docs/              KEYMAP.md (generated)
    DESIGN.md          plan, plugin audit, architecture, oracle plan, v0.1.0 acceptance
    RENAMES.md         old-to-new import and file table for the grouped layout

(`MED_` stands for "m3 edit".) Every module is `MED_<name>`, imported by path (`import engine.MED_buffer;`) and
used by its last segment (`MED_buffer.Buffer`). `engine/` imports nothing from
`ui/` and `tui`; `ui/` imports `engine/` and `tui`.

## Release

CI (`.github/workflows/test.yml`) runs `tests/test.sh` on Linux x86-64, Linux
aarch64 and macOS arm64 for every push to master. Pushing a `v*` tag runs
`.github/workflows/release.yml`: the test workflow is a hard precondition, then
it builds `m3` on the same three platforms and attaches
`m3-linux-x86_64`, `m3-linux-aarch64` and `m3-macos-arm64`
tarballs to the GitHub Release. The release is marked a pre-release; v0.0.2 is tagged on the
user's instruction. Version 0.1.0 is not tagged by the branch that introduced the default plugins; the lead tags after review.
