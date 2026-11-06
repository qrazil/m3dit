# Neovim parity

The owner's Neovim setup (`~/.config/nvim`: `init.lua`, `lua/config/{lazy,keymaps,autocomds}.lua`, 53 files in `lua/plugins/`) mapped to m3.
Read-only: nothing from the config except plugin names, option values and key names is copied here, and no key, token or secret.
Leader is `<Space>`, local leader `\`.

Status: **done** (works the same, tested), **partial** (works, what is missing is named), **missing** (m3 could have it, not built yet; the
seam is named), **out** (out of scope on purpose). The counts are at the end. A `profile` row means `:Profile nvim` (or the line `Profile nvim` in
`~/.config/m3/keymap.vim`) turns it on: `engine/MED_profile.m31` lists every line, so the keymaps that are editor behaviour are reproduced
and since 0.22.0 the profile REPLACES the leader tree (it is the `legacy` tree plus his own maps; the `default` tree is different; `:Profile default` takes his maps away again).

## Options (`init.lua`)

| his setting | m3 | status |
|---|---|---|
| `mouse = "a"` | the mouse is on by default (`--no-mouse` turns it off); profile sets `mouse=a` | done |
| `tabstop = 4`, `shiftwidth = 4`, `expandtab` | profile | done |
| `relativenumber` | `:set relativenumber`, profile | done |
| `ignorecase`, `smartcase` | profile | done |
| `smoothscroll` | the option is accepted; `CTRL-D/U/F/B/E/Y` and `zt zz zb` scroll with the core's animation (`:set animate`, `tests/anim_pty.py`) | partial |
| `mapleader = " "`, `maplocalleader = "\\"` | `<Space>` leader is the default; `\` local leader is not used by anything | done |

## `keymaps.lua`

| his map | m3 | status |
|---|---|---|
| `<leader>n` new file | `<Space>n` (`:enew`) | done |
| `jk` insert: Esc | built in (`:set nojk_escape` turns it off) | done |
| `<leader>ll`, `]]`, `[[` diagnostics float / next / prev | same keys | done |
| `<leader>sv sh se sc` splits | same keys | done |
| `<leader>ps` Lazy sync | no plugin manager | out |
| `<leader>ms` Mason | servers are on PATH | out |
| `<leader>cc`, `<leader>ca` CodeCompanion | AI chat | out |
| `<leader>b` buffer manager | profile: `:Buffers` picker (m3's own `<Space>b` prefix is replaced) | partial |
| `<leader>gn` / `gr` create / rename branch | profile: `:!git checkout -b ` / `:!git branch -m ` (typed name, then Enter) | done |
| `<leader>gdd`, `<leader>gt` DiffviewOpen | profile: `:Git diff` list (no side-by-side view yet) | partial |
| `<leader>z`, `o`, `w` | same keys | done |
| `<leader>R` reload all buffers | `<Space>R` reloads the file; `:bufdo e` is available | partial |
| terminal-mode `<C-\><C-]>` | the terminal plugin leaves input with its own key (`:terminal`); not mapped | missing |

## Plugins (`lua/plugins/*.lua`)

| plugin (file) | his keys / settings | m3 | status |
|---|---|---|---|
| aerial (disabled in the config) | `<leader>a`, `{` `}` | profile `<Space>a` = `:Symbols` picker | partial |
| nvim-autopairs | `config = true` | core `MED_autopair` (not yet a plugin: needs the insert-key hook, docs/CORE-AND-PLUGINS.md 10) | done |
| avante (disabled), CopilotChat (disabled), copilot (disabled), minuet-ai, codecompanion (disabled), claude-code | AI | not built | out |
| blink.cmp | `<Tab>` accept, `<C-j>` `<C-k>` move, `<CR>` accept, `<C-d>` docs, `<C-space>` | LSP completion popup in the core; profile `set pumkeys=blink` gives Tab / CTRL-J / CTRL-K; no documentation pane | partial |
| nvim-cmp (disabled) | | the same popup | done |
| block (disabled; private plugin) | | | out |
| buffer_manager | `<leader>b` | `:Buffers` picker; no editing of the list in place | partial |
| colortils (`color-utils`) | `:Colortils` | | out |
| conform.nvim | `format_on_save`, formatters per file type, fallback to LSP | `:Formatter LANG CMD` and `formatonsave`; the profile registers rustfmt, ruff, stylua, prettierd/prettier; `lspformat` is the fallback; maven spotless is out | done |
| diffview | `:DiffviewOpen` | `:Git diff` list; no two-pane diff, no file panel | partial |
| fzf-lua (disabled), mini.pick (active) | `<leader>ff fg fr fb fe fq gf gh`, git branch pickers `gb gc gC gp`, LSP pickers | finder: `<Space>ff fg fr fb fe fq`, `gf`, `gb`, `gc`, `gC` same keys; resume and the hunk list are not there | partial |
| git-conflict | `o t 0 b n p` in a conflict | not built (a plugin over `did_decorate` plus buffer keys) | missing |
| gitsigns | `-` `_` stage / reset, `>` `<` hunks, `<leader>hS hu hR hp hd hD hb`, toggles `tg tw tl tb td ta hq`, `ih` | signs, `:Hunk stage reset preview undo next prev`; the profile reproduces `- _ > < hu hS hR hb` and `hp` (hunk preview in a tracked buffer, else harpoon previous; `hP` is harpoon previous everywhere); missing: word diff, line highlight, deleted lines, line blame text, `ih`, stage a Visual range | partial |
| harpoon | `<leader>ha he hp hn`, `<leader>1..9` | `harpoon` plugin, same keys | done |
| indent-blankline (disabled) | | `guides` | done |
| lualine | auto theme, no separators, transparent section backgrounds | `statusline` plugin: mode, file, branch, hunks, diagnostics, filetype, position; transparent through `transparent_style` | partial |
| LuaSnip + friendly-snippets | snippets | VS Code format `snippets.json` / `snippets/LANGUAGE.json` next to the keymap file reads friendly-snippets' files unchanged; luasnip's own Lua snippets are out | partial |
| marks.nvim | marks in the sign column | `:marks`, `<Space>fm`; no signs | partial |
| markview.nvim | markdown rendering in the buffer | decision: the picker preview renders markdown; no in-buffer rendering (a plugin over the decoration seam, later; the standalone tui-markdown library is the renderer to reuse) | missing |
| mason, mason-lspconfig | | servers must be on PATH | out |
| mini.bracketed | `[b ]b ...` | `bracketed` plugin (b q t h c d); yank, comment, window, undo targets are missing | partial |
| mini.colors | `<leader>kk` | `:theme` and `<Space>fC`; no interactive tweaking | out |
| mini.diff (disabled), mini.extra | pickers for git branches | finder branches | done |
| mini.files | `<leader>e`; `R` refresh, `gs` sort by time | `explorer`: `<Space>e`; sort toggle and refresh key missing | partial |
| mini.indentscope | the scope guide of the cursor | `guides` draw all guides; the cursor's scope is not highlighted | partial |
| mini.jump2d (disabled) | | `jump`: `<Space>j` | done |
| mini.move | `H J K L` (line), `<C-h/j/k/l>` (selection) | `move` plugin on Alt keys; the profile maps his keys | done |
| mini.surround | `<leader>sa sd sf sF sh sr`, `n_lines`, `highlight_duration` | `ys ds cs S` and `<Space>sa sd sr`; find / find_left / highlight / next-last suffixes missing | partial |
| neogit, neo-git (disabled), vim-fugitive | `<leader>gg` | `<Space>gg` lists changed files; `:Git` reads (log, show, diff, blame); commit / push are not built | partial |
| neoscroll | animated `<C-u> <C-d> <C-b> <C-f> <C-y> <C-e> zt zz zb`, wheel | core scroll animation (`ui/MED_anim.m31`, `MED_glide`) | done |
| neotest (disabled) | | | out |
| neo-tree (disabled) | | `explorer` | done |
| no-neck-pain | `:NoNeckPain` | a centered-window option: a core renderer feature, not built | missing |
| nui | library | | out |
| nvim-highlight-colors | colour swatches as background | decoration plugin, not built | missing |
| nvim-java | | | out |
| nvim-lspconfig | servers via mason | `lsp`: diagnostics, hover, definition, references, rename, code action, completion, semantic tokens, format | done |
| nvim-notify | | `notify` plugin | done |
| nvim-ufo | `zR zM`, folds from treesitter/indent, open by default | core folds and `autofold`; `zR zM` same; `foldlevelstart=99` is the default | done |
| nvim-web-devicons | icons | not built (optional plugin in the order) | missing |
| THEME.lua | transparent themes | themes and `transparent_style` (docs/TRANSPARENCY.md) | done |
| todo-comments | | `todo` plugin | done |
| nvim-treesitter | highlight, indent | m3 has its own `syntax` library (no tree-sitter); indent is the core's | done |
| trouble | `<leader>xx xX cs cl xL xQ` | same keys except `cl` (LSP panel) | partial |
| which-key | `<leader>?` buffer-local maps | `whichkey` plugin and `<Space>?` (all maps) | partial |
| lazy.nvim | plugin manager | | out |
| autocmds (`autocomds.lua`) | the file only holds commented code | | out |

## What this milestone built

* `:Profile nvim` (above), `:Formatter`, option `formatonsave`, option `pumkeys`.
* The vi core pieces in `docs/VI-CORE.md` that the config relies on indirectly (`:args`, tags, `:grep`, `:make`).

## What it did not (honest list)

* The seams of docs/CORE-AND-PLUGINS.md section 10 are not cut: surround and autopairs are still core code, no new plugin API was added
  (the API is still 0.4.0), the explorer is not a docked-panel plugin, git signs are not a plugin. Reason: every one of them is an extraction
  of code entangled with the engine and needs the full oracle and golden suites to stay green at each step; this branch spent the budget on
  the vi core and the profile. Each is the next step in the order of section 10.
* git-conflict, markview, no-neck-pain, nvim-highlight-colors, a two-pane diff: no plugin yet.
* m31 requests: none new. (`CTRL-Z` / `:stop` need signals: the existing `docs/M31-ON-TRAP-REQUEST.md`.)

## Counts

66 rows with a status in the tables above:
**done 27, partial 20, missing 6, out 13** (the table counts are produced by `awk` over the last column; the keymap and option
tables are included). "Done" for a key means the row of `docs/KEYMAP.md` exists and its engine part is under the nvim oracle; the
profile's own lines are covered by `tests/t_vi.m31` (the J move, the options) and by the key parser at load, not each by a pty run.
