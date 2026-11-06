# Keymap review: sane IDE defaults

Status: decision document, 2026-11-05, against m3 0.20.0 (landscape branch on e300221). No engine code. It answers the owner's request
"review all keys with sane defaults and recommended in the ide setup of nvims" and "use the research for better keymaps if my defaults
do not make sense". It sits on top of `docs/PLUGIN-LANDSCAPE.md` (owner decisions D1 to D8 are taken as given) and `docs/KEYMAP.md`
(the generated table of what is bound today).

Decisions already taken by the owner and applied here without re-arguing them:

* The `nvim` profile is his config; where his keys and the default profile collide, his config wins.
* Harpoon "remove" leaves `<Space>hd` (his `<leader>hd` is gitsigns "Diff This").
* Hunk keys: `]h [h`, `gh{motion}` / `gH{motion}` apply / reset, `ih` / `ah`, group `<Space>gh` with `s r S R u p b d D`.
* `words` and `toggles` are on by default. An LSP installer, miller columns and a git dashboard are planned. which-key is core and shows the groups.
* Profiles: `minimal` (bare vi, no leader table), `default` (batteries included, sane IDE keys), `nvim` (his maps).

## 0. How this was researched

Everything below was read from files, not recalled. Shallow clones (2026-11-05) in a scratch directory, read-only:

| setup | commit | files read |
|---|---|---|
| LazyVim | 301a3f7 | `lua/lazyvim/config/keymaps.lua`, `plugins/{editor,ui,util,coding,treesitter}.lua`, `plugins/lsp/init.lua`, `plugins/extras/editor/{snacks_picker,snacks_explorer}.lua`, `extras/{dap,test}/core.lua` |
| AstroNvim | fc95d5d | `lua/astronvim/plugins/_astrocore_mappings.lua`, `_astrolsp_mappings.lua`, `gitsigns.lua`, `snacks.lua`, `toggleterm.lua`, `resession.lua`, `mason.lua` |
| NvChad | 87d6a41 | `lua/nvchad/mappings.lua` |
| kickstart.nvim | 8e35dbe | `init.lua` |
| LunarVim | aa51c20 | `lua/lvim/core/which-key.lua`, `lua/lvim/keymappings.lua` |
| snacks.nvim | 882c996 | `README.md` (the key table), `lua/snacks/words.lua` |
| mini.nvim | a321b53 | `lua/mini/{bracketed,surround,ai,operators,jump2d,diff,files,comment,move,splitjoin,clue}.lua` (default `mappings`) |
| Helix | master | https://raw.githubusercontent.com/helix-editor/helix/master/book/src/keymap.md (goto, match, window, space, unimpaired) |
| Zed | main | https://raw.githubusercontent.com/zed-industries/zed/main/assets/keymaps/vim.json |
| Kakoune | master | https://raw.githubusercontent.com/mawww/kakoune/master/doc/pages/modes.asciidoc ("User mode ... is empty by default") |
| Neovim 0.11.5 | local | `nvim -u NONE` default maps dumped with `nvim_get_keymap`, `runtime/doc/index.txt` (the `g`, `[`, `]` lists) |
| owner | local | `~/.config/nvim`: `init.lua`, `lua/config/keymaps.lua`, all `lua/plugins/*.lua` (53 files; the active ones decide) |

Web access worked. Helix and Zed were read from the raw files in their repositories, not through a summariser. Nothing is invented; where a
fact could not be checked it says "not verified".

Abbreviations in the "who agrees" columns: LV LazyVim, AN AstroNvim, NC NvChad, KS kickstart, LU LunarVim, SN snacks, MI mini.nvim,
HX Helix, ZD Zed (vim mode), KK Kakoune, NV Neovim 0.11 builtin, OW owner's config.

## 1. Inventory: every key m3 binds today

`docs/KEYMAP.md` is generated from `ui/MED_keymap.m31` and already lists every row. This section restates it by family so the review has
one table to point at. "src" is the table's own source column (`vim` builtin, `config` copied from the owner's config, `m3` invented here).
"profile" says where the key lives today: **always** = in the single built-in tree for everybody, **nvim** = added by `:Profile nvim`.

### 1.1 Leader tree (`ui/MED_keymap.m31` `defaults()`), all Normal mode unless noted

| key | action | class | src | profile |
|---|---|---|---|---|
| `<Space>w` | write file | core | config | always |
| `<Space>z` | close window | core | config | always |
| `<Space>o` | only this window | core | config | always |
| `<Space>n` | new buffer | core | config | always |
| `<Space>R` | reload file from disk | core | config | always |
| `<Space>sv` `sh` `se` `sc` | split right / below / equalize / close | core | config | always |
| `<Space>sn` | clear search highlight | core | m3 | always |
| `<Space>sa` (n, x) `sd` `sr` | surround add / delete / replace | surround | config | always |
| `<Space>qq` `qa` | quit / quit all | core | m3 | always |
| `<Space>bb` `bn` `bp` `ba` `bd` `bl` | switch (picker) / next / prev / alternate / delete / list | finder, core | m3 | always |
| `<Space>e` `E` | file tree / reveal file in tree | explorer | config, m3 | always |
| `<Space>ff` `fg` `fr` `fb` `fe` `fq` `fd` | files / live grep / recent / buffers / explorer picker / quickfix / lines of buffer | finder | config | always |
| `<Space>fw` `fh` `fc` `fk` `fo` `fm` `fx` `fs` `fl` `fC` | grep word / help keys / commands / keymaps / options / marks / diagnostics / symbols / plugins / colour schemes | finder | m3 | always |
| `<Space>ft` | TODO comments | todo | m3 | always |
| `<Space><Space>` `,` `/` `:` `?` | files / buffers / live grep / commands / all keys | finder, core | m3 | always |
| `<Space>j` | label jump | jump | m3 | always |
| `<Space>gg` `gf` `gb` `gc` `gC` | changed files / changed files / branches / remote branches / commit history | git | config | always |
| `<Space>gs` `gr` `gp` `gu` | stage / reset / preview / unstage hunk | git | m3 | always |
| `<Space>gl` `gd` `gm` `gB` `gt` | file log / diff / blame list / blame line / toggle signs | git | m3 | always |
| `<Space>ll` `]]` `[[` | diagnostic float / next / previous (typed as `<Space>]]`) | lsp | config | always |
| `<Space>xx` `xX` `xQ` `xL` | trouble-style diagnostics / buffer / quickfix / location list | lsp, finder | config | always |
| `<Space>cs` | symbols | finder | config | always |
| `<Space>cr` `ca` `cf` `ck` `ch` | rename / code action / format / signature help / inlay hints | lsp | m3 | always |
| `<Space>t` | terminal | terminal | config | always |
| `<Space>h` + `ha he hn hp hd` | harpoon add / menu / next / prev / remove | harpoon | m3 | always |
| `<Space>1` .. `9` | harpoon file N | harpoon | m3 | always |

### 1.2 Prefix families (vi / vim / nvim builtins, unchanged by this review)

| family | what is bound | src |
|---|---|---|
| `g` | 38 builtins (`gg ge gE gi gI gJ gj gk g0 g^ g$ gm gM go gp gP gq gw gu gU g~ g? gv g; g, ga g8 gf gn gN g& g_ g- g+ g* g# gR gs`), `gc` / `gcc` comment | vim |
| `g` (m3 additions) | `K` hover, `gd` definition, `grr` references, `grn` rename, `gra` code action | m3 (grr grn gra are nvim 0.11 defaults) |
| `z` | 39 view and fold keys (`zt zz zb z<CR> z. z- zh zl zH zL zs ze zf zF zo zO zc zC za zA zv zR zM zd zD zE zj zk zn zN zi`) | vim |
| `[` `]` | `[[ ]] [] ][ [{ ]} [( ]) [' ]' [\` ]\`` and `[<Space> ]<Space>` | vim, nvim 0.11 for `<Space>` |
| `<C-w>` | 31 window keys (`s v n c q o w W p t b h j k l H J K L r R x = + - < > _ \|`) | vim |
| `"`, `'`, `` ` ``, `m`, `q`, `@` | registers and marks | vim |
| `d c y < > = !` + doubles | operators and linewise doubles | vim |
| `ys yss yS ds cs` (+ Visual `S`) | surround | vim-surround, kept |

### 1.3 Plugin keys (from the plugins' `MapSpec`s)

| key | mode | action | plugin | src |
|---|---|---|---|---|
| `[b ]b [B ]B` | n | buffer prev / next / first / last | bracketed | m3 (nvim 0.11 has the same four) |
| `[q ]q [Q ]Q` | n | quickfix prev / next / first / last | bracketed | m3 (nvim 0.11 has the same four) |
| `[t ]t` | n | TODO prev / next | bracketed | m3 (nvim 0.11: tag prev / next) |
| `[h ]h` | n | git hunk prev / next | bracketed | m3 |
| `[c ]c` | n | git change prev / next | bracketed | m3 (vim: diff change) |
| `[d ]d` | n | diagnostic prev / next | bracketed | m3 (nvim 0.11 has them) |
| `<M-j> <M-k>` | n, x | move line / selection down / up | move | m3 |
| `<M-h> <M-l>` | n, x | shift line / selection left / right | move | m3 |
| `<C-q>` `<C-t>` | picker | send marked to quickfix / mark entry | finder | m3 |
| `jk` | i | leave Insert (`:set nojk_escape`) | core | config |
| `<C-^>` | n | alternate buffer | core | vim |
| `<Tab>` `<S-Tab>` | i, s | snippet expand / tabstops; completion next / prev | core, lsp | vim (nvim 0.11), m3 |
| `<C-Space>` | i | ask the language server for completions | lsp | m3 |
| `<C-n> <C-p> <Down> <Up> <C-y> <CR> <C-e>` | i (popup open) | select next / prev / accept / close | lsp | vim |

### 1.4 `:Profile nvim` (`engine/MED_profile.m31`, only `:Profile nvim`)

Options: `tabstop=4 shiftwidth=4 expandtab relativenumber ignorecase smartcase mouse=a smoothscroll pumkeys=blink lspformat`, formatters for
rust, python, lua, javascript, typescript, jsx, tsx, json, jsonc.

| key | mode | action | his config |
|---|---|---|---|
| `<Space>b` | n | `:Buffers` picker (replaces m3's `b` group) | buffer_manager |
| `<Space>gn` `gr` | n | create / rename branch (typed) | keymaps.lua |
| `<Space>gdd` `gt` | n | `:Git diff` list | keymaps.lua (DiffviewOpen) |
| `<Space>a` | n | `:Symbols` | aerial.lua, **disabled in his spec** (stale) |
| `H J K L` | n | dedent / move line down / move line up / indent | mini.move |
| `<C-h> <C-l> <C-j> <C-k>` | x | dedent / indent / move selection down / up | mini.move |
| `>` `<` | n | next / previous hunk | gitsigns |
| `-` `_` | n, x | stage / reset hunk | gitsigns |
| `<Space>hu` | n | undo stage hunk | gitsigns |
| `<Space>hS` | n | stage buffer (`git add -- %`) | gitsigns |

## 2. What the other setups bind

Only keys that matter for the default profile. A cell is the key; "-" means the setup has no binding for that job. Evidence file in section 0.

### 2.1 Leader groups

| job | LV | AN | NC | KS | LU | HX (space) | ZD | consensus |
|---|---|---|---|---|---|---|---|---|
| find files | `<leader>ff`, `<leader><leader>` | `ff` | `ff` | `sf`, `<leader>s.` recent | `f` / `sf` | `f` (`F` cwd) | `space f` | **`ff`**, `<leader><leader>` (LV, KS buffers) |
| buffers picker | `<leader>,` `fb` | `fb` | `fb` | `<leader><leader>` | `bf` | `b` | `space b` | `fb` (LV AN NC), `,` (LV) |
| live grep | `<leader>/`, `sg` | `fw` | `fw` | `sg` | `st` | `/` | `space /` | **`sg`** (LV KS) and `/` (LV KS HX ZD) |
| grep word | `sw` | `fW`/`fc` | - | `sw` | - | - | - | `sw` (LV KS) |
| recent | `fr` | `fo` | `fo` | `s.` | `sr` | - | - | `fr` (LV) |
| git files | `fg` | `fg` | - | - | - | `g` changed files | - | `fg` (LV AN) |
| help / keymaps | `sh` `sk` | `fh` `fk` | `fh`, `ch` cheatsheet | `sh` `sk` | `sh`/`sk`... | `?` palette | - | `sh` `sk` (LV KS LU) |
| commands | `sC`, `:` hist | `fC` | - | `sc` | `sC` | `?` | - | `sC` (LV LU) |
| diagnostics picker | `sd` `sD` | `lD` | - | `sd` | `lw` `ld` | `d` `D` | `space d` | `sd` (LV KS); `d` is Helix + OW |
| symbols | `ss` `sS` | `ls` `lG` | - | `gO` `gW` | `ls` `lS` | `s` `S` | `space s` `S` | `ss` (LV), `gO`/`gW` (KS, NV) |
| marks | `sm` | `f'` | `ma` | - | - | - | - | `sm` (LV) |
| resume | `sR` | - | - | `sr` | `sl` | `'` | - | `sR`/`sr` (LV KS LU) |
| explorer | `e` `E` | `e` | `e`, `<C-n>` | - | `e` | `e` `.` | - | **`e`** (LV AN NC LU HX) |
| new file | `fn` | `n` | `b` | - | - | - | - | `fn` (LV) |
| notifications | `n` | `uD` dismiss | - | - | - | - | - | `n` (LV, SN), `un` dismiss (LV SN) |
| save | `<C-s>` | `w`, `<C-s>` | `<C-s>` | - | `w` | - | - | `<C-s>` (LV AN NC) |
| quit | `qq` | `q` window, `Q` | - | - | `q` | - | - | `qq` (LV) |
| windows | `w` group, `-` `\|` split, `wd` `wm` | `\|` `\` split | - | - | - | `w` window mode | `space w v s h j k l q` | **`w` group** (LV HX ZD); split keys `-` `\|` (LV) |
| buffers group | `b` (`bb bd bo bD bp bP br bl bj`) | `b` (`bc bC bl bp bs..`) | - | - | `b` | - | - | `b` group (LV AN LU) |
| git group | `g` (`gg gG gl gL gb gf gd gD gs gS gB gY`) | `g` (`gl gL gp gr gR gs gS gd gb gc gC gt gT go`) | `gt` status | - | `g` (`gg gj gk gl gL gp gr gR gs gu gb gc gd`) | `g` changed files | `g u` stage&next | `g` group; **`gg` lazygit/dashboard** (LV AN LU) |
| hunk group | `gh`: `hs hr hS hu hR hp hb hB hd hD` | `g`: `r R s S p d l L` | - | `h`: `s r S R p i b d D q Q` | `g`: `s r R p u` | - | - | **`gh` + `s r S R u p b d D`** (LV, KS names under `h`) |
| code group | `c` (`ca cr cf cd cl cR cc cC cA co cs cS cm`) | `l` (`la lr lf ld li ll lG ls lh`) | `ch` | `gra grn` | `l` (`la lr lf ld lw lj lk li lI ls`) | `a` `r` `k` | `space a r k` | **`c`** (LV); `l` is AN LU |
| diagnostics list | `xx xX xL xQ xl xq` | `xq xl` | `ds` loclist | `q` loclist | - | `d` | - | `x` (LV AN) |
| UI toggles | `u` (`uf us uw uL ud ul uc ub uT uD ua ug uS uh uz uZ uC un ur`) | `u` (`ub ud ug ui ul un up us ut uv uw uh uf`) | `n` `rn` | `tb tw th` | - | - | - | **`u`** (LV AN) |
| terminal | `ft` `fT` `<C-/>` | `t` group (`tf th tv tl`), `<F7>`, `<C-'>` | `h` `v` `<A-v>` `<A-h>` `<A-i>` | `<Esc><Esc>` leaves | lazygit | - | - | `<C-/>` (LV SN), `t` group (AN) |
| session | `qs ql qS qd` | `S` group | - | - | - | - | - | `q` (LV) |
| lazy / mason | `l`, `cm` | `p` group, `pm` | - | - | `p`, `lI` | - | - | m3 has neither a plugin manager; installer key = `cm` (LV) |
| zen / scratch | `uz` `.` `S` | `uZ` | - | - | - | - | - | `.` scratch, `uz` zen (LV SN) |
| debug | `d` group | `d` | - | - | `d` | `G` | `space G` | NOT used by m3 (owner D1); `<Space>D` reserved |

### 2.2 Brackets, g-prefix, controls

| key | who | note |
|---|---|---|
| `]b [b` buffer | NV LV AN ZD MI | builtin in nvim 0.11 |
| `]q [q` quickfix | NV LV LU MI | builtin in nvim 0.11 |
| `]d [d` diagnostic | NV LV HX ZD MI | builtin in nvim 0.11 |
| `]e [e` error, `]w [w` warning | LV (keymaps.lua 137-140), AN | MI uses `]w` for window |
| `]h [h` hunk | LV (editor.lua 160-169), MI (mini.diff), KS `]c` | AN `]g [g`, ZD `] c` |
| `]H [H` first / last hunk | LV (editor.lua 174-175), MI | AN `]G [G` |
| `]t [t` TODO | LV (editor.lua 263-264) | NV tag, AN tab, HX type, MI treesitter |
| `]x [x` conflict marker | MI | owner's git-conflict uses `n p` inside the conflict |
| `]r [r` next reference | AN (snacks.lua 242-243), ZD (vim.json 223-224) | LV and SN use `]]` `[[` and shadow vim's section motions |
| `]]` `[[` | vim, NV, ZD (sections) | LV rebinds to references when an LSP is attached |
| `]f [f` function, `]a [a` argument | HX, LV (treesitter-textobjects) | needs text-object registry (D7) |
| `]c [c` | NV (diff change), LV (class), HX (comment), MI (comment) | KS and LV fall back to builtin inside a diff |
| `gd` definition | LV AN HX ZD (`g d`) | KS has `grd` |
| `gD` declaration | LV AN HX ZD | KS `grD` |
| `gr` references | LV (nowait), HX, ZD (`g r` in helix mode) | NV 0.11: `grr`; `gr` is a prefix and vim's `gr{char}` |
| `grr gri gra grn grt gO` | NV 0.11 builtins; KS uses them | |
| `gI` implementation | LV AN ZD | HX `gi` collides with vim `gi` insert |
| `gy` type definition | LV AN HX ZD | NV `grt` |
| `gK` signature help | LV AN | NV: `<C-S>` in Insert |
| `K` hover | LV AN NV-less | NV 0.11 maps `K` to hover on LSP buffers |
| `gh`, `gH` | MI mini.diff apply / reset; ZD `gh` hover | vim: start Select mode |
| `gc` / `gcc` | NV MI LV AN | `gco gcO` LV AN |
| `gx` | NV LV ZD | open URL |
| `<C-h/j/k/l>` window focus | LV AN NC KS LU (5 of 5 neovim setups), HX in window mode | shadows vi `^H ^J` (same as h / j) and `<C-l>` (redraw, nvim 0.11 default) |
| `<C-Up/Down/Left/Right>` resize | LV AN LU | |
| `<A-j/k>` move line | LV LU, MI (`mini.move` default is `<M-j>` in Alt form) | |
| `<C-s>` save | LV AN NC | shadows nvim 0.11 Insert `<C-S>` signature help only if mapped in Insert (LV does) |
| `<Esc>` clear hlsearch | LV NC KS | `<leader>ur` (LV) redraw + nohl + diffupdate |
| `<C-/>` terminal | LV SN | |
| visual `<` `>` stay selected | LV (keymaps.lua 87-88), AN, LU | |
| `H` `L` buffers | LV (`<S-h>` `<S-l>`) | shadows vi `H` `L`. Rejected below |
| `<Tab>` buffers | NC | shadows `<C-i>`. Rejected |

## 3. The proposed `default` profile

Principles, in priority order:

1. Never shadow a key that the `minimal` profile (bare vi) keeps. A default-profile map may shadow a Vim/nvim extra that vi does not have, only with evidence and a note.
2. Follow the majority when two or more of LV, AN, KS, LU, NC, HX, ZD agree. Where LazyVim is alone and costs a vi key, do not follow it.
3. Mnemonic letters, one job per letter, no leaf that is also a prefix.
4. Keep nvim 0.11 builtins (`gra grn grr gri grt gO`, Insert `<C-S>`, `[<Space> ]<Space>`, `]b [b ]q [q ]d [d`, `gc gcc`, `gx`).
5. Owner decisions D1 to D8 stand. Debug (`<Space>D`) stays reserved and empty.

"exists" = bound in m3 today. "from" = old key if renamed (the migration table in section 7 repeats these).

### 3.1 Leader tree (`<Space>`), mode Normal unless noted

Top-level leaves and groups first, then each group.

| key | action | class | exists | from |
|---|---|---|---|---|
| `<Space><Space>` | find files | finder | yes | |
| `<Space>,` | buffers picker | finder | yes | |
| `<Space>/` | live grep (project) | finder | yes | |
| `<Space>:` | commands | finder | yes | |
| `<Space>?` | all keys (which-key / `:Keys`) | core | yes | |
| `<Space>-` | split below | core | no | new (LV) |
| `<Space>\|` | split right | core | no | new (LV) |
| `<Space>j` | label jump | jump | yes | |
| `<Space>e` | file tree | explorer | yes | |
| `<Space>E` | reveal current file in the tree | explorer | yes | |
| `<Space>M` | miller columns at the file's directory | explorer | planned | new (owner D2; letter free in every setup read) |
| `<Space>n` | notification history | notify | no | was "new buffer" |
| `<Space>.` | scratch buffer (toggle) | scratch (opt-in plugin) | no | new (LV, SN) |
| `<Space>1` .. `9` | harpoon file N | harpoon | yes | |
| `<Space>D` | reserved: debug | - | no | (owner D1) |

**`f` find / files** (what you look for by name; LV `f` group, AN `f`)

| key | action | class | exists | from |
|---|---|---|---|---|
| `ff` | files | finder | yes | |
| `fF` | files in cwd (not project root) | finder | no | new (LV) |
| `fr` | recent files | finder | yes | |
| `fb` | buffers | finder | yes | |
| `fg` | git files | finder | no | **semantic change**: was live grep (LV AN agree) |
| `fe` | explorer picker | finder | yes | |
| `fc` | config file (the keymap file) | finder | no | was "commands" (LV `fc`) |
| `fn` | new file | core | no | was `<Space>n` (LV) |
| `fp` | projects / recent project roots | finder | no | new (LV AN), needs `session` plan |

**`s` search** (picker over text or lists; LV, KS)

| key | action | class | exists | from |
|---|---|---|---|---|
| `sg` | live grep (project) | finder | yes | `fg` |
| `sG` | live grep in cwd | finder | no | new (LV) |
| `sw` (n, x) | grep word / selection | finder | yes | `fw` |
| `sb` | lines of this buffer | finder | yes | `fd` |
| `sB` | grep open buffers | finder | no | new (LV) |
| `sh` | help (all keys) | finder | yes | `fh` |
| `sk` | keymaps | finder | yes | `fk` |
| `sC` | commands | finder | yes | `fc` |
| `sc` | command history | finder | no | new (LV KS) |
| `so` | options | finder | yes | `fo` |
| `sm` | marks | finder | yes | `fm` |
| `sd` | diagnostics (workspace) | finder, lsp | yes | `fx` |
| `sD` | diagnostics (this buffer) | finder, lsp | no | new (LV) |
| `ss` | symbols in this file | finder, lsp | yes | `fs`, `cs` |
| `sS` | symbols in the workspace | finder, lsp | no | new (LV HX) |
| `sq` | quickfix list | finder | yes | `fq` |
| `sl` | location list | finder | no | new (LV) |
| `st` | TODO comments | todo | yes | `ft` |
| `sR` | resume last picker | finder | no | new (LV KS LU HX `'`). Owner's `fr` is resume, see section 5 |
| `sj` | jumps | finder | no | new (LV) |
| `su` | undo history | finder | no | new (LV AN), needs undo tree picker |
| `sp` | plugins | finder | yes | `fl` |
| `s"` | registers | finder | no | new (AN `fr`, LU `sR`) |

**`b` buffers** (LV, AN, LU)

| key | action | class | exists | from |
|---|---|---|---|---|
| `bb` | alternate buffer | core | yes | `ba` (and `bb` was the picker; LV `bb` = alternate) |
| `bn` `bp` | next / previous | core | yes | |
| `bd` | delete buffer | core | yes | |
| `bD` | delete buffer and window | core | no | new (LV) |
| `bo` | delete other buffers | core | no | new (LV) |
| `br` | reload from disk | core | yes | `<Space>R` |
| `bl` | list buffers | core | yes | (unchanged; AN and LV use `bl` for "close left", m3 has no ordered tabline) |
| `bP` | pin buffer (harpoon add) | harpoon | no | optional alias of `ha` |

**`w` windows** (LV `w` group, HX window mode, ZD `space w`)

| key | action | class | exists | from |
|---|---|---|---|---|
| `ws` | split below | core | yes | `sh` |
| `wv` | split right | core | yes | `sv` |
| `wd` | close window | core | yes | `z`, `sc` |
| `wo` | only this window | core | yes | `o` |
| `w=` | equalize | core | yes | `se` |
| `wm` | maximize toggle (zoom) | core | no | new (LV `wm`) |
| `ww` | other window | core | no | new (LV via `<C-w>`) |
| `wh` `wj` `wk` `wl` | focus left / below / above / right | core | no | new (HX, ZD `space w h j k l`) |
| `wx` | exchange windows | core | no | new (HX `Ctrl-w` swap) |
| `wH` `wJ` `wK` `wL` | move window to far side | core | no | new (HX swap) |

**`g` git** (LV, AN, LU: `g` is git everywhere)

| key | action | class | exists | from |
|---|---|---|---|---|
| `gg` | git dashboard (today: changed files picker) | git | yes (picker); dashboard planned | |
| `gf` | history of this file | git | yes | `gl` (LV `gf`) |
| `gl` | commit log | git | no | `gC` (LV `gl`) |
| `gb` | branches (checkout) | git | yes | |
| `gc` | commit (planned write op); today remote branches | git | yes | owner decision: see section 8 |
| `gd` | diff, working tree | git | yes | |
| `gD` | diff against origin | git | no | new (LV) |
| `gS` | stash list | git | no | new (LV AN) |
| `gB` | open on the web (browse) | git | no | new (LV AN `go`); was "blame line" |
| `gP` `gF` | push / pull | git | planned | new (git write ops F3) |
| `gh` | +hunks (group) | git | yes | |
| `ghs` (n, x) | stage hunk | git | yes | `gs` |
| `ghr` (n, x) | reset hunk | git | yes | `gr` |
| `ghS` | stage buffer | git | no | new (LV KS) |
| `ghR` | reset buffer | git | no | new (LV KS) |
| `ghu` | undo stage hunk | git | yes | `gu` |
| `ghp` | preview hunk | git | yes | `gp` |
| `ghb` | blame line | git | yes | `gB` |
| `ghB` | blame list (buffer) | git | yes | `gm` (LV `ghB`) |
| `ghd` | diff this (file against index) | git | planned (needs core `:diffthis`, D4) | new (LV KS) |
| `ghD` | diff this against HEAD~ | git | planned (D4) | new (LV KS) |

**`c` code / LSP** (LV `c`)

| key | action | class | exists | from |
|---|---|---|---|---|
| `ca` (n, x) | code action | lsp | yes | |
| `cr` | rename symbol | lsp | yes | |
| `cR` | rename file | lsp | no | new (LV, SN, AN `R`) |
| `cf` (n, x) | format | lsp | yes | |
| `cd` | diagnostic at the cursor (float) | lsp | yes | `ll` (LV `cd`) |
| `cl` | language server info (`:Lsp`) | lsp | no | new (LV `cl`) |
| `cm` | language servers: install (the planned installer) | lsp | planned | new (LV `cm` Mason) |
| `co` | organize imports | lsp | no | new (LV) |
| `cA` | source action | lsp | no | new (LV) |
| `cs` | symbols (same as `ss`) | finder | yes | (kept for the old muscle memory; documented as alias) |

**`d` diagnostics** (HX `d`/`D`, ZD `space d`, owner's `dd ds dw`; LazyVim's debug `d` is dropped, owner D1)

| key | action | class | exists | from |
|---|---|---|---|---|
| `dd` | workspace diagnostics list | lsp | yes | `xx` / `fx` alias |
| `db` | buffer diagnostics list | lsp | no | new (LV `xX`) |
| `dl` | diagnostic at the cursor (float) | lsp | yes | `ll` |
| `dn` `dp` | next / previous diagnostic | lsp | no | duplicates `]d [d`: not added (note only) |
| `dt` | toggle diagnostics | toggles | no | LV `ud` kept as primary |

(`dn dp dt` are listed as not adding anything. Real keys: `dd db dl`.)

**`x` lists** (LV, AN, owner)

| key | action | class | exists | from |
|---|---|---|---|---|
| `xx` | diagnostics panel | lsp | yes | |
| `xX` | buffer diagnostics panel | lsp | yes | |
| `xQ` | quickfix panel | finder | yes | |
| `xL` | location list panel | finder | yes | |
| `xq` `xl` | open quickfix / location list window | core | no | new (LV AN) |
| `xt` | TODO panel | todo | no | new (LV) |

**`t` terminal** (AN `t` group; LV `ft`; `<C-/>` LV SN)

| key | action | class | exists | from |
|---|---|---|---|---|
| `tt` | toggle terminal | terminal | yes | `t` |
| `tf` `th` `tv` | float / horizontal / vertical terminal | terminal | no | new (AN) |
| `<C-/>` (n, t) | toggle terminal (also `<C-_>`, the byte terminals send) | terminal | no | new (LV, SN) |

**`u` UI toggles** (LV, AN; all via a core `:Toggle NAME`, on by default per D3)

| key | action | class | exists | from |
|---|---|---|---|---|
| `uw` | wrap | toggles | no | new (LV AN) |
| `ul` | line numbers | toggles | no | new (LV) |
| `uL` | relative numbers | toggles | no | new (LV) |
| `us` | spell | toggles | no | new (LV AN) |
| `ud` | diagnostics | toggles | no | new (LV AN) |
| `uh` | inlay hints | toggles | yes | `ch` (LV AN `uh`) |
| `uf` | format on save | toggles | no | new (LV AN) |
| `ug` | indent guides | toggles | no | new (LV) |
| `uG` | git signs | toggles | yes | `gt` (LV `uG`) |
| `uW` | git word diff | toggles | no | new (owner's `tw`) |
| `uB` | git line blame text | toggles | no | new (owner's `tb`) |
| `ur` | words (reference highlight) | toggles | no | new (AN `ur`, SN words) |
| `ua` | animation (scroll glide) | toggles | no | new (LV `ua`; m3 has `:set animate`) |
| `uc` | conceal | toggles | no | new (LV AN `uS`) |
| `ub` | background light / dark | toggles | no | new (LV AN) |
| `uC` | colour schemes | finder | yes | `fC` (LV `uC`) |
| `uz` | zen mode | toggles | no | new (LV SN) |
| `un` | dismiss notifications | notify | no | new (LV SN, AN `uD`) |
| `uR` | redraw, clear search highlight, diff update | core | no | new; LV puts this on `ur`, but `ur` is words here (AN) |

**`q` quit / session** (LV `q`)

| key | action | class | exists | from |
|---|---|---|---|---|
| `qq` | quit (window, asks if modified) | core | yes | |
| `qa` | quit all | core | yes | (LV `qq` = quit all; not followed, m3 `qq` stays one window) |
| `qs` | restore session | session | planned | new (LV) |
| `ql` | restore last session | session | planned | new (LV) |
| `qd` | do not save the session | session | planned | new (LV) |

**`h` harpoon**: `ha` add, `he` menu, `hn` next, `hp` previous, `hx` remove (from `hd`, owner decision), `<Space>1..9` select.

### 3.2 Non-leader keys

`g` prefix:

| key | mode | action | class | exists | from / note |
|---|---|---|---|---|---|
| `gd` | n | go to definition | lsp | yes | |
| `gD` | n | go to declaration | lsp | no | new (LV AN HX ZD) |
| `grr` | n | references | lsp | yes | nvim 0.11. Plain `gr` is **not** bound (vim `gr{char}`, and it would delay `grr grn gra gri grt`) |
| `gri` | n | implementation | lsp | no | nvim 0.11 default |
| `grt` | n | type definition | lsp | no | nvim 0.11 default |
| `grn` | n | rename | lsp | yes | nvim 0.11 default |
| `gra` | n, x | code action | lsp | yes | nvim 0.11 default |
| `gy` | n | type definition (alias of `grt`) | lsp | no | new (LV AN HX ZD) |
| `gI` | n | implementation (alias of `gri`) | lsp | no | new (LV AN ZD) |
| `gO` | n | document symbols | lsp | no | nvim 0.11 default (KS uses it) |
| `gW` | n | workspace symbols | lsp | no | new (KS) |
| `gK` | n | signature help | lsp | yes | `<Space>ck` (LV AN) |
| `K` | n | hover | lsp | yes | |
| `<C-S>` | i | signature help | lsp | no | nvim 0.11 default; **not** rebound to save |
| `gx` | n | open the URL or file under the cursor | core | no | nvim 0.11 default (LV ZD) |
| `gc` `gcc` | n, x, o | comment | comment | yes | |
| `gco` `gcO` | n | add comment below / above | comment | no | new (LV AN) |
| `gh{motion}` `gH{motion}` | n, x | apply / reset hunk in range | git | no | owner decision; mini.diff `gh` `gH`. Shadows vim's Select mode `gh` `gH`, which m3 does not offer outside snippets |
| `ih` `ah` | o, x | hunk text object | git | no | owner decision; needs text-object registry (D7) |

Brackets (all Normal; `[` previous, `]` next; capital = first / last where noted):

| pair | target | class | exists | from / evidence |
|---|---|---|---|---|
| `[b ]b` `[B ]B` | buffer | bracketed | yes | NV, LV, AN, ZD, MI |
| `[q ]q` `[Q ]Q` | quickfix | bracketed | yes | NV, LV, LU, MI |
| `[l ]l` `[L ]L` | location list | bracketed | no | nvim 0.11 builtin: add to the table, no new code |
| `[d ]d` `[D ]D` | diagnostic | bracketed | yes (`D` no) | NV, LV, HX, ZD |
| `[e ]e` | error | bracketed | no | new (LV AN) |
| `[w ]w` | warning | bracketed | no | new (LV AN) |
| `[h ]h` `[H ]H` | git hunk | bracketed | yes (`H` no) | LV, MI, owner decision |
| `[t ]t` | TODO | bracketed | yes | LV. Shadows nvim 0.11 `[t ]t` tag prev / next, see 4 |
| `[x ]x` | conflict marker | git (planned) | no | MI; plugin `conflict` is a build item |
| `[r ]r` | next / previous reference (words) | words | no | AN, ZD. Not `]]` `[[` (vi sections) |
| `[f ]f` | function | bracketed | no | HX, LV; needs text-object registry (D7) |
| `[i ]i` | indent change | bracketed | no | MI; needs registry |
| `[<Space>` `]<Space>` | blank line above / below | core | yes | NV, HX |
| `<A-n>` `<A-p>` | next / previous reference, even in Insert | words | no | LV, same job as `]r [r` |

Controls and others:

| key | mode | action | class | exists | evidence |
|---|---|---|---|---|---|
| `<C-h>` `<C-j>` `<C-k>` `<C-l>` | n | window focus left / below / above / right | core | no | LV AN NC KS LU (5 of 5). Shadows `^H` `^J` (= `h` `j`) and `<C-l>` redraw; redraw stays on `<Space>uR`. Insert-mode `<C-h>` (backspace) untouched |
| `<C-Up>` `<C-Down>` `<C-Left>` `<C-Right>` | n | resize window | core | no | LV AN LU |
| `<C-s>` | n, x | write | core | no | LV AN NC. Insert `<C-S>` stays signature help |
| `<Esc>` | n | clear search highlight | core | no | LV NC KS. Was `<Space>sn` |
| `<A-j>` `<A-k>` | n, x, i | move line / selection | move | yes (not Insert) | LV LU |
| `<A-h>` `<A-l>` | n, x | shift line / selection | move | yes | m3 only |
| `<` `>` | x | shift and keep the selection | core | no | LV AN LU. Deviates from vi (selection is dropped) |
| `<C-/>` `<C-_>` | n, t | toggle terminal | terminal | no | LV SN |
| `jk` | i | leave Insert | core | yes | OW, AN better-escape. Option, off in `minimal` |

### 3.3 Which-key group labels (no icons)

| prefix | label | prefix | label |
|---|---|---|---|
| `<Space>` | leader | `<Space>t` | terminal |
| `<Space>f` | files | `<Space>u` | ui toggles |
| `<Space>s` | search | `<Space>q` | quit / session |
| `<Space>b` | buffers | `<Space>h` | harpoon |
| `<Space>w` | windows | `<Space>x` | lists |
| `<Space>g` | git | `<Space>d` | diagnostics |
| `<Space>gh` | hunks | `<Space>c` | code |
| `g` | goto | `]` `[` | next / previous |
| `z` | view / folds | `<C-w>` | windows |

## 4. Changes to existing m3 defaults, with reasons

"Flag" means the user can lose a habit. Each has a `:Profile legacy` alias (section 7).

| # | existing key | change | reason and evidence |
|---|---|---|---|
| C1 | `<Space>s` = split + surround | becomes **search**; splits move to `<Space>w`; surround leaf rows `sa sd sr` removed from default | `s` is search in LV (editor.lua 76), KS (`sf sg sw sd sh sk`), LU; mini.surround's own `sa` collides with vim `s` (substitute) so only the owner's config uses it. `ys ds cs S` stay. |
| C2 | `<Space>w` write | becomes the **windows** group; save on `<C-s>` | `w` windows: LV, HX, ZD. Save: `<C-s>` LV (keymaps.lua 81), AN, NC. `:w` and `ZZ` still work. |
| C3 | `<Space>z`, `o`, `sc` | `wd`, `wo`, `wd` | follows C2 (HX window mode `q` `o`) |
| C4 | `<Space>n` new buffer | `<Space>fn`; `n` = notifications | LV keymaps.lua 98 (`fn`), ui.lua 286 (`n`), SN README |
| C5 | `<Space>R` reload | `<Space>br` (buffer reload); `cR` = rename file | AN and LV both bind rename file on `R` / `cR`; reload is a buffer job |
| C6 | `<Space>bb` picker, `ba` alternate | `bb` alternate; picker is `<Space>,` / `fb` | LV keymaps.lua 38-39 (`bb`, `` ` ``) |
| C7 | `<Space>fg` live grep | `fg` git files; grep is `sg` and `/` | LV (snacks_picker.lua 70), AN (snacks.lua 201) both `fg` = git files. **Silent meaning swap: flag** |
| C8 | `fd fh fc fk fo fm fx fs fl fC ft fw fq` | move to `sb sh sC sk so sm sd ss sp uC st sw sq` | LV snacks_picker.lua 84-109, 165; KS init.lua 555-565. `f` keeps "things that are files" |
| C9 | `<Space>gs gr gp gu` (hunk ops) | `ghs ghr ghp ghu` | owner decision; LV editor.lua 176-181 |
| C10 | `<Space>gl` file log, `gm`, `gB`, `gt` | `gf`, `ghB`, `ghb`, `uG`; `gl` = repo log | LV snacks_picker/keymaps.lua 169-178, editor.lua 182-185, 201 |
| C11 | `<Space>l`, `ll`, `<Space>]]`, `<Space>[[` | `dl` / `cd`; `]d [d` | the leader copies of `]d [d` duplicate a builtin (nvim 0.11 `[d ]d`). Only the owner's config has them |
| C12 | `<Space>ck`, `<Space>ch` | `gK`, `uh` | gK LV (lsp/init.lua), AN; uh LV (keymaps.lua 164), AN. Insert `<C-k>` would shadow digraphs |
| C13 | `<Space>t` terminal leaf | `tt`, plus `<C-/>` | a leaf cannot also be a group; AN `t` group, LV/SN `<C-/>` |
| C14 | `[c ]c` bound to hunks | **removed**; hunks are `[h ]h` only | vim: `[c ]c` jump between changes in diff mode (nvim index.txt). LV editor.lua 160-169 and KS init.lua 366-380 both fall back to the builtin when `vim.wo.diff`. Core `:diffthis` is planned (D4), so `[c ]c` must work there |
| C15 | `[t ]t` TODO | kept, **but flag**: shadows nvim 0.11 `[t ]t` (tag) | LV editor.lua 263-264 does the same. Tag navigation stays on `<C-]>`, `<C-t>`, `:tnext`; vi has no `]t` |
| C16 | `<Space>hd` harpoon remove | `hx` | owner decision (D8): his `hd` is gitsigns diff this |
| C17 | `<Space>sn` clear highlight | `<Esc>` in Normal (and `<Space>uR`) | LV keymaps.lua 52-56, NC mappings, KS init.lua 186 |
| C18 | `[[` `]]` (not changed in m3) | **do not adopt** LV / SN reference jumps on `]]` `[[` | vi section motions (minimal keeps them, ZD keeps them too). Use `]r [r` (AN snacks.lua 242, ZD vim.json 223) |
| C19 | Not adopted: `H` `L` for buffers (LV `<S-h>` `<S-l>`), `<Tab>` buffers (NC), `s` Flash (LV), `ys` replaced by `gs` (LV mini.surround), plain `gr` (LV, owner) | vi core / nvim 0.11 keys | `H L` are screen-top and bottom; `<Tab>` is `<C-i>`; `s` is substitute; plain `gr` blocks `grr grn gra gri grt` |
| C20 | Visual `<` `>` keep selection (new) | deviation from vi | LV, AN, LU. Off in `minimal` |

## 5. The `nvim` profile against his config

### 5.1 How the layering must work

Today `:Profile nvim` runs `nnoremap` lines on top of the built-in tree. That cannot express "his `<Space>b` is a leaf, so the `b` group
goes" or "his `<Space>w` writes, so there is no windows group": a map on a prefix does not remove the longer keys under it.
**The profile has to replace the leader tree, not add to it** (build item B1). With that, the profile is exactly his table plus the
non-leader parts of section 5.2, and it is the only table active when `nvim` is selected. Everything else of `default` that he does not bind is
still available if it does not collide (the brackets `]e ]w ...`, `<C-h/j/k/l>` window focus, `<C-s>`, `gK`...), see 5.3.

### 5.2 His keys, one by one

Active means not `enabled = false` in his spec.

| his key | his action | in `nvim` profile today | status |
|---|---|---|---|
| `<leader>n` | new file | `<Space>n` | ok |
| `jk` (i) | Esc | built in | ok |
| `<leader>ll` `]]` `[[` | diag float, next, prev | ok | ok |
| `<leader>sv sh se sc` | splits | ok | ok (**collides with his own `sh` surround highlight**: gitsigns-style first loaded wins; m3 takes splits) |
| `<leader>ps` `ms` | Lazy / Mason | not mapped | out (m3 has no plugin manager; the installer lands as `cm`) |
| `<leader>cc` `ca` | CodeCompanion | not mapped | out. **Collides with default `ca` code action**: in `nvim` profile `ca` is not code action; `gra` is |
| `<leader>b` | buffer manager | `:Buffers` | partial (no in-place editing of the list) |
| `<leader>gn` `gr` | new / rename branch | typed `:!git ...` | ok |
| `<leader>gdd` `gt` | DiffviewOpen | `:Git diff` list | partial (no two-pane view; core `:diffthis` first, D4) |
| `<leader>z` `o` `w` `R` | close, only, write, reload all | ok | `R` partial |
| terminal `<C-\><C-]>` | leave terminal input | not mapped | **missing** |
| `blink.cmp` Tab, `<C-j>` `<C-k>` `<S-j>` `<S-k>` `<C-d>` `<CR>` `<C-space>` | accept, move, scroll docs, show docs | `set pumkeys=blink` | partial (no docs pane, no doc scroll) |
| mini.move `H J K L` (n), `<C-h/j/k/l>` (x) | move / shift | ok | ok. Shadows hover `K` in Normal on purpose |
| gitsigns `>` `<` `-` `_` (n, x) | hunk nav, stage, reset | ok for n and the single-line x | **missing**: visual-range stage / reset (`-` `_` pass a line range), "Hunk i of n" message |
| gitsigns `<leader>hS hu` | stage buffer, undo | ok | ok |
| gitsigns `<leader>hR hp hd hD hb hq` | reset buffer, preview, diff this, diff vs base, blame, quit diff | not mapped | **missing** (needs core `:diffthis`, `hq` = leave a diff view) |
| gitsigns `ih` (o, x) | select hunk | not mapped | **missing** (text-object registry D7) |
| gitsigns `<leader>tg tw tl tb td ta` | toggle signs, word diff, line highlight, line blame, deleted, all | not mapped | **missing**: m3 has signs toggle only; word diff, line highlight, deleted-line display and inline blame text are not built |
| harpoon `<leader>ha he hp hn`, `1..9` | | ok | `hp` **collides with his own gitsigns `hp`** (preview hunk); gitsigns is buffer-local so it wins in tracked files. Decision in 8 |
| trouble `<leader>xx xX cs cl xL xQ` | | `xx xX xL xQ cs` | partial (`cl` LSP panel missing) |
| mini.picker `<leader>ff` | files | ok | ok |
| mini.picker `<leader>fr` | **resume** last picker | m3 `fr` is **recent files** | **semantic collision**: in the profile `fr` must be resume. Not done today |
| mini.picker `<leader>fg` | live grep, **current buffer only** (`scope = "current"`) | m3 `fg` is project grep | collision of meaning; profile must map `fg` to buffer lines |
| mini.picker `<leader>fb fe fq` | buffers, explorer, quickfix | ok | ok |
| mini.picker `<leader>gf` | modified git files | ok | ok |
| mini.picker `<leader>gh` | hunks of the current file (picker) | not mapped | **missing** (hunk list picker). Collides with default `gh` group |
| mini.picker `<leader>gp` | pick a branch to compare in Diffview | not mapped (m3 `gp` is preview hunk) | **missing**, collides with m3 `gp` |
| mini.picker `<leader>gb gc gC` | branches, remote branches, commit history | ok | ok |
| mini.picker `<leader>gdr` | diff HEAD against a remote branch | not mapped | **missing** (two-pane diff) |
| mini.picker `<leader>dd ds dw` | diagnostics, document symbols, workspace symbols | not mapped | **missing in the profile** (the pickers exist: `Diagnostics`, `Symbols`; workspace symbols to confirm) |
| mini.picker (lua) `gd gr gi gt` | definition, references, implementation, type definition as **pickers** | m3 `gd` jumps, `grr` is a list | partial. His `gr` shadows nvim 0.11 `grr grn gra` (they wait `timeoutlen`); `gt` shadows "next tab". Reproduced only if he asks |
| mini.surround `<leader>sa sd sr` (+ `sf sF sh`) | | `sa sd sr` | partial: find / find_left / highlight missing; `sh` clashes with split |
| mini.files `<leader>e` + `R` refresh, `gs` sort by time | miller columns | tree | **missing** (miller columns planned, D2) |
| mini.bracketed (all defaults, active) | `[b [c [d [f [i [j [l [o [q [t [u [w [x [y` | `b q t h c d` | **partial and colliding**: his `[c` = comment block, `[w` = window, `[t` = treesitter node, `[x` = conflict, `[f` = file. m3's `[c` hunk and `[t` TODO are replaced in the profile by his meanings; targets missing: comment, window, treesitter, file, indent, jump, location, oldfile, undo, yank |
| mini.jump2d (disabled) | | `<Space>j` | n/a |
| mini.colors `<leader>kk` | | not mapped | out |
| aerial (disabled) `<leader>a` | | profile maps `<Space>a` Symbols | **stale**: aerial is `enabled = false`; drop the line unless he asks |
| nvim-notify, neoscroll, nvim-ufo, todo-comments | no keys of their own | ok | ok |
| which-key `<leader>?` | buffer-local maps | `<Space>?` shows all | partial |
| git-conflict `o t 0 b n p` (buffer-local inside a conflict) | | not built | **missing** (plugin `conflict`) |
| neogit `<leader>gg`, fugitive `<leader>gg` | status | `gg` changed files | partial (dashboard planned) |
| diffview `:DiffviewOpen`, `hq` | | | missing (D4) |

### 5.3 What `default` steals from the `nvim` profile (all resolved by "his wins")

| default key | his key | resolution |
|---|---|---|
| `<Space>w` group | `<leader>w` write | profile replaces the tree: `w` is a leaf |
| `<Space>b` group | `<leader>b` buffer manager | leaf |
| `<Space>n` notifications | `<leader>n` new file | his |
| `<Space>s` search group | `sv sh se sc sa sd sf sF sr` splits and surround | his. The pickers on `s` are not available in the profile; their `f`-based legacy keys are |
| `<Space>c` code (`ca`, `cr`, `cf`, `cd`) | `cc ca` AI chat, `cs cl` trouble | `ca` is his AI; code action = `gra`; `cr` `cf` stay if he does not bind them (he does not) |
| `<Space>t` terminal group | `tg tw tl tb td ta` gitsigns toggles | his toggles; terminal by `<C-/>` or `:terminal` |
| `<Space>d` group | `dd ds dw` | **compatible**: same jobs |
| `<Space>gh` hunks group | `<leader>gh` hunk picker (leaf) | his |
| `<Space>gd` diff leaf | `gdd gdr` prefix | his prefix |
| `<Space>gp` push | `gp` Diffview branch pick | his (push stays a command `:Git push`) |
| `<Space>gc` commit (planned) | `gc` remote branches | his |
| `<Space>fg` git files | `fg` buffer grep | his |
| `<Space>fr` recent | `fr` resume | his |
| `<Space>h` harpoon + `hx` | `hS hu hR hp hd hD hb hq` | hunk ops are his; harpoon `ha he hn` remain, `hx` is free, `hp` clashes with his own file (decision in 8) |
| `]w ]e` warning / error, `]t` TODO, `]c` | mini.bracketed `]w` window, `]t` treesitter, `]c` comment | his; default `]e` stays (he has none) |
| `<C-l>` window focus | `<C-l>` visual indent (mini.move) | different mode; no collision. Normal `<C-l>` redraw is lost in both |
| `gh` / `gH` hunk operator | none | free |
| `<C-s>` save | none | free |

Collisions inside his own config, so they are listed rather than solved: `sh` (split vs surround highlight), `hp` (harpoon previous vs
gitsigns preview), `cs` (trouble symbols vs nothing else), `<leader>gp`/`gb`/`gc`/`gC` are defined twice (commented out copies only), `<leader>gh` and gitsigns' `hp...` do not collide.

## 6. Three profiles side by side

| | `minimal` | `default` | `nvim` |
|---|---|---|---|
| purpose | bare vi, nothing the vi spec does not have | batteries included, sane IDE keys | the owner's maps and options |
| leader key | none (`<Space>` is `l`), no leader table, no which-key groups | `<Space>`, tree in section 3 | `<Space>`, his tree only (B1) |
| `g` family | vi only (`gg ge gJ ...` that exist in vi / vim) | + `gd gD gy gI gK gx gh gH gc gco grr gri grt grn gra gO gW` | + his `gd gr gi gt` pickers if enabled |
| `[` `]` | `[[ ]] [] ][ [{ ]} [( ])` and marks | + `b q l d e w h t x r` pairs, `[<Space>` | + mini.bracketed set, `> <` hunk nav, `- _` stage/reset |
| controls | vi only; `<C-w>` windows | `<C-h/j/k/l>` focus, `<C-arrows>` resize, `<C-s>` save, `<C-/>` terminal, `<Esc>` nohl, `<A-hjkl>` move | `H J K L` move, visual `<C-hjkl>`, blink Tab/`<C-j>`/`<C-k>`, `jk` |
| plugins | none | harpoon, move, bracketed, todo, whichkey, notify, statusline, session, finder, git, explorer, lsp, terminal, words, toggles | default's, with his keys over them |
| options | vi defaults | m3 defaults (mouse on, words on, toggles on) | + `tabstop=4 shiftwidth=4 expandtab relativenumber ignorecase smartcase smoothscroll pumkeys=blink lspformat` + formatters |
| `jk` | off | on | on |
| visual `<` `>` | vi | keep selection | keep selection (his has no map; follows default) |
| which-key | none | on | on, his groups |
| select with | `:Profile minimal` | default, nothing to type | `:Profile nvim` |

## 7. What changes for existing users

Everyone who runs 0.20.0 with the default tree has muscle memory for the keys in section 4. The migration must be gentle:

1. **`:Profile legacy`**: a fourth, opt-in table that is exactly today's built-in tree (so the old keys keep working). It is generated from the
   current `defaults()` and kept for two releases, then removed. Shown once in the changelog and in `:Keys`.
2. **A one-time notice** the first time an old key is pressed in a version after the change would be the friendliest. If that is too much code:
   the which-key popup on the old group lists the new home of each key ("moved to `<Space>sg`") for one release (build item B8).
3. **Who is affected** (old to new). Everything is also in the CHANGELOG under "Changed".

| old | new |
|---|---|
| `<Space>w` / `z` / `o` / `n` / `R` | `<C-s>` / `wd` / `wo` / `fn` (notifications on `n`) / `br` |
| `<Space>sv sh se sc` | `wv ws w= wd` (also `<Space>\|` and `<Space>-`) |
| `<Space>sa sd sr` | `ys ds cs` (unchanged) and Visual `S`; `legacy` / `nvim` keep the leader forms |
| `<Space>sn` | `<Esc>` |
| `<Space>bb` / `ba` | `fb` (or `,`) / `bb` |
| `<Space>fg fd fh fc fk fo fm fx fs fl fC ft fw fq` | `sg sb sh sC sk so sm sd ss sp uC st sw sq` (`fg` is now git files) |
| `<Space>gs gr gp gu gl gm gB gt` | `ghs ghr ghp ghu gf ghB ghb uG` |
| `<Space>ll`, `<Space>]]`, `<Space>[[` | `dl` (or `cd`), `]d`, `[d` |
| `<Space>ck ch` | `gK uh` |
| `<Space>t` | `tt` or `<C-/>` |
| `<Space>hd` | `hx` |
| `[c ]c` | `[h ]h` (`[c ]c` are back to the diff-mode builtins) |

`minimal` and the vi keys are not affected by any of this.

## 8. Decisions for the owner

| # | question | recommendation |
|---|---|---|
| K1 | `fg` changes meaning from live grep to git files (LV and AN agree). Accept, or keep `fg` = live grep and move git files to `fG`? | accept the swap; `legacy` and `nvim` keep the old meaning |
| K2 | `<Space>d` is diagnostics (HX, ZD, your own `dd ds dw`) instead of LazyVim's debug. Debug stays `<Space>D`, empty (D1). | accept |
| K3 | In the `nvim` profile, harpoon `hp` (previous) clashes with your own gitsigns `hp` (preview hunk). Move harpoon previous to `hP`? | `hP` in the profile only |
| K4 | Miller columns key. | `<Space>M` (unused by every setup read). Alternatives: `<Space>fm`, replace `e` once the panel exists |
| K5 | `gc` today lists remote branches (yours); the planned git write ops need `commit`. | commit on `gc`, remote branches stay on `gb` with a toggle, in `default` only; `nvim` keeps yours |
| K6 | `[t ]t` TODO shadows the nvim 0.11 tag pair. Keep (LV does) or move to `[T ]T`? | keep |
| K7 | Visual `<` `>` keeping the selection deviates from vi. | accept in `default`, off in `minimal` |
| K8 | Drop the stale `nnoremap <Space>a <Cmd>Symbols<CR>` (aerial is disabled in your spec)? | drop |
| K9 | Should the `nvim` profile also reproduce your `gd gr gi gt` as pickers? `gr` makes `grr grn gra` wait `timeoutlen` and `gt` hides "next tab". | no; keep nvim 0.11's `grr` family and tell him |
| K10 | Save on `<C-s>` in Normal and Visual. Terminals with XOFF flow control need `stty -ixon`; m3 reads raw bytes so it is unaffected. | accept |
| K11 | `bl` keeps "list buffers" although LV and AN bind it to "close left". | keep, no tabline order |
| K12 | Surround `sa sd sr` leader rows disappear from `default` (kept in `nvim` and `legacy`). | accept |

## 9. Build plan for the parity agent

Ordered. Size: S under a day, M a few days, L a milestone. Everything is table-driven in `ui/MED_keymap.m31`, so the tests are the generated
`docs/KEYMAP.md` plus a pty check per profile.

| # | item | size | needs |
|---|---|---|---|
| B1 | **Profile = a tree.** `defaults()` takes a profile id; `minimal` returns no leader rows and no plugin maps; `nvim` returns his tree and drops default rows it collides with; `default` is section 3. `MED_profile.names()` gains `minimal default nvim legacy`. A profile row carries the profile ids it belongs to; `gen_keymap.sh` prints a profile column | M | none |
| B2 | Move existing rows to their new keys (section 4, C1 to C13, C16, C17); fix which-key group labels (3.3); `which-key` shows `gh`, `[`, `]` | S | B1 |
| B3 | `:Profile legacy` generated from today's table; changelog "Changed" section; which-key shows the new home for an old key for one release | S | B1 |
| B4 | Simple ex-backed rows: `<Space>-`, `<Space>\|`, `wm ww wh wj wk wl wx wH wJ wK wL`, `xq xl`, `cl cd`, `sc sB sD sG sj sl sR`, `bD bo` | S | none |
| B5 | Control keys: `<C-h/j/k/l>`, `<C-arrows>`, `<C-s>`, Normal `<Esc>` nohl, Visual `<` `>` keep, `<A-j/k>` in Insert | S | B1 |
| B6 | nvim 0.11 g-keys and the missing bracket entries: `gri grt gO gW gy gI gD gK gx gco gcO`, `[l ]l [L ]L [D ]D [e ]e [w ]w`; remove `[c ]c` hunk binding | S-M | lsp API for `gO` `gW` |
| B7 | `:Toggle NAME` and the `u` group (toggles on by default: words, signs, guides, wrap, numbers, spell, diagnostics, inlay hints, format on save, animate, conceal, background, zen) | M | options exist for most |
| B8 | `words` plugin: `]r [r`, `<A-n> <A-p>`, subtle underline, LSP `documentHighlight` with a word-under-cursor fallback | M | decoration seam |
| B9 | Hunk ops: `]H [H`, `<Space>ghs ghr ghS ghR ghu ghp ghb ghB` and `gh{motion}` / `gH{motion}` (operator that takes a motion and applies to the range) | M | operator hook; `ih ah` need B13 |
| B10 | `terminal` group `tt tf th tv`, `<C-/>` and `<C-_>` (check the byte the terminal sends) | S | terminal plugin |
| B11 | Nvim profile fill-in: `dd ds dw`, `fr` resume, `fg` buffer grep, `gh` hunk picker, `hp hD` etc as the features land; remove the aerial line | S then grows | resume picker, hunk picker |
| B12 | Core `:diffthis`, then `ghd ghD` and `hq` | L | D4 (already planned) |
| B13 | Text-object registry (`ih ah`, `]f [f`, `[i ]i`, mini.ai `an in`) | L | D7 (0.28.0) |
| B14 | LSP installer `cm` (`:Lsp install`) | L | D5 |
| B15 | Miller columns `<Space>M` and the git dashboard `gg` | L | D2, panel API, F3 |
| B16 | `conflict` plugin: `[x ]x`, choose ours / theirs / both / none | M | git plugin |
| B17 | Session restore `qs ql qd`; scratch buffer `<Space>.` | M | session plugin |
| B18 | Docs: regenerate `docs/KEYMAP.md`, update `docs/NVIM-PARITY.md` rows, README keymap section; oracle case for `[c ]c` in diff mode once `:diffthis` exists | S | after each |

First slice that makes sense on its own: B1 + B2 + B3 + B5 (S/M, no new features, only moves keys and makes profiles real), then B4, B6, B7.

## 10. snacks.nvim and mini.nvim, module by module

Two different things are compared. **Default in module** = what the module binds by itself when set up (read in its source under the commit of section 0).
**Bound by LazyVim** = what LazyVim adds (snacks's README key table is the same list LazyVim copies; it is a suggestion, not a module default).
Most snacks modules bind nothing by themselves: keys come from the user. mini.nvim modules bind their defaults on `setup()`.

### 10.1 snacks.nvim

| module | default in module | bound by LazyVim | m3 `default` profile |
|---|---|---|---|
| picker, input window | `<CR>` confirm, `<Esc>` `<C-c>` `q` (normal) cancel, `<C-j> <C-k> <C-n> <C-p> <Down> <Up>` move, `<Tab>` / `<S-Tab>` select and move, `<C-a>` select all, `<C-q>` to quickfix, `<C-s>` split, `<C-v>` vsplit, `<C-t>` tab, `<C-u> <C-d>` scroll list, `<C-b> <C-f>` scroll preview, `<A-p>` preview, `<A-m>` maximize, `<A-h>` hidden, `<A-i>` ignored, `<A-f>` follow, `<A-r>` regex, `<A-w>` cycle window, `<C-g>` live toggle, `<C-w>HJKL` layout, `<C-Down> <C-Up>` history, `/` toggle focus, `?` help, `gg` `G`, `j` `k` (list). `defaults.lua` 222-276 | picker keys in section 3.1 of this doc (`<leader>ff fg fr fb sg sw sd ss ...`, `snacks_picker.lua` 59-166); LV adds `<c-t>` trouble open, `<a-t>` | m3 finder already has `<C-q>` (to quickfix) and `<C-t>` (mark, differs from snacks' tab). **Align**: `<C-s>` split, `<C-v>` vsplit, `<C-j> <C-k>` move, `<A-p>` preview, `<A-h>` hidden, `<A-i>` ignored, `?` help, `<C-a>` select all. m3 `<C-t>` mark should move to `<Tab>` (snacks `<Tab>` = select and next), leaving `<C-t>` for tab |
| picker, list window | same list, `dd` bufdelete in the buffers source (`sources.lua` 35), `<c-x>` bufdelete in input, `<Tab>` git_stage in git_status (452), `<c-r>` git_restore | same | `dd` delete buffer in the buffers picker and `<Tab>` stage in the status picker: add to finder (S) |
| explorer | `l` open, `h` close dir, `<BS>` up, `a` add, `d` delete, `r` rename, `c` copy, `m` move, `y` / `p` yank / paste, `o` system open, `.` focus, `I` `H` toggle ignored / hidden, `Z` close all, `P` preview, `u` refresh, `]g [g` git next / prev, `]d [d`, `]w [w`, `]e [e` diagnostics (`sources.lua` 80-107) | `<leader>e` (root), `<leader>E` (cwd), via `<leader>fe` `fE` (`snacks_explorer.lua` 21-22) | `<Space>e` / `E` as in LV. The in-explorer keys follow the same letters (they are also oil/neo-tree/NvChad habits); the explorer's `]d [d ]w [w ]e [e` match the buffer brackets of section 3.2 |
| lazygit | none (README: `Snacks.lazygit()`) | `<leader>gg` root, `<leader>gG` cwd (keymaps.lua 169-170) | `gg` is the git dashboard (planned); `gG` = dashboard of cwd |
| terminal | window keys `q` hide, `gf` open file (`terminal.lua` 38-41, 298) | `<c-/>` and `<c-_>` toggle (n, t), `<leader>ft` root, `<leader>fT` cwd (keymaps.lua 193-196) | `<C-/>` `<C-_>`; `tt` (AN `t` group); no `ft` (f = files) |
| words | none (`Snacks.words.jump`) | `]]` `[[` `<a-n>` `<a-p>` (lsp/init.lua 94-99); AN uses `]r [r` (snacks.lua 242-243) | `]r [r`, `<A-n> <A-p>`; `]]` `[[` stay vi sections (section 4, C18). On by default (D3) |
| zen | window `keys = { q = false }` (`zen.lua` 59) | `<leader>uz` zen, `<leader>uZ` zoom (keymaps.lua 202-203); SN README `<leader>z` | `uz`, `wm` (zoom). Not `<Space>z` (owner's close window) |
| scratch | picker `<CR>` opens (`scratch.lua` 62-66) | `<leader>.` toggle, `<leader>S` select (util.lua 34-35) | `<Space>.` toggle; `S` select not added (S = reserved) |
| toggle | none; `Toggle:map(keys)` | all `u*` in section 3.1 (keymaps.lua 145-164) | `u` group via core `:Toggle` (B7) |
| notifier | history window `q` close (`notifier.lua` 105) | `<leader>n` history, `<leader>un` dismiss (ui.lua 286, 293) | `<Space>n`, `un` |
| bufdelete | none | `<leader>bd` (SN README 292) | `bd` (exists) |
| gitbrowse | none | `<leader>gB` n,x; `<leader>gY` copy link (keymaps.lua 177-178) | `gB` open on web |
| rename | none | `<leader>cR` (lsp/init.lua) | `cR` |
| scope (indent) | `ii` `ai` text objects, `[i` `]i` jumps (`scope.lua` 60-100) | LV does not change it | needs text-object registry (D7); same letters as mini.indentscope (`ii ai [i ]i`, so two projects agree) |
| gh (GitHub issues / PR pickers) | picker keys | `<leader>gi gI gp gP` (snacks_picker.lua 79-82) | not planned (no GitHub client); letters stay free |
| dashboard | `f` `n` ... buttons | LV `alpha`/dashboard extras | out |
| dim, scroll, animate, indent, profiler | toggles only | `uD ua ug uS dpp dph` | `ua` (animate), `ug` (guides) |

What this changes in the doc above: nothing about the leader tree (LV/snacks agree with it), but three finder details: `<Tab>` marks and `<C-t>` opens in a tab; `<C-v>`/`<C-s>`
split from the picker; `dd` and `<Tab>` per source. They go into build item B19.

### 10.2 mini.nvim

Defaults are the `config.mappings` of each module (source in section 0). "LV" is the key LazyVim uses for the same job, if it ships it.

| module | default in module | bound by LazyVim | m3 `default` profile |
|---|---|---|---|
| mini.bracketed | `[b ]b`, `[c ]c` comment, `[d ]d`, `[f ]f` file, `[i ]i` indent, `[j ]j` jump, `[l ]l` location, `[m ]m` multicursor, `[o ]o` oldfile, `[q ]q`, `[t ]t` treesitter, `[u ]u` undo, `[w ]w` window, `[x ]x` conflict, `[y ]y` yank; capitals first / last | not shipped as is: LV defines its own `[b ]b [q ]q [d ]d [e ]e [w ]w [t ]t` | b q d agree; `x` agrees; `w` = warning (LV AN) vs window (MI): warning; `c` kept for diff mode; `t` = TODO (LV) vs treesitter (MI). Owner has mini.bracketed active: his meanings win in `nvim` |
| mini.surround | `sa sd sf sF sh sr` (+ `n` / `l` suffixes) | `gsa gsd gsf gsF gsh gsr gsn` (extras/coding/mini-surround.lua 10-17, `gs` to keep `s`) | not leader-based: `ys ds cs S` (vim-surround). Both MI and LV defaults take `s` or `gs`, which are vi keys (`gs` = sleep in m3). Reject |
| mini.ai | `a` `i` + `n` `l` (`an in al il`), `g[` `g]` | LV ships mini.ai with its own `o f c t d e u U` objects (coding.lua) | needs registry (D7); `an in al il` and `g[ g]` are free letters |
| mini.operators | `g=` evaluate, `gx` exchange, `gm` multiply, `gr` replace, `gs` sort | not shipped | reject: `gx` is nvim's open URL, `gr` is the LSP prefix, `gs` is sleep, `gm` is vi's. If wanted later: `g=` only |
| mini.comment | `gc` `gcc` `gc` (visual), `gc` object | nvim 0.11 builtin; LV adds `gco gcO` | yes (`comment` plugin), `gco gcO` to add |
| mini.diff | `gh` apply, `gH` reset, `gh` object, `[H [h ]h ]H` | LV uses gitsigns (`]h [h ]H [H` and `<leader>gh*`) with the same bracket letters; extras/editor/mini-diff.lua exists | **yes: `gh gH ih ah [h ]h [H ]H`** |
| mini.files | `l` in, `L` in+, `h` out, `H` out+, `q` close, `'` `m` marks, `<BS>` reset, `@` cwd, `g?` help, `=` synchronize, `<` `>` trim | `<leader>fm` `fM` (extras/editor/mini-files.lua) | miller columns (planned): adopt `h l H L q g? = @ <BS>` inside the panel; entry key `<Space>M` (K4) |
| mini.pick | `<CR>` choose, `<C-s>` split, `<C-v>` vsplit, `<C-t>` tab, `<M-CR>` choose marked, `<C-x>` mark, `<C-a>` mark all, `<C-n> <C-p>` move, `<C-f> <C-b>` scroll, `<C-g>` move start, `<C-Space>` refine, `<S-Tab>` info, `<Esc>` stop | not used (snacks or telescope) | the finder keys of 10.1 are a superset; add `<C-n> <C-p>` (exist) and `<C-x>` mark as an alias of `<Tab>` |
| mini.clue | triggers are chosen by the user; clues for `g z [ ] <C-w> " '` and registers via `gen_clues` | LV uses which-key | which-key (core) already shows the same prefixes (`g z [ ] <C-w>` and registers) |
| mini.jump2d | `<CR>` start jumping | not shipped (flash) | `<Space>j` (exists); not `<CR>` (vi: next line) |
| mini.jump | `f F t T ;` with labels | not shipped | vi `f t ; ,` stay vi |
| mini.move | `<M-h> <M-j> <M-k> <M-l>` (n, x) | LV `<A-j> <A-k>` (n, i, v) and extras mini-move | **m3 `move` = MI defaults already.** The owner's `H J K L` and Visual `<C-hjkl>` are overrides of the module's defaults |
| mini.splitjoin | `gS` toggle | not shipped | optional, `gS` is free in vi (not a vim key) |
| mini.align | `ga` start, `gA` preview | not shipped | reject for now: `ga` is vi's "ascii of character" (m3 has it) |
| mini.indentscope | `ii` `ai` objects, `[i` `]i` | not shipped (snacks indent/scope) | registry (D7) |
| mini.basics | `j` `k` by screen line, `go` `gO` blank lines, `gy` `gp` clipboard, `gV`, `g/` visual search, `<C-c>` stop and redraw, **`<C-s>` save (n, x, i)**; opt-in: `windows` = **`<C-h/j/k/l>` focus and `<C-arrows>` resize**, `move_with_alt`; option toggles on `\` + `b c C d h i l n r s w` (basics.lua 199-262, 334-346) | not shipped (LV defines the same in keymaps.lua) | **agrees** with `<C-s>`, `<C-hjkl>`, `<C-arrows>` of section 3.2 (now MI, LV, AN, NC, KS, LU). Not adopted: `gO` (nvim 0.11 doc symbols), `gy` / `gp` (vi `gp` put), `\` toggles (m3 leader tree has `u`) |
| mini.completion | `<C-Space>` force two-step, `<A-Space>` fallback, `<C-f> <C-b>` scroll | blink.cmp | m3 lsp: `<C-Space>` (same), `<C-y>` accept |
| mini.snippets | `<C-j>` expand, `<C-l>` / `<C-h>` jump, `<C-c>` stop | LuaSnip / native | m3: `<Tab>` / `<S-Tab>` (nvim 0.11), keep |
| mini.extra / visits / starter / sessions | pickers, `<leader>`-less | not shipped | `visits` ~ frecency (exists) |

Summary of what mini and snacks add to the default: the picker in-key list (B19), `<C-s>`/`<C-hjkl>` (confirmed by a sixth setup), `gh gH [h ]h [H ]H` (mini.diff
exact), `ii ai [i ]i` (both mini.indentscope and snacks.scope), `]r [r` (words). It confirms the rejection of `sa sd sr` and `g=/gx/gr/gs/gm` operators.

## 11. His keys: kept, changed, or worth changing

The owner's keys win in the `nvim` profile and none is dropped there. Column "decision": **kept** = `default` uses the same key; **changed in default** = `default`
uses another key (evidence given), the `nvim` profile keeps his; **suggest changing his** = the other convention is clearly better and he could switch (his call).
"LV" etc. as in section 0.

| his key | job | decision | evidence / reason |
|---|---|---|---|
| `jk` (i) | leave Insert | kept | AN better-escape; option, off in `minimal` |
| `<leader>n` | new file | changed in default (`fn`, `n` = notifications) | LV keymaps.lua 98, ui.lua 286; SN README. Suggest changing his: low value, ignore |
| `<leader>ll` | diagnostic float | changed in default (`cd`, `dl`) | LV keymaps.lua 134 `cd`; AN `ld`, `gl`. Suggest: `cd` |
| `<leader>]]` `[[` | next / prev diagnostic | changed in default (`]d [d`) | nvim 0.11 already binds `]d [d`; three-key forms are redundant. **Suggest changing his**: drop them |
| `<leader>sv sh se sc` | splits | changed in default (`wv ws w= wd`, `<Space>\|`, `<Space>-`) | LV w group + `-` `\|` (keymaps.lua 199-201), HX window mode, ZD `space w`. His `sh` clashes with his surround `sh`. **Suggest**: `<leader>-` `<leader>\|` |
| `<leader>ps` `ms` | Lazy / Mason | out (installer on `cm`) | LV `cm` (lsp/init.lua 285), AN `pm`. Suggest: `cm` |
| `<leader>cc` `ca` | CodeCompanion chat / actions | changed in default (`ca` = code action) | LV `ca`, AN `la`, HX `space a`, nvim 0.11 `gra`. `ca` taken by AI hides code action. **Suggest changing his**: put AI under its own letter (`<leader>a` is free in his spec: aerial is disabled) |
| `<leader>b` | buffer manager | changed in default (`b` group) | LV, AN, LU all use `b` as a group; a leaf blocks `bb bd bo`. Suggest: `<leader>bm` or `<leader>,` |
| `<leader>gn` `gr` | new / rename branch | not in default (planned git write ops use the dashboard) | `gr` is also the AN/LV reset-hunk family in other setups; keep his in `nvim` |
| `<leader>gdd` `gt` | Diffview whole / current file | changed in default (`gd` diff, `ghd` diff this) | LV snacks_picker.lua 75-76, editor.lua 184. His `gt` and `hd` do the same job twice. **Suggest**: drop `gt`, use `hd` |
| `<leader>z` `o` | close, only | changed in default (`wd`, `wo`) | LV `wd`, HX `q` `o`. Suggest: keep, but add `<leader>wd` |
| `<leader>w` | write | changed in default (`<C-s>`) | LV, AN, NC, MI basics: `<C-s>` works in every mode. **Suggest adding** `<C-s>`, keeping `<leader>w` |
| `<leader>R` | reload all buffers | changed in default (`br` current, `cR` rename file) | AN `R` rename file, LV `cR`. Keep his in `nvim` |
| `<C-\><C-]>` (t) | leave terminal input | kept in `nvim` | default uses `<C-\><C-n>` (nvim builtin) and `<C-/>` to toggle. KS `<Esc><Esc>`, NC `<C-x>` |
| blink `<Tab>` `<C-j>` `<C-k>` `<S-j>` `<S-k>` `<C-d>` | completion | nvim only (`pumkeys=blink`) | default: `<C-n> <C-p> <C-y>` (vi / vim). `<S-j>` / `<S-k>` in Insert are fine; kept |
| mini.move `H J K L` (n) | move line | changed in default (`<A-j>` ...) | **suggest changing his.** `J` joins lines, `K` is hover/keywordprg, `H` `L` are screen top / bottom; mini.move's own defaults are Alt keys (`move.lua` mappings) and LV uses `<A-j/k>` |
| mini.move `<C-h/j/k/l>` (x) | move selection | changed in default (`<A-hjkl>` n and x) | MI defaults are Alt; normal `<C-hjkl>` is window focus in all five other setups. Suggest: `<A-hjkl>` |
| gitsigns `>` `<` | next / prev hunk | changed in default (`]h [h`) | **suggest changing his.** `>` `<` are the indent operators: mapping them in Normal kills `>>`, `>ip`, `<<` (this is why `minimal` keeps them). LV editor.lua 160-169, MI diff `]h [h`, owner decision |
| gitsigns `-` `_` (n, x) | stage / reset hunk | changed in default (`ghs ghr`, and `gh{motion}`) | `-` and `_` are vi motions. LV editor.lua 176-177, MI `gh gH`. **Suggest**: `ghs ghr` |
| gitsigns `<leader>hS hu hR hp hd hD hb` | buffer / undo / reset buffer / preview / diff / diff base / blame | changed in default (`ghS ghu ghR ghp ghd ghD ghb`) | LV editor.lua 178-185 (`gh`), KS uses `h` (init.lua 383-396). `h` collides with his harpoon `h`. **Suggest**: move to `gh` |
| gitsigns `<leader>hq` | quit diff view | no default key | KS `hq` is the hunk quickfix list; his meaning has no precedent. Keep in `nvim` (needs `:diffthis`) |
| gitsigns `<leader>tg tw tl tb td ta` | toggles | changed in default (`uG uW uB`, others as `u*`) | LV `uG`, AN `u`; KS binds `tb tw` on `t` (init.lua 398-399), so `t` is not unreasonable. Majority `u` (LV, AN). **Suggest**: optional |
| gitsigns `ih` | hunk object | kept | KS init.lua 401 `ih`; AN `ig`; MI `gh`. Default has `ih` and `ah` |
| harpoon `<leader>ha he hn hp 1..9` | | kept (`hd` remove becomes `hx`) | `hp` clashes with his own gitsigns `hp` (K3) |
| mini.picker `<leader>ff` | files | kept | LV, AN, NC, KS-ish |
| mini.picker `<leader>fr` | **resume** | changed in default (`fr` recent, `sR` resume) | LV `fr` = recent (snacks_picker.lua 71), `sR` resume (107), KS `sr`, HX `'`. **Suggest**: resume on `<leader>sR` or `'` |
| mini.picker `<leader>fg` | live grep **current buffer** | changed in default (`sb` lines, `fg` git files) | LV `fg` git files, `sb` buffer lines (84), AN `fg`. **Suggest**: `sb` |
| mini.picker `<leader>fb fe fq` | buffers, explorer, quickfix | kept | LV `fb`, `fe`; `fq` kept in m3, `sq` is the LV spelling |
| mini.picker `<leader>gf` | modified git files | changed in default (`gf` = history of this file) | LV `gf` file history (keymaps.lua 175). **Suggest**: `gs` status picker (LV snacks_picker.lua 77) |
| mini.picker `<leader>gh` | hunks of this file (picker) | changed in default (`gh` group) | LV `gd` = diff hunks picker. **Suggest**: `<leader>gd` or `ghl` |
| mini.picker `<leader>gp` `gdr` | compare against a branch / remote | no default key | no precedent in the setups read; `gD` is diff vs origin (LV 76). Suggest: `gD` |
| mini.picker `<leader>gb gc gC` | branches, remote branches, commits | `gb` kept; `gc` changed (commit planned); `gC` changed (`gl`) | AN `gb gc gC`, LU `gb gc gC` (which-key.lua 187-210) both use these letters for branch / commit. **Both views are valid: keep his in `nvim`** |
| mini.picker `<leader>dd ds dw` | diagnostics, doc symbols, ws symbols | `dd` kept; `ds dw` changed (`ss sS`) | HX `d` `D`, `s` `S`; LV `sd ss sS`; nvim 0.11 `gO`. **Suggest**: `gO`, `gW` for symbols |
| mini.picker `gd` | definition picker | kept (jump) | LV, AN, HX, ZD, KS all `gd` |
| mini.picker `gr` | references picker | changed in default (`grr`) | **suggest changing his**: `gr` is a prefix of nvim 0.11 `grr grn gra gri grt gO` so those wait `timeoutlen`; LV has the same trade (nowait) but KS keeps `grr`; `gr{char}` is vi. Use `grr` |
| mini.picker `gi` | implementation picker | changed in default (`gri`, `gI`) | **suggest changing his**: `gi` is vi "insert where Insert stopped" (nvim `index.txt`, kept by `minimal`). LV, AN, ZD use `gI` |
| mini.picker `gt` | type definition picker | changed in default (`grt`, `gy`) | **suggest changing his**: `gt` is "next tab page" in vi/vim. LV, AN, HX, ZD use `gy` |
| mini.surround `<leader>sa sd sf sF sh sr` | surround | changed in default (`ys ds cs S`) | MI defaults are `sa sd ...` without a leader, LV uses `gs*`; vim-surround keys are already in m3. His leader form is fine in `nvim`; `sh` collides with his split |
| mini.files `<leader>e`, `R`, `gs` | explorer | kept (`e`); panel keys follow mini.files (10.2) | His `R` and `gs` are his additions; `R` is not a mini.files default (default is `=` synchronize) |
| mini.bracketed (all) | | `b q d` kept; `w` `t` `c` changed in default | LV/AN: `]w` warning, `]t` TODO; MI: window, treesitter. Both valid; `nvim` has the MI set |
| trouble `<leader>xx xX xL xQ cs` | | kept | LV editor.lua 217-222, same keys |
| trouble `<leader>cl` | LSP panel | changed in default (`cl` = LSP info) | LV: `cl` is Lsp Info (lsp/init.lua), `cS` is Trouble lsp (editor.lua 220). **Suggest**: `cS` |
| which-key `<leader>?` | buffer-local keys | kept | LV editor.lua 106 |
| git-conflict `o t 0 b n p` | choose ours / theirs / none / both / next / prev (in a conflict) | kept in `nvim` | default uses `[x ]x` (MI); buffer-local, no collision |
| neogit / fugitive `<leader>gg` | git status | kept | LV, AN, LU `gg` = lazygit / git UI |
| `<leader>kk` | colour tweak | out | LV `uC` colorschemes |
| neoscroll keys | animated scroll | kept (core) | |
| `<leader>a` (aerial, disabled) | outline | not kept | disabled in his spec; drop |

Rows can be both "changed in default" and "suggest changing his". Where there is no strong evidence the row says so and his key stays.
The strongest cases, which shadow a vi key or a nvim 0.11 default: `>` `<` (indent operators), `-` `_` (motions), `H J K L` (screen / join / hover), `gi` (insert), `gt` (next tab), `gr` (LSP prefix and virtual replace).

## 12. Addendum build items

| # | item | size |
|---|---|---|
| B19 | finder in-picker keys aligned with snacks / mini.pick: `<Tab>` mark and next (move `<C-t>` mark to it, `<C-t>` open in tab), `<C-s>` `<C-v>` split, `dd` delete buffer in the buffers source, `<Tab>` stage in the status source | S |
| B20 | explorer panel keys (`a d r c m y p o . I H Z P u ]g [g ]d [d`) as in snacks / neo-tree, and the miller panel keys of mini.files (`h l H L q g? = @ <BS>`) | M |
| B21 | in `nvim`: `fr` resume, `fg` buffer lines, `gh` hunk picker, `dd ds dw`, `gdr gp`, `<leader>t*` toggles (as features land) | S then grows |
