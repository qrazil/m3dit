# Divergence audit (0.26.0): what m3 carries from vim and nvim, and what it should keep

Status: **proposal for the owner to veto.** Nothing in this file has been removed or changed yet; the DROP and CHANGE items are implemented only after the owner confirms them, in small commits, each with a migration line in CHANGELOG.md.

Design law (owner): nvim and helix are idea sources; m3 does not copy their mistakes or their unwanted features. **Lean toward divergence when there is a good reason**: better or new functionality, a better default, a simpler design, or performance. Parity is a means, not a goal. The nvim oracle corpus stays the regression reference for the vi core (motions, operators, text objects, registers, marks, macros, ex basics, and every behaviour the corpus gates), which stays compatible by default; a divergence there needs a `tests/oracles/divergences.tsv` row and a one-line justification. docs/CORE-STATUS.md shows that file as a table.

Read for this audit: docs/NVIM-PARITY.md, docs/VI-CORE.md, docs/OPTIONS.md, docs/KEYMAP.md, the 72 oracle corpus files (`tests/oracles/corpus`, 42008 cases against nvim 0.11.5), `engine/MED_ex.m31` (the command table) and `engine/MED_option.m31`.

## Verdicts

| verdict | meaning |
|---|---|
| **KEEP** | core vi, muscle memory, or something m3 uses itself |
| **DROP** | legacy with no clear value: stop carrying it (remove it, or refuse it with a clear message) |
| **CHANGE** | keep the idea, give it a different m3 behaviour or default |
| **IMPROVE** | m3 can do better than vim/nvim: faster, clearer or a new capability; a concrete change and its benefit are proposed (section 5) |

The default for a legacy or odd vim behaviour is DROP or CHANGE. A **KEEP** needs a reason: it is core vi muscle memory (motions, operators, text objects, registers, marks, macros, ex basics), it is gated by the oracle corpus, or m3 uses it itself. Every CHANGE, IMPROVE and DROP carries its **migration** for someone coming from vim.

What "how sure" means below: items marked *(checked)* were checked against the code, `:set` behaviour or the oracle corpus in this audit; the others follow from the docs and are marked for confirmation before any work.

## Summary

| area | KEEP | CHANGE | DROP |
|---|---|---|---|
| options that act (153) | 153 | 0 | 0 |
| options stored only (173) | 7 | 23 | 142 |
| ex commands (241 names in the command table) | 210 | 18 | 13 |
| keys and behaviours | see sections 3 and 4 | | |

## 1. Options (docs/OPTIONS.md: 326 options, 153 act, 173 stored only)

### 1.1 Options that act: KEEP (153)

Every option the editor reads is kept: each one has an effect somebody can see, and a number of them (indent, wrap, search, folds, scrolling) are gated by the oracle corpus. Their names: `number` `relativenumber` `hlsearch` `incsearch` `list` `wrap` `cursorline` `showcmd` `softtabstop` `scrolloff` `hidden` `smartindent` `cindent` `magic` `undofile` `trimtrailing` `mouse` `background` `laststatus` `foldenable` `cmdheight` `splitbelow` `linebreak` `report` `shortmess` `whichwrap` `virtualedit` `selection` `nrformats` `matchpairs` `iskeyword` `fileformat` `fileencoding` `clipboard` `backspace` `formatoptions` `comments` `cpoptions` `smarttab` `shiftround` `foldmethod` `undolevels` `autoread` `belloff` `display` `sidescroll` `sidescrolloff` `numberwidth` `colorcolumn` `tabstop` `shiftwidth` `textwidth` `expandtab` `autoindent` `ignorecase` `smartcase` `wrapscan` `joinspaces` `startofline` `commentstring` `surround` `lsp` `lspcomplete` `lspformat` `semantictokens` `indentguides` `whichkey` `comment` `autopairs` `listchars` `fillchars` `wrapmargin` `scroll` `autowrite` `autowriteall` `autosave` `recover` `confirm` `wildmode` `completeopt` `showmatch` `cursorcolumn` `history` `switchbuf` `foldlevel` `foldminlines` `foldnestmax` `foldignore` `foldmarker` `foldlevelstart` `animate` `animatetime` `animatescroll` `animatefade` `animateflash` `scrollbar` `transparent` `finderscore` `finderhalflife` `cursorshape` `breakindent` `showbreak` `breakat` `breakindentopt` `endofline` `bomb` `readonly` `filetype` `syntax` `jumpoptions` `formatonsave` `pumkeys` `lines` `path` `suffixesadd` `tags` `grepprg` `makeprg` `shell` `errorformat` `isfname` `isident` `isprint` `paste` `indentkeys` `cinkeys` `cinoptions` `cinwords` `title` `statusline` `cursorlineopt` `backupcopy` `fsync` `buflisted` `cdpath` `complete` `diffopt` `foldclose` `foldopen` `keymodel` `mousemodel` `paragraphs` `scrollopt` `sections` `sessionoptions` `shada` `shellpipe` `tabclose` `viewoptions` `wildignore` `wildoptions` `write` `writedelay`.

### 1.2 Stored only: proposal

A **stored only** option is accepted by `:set`, keeps its value and changes nothing. That was a choice ("a `:set` in a user's init file must not stop at E518", docs/CORE-STATUS.md, Choices made without the owner). It has a cost: `:set noswapfile` or `:set lazyredraw` looks as if it did something, and `:set opt?` answers with a value nothing reads.

**Proposal** (owner decides):

1. The CHANGE rows below become options that act (small, each in its own commit).
2. The DROP rows are refused. Typed at the `:` prompt: `E5xx: 'swapfile' is not used by m3 (see docs/OPTIONS.md)` and nothing is stored. Read from a keymap or init file: no error and no stop; one line in `:messages` ("'swapfile' ignored: m3 has no swap file"), so a config shared with vim or nvim still loads.
3. `docs/OPTIONS.md` then lists only options that act, plus a short table of the refused names with the reason (this file's table is the source).
4. `scripts/options_doc.py` is fixed first: it searches `engine/` and `ui/` only, so options read by a plugin (`treewidth`, `treehidden`, `treeglyphs`, `todohl`, `bufferline`, `gitsigns`) are wrongly listed as stored only (row O1 *(checked)*).

| group | verdict | reason | migration | options |
|---|---|---|---|---|
| O1 | **KEEP** | acts in a plugin (explorer, todo, statusline, git); options_doc.py only looked in engine/ and ui/, so the table is wrong, not the option | none (the option already works; only the generated table was wrong) | `treewidth` `treehidden` `treeglyphs` `todohl` `bufferline` `gitsigns` |
| O2 | **CHANGE** | make it act: a user sets these expecting an effect and silent acceptance hides that they do nothing | the option starts to act; `:set nosplitright` (or the other off form) is the old behaviour; nobody could rely on a no-op | `splitright` `gdefault` `tildeop` `signcolumn` `timeout` `timeoutlen` `ttimeout` `ttimeoutlen` `modifiable` `fixendofline` `copyindent` `preserveindent` `scrolljump` `pumheight` `keywordprg` `formatprg` `equalprg` `infercase` `foldcolumn` `showtabline` `showmode` `ruler` `matchtime` |
| O3 | **DROP** | m3 has no swap file, backup file, viminfo or undo-reload: it keeps a recovery copy and an undo file of its own (docs/CORE-STATUS.md) | refused at the prompt, ignored with one `:messages` line from a file; behaviour does not change (m3 never had these files) | `swapfile` `backup` `writebackup` `backupext` `patchmode` `makeef` `updatecount` `undoreload` `shadafile` `writeany` |
| O4 | **DROP** | the screen is always redrawn from a true-colour, UTF-8 model; there is nothing to tune | same as O3; the screen model is unchanged | `lazyredraw` `redrawtime` `termguicolors` `encoding` `fileencodings` `fileformats` `endoffile` `synmaxcol` `maxmempattern` `conceallevel` `regexpengine` `columns` |
| O5 | **DROP** | right-to-left, input methods, digraphs, Lisp and key remapping layers: not planned, no oracle case | same as O3; no feature disappears because none was there | `revins` `rightleft` `allowrevins` `iminsert` `imsearch` `digraph` `lisp` `lispoptions` `langmap` `langremap` `casemap` `emoji` `ambiwidth` `delcombine` |
| O6 | **DROP** | m3 lays out windows and tab pages itself (equal sizes, one panel); these size and bind knobs have no counterpart | same as O3; window layout is unchanged | `equalalways` `winheight` `winminheight` `winwidth` `winminwidth` `winfixheight` `winfixwidth` `winfixbuf` `winhighlight` `winblend` `winborder` `winaltkeys` `splitkeep` `tabpagemax` `eadirection` `scrollbind` `cursorbind` `previewwindow` `previewheight` `helpheight` `cmdwinheight` `winbar` |
| O7 | **DROP** | an expression or function option: m3 has no Vimscript or Lua, so the option can never act; a user script cannot set it either | same as O3; a script that needs a function option has to be an m31 plugin | `operatorfunc` `completefunc` `omnifunc` `tagfunc` `findfunc` `formatexpr` `indentexpr` `includeexpr` `foldexpr` `foldtext` `thesaurusfunc` `quickfixtextfunc` `statuscolumn` `rulerformat` `tabline` |
| O8 | **DROP** | tag-file details of vi that no ctags file in use needs: the stack and the files are read, these refine them | same as O3 | `tagstack` `tagcase` `taglength` `tagbsearch` `tagrelative` `showfulltag` |
| O9 | **DROP** | vi compatibility switches that nvim already removed or fixed (nvim has no 'terse', 'warn', 'more' prompts, 'exrc' risk, modelines are off for security in most setups) | same as O3; `modeline` stays refused on purpose (security) | `terse` `warn` `more` `exrc` `secure` `modeline` `modelines` `modelineexpr` `debug` `verbose` `verbosefile` `eventignore` `maxfuncdepth` `maxmapdepth` |
| O10 | **DROP** | Select mode and paste hacks (docs/NVIM-PARITY: selection stays a Visual feature only) | same as O3 | `selectmode` `pastetoggle` |
| O11 | **DROP** | bells, titles and menus of a terminal vi: m3 draws none of them | same as O3 | `visualbell` `errorbells` `titlelen` `titleold` `titlestring` `menuitems` `messagesopt` `showcmdloc` `cedit` `wildmenu` `wildchar` `wildcharm` |
| O12 | **DROP** | mouse tuning that the terminal library decides | same as O3 | `mousefocus` `mousehide` `mousemoveevent` `mousescroll` `mousetime` |
| O13 | **DROP** | completion sources and file lists the finder replaces (dictionary, thesaurus, include, define, suffixes, wildignorecase) | same as O3; use the finder for file and word lists | `dictionary` `thesaurus` `include` `define` `suffixes` `wildignorecase` `fileignorecase` `grepformat` `helplang` `loadplugins` |
| O14 | **DROP** | shell plumbing: m3 runs commands itself through one shell invocation | same as O3; `:set shell` stays (it acts) | `shellcmdflag` `shellquote` `shellredir` `shellxescape` `shellxquote` `shelltemp` `autochdir` |
| O15 | **DROP** | buffer-type switches for features m3 does not have (diff mode, bound buffers, quoted escapes) | same as O3; `inccommand` and `updatetime` move to IMPROVE (section 5) | `bufhidden` `buftype` `diff` `binary` `modified` `quoteescape` `spell` `inccommand` `updatetime` |
| O16 | **KEEP** | m3 animates scrolling by itself (`:set animate`); the option is accepted for a shared config and stays harmless | none; stays accepted so a shared config loads | `smoothscroll` |
| O17 | **DROP** | Vim's 'varsofttabstop' / 'vartabstop' (variable tab stops): rare, no oracle case | same as O3 | `varsofttabstop` `vartabstop` |
| O18 | **DROP** | 'pumblend' 'pumwidth': the completion popup is drawn by m3 with the theme | same as O3 | `pumblend` `pumwidth` |

## 2. Ex commands (the 241 names in `command_table()` of `engine/MED_ex.m31`)

| group | verdict | reason | migration | commands |
|---|---|---|---|---|
| X1 | **KEEP** | core vi / ex, under the oracle corpus (45-50, 78, 118, 119) | - | `substitute` `delete` `move` `t` `copy` `join` `global` `vglobal` `yank` `undo` `redo` `put` `normal` `k` `mark` `number` `print` `set` `setlocal` `setglobal` `read` `write` `wq` `quit` `update` `xit` `wall` `qall` `wqall` `xall` `edit` `file` `sort` `retab` `left` `right` `center` `earlier` `later` `registers` `display` `marks` `jumps` `changes` `messages` `echo` `echomsg` `execute` `let` `history` `pwd` `version` `redraw` `nohlsearch` `startinsert` `stopinsert` `noautocmd` `undojoin` `delmarks` `fold` `foldopen` `foldclose` |
| X2 | **KEEP** | mapping, abbreviation and command definition (corpus 60-64, 104, 105, 117) | - | `map` `nmap` `vmap` `xmap` `omap` `imap` `cmap` `noremap` `nnoremap` `vnoremap` `xnoremap` `onoremap` `inoremap` `cnoremap` `unmap` `nunmap` `vunmap` `xunmap` `ounmap` `iunmap` `cunmap` `mapclear` `nmapclear` `vmapclear` `xmapclear` `omapclear` `imapclear` `cmapclear` `abbreviate` `iabbrev` `noreabbrev` `inoreabbrev` `unabbreviate` `iunabbrev` `abclear` `iabclear` `cabbrev` `cnoreabbrev` `cunabbrev` `cabclear` `autocmd` `augroup` `doautocmd` `command` `delcommand` `source` |
| X3 | **KEEP** | buffers, windows and tab pages, the daily set | - | `enew` `bnext` `bprevious` `bNext` `buffer` `bdelete` `bwipeout` `bunload` `bfirst` `brewind` `blast` `ls` `buffers` `files` `close` `only` `split` `vsplit` `new` `vnew` `wincmd` `resize` `vertical` `tab` `tabnew` `tabedit` `tabnext` `tabprevious` `tabNext` `tabfirst` `tabrewind` `tablast` `tabclose` `tabonly` `tabs` `tabmove` `checktime` `recover` `preserve` |
| X4 | **KEEP** | m3's own commands (capitalised, plugin-owned or core features): not vim behaviour | - | `Rename` `Delete` `Create` `Mkdir` `Files` `Buffers` `Grep` `Commands` `help` `Explore` `Sexplore` `Vexplore` `Keys` `Plugins` `PluginEnable` `PluginDisable` `Recent` `Registers` `Symbols` `Branches` `Commits` `Changed` `colorscheme` `theme` `Session` `terminal` `Lsp` `Formatter` `Profile` `highlight` `syntax` `filetype` |
| X5 | **KEEP** | the argument list and the replace-everywhere family (`:argdo`, `:bufdo`, `:cdo` are how project-wide replace works) | - | `args` `next` `Next` `previous` `argadd` `argdelete` `argdo` `windo` `tabdo` `bufdo` `cdo` `cfdo` |
| X6 | **KEEP** | `:make`, `:grep` and `:vimgrep` fill the generic list (0.25.0) | - | `make` `grep` `vimgrep` |
| X7 | **KEEP** | the generic list (0.25.0) | - | `List` `ListNext` `ListPrev` `ListFirst` `ListLast` `ListClear` `lnext` `lprev` `lfirst` `llast` `lclear` `list` |
| X8 | **CHANGE** | the `:c*` quickfix commands stay as thin aliases on the default list for the oracle and vim habit; decide whether `:cdo` / `:cfdo` stay and the rest go (the list commands above do the same job) | one release with a message `:cnext is :lnext`, then the `:c*` names go except `:cdo` / `:cfdo` (decision 4); `:command Cn lnext` in a keymap file restores any of them | `cc` `clist` `cwindow` `copen` `cclose` `cnext` `cprevious` `cNext` `cfirst` `clast` |
| X9 | **DROP** | `l` forms that exist only because vim has a location list; they are the same command as the plain form here | `:lgrep` -> `:grep`, `:lvimgrep` -> `:vimgrep`, `:lmake` -> `:make` (same result today); a message names the replacement | `lgrep` `lvimgrep` `lmake` |
| X10 | **DROP** | `:z` prints a page of lines and `:first`/`:rewind`/`:last`/`:wnext` walk the argument list under names that shadow nothing a visual editor needs; `:z` has no use with a screen, the rest duplicate `:next`/`:previous` | `:z` -> `<C-f>` / `:5` / `z<CR>`; `:first` `:last` `:rewind` -> `:args` + `:next` / `:previous`; none needs a profile | `z` `first` `rewind` `last` `wnext` |
| X11 | **DROP** | Ex-mode extras: `:append` `:insert` `:change` read text a line at a time up to `.`; useful in a script piped into ex, which m3 cannot be (no headless mode) | scripts that pipe text into `ex` cannot run anyway (no headless mode); interactively use `o` / `O` / `cc` | `append` `insert` `change` `exinput` `visual` |
| X12 | **CHANGE** | a ctags match list is a list: `:tag` with several matches should fill the generic list (walked with `:lnext`) instead of keeping a private match index; then `:tnext` `:tprevious` `:tNext` `:trewind` `:tfirst` `:tlast` `:tselect` `:tjump` go (today `:tselect` and `:tjump` already jump to the first match like `:tag`) | `:tag` with several matches opens the list; `:lnext` / `]l` replace `:tnext`; `:tselect` -> `:tag`; the first match still opens directly | `tselect` `tjump` `tnext` `tprevious` `tNext` `trewind` `tfirst` `tlast` |
| X13 | **KEEP** | tags: `:tag`, `:pop`, `:tags` and CTRL-] / CTRL-T over ctags files | - | `tag` `pop` `tags` |
| X14 | **KEEP** | `write!` is the engine's spelling of `:w!` | - | `write!` |

Tension to settle: docs/VI-CORE.md lists `:append` `:insert` `:change`, `gQ` Ex mode and `:z` because POSIX `vi`/`ex` require them. Group X10 and X11 propose dropping them anyway, since m3 has no headless mode and no teletype Ex mode to make them useful. If the owner wants POSIX completeness, veto those two groups.

Search and substitute (the corpus covers all of it, 46 and 85):

| item | verdict | reason |
|---|---|---|
| `:s` flags `g c i I n e &` and `\=` expressions | **KEEP** | daily use; `\=` is the one Vimscript-flavoured feature people really use |
| `:s` flags `#` `l` `p` (print the last line afterwards) and `r` | **DROP** | print flags have no use without a teletype; `r` only changes which pattern `&` reuses |
| `'magic'` / `\M` `\V` very-magic modes | **KEEP** | in the regex corpus (185 cases) |
| `'wrapscan'`, `'ignorecase'`, `'smartcase'`, `'incsearch'`, `'hlsearch'` | **KEEP** | act |

## 3. Keys

The leader trees (`<Space>...`) are m3's own and were decided in 0.22.0 (docs/KEYMAP-REVIEW.md); this section is about the keys that came from vim.

| chord | verdict | reason | migration |
|---|---|---|---|
| `gg` `ge` `gE` `gj` `gk` `g0` `g^` `g$` `g_` `gm` `gM` `go` `gi` `gI` `gJ` `gp` `gP` `gv` `g;` `g,` `g&` `g-` `g+` `g*` `g#` `gn` `gN` `gu` `gU` `g~` `gw` `gq` `gx` `gf` `gF` | **KEEP** | everyday editing and navigation, in the corpus | - |
| `ga` | **KEEP** | shows the code point under the cursor; cheap and handy with UTF-8 | - |
| `g8` | **DROP** | the UTF-8 byte sequence of the character; `ga` and `:ascii`-style answers cover the need | `ga` shows the code point; `:echo` is not needed |
| `g?` `g??` `g?g?` (rot13) | **DROP** | an operator for a joke cipher; the one chord in the corpus that exists only for fun | `:%s/.../\=rot13/` is not provided; use an external filter `!{motion}tr A-Za-z N-ZA-Mn-za-m` |
| `gR` `gr` virtual replace | **DROP** | `gR` is handled "like Replace mode" (engine note), so it pretends to be Virtual Replace; `gr` is taken by LSP references in nvim 0.11 anyway | `R` (Replace mode); the difference only shows on tabs |
| `gQ` Ex mode | **DROP** | see group X11; the command line is already the Ex line | the command line `:` |
| `gh` `gH` Select mode | **CHANGE** | already repurposed as the hunk operators (0.23.0); m3 has no Select mode and will not get one | none (the keys are the hunk operators now) |
| `gs` sleep, `g CTRL-G`, `g CTRL-H`, `gK` | **DROP** | obscure; `gK` runs 'keywordprg' on a visual selection | none |
| `zt` `zz` `zb` `z<CR>` `z.` `z-` `zh` `zl` `zH` `zL` `zs` `ze` | **KEEP** | scrolling, with the animation (`:set animate`) | - |
| `zo` `zO` `zc` `zC` `za` `zA` `zv` `zx` `zX` `zm` `zM` `zr` `zR` `zn` `zN` `zi` `zf` `zF` `zd` `zD` `zE` `zj` `zk` | **KEEP** | folding (corpus 101, 108, 110, 111, 113) | - |
| `z=` `zg` `zG` `zw` `zW` `zug` `zuw` (spell) | **DROP** | 'spell' is stored only and there is no spell checker (docs/CORE-STATUS.md); the keys do nothing | none (no spell checker); a `spell` plugin could return the keys |
| `z^` `z+` `zp` `zP` `zy` | **DROP** | page-line scrolls and block yank without trailing blanks; rare, no value beside `<C-f>` / `<C-b>` and `y` | `<C-f>` / `<C-b>`, `y` |
| `[(` `[{` `])` `]}` `[[` `]]` `[]` `][` `['` `]'` `` [` `` `` ]` `` `[p` `]p` `[z` `]z` | **KEEP** | motions in the corpus; `[p` `]p` paste with indent | - |
| `[m` `]m` `[M` `]M` (Java methods), `[*` `]*` `[/` `]/` (C comments), `[#` `]#` (#if), `[s` `]s` (spelling), `[i` `[I` `[d` `[D` `[f` (include search) | **DROP** | C-source navigation of 1990s vi; LSP symbols, the finder and `]d` diagnostics do these jobs; `[d` `]d` stay as m3's diagnostics pair | `]d` for diagnostics, the finder `<Space>fs` for symbols, `%` for blocks |
| `CTRL-W` window commands `s v n c o q w h j k l H J K L x r R + - < > = _ | T` | **KEEP** | the window set (corpus 81 and the pty tests) | - |
| `CTRL-W ]` `CTRL-W f` `CTRL-W P` `CTRL-W z` `CTRL-W }` (preview window, tag in a split) | **DROP** | there is no preview window; the finder previews | the finder previews; `CTRL-]` jumps |
| `CTRL-V` visual block, `CTRL-A` `CTRL-X` (and `g CTRL-A`), `CTRL-O` `CTRL-I`, `CTRL-E` `CTRL-Y` `CTRL-D` `CTRL-U` `CTRL-F` `CTRL-B` | **KEEP** | core | - |
| `Q` (replays the last macro), `K` (hover / keywordprg), `Y` (= `y$`) | **KEEP** | nvim 0.11 defaults; recorded in the divergences table where they differ from vi | - |
| `U` (undo line) | **KEEP** | vi muscle memory; in corpus 41; low cost | - |
| `ZZ` `ZQ` | **KEEP** | vi muscle memory | - |
| insert-mode `CTRL-K` digraphs | **KEEP** | `engine/MED_digraph.m31` exists and `CTRL-K a:` is a fast way to type symbols; only the 'digraph' option (BS-composed digraphs) is dropped | - |
| insert-mode `CTRL-X` completion submodes (`CTRL-X CTRL-L` ...) | **CHANGE** | the LSP popup plus `CTRL-N` / `CTRL-P` keyword completion exist; the submodes are a separate vi-era key language (needs confirmation which exist) | - |
| `<Space>xL` and `<Space>xQ`, `<Space>fq`, `<Space>sq` (the list) | **CHANGE** | four default slots open the same list since 0.25.0; keep `<Space>xQ` (his key) and one of `fq` / `sq` per profile, drop the duplicate `xL` in the default profile | - |

The chords above are those that occur in the oracle corpus: `g` followed by one of `!#$&'*+,-/038:;<>?EIJMNPRSTU^_`acegijklmnopqrstuvwx|~` and `z` followed by one of `!'+-./02345:;<=>ACDEFGHJLMNOPRVX[]^abcdefghijklmnoprstvwxyz{|}~` (a rough text scan, so a character may be there by accident); a chord not in the corpus is judged from the docs and marked for confirmation.

## 4. Behaviours

| behaviour | verdict | reason | migration |
|---|---|---|---|
| one list store (no per-window location lists) | **KEEP** | done in 0.25.0; docs/LIST.md | - |
| old tag stack details: `tagstack`, `tagcase`, `taglength`, `tagbsearch`, the `;` upward search | **DROP** | ctags files are read linearly; nothing needs the refinements (group O8) | - |
| cscope | **DROP** | never built; stays absent | none |
| Select mode | **DROP** | never built; stays absent (`selectmode` refused) | `v` / `V` with an operator |
| open mode (`:open`, `:ex`) | **DROP** | never built; nvim has none either | - |
| swap files, backup files, viminfo / shada | **DROP** | m3 keeps one recovery copy per modified buffer and an undo file of its own | - |
| Vimscript (functions, `if`/`while`, expressions) beyond `:let` of simple values, `\=` in `:s`, `"=` register | **KEEP** | what exists stays; m3 does not grow a Vimscript (an m31 plugin is the extension language) | - |
| modelines | **DROP** | a security risk with little use; `modeline` is stored only | put the settings in `.m3.vim` / the project config (`MED_projconf`) |
| 'compatible' mode and its `cpoptions` flags | **DROP** | nvim is never in vi-compatible mode; m3 follows nvim | - |
| `:set` forms `opt&` `opt!` `invopt` `opt+=` `opt-=` `opt^=` `opt?` | **KEEP** | the option grammar; in corpus 97 | - |
| 'wrapmargin' (acts since 0.20.0, for POSIX vi) | **DROP** | 'textwidth' is the better tool and wrapmargin depends on the window width; added for POSIX completeness only (owner decides: veto if vi completeness is wanted) | - |
| 'paragraphs' and 'sections' (nroff macros `.PP`, `.SH`) read by `{` `}` `[[` `]]` | **KEEP** | oracle-gated (corpus 119) and cheap; `{` `}` are core motions | - |
| undo: `u` `CTRL-R` `U` `g-` `g+` `:earlier` `:later`, undo files | **KEEP** | core; corpus 41, 49, 75, 116 | - |
| registers: `"a-z` `"A-Z` `"0-9` `"-` `"_` `".` `":` `"/` `"%` `"=`, `"*` `"+` | **KEEP** | core; corpus 74, 106 | - |
| marks: `a-z` `A-Z` `'[ '] '< '> '^ '. '"` and `0-9` (file marks of viminfo) | **KEEP** | the letter marks and the change marks; the file marks `0-9` come from shada, which m3 does not have (not verified that they are absent: confirm before dropping) | - |
| folds: manual, indent, marker, and the m3 `autofold` | **KEEP** | corpus 101, 108, 110, 111, 113; syntax / expr folds need Vimscript or tree-sitter and do not exist | - |
| `:s` with a count and `:&&` `g&` | **KEEP** | corpus 46 | - |
| `CTRL-R CTRL-W` / `CTRL-R CTRL-R x` / `CTRL-R CTRL-O x` (literal register insert) | **KEEP** | in corpus 79 where present; cheap | - |

## 5. IMPROVE: where m3 can do better than vim and nvim

Each row is a proposal with its benefit and its migration. Performance rows say "measure first": the harness is `bench/uxperf.py` (docs/UX-PERF.md) and a before/after number goes into the commit that makes the change, as in 0.8.0. The oracle-gated engine behaviour does not change; where a row touches it the divergences.tsv entry is named.

### 5.1 Defaults

The engine keeps vim's defaults (`tabstop=8`, `shiftwidth=8`, `ignorecase` off ...) because the oracle runs the bare engine against `nvim -u NONE`. The **`default` profile** is where m3 starts better; `:Profile legacy` is the vim-flavoured escape hatch that already exists for keys, and would also reset these options.

| id | change | benefit | migration |
|---|---|---|---|
| D1 | the `default` profile sets `ignorecase` + `smartcase`, `scrolloff=5`, `splitright`, `splitbelow`, `undofile`, `shiftwidth=4` + `expandtab` unless a project config or `.editorconfig`-style file says otherwise | the first minute in the editor matches what nearly every vim/nvim user configures first; no oracle impact (engine defaults are untouched) | `:Profile legacy`, or `:set` lines in the keymap file; projects keep their own settings through `MED_projconf` |
| D2 | `undofile` on by default in the `default` profile | undo survives restarts and crashes; the state directory is already used for recovery files | `:set noundofile` |
| D3 | `formatonsave`, `animate`, mouse and the sign column are already on | (done) | - |

### 5.2 Capabilities

| id | change | benefit | migration |
|---|---|---|---|
| C1 | live `:s` preview (the idea of nvim's `inccommand`, which is stored only today): the buffer shows the replacement while the command line is open, Esc undoes it | see the result before Enter; replaces the habit of `:s///gc` or undo after a mistake | `:set noinccommand`; nothing else changes |
| C2 | `:marks` `:registers` `:jumps` `:changes` `:ls` `:messages` open as finder lists with a preview and jumping (the generic list for jumps and changes, so `]l` walks them) instead of a text dump over the screen | one UI for every list; selectable; searchable | `:set listoutput=text` (a small option) keeps the dump; the text form of `:ls`, `:registers` and `:marks` can be had with `:redir`-style commands only through that option |
| C3 | search match count `[3/17]` in the message line while searching, as nvim shows with `shortmess-=S` | nvim hides it by default; knowing there are 17 matches is the common reason to press `n` | `:set noshowmatchcount` |
| C4 | `:tag` with several matches fills the generic list (group X12) | one list UI for tags, grep, references and hunks | `:lnext` / `]l`; the first match still opens directly |
| C5 | one-key `:set` typo help: an unknown or refused option answers with the nearest name (`'splitrigth' is not an option; did you mean 'splitright'?`) | the refusal in 1.2 is friendlier than silence | none |

### 5.3 Performance candidates (measure first)

What the code shows today: a buffer is `List<str>` of lines (`engine/MED_buffer.m31`); the undo tree stores `Edit` splices and each undo node copies the marks map (`node.namedm = snapshot_named()` in `engine/MED_editor.m31`); the regex is m3's own (`engine/MED_regex.m31`); syntax and folds run per window; plugins are compiled in. UX-PERF.md budgets: key to first byte p50 under 5 ms (measured 1.6-1.9 ms at 80x24); a 1 MB unbracketed key storm took 29.7 s (about 30 microseconds per key) and a 1 MB bracketed paste 0.25 s.

| id | candidate | benefit | how to measure | migration |
|---|---|---|---|---|
| P1 | **start-up**: look at what runs before the first frame (option table, keymap trees for all profiles, plugin activation, syntax tables); build only the active profile's tree and activate plugins on their trigger (`wants`, filetype, first use) | stay inside the +2 ms rule while plugins grow | `m3 --version` wall time and first-frame time over 50 runs, before and after | none (behaviour identical) |
| P2 | **large files**: a `largefile` threshold (a size or a long line) that switches off syntax, guides, folds-by-syntax and the sign column for that buffer, with a message and `:set nolargefile` to override; chunk the line list only if measurement shows O(n) line insertion/deletion hurts (a 1M-line file with `:g/x/d`) | opening a 200 MB log is instant instead of unusable; the list structure stays simple until proven slow | open and `G` on a 100 MB file; `:g/pat/d` on 1M lines | `:set nolargefile`; a message tells why highlighting is off |
| P3 | **undo memory**: store only the marks that changed in an undo node (or share an immutable map) instead of copying the whole marks map per node | memory grows with edits, not with edits times marks | resident size after 100k edits with 26 marks | none |
| P4 | **regex**: compile a pattern once per `:s` / `:g` / search command (not per line), and skip lines with a literal-prefix / required-byte test before the matcher runs | `:%s/x/y/g` and `:g/pat/` on a million lines | `:%s` and `:g` timings over a 1M-line file, same results against the 185-case regex corpus | none; output identical (the corpus gates it) |
| P5 | **redraw**: only the changed cells are sent already (UX-PERF.md: a cell move under 400 bytes); look at the cost of recomputing wraps and syntax for the whole window on a one-cell change | keep key-to-frame flat on very long lines and wrapped files (12.9 ms p50 on the 340-column wrap case) | `bench/uxperf.py --only wrap,key` | none |
| P6 | **input storms**: 30 microseconds per key for held `j`/`k` in a storm; profile one key through parse, mapping, engine and frame planning | a pasted macro or a key-repeat storm finishes in a third of the time | `bench/uxperf.py --only storm` | none |

### 5.4 Oracle impact of the DROP and CHANGE items

Upper bounds: a count is the number of the 42008 corpus cases whose key text contains the chord or command (it may sit inside a pattern or in Insert mode). Each accepted item needs a `divergences.tsv` row (`skip` for cases it makes meaningless, `flip` where nvim still does something m3 refuses) and a one-line justification; no row means no divergence. Where the count is large (`:z`: 315 cases in the vi-core files) the behaviour is gated by the corpus and stays compatible unless the owner accepts the justification.

| item | corpus cases (upper bound) | files |
|---|---|---|
| `g?` rot13 | 71 | 115_core_ex_motion_probe.txt, 116_core_undo_dot_opts_probe.txt, 43_opmarks.txt, 73_ops.txt |
| `gR` virtual replace | 41 | 115_core_ex_motion_probe.txt, 79_insert.txt, 98_textwidth.txt |
| `g8` | 17 | 116_core_undo_dot_opts_probe.txt, 73_ops.txt |
| `:z` | 315 | 118_vi_core.txt, 119_vi_options_ex.txt, 50_ex_z.txt |
| `:append` `:insert` `:change` | 3 | 118_vi_core.txt |
| `:s` print flags `#` `l` `p` | 11 | 86_cmdline.txt |
| 'wrapmargin' | 2 | 116_core_undo_dot_opts_probe.txt, 119_vi_options_ex.txt |
| spell keys `z=` `zg` `zG` `zw` `zW` | 42 | 101_folds_fuzz.txt, 108_autofolds.txt, 113_marker_folds.txt, 119_vi_options_ex.txt, 50_ex_z.txt |
| `zp` `zP` `zy` `z^` `z+` | 68 | 101_folds_fuzz.txt, 108_autofolds.txt, 113_marker_folds.txt, 115_core_ex_motion_probe.txt, 50_ex_z.txt |
| `CTRL-W ]` `f` `P` `z` `}` | 7 | 92_autopairs_fuzz.txt |
| `:lgrep` `:lvimgrep` `:lmake` | 0 |  |
| marks `0-9` | 8 | 106_marks_registers.txt, 48_ex_misc.txt, 92_autopairs_fuzz.txt |

## 6. Divergence tooling (done in this milestone)

* `tests/oracles/divergences.tsv` is the single source: `id`, vim behaviour, m3 behaviour, reason, `oracle` (`skip`, `flip`, `doc`) and a `selector` (a regular expression searched in a case's key notation).
* `tests/oracles/oracle_nvim.py` reads it: `skip` takes the matching corpus cases out of the comparison (counted, listed with `-v`), `flip` keeps them and expects them to differ (and reports one that starts to match), `doc` marks a divergence the corpus cannot see.
* `scripts/divergences.py --write docs/CORE-STATUS.md` generates the table "Deliberate divergences from vim/nvim"; `--check` is part of `tests/test.sh`, so the table cannot drift from the file.
* `tests/oracles/known_divergences.txt` stays for single cases that are artifacts of the headless harness; the eight `:l` / `:list` cases it carried moved into `divergences.tsv` as two `skip` rows.

## 7. What the owner decides

1. The DROP rows of sections 1 to 4: yes / no per group id (O2 .. O18, X8 .. X12, and the key and behaviour rows).
2. Refuse or ignore for stored-only options: the two-way rule of 1.2 (error at the prompt, a `:messages` line from a file).
3. The tension in section 2 (POSIX `:append` `:z` `gQ` against "no headless mode").
4. Whether `:cc` `:clist` `:cwindow` `:copen` `:cclose` `:cnext` ... (X8) go now or after a release.

Nothing is implemented until the owner answers; each accepted group becomes one small commit with a CHANGELOG migration line (and an `E` message for a refused option).
