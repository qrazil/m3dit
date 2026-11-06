# Plugin landscape: what else should m3 build?

Status: decision document, 2026-11-05, against m3 0.20.0 (master 7665cf9). No code. It answers three questions from the owner:
(1) is `docs/NVIM-PARITY.md` a complete inventory of what he uses, (2) what do the popular setups ship that m3 does not,
(3) what to build, in what form (core, default plugin, opt-in plugin, not planned) and in what order. It builds on
`docs/CORE-AND-PLUGINS.md` (decision record, section 10 seams), `docs/CORE-STATUS.md`, `docs/DAILY-DRIVER.md`, `docs/VI-CORE.md`
and `docs/EXTENSIONS.md`; it does not repeat what they already say is done or planned (git plugin, explorer, terminal, surround,
autopairs, which-key to core, `colors`, `icons`, `trouble`, `indentscope`, markdown render).

How the research was done (everything below was read, nothing is from memory unless it says "not verified"):

* Owner's config: `~/.config/nvim` (init.lua, `lua/config/*.lua`, all 53 `lua/plugins/*.lua`, `lazy-lock.json`, 62 entries) and the 19
  `nox*.git` repos cloned read-only to a scratch directory, plus `apps/nox/NOX_API.md`.
* Setups: shallow clones of LazyVim, AstroNvim, astrocommunity, NvChad, LunarVim, kickstart.nvim, folke/snacks.nvim,
  nvim-mini/mini.nvim and mawww/kakoune (default branches, 2026-11-05); the READMEs of snacks and mini.nvim; Helix and Zed
  documentation pages; Helix's own crates inside the `nox` repo (it is a Helix fork).
* Stars: GitHub REST API, unauthenticated, fetched 2026-11-05. A "?" means not fetched; no number is estimated.
* WebFetch and WebSearch worked. WebFetch summarises pages with a small model, so claims taken from a fetched page (Helix and
  Zed rows) are marked with the page; claims taken from cloned source are exact.

Sources (URLs):
https://github.com/folke/snacks.nvim (README, `docs/*.md`, `lua/snacks/picker/config/sources.lua`) ·
https://github.com/nvim-mini/mini.nvim (README, `readmes/*.md`) ·
https://github.com/LazyVim/LazyVim (`lua/lazyvim/plugins/*.lua`, `plugins/extras/*`, `config/{keymaps,autocmds,init}.lua`) ·
https://www.lazyvim.org/extras · https://github.com/AstroNvim/AstroNvim (`lua/astronvim/plugins/*.lua`) ·
https://github.com/AstroNvim/astrocommunity (`lua/astrocommunity/*`) · https://github.com/NvChad/NvChad (`lua/nvchad/plugins/init.lua`, `mappings.lua`) ·
https://github.com/LunarVim/LunarVim (`lua/lvim/plugins.lua`) · https://github.com/nvim-lua/kickstart.nvim (`init.lua`) ·
https://docs.helix-editor.com/editor.html · https://docs.helix-editor.com/keymap.html ·
https://github.com/zed-industries/zed (`docs/src/SUMMARY.md`, `git.md`, `finding-navigating.md`, `running-testing.md`, `editing-code.md`) ·
https://zed.dev/docs/ · https://github.com/mawww/kakoune (`README.asciidoc`, `rc/`) · https://api.github.com/repos/OWNER/REPO (stars).

---

## 1. Question 1: is NVIM-PARITY a complete inventory?

**Answer: complete at the level of plugin spec files, not complete at the level of the config's contents.** All 53 files in
`lua/plugins/` have a row (checked file by file), the options in `init.lua` (8 of 8) and the keymaps in `keymaps.lua` (21 maps) are all
there, and the row counts in the doc are right (66 rows: done 27, partial 20, missing 6, out 13; recounted with awk). What it
misses is below: plugins that are in the lockfile but have no spec file, behaviour inside a spec that is not named, key
collisions, and two statements that are too optimistic.

### 1.1 Everything in the config (complete list)

Active means not `enabled = false`. Source: spec files plus `lazy-lock.json`.

| area | active | disabled in the spec | present only in the lockfile (no spec file) |
|---|---|---|---|
| plugin manager | lazy.nvim (`checker.enabled = true`: update check) | | |
| LSP | nvim-lspconfig, mason, mason-lspconfig (ensure: lua_ls, pyright, rust_analyzer, eslint), nvim-java (jdtls) | | **nvim-lsp-file-operations**, **spring-boot.nvim**, **nvim-dap** |
| completion | blink.cmp (+ minuet-ai source), LuaSnip, friendly-snippets | nvim-cmp (+ cmp-buffer/path/cmdline/nvim-lsp), copilot, copilot-cmp | |
| treesitter | nvim-treesitter (15 languages ensured, `auto_install`, highlight + indent) | | |
| formatting | conform.nvim (`format_on_save`, 7 file types, custom `spotless_maven`, file-based, `stdin = false`) | | |
| find | mini.pick + mini.extra (files, grep current buffer, resume, buffers, quickfix, explorer, git files/hunks/branches/commits, LSP pickers, diagnostics) | fzf-lua (with no-ignore and invert-match toggles) | |
| files | mini.files (`R` refresh, `gs` sort by mtime, `winblend = 0`) | neo-tree, nvim-window-picker (neo-tree dep) | **nvim-window-picker** |
| git | gitsigns (current-line blame ON, `numhl`, 18 maps), diffview, vim-fugitive, git-conflict | neogit, mini.diff | |
| motion/edit | mini.surround, mini.move, mini.bracketed, mini.indentscope, nvim-autopairs, harpoon (harpoon2), marks.nvim, buffer_manager | mini.jump2d | |
| UI | lualine (transparent), nvim-notify, which-key, trouble, todo-comments, nvim-ufo, neoscroll, markview, nvim-highlight-colors, no-neck-pain, colortils, mini.colors, nvim-web-devicons, nui | indent-blankline, aerial, `block` (private) | |
| themes | gruvbox-material (hard, italics, transparent) | nightfox, tokyonight | |
| AI | claude-code.nvim, CodeCompanion, minuet-ai | avante, CopilotChat, copilot | |
| tests | | neotest | |
| autocmds | none live (`autocomds.lua` is all comments); the blink spec re-applies transparent highlight groups on `ColorScheme` | | |
| options | mouse, tabstop 4, expandtab, shiftwidth 4, relativenumber, ignorecase, smartcase, smoothscroll (plus ufo: foldcolumn 0, foldlevel 99, foldenable) | | |

### 1.2 Gaps in NVIM-PARITY

| # | gap | what the doc says | what is true | action |
|---|---|---|---|---|
| G1 | **nvim-dap is installed.** It is in the lockfile as a dependency of nvim-java (which bundles java-debug and java-test) and is not mentioned anywhere in the doc | nothing | the owner has a debugger and a Java test runner in his editor whether he uses them or not; DAP is "declined" in ROADMAP item 18 | owner decision D1 below |
| G2 | **nvim-lsp-file-operations** (active, a neo-tree dependency): renaming or moving a file in the tree sends `workspace/willRenameFiles` so the server fixes imports | no row | m3's tree renames files, sends nothing to the server | new row; feature F7 below |
| G3 | **spring-boot.nvim**, **nvim-java** specifics: `jdt://` class URIs for definitions into decompiled classes, `workspace/executeCommand` actions, organise imports | row says `out` / "servers must be on PATH" | jdtls needs init options, `jdt://` document content (`java/classFileContents`), and commands; with only PATH lookup, Java works at the level of diagnostics, completion, hover and goto in source only (not verified by running jdtls) | owner decision D6; keep `out`, say so in the row |
| G4 | **LSP pickers**: `gd gr gi gt` (definition, references, implementation, type definition) and `<leader>ds dw dd` (document symbols, workspace symbols, diagnostics) go through mini.extra pickers | row "LSP pickers" under fzf-lua/mini.pick = `partial` | CORE-STATUS says `textDocument/documentSymbol`, `workspace/symbol`, `typeDefinition`, `implementation` are not requested at all. Four of the seven keys cannot work today. The nvim-lspconfig row says `done` and hides this | downgrade lspconfig row to `partial`; feature F1 |
| G5 | `<leader>gp` (pick a remote branch, open Diffview against it) and `<leader>gdr` (diff HEAD against a remote branch) | not listed | not built, depends on a diff view | new rows; F5 |
| G6 | gitsigns **current-line blame is on by default** (virtual text at end of line), `numhl = true`, custom sign glyphs (`+ ~ - ^ * !`), `>` `<` also centre the cursor (`zz`) and print "Hunk i of n", `<leader>hd` diffthis, `<leader>hD` diff against base | "line blame text" listed missing; the rest not | m3 has no virtual text of any kind (TRANSPARENCY.md: "no virtual text exists"), so blame text cannot be drawn by a plugin either | F2 is the enabler |
| G7 | blink.cmp: ghost text, auto brackets on accept, docs shown automatically, `S-j`/`S-k` scroll the docs, rounded border, kind icons, signature window | "no documentation pane" | ghost text and auto-brackets are also missing | F2 (ghost text), F9 |
| G8 | mini.surround maps `<leader>sh` = highlight, **the same keys as `keymaps.lua`'s `<leader>sh` = horizontal split** | surround row partial | one of the two wins in nvim (`keymaps.lua` is required after lazy.setup, so the split probably wins and surround-highlight is dead; not run). m3's default has `<Space>sh` = split | note in the row; no work |
| G9 | key collisions between m3's default `<Space>` table and his config: `<Space>hd` (m3: Harpoon remove; his: gitsigns diffthis), `<Space>hp` (noted), `<Space>gs gr gu gp` (m3 hunk keys vs his `gr` rename branch, `gp` Diffview-compare), `<Space>dd` (his: diagnostics picker; his mini.diff overlay used the same key and is disabled) | only `hp` | profile `nvim` should state which side wins for each | parity agent |
| G10 | conform `spotless_maven`: a **file-based** formatter (`stdin = false`, edits the file on disk, then the buffer reloads) | "maven spotless is out" | not checked whether `:Formatter` can run a command that rewrites the file instead of filtering stdin; if not, any formatter that works in place cannot be used | ask the parity agent; small |
| G11 | the active colour scheme is gruvbox-material **hard contrast, italics, transparent**; m3 ships `gruvbox-material` and `gruvbox-material-soft` | "themes and transparent_style" | the contrast variant is not stated; hard may not exist | check `themes/gruvbox-material.toml` against the plugin's hard palette |
| G12 | mini.pick: the window is 61.8 percent of the screen, centred; the mouse wheel moves the selection, `S-Up`/`S-Down` scroll the preview; fzf-lua (off) had "ignore .gitignore" and "invert match" toggles | not listed | finder has `ignore` and `hidden` toggles (FINDER.md); wheel and preview scrolling not checked | minor |
| G13 | treesitter: 15 ensured languages (c, java, python, lua, vim, vimdoc, query, javascript, typescript, json, html, rust, tsx, groovy, cpp) | "m3 has its own syntax library" | the `syntax` library has grammars named c, cpp, java, groovy, tsx, typescript, javascript, json, html, lua, python, rust, vim (grep of the library, not a highlight run); vimdoc and query are irrelevant | none |
| G14 | mini.bracketed targets: the default setup enables buffer, comment, conflict, diagnostic, file, indent, jump, location, oldfile, quickfix, treesitter, undo, window, yank | "b q t h c d present; yank, comment, window, undo missing" | also missing: conflict, file, indent, jump, location, oldfile (treesitter is out) | complete the list; F10 |
| G15 | the **nox editor repos** (his Helix fork) contain two tools that nvim does not have in his config: `nox-files` (miller columns, `<Space>m`) and `nox-git` (a lazygit-style dashboard with commit, push, pull). CORE-AND-PLUGINS marks both NOT PLANNED | consistent with the decision | but commit, push and pull are in his muscle memory for nox (`<Space>gc gp gl`) and NVIM-PARITY says "commit / push are not built" | D2 |

Verdict for the doc: add rows G1, G2, G3, G4, G5, G14 and change `nvim-lspconfig` to `partial`; counts become done 26, partial 21, missing 9 (G1/G2/G5 are
missing, G3 is out), out 14. Everything else is a note inside an existing row.

---

## 2. Question 2: what the popular setups ship

Legend for the tables: **D** default (on after install), **O** optional or an extra the user turns on, **C** a community pack
exists (astrocommunity), **-** absent, **?** not verified. Distros: LV LazyVim, AN AstroNvim, NC NvChad, KS kickstart.nvim, LU LunarVim.
Box editors: HX Helix, ZD Zed, KK Kakoune ("box" = in the shipped editor without extensions). Stars are for the plugin named in the last
column, 2026-11-05.

Reading the distros' sizes: LazyVim 27,804 stars (pushed 2026-10-28), AstroNvim 14,476, NvChad 28,528, kickstart 31,652, LunarVim 19,246
(last push 2025-06-05, so LunarVim is a weak signal now), snacks.nvim 8,198, mini.nvim 9,634.

### 2.1 Popularity matrix (features, not plugins)

| feature | LV | AN | NC | KS | LU | HX | ZD | KK | leading plugin (stars) | m3 today |
|---|---|---|---|---|---|---|---|---|---|---|
| LSP client + diagnostics | D | D | D | D | D | box | box | - | nvim-lspconfig (?) | core |
| **LSP installer** (mason) | D | D | D | D | D | - | box (auto-install, not verified in the pages read) | - | mason (?) | not planned |
| completion popup | D blink | D blink | D cmp | D blink | D cmp | box | box | box | blink.cmp (6,656), nvim-cmp (9,487) | core |
| fuzzy picker | D snacks | D telescope/fzf/snacks | D telescope | D telescope | D telescope | box | box | - | telescope (19,850), fzf-lua (4,480) | core |
| file tree | D snacks/neo-tree | D neo-tree | D nvim-tree | O neo-tree | D nvim-tree | - (picker only) | box (project panel) | - | neo-tree (5,641) | core, plugin planned |
| git signs, hunks, blame | D | D | D | D | D | box (diff gutter) | box | rc/git | gitsigns (7,166) | core |
| **git write ops** (stage file, commit, push, pull, stash, branches) | O lazygit key | O | - | - | - | - | **box (git panel)** | rc/git (`:git`) | neogit (5,667) | **missing** |
| **2-pane diff / diff view** | O mini-diff (overlay only) | C | - | - | - | - | **box (project diff)** | - | diffview (5,882; last push 2024-08) | **missing** |
| **conflict resolution** | - | - | - | - | - | - | box (buttons) | - | git-conflict (?) | **missing** |
| which-key | D | D | D | D | D | box (auto-info) | - | box (auto info) | which-key (7,333), mini.clue | plugin, done |
| statusline | D lualine | D heirline | D | D mini | D lualine | box | box | - | lualine (8,172) | done |
| bufferline | D | D | D tabufline | - | D | box | box (tabs) | - | bufferline (4,388) | done |
| indent guides | D snacks | D snacks | D ibl | O | D ibl | box | ? | - | indent-blankline (5,003) | core; scope overlay planned |
| autopairs | D mini.pairs | D | D | O | D | box | box | - | nvim-autopairs (4,103) | core |
| **auto-close tags** | D (ts-autotag) | D | - | - | - | - | ? | - | nvim-ts-autotag (?) | **missing** |
| comment toggle | D ts-comments | D | D | - | D | box | box | rc/comment | ts-comments (?) | core `gc` |
| **text objects beyond vi** (argument, function, call, class) | D (mini.ai + TS textobjects) | D (TS textobjects) | - | D (mini.ai) | - | **box (TS: function, class, argument, comment, test)** | ? | box (blocks, sentences) | mini.ai (631 standalone; part of mini.nvim 9,634), treesitter-textobjects (2,825) | **missing** |
| surround | O | O | - | D (mini.surround) | - | box (`ms`) | - | - | nvim-surround (4,324), mini.surround | core, extraction planned |
| flash / label jump | D flash | O | - | - | - | box (`gw`) | - | rc/jump | flash.nvim (4,271) | `jump` plugin |
| project search + replace panel | D grug-far | O | - | - | - | - | box (multibuffer search) | - | grug-far (2,027), nvim-spectre (2,410) | `:cdo` only |
| trouble / diagnostics list | D | O | - | - | - | box (pickers) | box | - | trouble (6,911) | picker; `trouble` planned |
| todo-comments | D | D | - | D | - | - | - | - | todo-comments (4,220) | plugin, done |
| session restore | D persistence | D resession | - | - | O project | - | box | rc/tools/autorestore | persistence (1,013), resession (?) | `session` plugin |
| terminal | D snacks | D toggleterm | D | - | D toggleterm | - | box | via windowing scripts | toggleterm (5,619) | core |
| notifications | D snacks+noice | D snacks | - | O fidget | - | - | - | - | nvim-notify (?), noice (5,827) | plugin, done |
| dashboard / start screen | D snacks | D snacks | ? | - | D alpha | - | box (welcome page) | - | alpha / snacks | **declined by the owner** |
| bigfile guard | D snacks | - | - | - | D bigfile.nvim | - | - | - | snacks.bigfile | none (m3 opens 50 MB in 0.8 s) |
| **word under cursor: highlight and jump** | D snacks.words | D snacks.words | - | - | D illuminate | - | ? | - | vim-illuminate (2,475) | **missing** |
| **toggle menu** (wrap, spell, diagnostics, numbers, hints...) | D snacks.toggle | D (15 toggles in core maps) | - | - | - | - | - | - | snacks.toggle | `:set`, no menu |
| scratch buffer | D snacks.scratch | - | - | - | - | - | - | - | snacks.scratch | none |
| git browse (open or copy GitHub URL) | D snacks.gitbrowse | D | - | - | - | - | - | - | snacks.gitbrowse, gitlinker (C) | **missing** |
| lazygit float | D | - | - | - | - | - | - | - | snacks.lazygit | external `mgit`/`gitui` |
| undo tree | - | C | - | - | - | - | - | - | undotree (4,554), snacks undo picker | undo tree commands, no view |
| linter on save | D nvim-lint | D none-ls | - | O | D none-ls | - | via LSP | rc/lint | nvim-lint (2,786) | none |
| formatter on save | D conform | D none-ls | D conform | D conform | D none-ls | box (LSP) | box | rc/format | conform (5,393) | core `:Formatter` |
| tasks / run build | O overseer | C | - | - | - | - | **box (tasks)** | rc/make, grep | overseer (1,948) | `:make` only |
| test runner | O neotest | C | - | - | - | - | - | - | neotest (3,117) | not planned |
| **debugger (DAP)** | O dap.core | **D** | - | O | **D** | **box (helix-dap crate)** | **box** | - | nvim-dap (7,297) | declined |
| outline / symbols sidebar | O aerial/outline | **D aerial** | - | - | O navic | - | **box (outline panel)** | - | aerial (2,358) | picker only |
| sticky context / breadcrumbs | O treesitter-context | - | - | - | **D breadcrumbs** | - | ? | - | nvim-treesitter-context (3,241), navic, dropbar | none |
| rainbow delimiters | - | - | - | - | - | ? | ? | - | rainbow-delimiters (897) | none |
| colour swatches | O mini-hipatterns | **D highlight-colors** | - | - | - | **box (LSP swatches)** | - | - | nvim-highlight-colors (1,053) | `colors` planned |
| inline / end-of-line diagnostics | D (vim.diagnostic virtual text) | toggle | - | - | - | **box** | box | - | tiny-inline-diagnostic (C) | **none** (no virtual text) |
| centred / zen layout | key | D snacks.zen config | - | - | - | - | ? | - | snacks.zen, no-neck-pain (?) | none |
| window zoom | D toggle | - | - | - | - | - | ? | - | | none (`<C-w>_` and `<C-w>\|` exist) |
| rename file + LSP imports | - | D map "Rename file" | - | - | - | - | - | - | snacks.rename, nvim-lsp-file-operations (C) | none |
| indent detection | - | D guess-indent | - | D guess-indent | - | - | - | - | guess-indent, vim-sleuth (?) | editorconfig only |
| multiple cursors | - | D mapping | - | - | - | **box** | box | **box** | multicursor.nvim (1,544), vim-visual-multi (C) | optional, roadmap 20 |
| yank history, registers picker | O yanky | - | - | - | - | - | - | - | yanky (1,294), snacks registers | `:Registers` |
| increment dates/booleans | O dial | - | - | - | - | - | - | - | dial.nvim (?) | none |
| split/join arguments | - | - | - | - | - | - | - | - | treesj (1,364), mini.splitjoin (C) | none |
| align text | - | - | - | - | - | **box (`&`)** | - | **box** | mini.align (C), vim-easy-align (C) | `:left :right :center` only |
| project switcher | - | - | - | - | **D project.nvim** | - | box (recent projects) | - | snacks projects picker, project.nvim (C) | recent files only |
| minimap | - | - | - | - | - | - | ? | - | mini.map, neominimap (C) | `scrollbar` option |
| image viewer | O snacks.image | O | - | - | - | - | - | - | snacks.image | never |
| REPL / code runner | - | C | - | - | - | - | **box** | - | molten, sniprun (C) | never |
| GitHub PRs/issues in editor | O octo | C | - | - | - | - | - | - | octo (3,407), snacks.gh | never |
| AI chat / completion | O | O/C | - | - | - | - | box | - | | out of scope |

Notes on the box editors. Helix (editor.md, keymap.md, and `helix-dap` in the nox tree): pickers for files, buffers, jumplist, changed
files, symbols, diagnostics, global search and "last picker"; tree-sitter text objects and unimpaired motions; surround and
auto-pairs; inlay hints, signature help, colour swatches, inline and end-of-line diagnostics; indent guides, soft wrap, rulers,
bufferline, whitespace rendering; auto-save, atomic save, trim whitespace, final newline; a diff gutter; a DAP crate (`helix-dap`). It has **no**
file tree, no terminal, no git panel, no search-replace panel, no session restore. Zed (SUMMARY.md and four docs pages): project
panel, outline panel, tab switcher, multibuffers (edit search results and references in place), terminal, **tasks**, **debugger**,
REPL, a full git panel (stage, commit, branches, blame, project diff, conflict buttons, stash, push and pull, file history,
worktrees), call hierarchy, vim and helix modes, collaboration, remote development, edit prediction. Kakoune (`rc/`): tools autorestore,
autowrap, clang, comment, ctags, doc, fifo, format, git, go, grep, jump, lint, make, man, menu, patch, python, rust, spell; 132 filetype
files; windowing scripts for tmux, kitty, wezterm, sway and others; editorconfig and modeline detection. Neither Helix nor Kakoune
ships a file tree or a project-wide replace; Zed ships both through the panel and the multibuffer. m3 sits between them: closer to Zed
in chrome (tree, picker, git signs, terminal), closer to Helix in scope.

### 2.2 snacks.nvim, module by module (all 32 modules of the README)

Everything is off until enabled; LazyVim enables bigfile, quickfile, indent, input, notifier, scope, scroll, words, dashboard, terminal,
scratch, toggle, picker, explorer; AstroNvim enables dashboard, input, notifier, picker, indent, scope, words, zen, gitbrowse.

| module | what it does | m3 |
|---|---|---|
| animate, scroll | easing library, smooth scroll | core (`MED_anim`, `MED_glide`) |
| bigfile | turns off syntax, LSP, matchparen above a size | F11 (measure first) |
| bufdelete | delete a buffer without closing its windows | F11 (check `<Space>bd`) |
| dashboard | start screen | declined by the owner |
| debug, profiler | Lua debugging | n/a (m31) |
| dim, zen | dim inactive scope; zen mode (centred, dimmed) | F12 |
| explorer, picker (with ~70 sources: files, grep, buffers, recent, projects, undo, registers, marks, jumps, keymaps, commands, command_history, search_history, colorschemes, highlights, icons, lines, man, notifications, pickers, resume, spelling, treesitter, todo, zoxide, qflist, loclist, diagnostics, LSP definitions/references/implementations/type definitions/symbols/workspace symbols/incoming and outgoing calls, git branches/files/grep/log/log_file/log_line/stash/status/diff, GH issues/PRs/diffs/actions) | | core picker; missing sources: `undo`, `jumps`, `search_history`/`command_history`, `projects`, LSP symbol kinds, `git_stash`, `git_log_line`, `resume` |
| gh | GitHub CLI inside the editor | not planned |
| git, gitbrowse, lazygit | blame line, git root; open URL; lazygit float | F4 (gitbrowse); lazygit = external |
| image | kitty graphics | never |
| indent, scope | guides; scope detection, text objects, jumps | guides core; scope overlay planned; scope text objects `ii ai` fold into F8 |
| input, notifier, notify | nicer input, toasts | plugin API `input`/`select` (CORE-AND-PLUGINS 4.5); `notify` done |
| keymap, layout, win, util | library | n/a |
| quickfile | render the file before plugins load | n/a (m3 starts in 0.23 s) |
| rename | LSP-aware file rename | F7 |
| scratch | persistent scratch buffers | F12 |
| statuscolumn | custom sign/number/fold column | core |
| terminal | float/split terminals, toggle | terminal extraction (named and float terminals to be in its spec) |
| toggle | toggles with which-key state | F6 |
| words | highlight and jump between references (LSP) | F6 |

### 2.3 mini.nvim, module by module (all 46 modules)

| module(s) | m3 |
|---|---|
| ai | F8 text objects |
| align, operators (exchange, replace with register, multiply, sort, evaluate), splitjoin, keymap | opt-in editing plugins (F13) |
| animate, icons, notify, starter, statusline, tabline, statuscolumn, map | core or planned or declined (starter, map) |
| basics, deps, doc, test, base16, hues, colors, fuzzy | n/a or core (themes) |
| bracketed, move, surround, pairs, comment, jump, jump2d, clue, files, pick, extra, visits, sessions, diff, git | exist (done, partial or planned); see G14 and 2.4 |
| bufremove | F11 |
| cmdline (autocomplete, autocorrect, range peek) | not planned; command-line completion exists |
| completion, snippets | core |
| cursorword | F6 (`words`) |
| hipatterns | `colors` plus todo; a generic "highlight these regexes" option is cheap once `did_decorate` has a regex form (F14) |
| indentscope | planned `indentscope` (owner uses it: make it default, F10) |
| misc (restore cursor, zoom, put_text, resize_window, bench) | `session` has restore; zoom in F12 |
| trailspace | core: `trim_trailing_whitespace` of editorconfig exists (MED_projconf); a highlight option `listchars trail` exists; add a `:Trim` command only (S) |

### 2.4 What the owner already uses that m3 has or has planned (so it is not re-proposed)

harpoon, mini.move, mini.bracketed (partial), mini.surround (partial), mini.files (explorer), mini.pick (finder), mini.indentscope
(planned), mini.jump2d (`jump`), gitsigns (core, extraction planned), which-key, trouble (planned), todo-comments, nvim-ufo (core
folds), neoscroll (core), conform (`:Formatter`), blink (popup), lualine (`statusline`), nvim-notify, nvim-autopairs, snippets,
themes, markview (planned, roadmap 22), nvim-highlight-colors (planned `colors`), nvim-web-devicons (planned `icons`).

---

## 3. Question 3: decisions

Size: **S** under about 300 lines and no new seam, **M** a module plus tests or one small API addition, **L** a new subsystem or an
engine change that needs the oracle. Class: **CORE** batteries-included in every build; **DEFAULT** plugin in the `default` profile
(removable with `--without`); **OPT-IN** plugin in `full` only; **NOT PLANNED**. API names refer to `docs/CORE-AND-PLUGINS.md`
section 10 (seams) and `docs/EXTENSIONS.md`; "new" means not listed there. A flag marks a conflict with "not a full IDE".

### 3.1 Features, ranked

Rank = breadth of evidence, then whether the owner's own config uses it, then cost. F1 to F12 are the build list.

| # | feature | evidence | needs from m3 | size | class | reason |
|---|---|---|---|---|---|---|
| **F1** | LSP navigation set: documentSymbol, workspaceSymbol, typeDefinition, implementation, declaration (later: call hierarchy), symbol pickers, `:Symbols` from the server | owner (6 keys: `gd gr gi gt ds dw`); Helix, Zed, snacks, LV, AN, LU | core change in `MED_lsp`; picker sources with kinds; no API | M | **CORE** | CORE-STATUS already lists it as missing; every box editor has it; the owner's keymap breaks without it |
| **F2** | Virtual text / inline text decorations: end-of-line text, inline blame, inline and end-of-line diagnostics, completion ghost text, swatches | owner (gitsigns blame, blink ghost text); Helix and Zed box; LV default; AN toggle; tiny-inline-diagnostic (C) | renderer change in `App.draw_line`; **new API**: `Registry.did_virtual(option, VirtualDecorator)` returning end-of-line and inline `{text, scope}` chunks (the gap `nox-indent` recorded as `set_inline_text`, CORE-AND-PLUGINS 1.3) | M | **CORE** (renderer, option `diagnostics=eol\|off`, default `off` so bare vi is unchanged) + API | one enabler for four visible features; today none of them can exist, in core or in a plugin |
| **F3** | Git write operations and gitbrowse: stage and unstage file, commit (message in a buffer or prompt), push, pull, fetch, stash, branch create/rename (the owner's `<leader>gn gr` are `:Git checkout -b`), `:GitBrowse` (open or copy the URL of file, line range, commit) | owner (nox `<Space>gc gp gl`, nvim `gn gr`); Zed box; LV and AN gitbrowse; snacks | the git plugin extraction (section 10 item 10: signs, overlay, picker actions) plus `Ctx.copy`/`Ctx.open_url` (new, S) | M | **DEFAULT** (inside `git`) | thin ex commands over m31git, not a git UI; fugitive-style panels stay declined. Flag: edge of "not a full IDE", acceptable as commands |
| **F4** | Conflict resolution: highlight `<<<<<<<`, `co ct cb c0`, `]x [x` | owner (git-conflict, active); Zed box | `did_decorate` (exists), buffer-local maps (S1, exists), `Ctx.replace_lines` | S | **DEFAULT** | active in his config today and needs nothing new; a git operation he does weekly |
| **F5** | Diff mode: `:diffthis`, `:diffoff`, `]c [c`, `do dp`, then a diffview-like plugin (file list picker, side-by-side) | owner (diffview: `gdd gt gp gdr gC`, active); Zed box (project diff); nvim and Vim core | engine/renderer change (Vim feature, oracle can check against nvim); scroll binding; the plugin later needs a panel or two split buffers | L | **CORE** (`:diffthis`), **DEFAULT** (`diffview`-lite on top) | DAILY-DRIVER gap 4; the largest item he uses that m3 lacks. Note the upstream project (diffview) has no push since 2024-08 |
| **F6** | `words` (highlight other uses of the word under the cursor, jump with `]w [w`; LSP `documentHighlight` when a server is on) and `toggles` (a `<Space>u` group that flips wrap, relativenumber, guides, diagnostics, inlay hints, signs, autosave, transparency with state shown in which-key) | words: LV, AN (snacks.words), LU (illuminate, 2,475), mini.cursorword; toggles: LV (snacks.toggle), AN (15 toggles) | `Decorator` (exists) + `CursorMoved` (exists); toggles need `Ctx.is_flag_on` (exists) and a set-flag (new, S) | S + S | **DEFAULT** both | three of five distros ship words; the toggle group is discoverability, the thing which-key already sells |
| **F7** | File operations seen by LSP: `workspace/willRenameFiles` and `didRenameFiles`, `:Rename NEW`, `:Move`, tree rename | owner (nvim-lsp-file-operations active); AN "Rename file" map; snacks.rename | core LSP (`MED_lsp`), ex command in core, tree calls it | S | **CORE** | closes G2; without it a rename in the tree breaks imports in TS/Java/Rust |
| **F8** | Text objects beyond vi: argument `ia aa`, function call `if af`, quote/bracket aliases, whole buffer `ie`, indent scope `ii ai`; built lexically (brackets, commas, indent) with the syntax library for strings and comments; no parse tree | LV (mini.ai + TS textobjects, default), AN, KS (mini.ai), Helix box (function, class, argument, comment, test) | the **text-object registry** in the engine (same family as the operator registry of section 10 item 7: a plugin declares `i`/`a` objects, the engine resolves them for operators, Visual, counts and `.`) | M to L | **DEFAULT** (engine hook is core) | the most popular editing feature m3 lacks, and Helix ships it in the box. Flag: tree-sitter text objects (function/class precision) stay out; the lexical version is honest and falls back |
| **F9** | Project-wide search and replace: a picker-based `:Replace` (type the pattern, `<C-r>` asks for the replacement, preview of each change, apply with `:cfdo s///` semantics, undo per file) | LV default (grug-far, 2,027), astrocommunity has 4 (spectre 2,410, sad), Zed multibuffer | `Ctx.pick_lines` and `open_picker` exist; needs write access to files not open (`Buf` handle, API item on the list) or call the core's `:cfdo` through `Ctx.run_ex` (new, S) | M | **DEFAULT** | DAILY-DRIVER gap 1 is done at the command level (`:cdo`); what is missing is the ergonomic loop; cheap because the core exists |
| **F10** | Finish the owner's partials: `bracketed` targets (yank, comment, window, undo, file, indent, jump, oldfile, conflict), surround find/highlight/n_lines/next-last, `indentscope` (as default), mini.files `R`/`gs` equivalents, picker resume and hunk list, gitsigns leftovers (word diff, line highlight, deleted lines, `ih` text object, Visual stage), trouble LSP panel | owner (all in his config); G14 | additive; `indentscope` needs only `Decorator`; surround extras need the engine (do after F8's registry) | M (many S) | **DEFAULT** | these are the rows marked partial in NVIM-PARITY; they are his daily keys |
| **F11** | Safety and hygiene in core: `bigfile` threshold (turn off syntax, guides, git, todo above N MB; measure first, since 50 MB opens in 0.8 s), `bufdelete` keeps the window layout, undo picker source (`:UndoTree` as a picker with diff preview), indent detection (`detectindent`, sleuth-style) and `:Trim` | bigfile: LV, LU; bufdelete: LV, AN, mini.bufremove; undo: undotree (4,554), snacks `undo`; detection: AN, KS (guess-indent) | core options and one picker source | S each | **CORE** | all are Vim-adjacent behaviours a plain editor should have; none needs an API |
| **F12** | Small conveniences: `scratch` (persistent per-project scratch file, `<Space>.`), `projects` picker (recent project directories from `session` and frecency, `cd` plus session restore), window zoom toggle, centred layout (`:set center=N`, the owner's no-neck-pain) and `zen` on top | scratch: LV; projects: LU, snacks, Zed; zoom: LV, mini.misc; zen: AN, snacks; no-neck-pain: owner | scratch/projects: state files (exists); zoom: window model; centre: renderer margins (core) | S each | `scratch`, `projects` **DEFAULT**; zoom, centre **CORE**; `zen` **OPT-IN** | cheap, visible, each backed by at least two setups |
| F13 | Editing extras: `dial` (increment dates, booleans, semver), `splitjoin` (`gS gJ`), `align` (`ga`-style; `ga` is taken by ascii), `operators` (exchange `cx`, replace with register `gr`... note `gr` is taken), auto-close HTML tags | dial (LV extra), treesj 1,364 and mini.splitjoin (C), mini.align, vim-exchange (C), ts-autotag (LV, AN default) | operator registry (section 10 item 7); the insert hook (item 8) for tags | M each | **OPT-IN** | wanted by some, bare-vi purity says opt-in; auto-close tags is the one to promote after the autopairs extraction (the owner edits tsx and html) |
| F14 | `:Lsp doctor` (server per file type, found or missing on PATH, the install command to run), `:Lint LANG CMD` (like `:Formatter`; output through `errorformat` into diagnostics), `:Task` runner (named commands in `.m3.toml`, run in the terminal pane, errors to quickfix) | mason in 5 of 5 distros; lint: LV, AN, LU (+ KS optional); tasks: Zed box, overseer (1,948), Kakoune make/grep | doctor: core, no API; lint needs `Ctx.set_diagnostics(source, list)` (new, S); tasks need the terminal extraction | S + M + M | doctor **CORE**; `lint`, `tasks` **OPT-IN** | doctor answers the one real cost of "no LSP installer"; flag: `tasks` is as far toward an IDE as m3 should go |
| F15 | Context chrome: breadcrumbs in `winbar` and sticky scope header (from LSP document symbols, falling back to indent), outline sidebar | LU (breadcrumbs default), LV extra (treesitter-context 3,241, aerial, navic), AN aerial default, Zed outline panel | F1 first; sidebar needs the docked panel API (section 10 item 12) | M, then L | **OPT-IN** | wanted but not needed; sequence after F1 and the explorer |
| F16 | Smaller opt-ins: rainbow brackets (897), `hipatterns` generic regex highlights, minimap, smart-splits (tmux/wezterm pane crossing; AN default), window picker by label (owner, AN) | rainbow-delimiters C; mini.hipatterns; AN smart-splits | `Decorator`, `Ctx.system` (for the multiplexer call) | S each | **OPT-IN**, build on demand | low evidence or low value |
| F17 | **Debugger (DAP)** | LV extra, AN default, LU default, KS optional, Helix box (`helix-dap` is in the nox tree), Zed box; owner: pulled in by nvim-java, nvim-dap 7,297 | a DAP client, breakpoints UI, variables panel, adapter configs | XL | **NOT PLANNED** (flag: IDE) | decision D1 below |
| F18 | **Test runner** (neotest, vim-test) | LV extra, astrocommunity test; owner: neotest disabled | an adapter per framework | L | **NOT PLANNED** (flag: IDE) | `:Task` covers "run the tests, jump to failures"; adapters per framework are IDE work |
| F19 | **LSP installer** (mason) | 5 of 5 distros; Zed auto-installs; Helix and Kakoune do not | package registry, downloads, platforms | L | **NOT PLANNED** (flag: IDE) | the decided scope; F14 `doctor` removes the surprise |
| F20 | Declined or out: startup dashboard (owner), noice-style command-line UI, image viewer, REPL, GitHub PR/issues (octo 3,407, snacks.gh), AI, vimtex and note taking, remote development, spell (ROADMAP), tree-sitter features (ROADMAP), `inc-rename` live preview (860), refactoring.nvim (3,661; needs tree-sitter), yank ring (1,294; `bracketed` yank covers the muscle memory) | | | | **NOT PLANNED** | outside "Neovim-with-plugins class" or already decided |

Excluded because m3 has or has planned them: picker and its sources, tree, terminal, git signs and `:Git` reads, surround, autopairs, comment,
harpoon, which-key, statusline and bufferline, notify, todo, session, folds, snippets, themes, smooth scroll, indent guides, colour
swatches (`colors`), icons, trouble, markdown rendering, multi-cursor (roadmap 20, optional).

### 3.2 Conflicts with "not a full IDE", stated plainly

* F17 (DAP), F18 (test adapters), F19 (installer): NOT PLANNED. They are the three things every IDE-type distro has and Zed/Helix half-ship.
  Re-evaluation rule from the brief: only a daily-driver blocker moves them. Evidence found: the owner's lockfile carries nvim-dap and
  nvim-java, but neotest is disabled in his spec and nothing in his keymaps starts a debugger. Not a blocker on the evidence; owner to confirm (D1).
* F14 `tasks`, F3 git write ops, F9 replace, F15 outline: inside the class, as commands and pickers, not as panels with state.
* F5 `diffview`-lite and F15 outline sidebar need the docked panel API: that is infrastructure, not IDE scope.

### 3.3 Build order (m3 0.23.0 and later)

Assumption: 0.21.0 to 0.22.x are the parity agent's extractions (git, explorer, terminal, finder; section 10 items 10 to 13), so
the git plugin and the docked panel exist from 0.23. If they slip, milestones M3 and M7 move after them; M1, M2, M4 and M5 do not
depend on them.

| milestone | content | why this order | sizes |
|---|---|---|---|
| **0.23.0 LSP completeness** | F1 (symbols, type definition, implementation, picker keys), F7 (file rename, `:Rename`), `:Lsp doctor` (F14), selection range expand/shrink (`an`/`in` on `selectionRange`, S), F11 hygiene (bigfile threshold, bufdelete layout, undo picker, detectindent, `:Trim`) | the owner's six LSP keys and the tree rename are broken or missing now; all core, no new API, so no dependency on the parity agent | M + S + S + S + 5xS |
| **0.24.0 Virtual text** | F2 (renderer, `did_virtual` API 0.5), then on it: blame at end of line (gitsigns default), end-of-line diagnostics, completion ghost text, `colors` swatches | one API unlocks four features; do it before the plugins that need it | M, then 4xS |
| **0.25.0 Git complete** | F3 (write ops, gitbrowse), F4 (conflicts), gitsigns leftovers from F10, `ih`/Visual stage | after the git extraction; the owner's weekly workflow | M + S + S |
| **0.26.0 Diff** | F5: core `:diffthis` family, then `diffview` plugin (file list, side by side, compare to a branch/commit; the keys `gdd gt gp gdr gC` of his config) | the biggest item, alone in a milestone so the oracle can gate it | L |
| **0.27.0 Search and words** | F9 `:Replace`, F6 `words` and `toggles`, F12 (`scratch`, `projects`, zoom, centre) | all built on existing seams; high daily value for the cost | M + S + S + 4xS |
| **0.28.0 Text objects** | F8 registry and `textobj` plugin, then F10 surround extras and `bracketed` completion on the same registry, F13 `dial` `splitjoin` `align` `operators` | needs the engine seam (oracle-gated), so isolated | M-L + M + 4xM |
| **0.29.0 Chrome and runners** | F14 `lint` and `tasks`, F15 breadcrumbs, sticky header, outline sidebar (after the explorer's panel API), F12 `zen`, F16 as asked | opt-in material last; re-evaluate F17 to F19 here with the owner | M + M + M + L |

Top 12 with sizes, in build order: F1 (M), F7 (S), `:Lsp doctor` (S), F11 (S x5), F2 (M), F3 (M), F4 (S), F5 (L), F9 (M), F6 (S + S),
F8 (M-L), F10 (M). F12 follows inside 0.27.0.

### 3.4 Five things the owner does not know he is missing

1. **Text objects for arguments and calls** (`daa`, `cif`, `vii`): LazyVim and kickstart ship mini.ai, Helix ships tree-sitter ones in the
   box, he has none of them in nvim. m3 can have the lexical version (F8).
2. **Search and replace across the project with a preview** (grug-far in LazyVim by default; spectre, sad in astrocommunity): he has `:cdo` in
   m3 only; F9 makes the loop pleasant.
3. **Word-under-cursor highlighting and jumps** (snacks.words, illuminate, mini.cursorword): the cheapest "feels like an IDE" feature (F6).
4. **Copy the GitHub URL of this line** (`gitbrowse`, in LazyVim and AstroNvim by default): one key during a code review (F3).
5. **An undo history he can see** (a picker with diffs, F11): m3 has the undo tree commands but no view; undotree has 4,554 stars.

And three facts from section 1 that he probably does not know: nvim-dap is already installed through nvim-java (G1); four of his mini.pick LSP
keys cannot work in m3 yet (G4); his gitsigns shows blame at the end of the line all the time, and m3 cannot draw any text there (G6).

### 3.5 Owner decisions needed

| # | question | recommendation |
|---|---|---|
| D1 | Do you debug (nvim-dap via nvim-java) or run Java tests in nvim? | If no: keep DAP and test runners NOT PLANNED. If yes: DAP becomes the single exception to scope, post-1.0 per ROADMAP, as an opt-in plugin |
| D2 | nox had miller columns and a lazygit-style dashboard (commit, push, pull); m3's record says NOT PLANNED. Keep that, with F3's commands covering commit/push/pull? | yes: commands only, no dashboard |
| D3 | Are `words` (F6) and `toggles` on or off by default? | on for `toggles`, `words` on but subtle (underline, not background) |
| D4 | F5 is L. Build the core `:diffthis` first and the `diffview` plugin second, or the other way round? | core first: it is a Vim feature the oracle can check |
| D5 | Accept "no LSP installer", with `:Lsp doctor` printing the install command? | yes |
| D6 | Is Java (jdtls, spotless, `jdt://`) a use you want m3 to handle? (G3, G10) | plan only after 0.23; needs a jdtls session to test |
| D7 | May the engine gain a text-object registry (touches `MED_vim`, oracle-gated)? | yes, in its own milestone (0.28.0) |
| D8 | Which side wins the key collisions in profile `nvim` (G8, G9)? | his config wins; harpoon remove moves to `<Space>hD` |

---

## 4. Method notes and limits

* Popularity counts come from reading each distro's plugin specs on the default branch on 2026-11-05. "Default" in LazyVim means
  declared in `lazyvim/plugins/*.lua` or enabled in its snacks options; its extras are in `plugins/extras/` (ai 9, coding 8, dap 2, editor 18,
  formatting 2, lang 49, linting 1, lsp 2, test 1, ui 9, util 9). "AN default" means a spec under `astronvim/plugins/`. LunarVim's last push is
  2025-06-05, so it is counted but not trusted.
* Star counts are a proxy for adoption, not quality. Examples of why not to lean on them: diffview (5,882) and toggleterm (5,619) have not been
  pushed since 2024-08 and 2025-03; mini.ai is part of mini.nvim, so its standalone 631 understates it.
* Helix and Zed rows rest on documentation pages read through a summarising fetch; where a page did not mention a feature the cell is "?",
  not "absent". The Zed pages did not cover sticky scroll, minimap, breadcrumbs or code folding.
* The statement that jdtls support is limited (G3) and that `keymaps.lua` shadows surround's `sh` (G8) were not run; both are marked.
* Not checked: whether the m3 `explorer` already handles a `Rename` that notifies LSP (it does not send anything: grep of `MED_lsp` for
  `willRename` finds nothing); whether `:Formatter` supports in-place formatters (G10).

## Owner decisions (2026-11-05)

These answer D1 to D8 above and override the recommendations where they differ.

| | Decision |
|---|---|
| D1 | No DAP for now. Revisit after a stable release; it is not part of v1. |
| D2 | Miller columns and the git dashboard are wanted, not "not planned". Both become planned features (the dashboard needs the git write operations of F6; miller columns need the explorer panel API). |
| D3 | `words` and `toggles` are on by default. |
| D4 | Core `:diffthis` first, the diff plugin second. |
| D5 | An LSP installer is a must, because it will raise adoption. This reverses the earlier "no LSP installer" decision: `:Lsp doctor` stays as the diagnostic, an installer (`:Lsp install <server>`, per-filetype suggestions, registry of known servers) is added and scheduled with the LSP milestone. |
| D6 | jdtls and Java specifics come after DAP, in v2 or a 1.x release. |
| D7 | The engine gains a text-object registry, in its own oracle-gated milestone. |
| D8 | Key collisions get fixed. In the `nvim` profile his config wins. m3's Harpoon remove moves off `<Space>hd`; his `<leader>hd` is gitsigns "Diff This" (diff the file against the index), `<leader>hD` is "Diff Against Base" (`diffthis("~")`), `<leader>hp` previews the hunk. |
