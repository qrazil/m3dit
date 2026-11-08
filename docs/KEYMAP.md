# Keymap

Generated from `ui/MED_keymap.m31` by `scripts/gen_keymap.sh`; do not edit by hand.
The in-editor listing (`<Space>?`, `:Keys`) is built from the same table.

Source column: `vim` is a Vim / Neovim default that the engine is checked against (nvim parity),
`config` mirrors the owner's Neovim config, `m3` is specific to this editor.
A plugin can be switched off with `:PluginDisable NAME`; its rows then disappear everywhere.
Your own maps (the keymap file, `:map`) are tried before these rows and may use `<Cmd>` (an ex line that runs
without leaving the mode) and `<buffer>` (this buffer only). A plugin compiled into the build adds its rows
through the extension API (`MapSpec`, docs/EXTENSIONS.md) and its keys run their command with `<Cmd>`.

## Profiles

A profile is a whole key tree (`:Profile NAME`, `--profile NAME`, or the line `Profile NAME` first in the keymap file); choosing one
replaces the leader tree and the plugins' keys, it does not add to them.

| profile | what it is |
|---|---|
| `default` | batteries included, sane IDE keys (docs/KEYMAP-REVIEW.md); what a normal build starts in |
| `minimal` | bare vi: no leader tree, no plugin keys, `<Space>` moves right; what a `--no-plugins` build starts in |
| `nvim` | the owner's Neovim keys: the `legacy` tree plus his own maps and options (`engine/MED_profile.m31`) |
| `legacy` | the tree of m3 0.21.0 and before, for people who want their old keys back |

## Leader (`<Space>`), `default` profile

| keys | mode | action | plugin | source |
|---|---|---|---|---|
| `<Space>?` | Normal | All keys | core | m3 |
| `<Space>-` | Normal | Split below | core | m3 |
| `<Space>\|` | Normal | Split right | core | m3 |
| `<Space>j` | Normal | Jump to a label | jump | m3 |
| `<Space>e` | Normal | File tree (the current file revealed) | explorer | m3 |
| `<Space>n` | Normal | Notification history | notify | m3 |
| `<Space>f` | Normal | +files | finder | m3 |
| `<Space>ff` | Normal | Find files | finder | m3 |
| `<Space>fr` | Normal | Recent files | finder | m3 |
| `<Space>fb` | Normal | Buffers | finder | m3 |
| `<Space>fg` | Normal | Live grep (this buffer) | finder | m3 |
| `<Space>fe` | Normal | File explorer (picker) | finder | m3 |
| `<Space>fn` | Normal | New file | core | m3 |
| `<Space>s` | Normal | +search | finder | m3 |
| `<Space>sg` | Normal | Live grep (project) | finder | m3 |
| `<Space>sw` | Normal | Grep the word under the cursor | finder | m3 |
| `<Space>so` | Normal | Options | finder | m3 |
| `<Space>sm` | Normal | Marks | finder | m3 |
| `<Space>ss` | Normal | Symbols in this file | finder | m3 |
| `<Space>sq` | Normal | Generic list | finder | m3 |
| `<Space>sC` | Normal | Commands | finder | m3 |
| `<Space>sp` | Normal | Plugins | finder | m3 |
| `<Space>sn` | Normal | Clear search highlight | core | m3 |
| `<Space>b` | Normal | +buffers | core | m3 |
| `<Space>bb` | Normal | Alternate buffer | core | m3 |
| `<Space>bd` | Normal | Delete buffer | core | m3 |
| `<Space>br` | Normal | Reload the file from disk | core | m3 |
| `<Space>w` | Normal | +windows | core | m3 |
| `<Space>wd` | Normal | Close window | core | m3 |
| `<Space>wo` | Normal | Only this window | core | m3 |
| `<Space>w=` | Normal | Equalize windows | core | m3 |
| `<Space>g` | Normal | +git | finder | m3 |
| `<Space>gg` | Normal | Changed files | finder | m3 |
| `<Space>gb` | Normal | Branches (checkout) | finder | m3 |
| `<Space>gl` | Normal | Commit log | finder | m3 |
| `<Space>gn` | Normal | New branch (type the name) | finder | m3 |
| `<Space>gR` | Normal | Rename the branch (type the name) | finder | m3 |
| `<Space>c` | Normal | +code | lsp | m3 |
| `<Space>cr` | Normal | Rename symbol | lsp | m3 |
| `<Space>ca` | Normal | Code action | lsp | m3 |
| `<Space>cf` | Normal | Format buffer | lsp | m3 |
| `<Space>cd` | Normal | Show diagnostics at the cursor | lsp | m3 |
| `<Space>D` | Normal | +diagnostics | lsp | m3 |
| `<Space>Dd` | Normal | Diagnostics (workspace) | lsp | m3 |
| `<Space>Db` | Normal | Diagnostics of this buffer | lsp | m3 |
| `<Space>t` | Normal | Terminal | terminal | m3 |
| `<Space>u` | Normal | +ui toggles | core | m3 |
| `<Space>uh` | Normal | Toggle inlay hints | lsp | m3 |
| `<Space>uC` | Normal | Colour schemes (themes) | finder | m3 |
| `<Space>q` | Normal | +quit | core | m3 |
| `<Space>qq` | Normal | Quit | core | m3 |
| `<Space>qa` | Normal | Quit all | core | m3 |
| `<Space>h` | Normal | +harpoon | harpoon | m3 |
| `<Space>gh` | Normal | +hunks | git | m3 |
| `<Space>ha` | Normal | Harpoon: add this file | harpoon | m3 |
| `<Space>he` | Normal | Harpoon: menu | harpoon | m3 |
| `<Space>hn` | Normal | Harpoon: next | harpoon | m3 |
| `<Space>hp` | Normal | Harpoon: previous | harpoon | m3 |
| `<Space>hx` | Normal | Harpoon: remove this file | harpoon | m3 |
| `<Space>1` | Normal | Harpoon: file 1 | harpoon | m3 |
| `<Space>2` | Normal | Harpoon: file 2 | harpoon | m3 |
| `<Space>3` | Normal | Harpoon: file 3 | harpoon | m3 |
| `<Space>4` | Normal | Harpoon: file 4 | harpoon | m3 |
| `<Space>5` | Normal | Harpoon: file 5 | harpoon | m3 |
| `<Space>6` | Normal | Harpoon: file 6 | harpoon | m3 |
| `<Space>7` | Normal | Harpoon: file 7 | harpoon | m3 |
| `<Space>8` | Normal | Harpoon: file 8 | harpoon | m3 |
| `<Space>9` | Normal | Harpoon: file 9 | harpoon | m3 |
| `<Space>st` | Normal | TODO comments | todo | m3 |
| `<Space>ghs` | Normal | Stage hunk | git | m3 |
| `<Space>ghr` | Normal | Reset hunk | git | m3 |
| `<Space>ghp` | Normal | Preview hunk | git | m3 |
| `<Space>ghu` | Normal | Unstage hunk | git | m3 |
| `<Space>ghb` | Normal | Blame line | git | m3 |
| `<Space>ghB` | Normal | Git blame list (buffer) | git | m3 |
| `<Space>gL` | Normal | Log of this file | git | m3 |
| `<Space>gd` | Normal | Diff, working tree | git | m3 |
| `<Space>uG` | Normal | Toggle git signs | git | m3 |
| `<Space>gc` | Normal | Commit (type the message) | git | m3 |
| `<Space>gp` | Normal | Pull | git | m3 |
| `<Space>gP` | Normal | Push | git | m3 |

## Other keys of the default plugins, `default` profile (from their `MapSpec`s)

| keys | mode | action | plugin | source |
|---|---|---|---|---|
| `<M-j>` | Normal | move the line down | move | m3 |
| `<M-j>` | Visual | move the selection down | move | m3 |
| `<M-k>` | Normal | move the line up | move | m3 |
| `<M-k>` | Visual | move the selection up | move | m3 |
| `<M-h>` | Normal | shift the line left | move | m3 |
| `<M-h>` | Visual | shift the selection left | move | m3 |
| `<M-l>` | Normal | shift the line right | move | m3 |
| `<M-l>` | Visual | shift the selection right | move | m3 |
| `[b` | Normal | previous buffer | bracketed | m3 |
| `]b` | Normal | next buffer | bracketed | m3 |
| `[B` | Normal | first buffer | bracketed | m3 |
| `]B` | Normal | last buffer | bracketed | m3 |
| `[l` | Normal | previous list entry | bracketed | m3 |
| `]l` | Normal | next list entry | bracketed | m3 |
| `[L` | Normal | first list entry | bracketed | m3 |
| `]L` | Normal | last list entry | bracketed | m3 |
| `[t` | Normal | previous TODO comment | bracketed | m3 |
| `]t` | Normal | next TODO comment | bracketed | m3 |
| `[h` | Normal | previous git hunk | bracketed | m3 |
| `]h` | Normal | next git hunk | bracketed | m3 |
| `[H` | Normal | first git hunk | bracketed | m3 |
| `]H` | Normal | last git hunk | bracketed | m3 |
| `[d` | Normal | previous diagnostic | bracketed | m3 |
| `]d` | Normal | next diagnostic | bracketed | m3 |

## Leader (`<Space>`), `nvim` and `legacy` profiles

| keys | mode | action | plugin | source |
|---|---|---|---|---|
| `<Space>w` | Normal | Write file | core | config |
| `<Space>z` | Normal | Close window | core | config |
| `<Space>o` | Normal | Only this window | core | config |
| `<Space>n` | Normal | New buffer | core | config |
| `<Space>R` | Normal | Reload the file from disk | core | config |
| `<Space>s` | Normal | +split/surround | core | config |
| `<Space>sv` | Normal | Split right | core | config |
| `<Space>sh` | Normal | Split below | core | config |
| `<Space>se` | Normal | Equalize windows | core | config |
| `<Space>sc` | Normal | Close window | core | config |
| `<Space>sn` | Normal | Clear search highlight | core | m3 |
| `<Space>sa` | Normal | Surround add (ys{motion}{char}) | surround | config |
| `<Space>sa` | Visual | Surround selection (S{char}) | surround | config |
| `<Space>sd` | Normal | Surround delete (ds{char}) | surround | config |
| `<Space>sr` | Normal | Surround replace (cs{old}{new}) | surround | config |
| `<Space>q` | Normal | +quit | core | m3 |
| `<Space>qq` | Normal | Quit | core | m3 |
| `<Space>qa` | Normal | Quit all | core | m3 |
| `<Space>b` | Normal | +buffer | core | m3 |
| `<Space>bb` | Normal | Switch buffer | finder | m3 |
| `<Space>bn` | Normal | Next buffer | core | m3 |
| `<Space>bp` | Normal | Previous buffer | core | m3 |
| `<Space>ba` | Normal | Alternate buffer | core | m3 |
| `<Space>bd` | Normal | Delete buffer | core | m3 |
| `<Space>bl` | Normal | List buffers | core | m3 |
| `<Space>e` | Normal | File tree | explorer | config |
| `<Space>E` | Normal | Reveal file in the tree | explorer | m3 |
| `<Space>f` | Normal | +find | finder | config |
| `<Space>ff` | Normal | Find files | finder | config |
| `<Space>fg` | Normal | Live grep | finder | config |
| `<Space>fr` | Normal | Recent files | finder | config |
| `<Space>fb` | Normal | Buffers | finder | config |
| `<Space>fe` | Normal | File explorer (picker) | finder | config |
| `<Space>fq` | Normal | Generic list | finder | config |
| `<Space>fd` | Normal | Lines of this buffer | finder | config |
| `<Space>fw` | Normal | Grep the word under the cursor | finder | m3 |
| `<Space>fh` | Normal | Help: all keys | finder | m3 |
| `<Space>fc` | Normal | Commands | finder | m3 |
| `<Space>fo` | Normal | Options | finder | m3 |
| `<Space>fm` | Normal | Marks | finder | m3 |
| `<Space>fx` | Normal | Diagnostics | finder | m3 |
| `<Space>fs` | Normal | Symbols in this file | finder | m3 |
| `<Space>fl` | Normal | Plugins | finder | m3 |
| `<Space>fC` | Normal | Colour schemes (themes) | finder | m3 |
| `<Space><Space>` | Normal | Find files | finder | m3 |
| `<Space>,` | Normal | Switch buffer | finder | m3 |
| `<Space>/` | Normal | Live grep | finder | m3 |
| `<Space>:` | Normal | Commands | finder | m3 |
| `<Space>?` | Normal | All keys | core | m3 |
| `<Space>j` | Normal | Jump to a label | jump | m3 |
| `<Space>g` | Normal | +git | finder | config |
| `<Space>gg` | Normal | Changed files (status) | finder | config |
| `<Space>gf` | Normal | Changed files | finder | config |
| `<Space>gb` | Normal | Branches (checkout) | finder | config |
| `<Space>gc` | Normal | Remote branches (checkout as local) | finder | config |
| `<Space>gC` | Normal | Commit history | finder | config |
| `<Space>l` | Normal | +diagnostics | lsp | config |
| `<Space>ll` | Normal | Show diagnostics at the cursor | lsp | config |
| `<Space>]]` | Normal | Next diagnostic | lsp | config |
| `<Space>[[` | Normal | Previous diagnostic | lsp | config |
| `<Space>x` | Normal | +trouble | lsp | config |
| `<Space>xx` | Normal | Diagnostics | lsp | config |
| `<Space>xX` | Normal | Diagnostics of this buffer | lsp | config |
| `<Space>xQ` | Normal | Generic list | finder | config |
| `<Space>xL` | Normal | Generic list | finder | config |
| `<Space>cs` | Normal | Symbols | finder | config |
| `<Space>c` | Normal | +code | lsp | m3 |
| `<Space>cr` | Normal | Rename symbol | lsp | m3 |
| `<Space>ca` | Normal | Code action | lsp | m3 |
| `<Space>cf` | Normal | Format buffer | lsp | m3 |
| `<Space>ck` | Normal | Signature help | lsp | m3 |
| `<Space>ch` | Normal | Toggle inlay hints | lsp | m3 |
| `<Space>t` | Normal | Terminal | terminal | config |
| `<Space>h` | Normal | +harpoon | harpoon | m3 |
| `<Space>ha` | Normal | Harpoon: add this file | harpoon | m3 |
| `<Space>he` | Normal | Harpoon: menu | harpoon | m3 |
| `<Space>hn` | Normal | Harpoon: next | harpoon | m3 |
| `<Space>hp` | Normal | Harpoon: previous | harpoon | m3 |
| `<Space>hd` | Normal | Harpoon: remove this file | harpoon | m3 |
| `<Space>1` | Normal | Harpoon: file 1 | harpoon | m3 |
| `<Space>2` | Normal | Harpoon: file 2 | harpoon | m3 |
| `<Space>3` | Normal | Harpoon: file 3 | harpoon | m3 |
| `<Space>4` | Normal | Harpoon: file 4 | harpoon | m3 |
| `<Space>5` | Normal | Harpoon: file 5 | harpoon | m3 |
| `<Space>6` | Normal | Harpoon: file 6 | harpoon | m3 |
| `<Space>7` | Normal | Harpoon: file 7 | harpoon | m3 |
| `<Space>8` | Normal | Harpoon: file 8 | harpoon | m3 |
| `<Space>9` | Normal | Harpoon: file 9 | harpoon | m3 |
| `<Space>ft` | Normal | TODO comments | todo | m3 |
| `<Space>gs` | Normal | Stage hunk | git | m3 |
| `<Space>gr` | Normal | Reset hunk | git | m3 |
| `<Space>gp` | Normal | Preview hunk | git | m3 |
| `<Space>gu` | Normal | Unstage hunk | git | m3 |
| `<Space>gl` | Normal | Git log of this file | git | m3 |
| `<Space>gd` | Normal | Git diff (working tree) | git | m3 |
| `<Space>gm` | Normal | Git blame list | git | m3 |
| `<Space>gB` | Normal | Blame line | git | m3 |
| `<Space>gt` | Normal | Toggle git signs | git | m3 |

## Other keys of the default plugins, `nvim` and `legacy` profiles

| keys | mode | action | plugin | source |
|---|---|---|---|---|
| `<M-j>` | Normal | move the line down | move | m3 |
| `<M-j>` | Visual | move the selection down | move | m3 |
| `<M-k>` | Normal | move the line up | move | m3 |
| `<M-k>` | Visual | move the selection up | move | m3 |
| `<M-h>` | Normal | shift the line left | move | m3 |
| `<M-h>` | Visual | shift the selection left | move | m3 |
| `<M-l>` | Normal | shift the line right | move | m3 |
| `<M-l>` | Visual | shift the selection right | move | m3 |
| `[b` | Normal | previous buffer | bracketed | m3 |
| `]b` | Normal | next buffer | bracketed | m3 |
| `[B` | Normal | first buffer | bracketed | m3 |
| `]B` | Normal | last buffer | bracketed | m3 |
| `[l` | Normal | previous list entry | bracketed | m3 |
| `]l` | Normal | next list entry | bracketed | m3 |
| `[L` | Normal | first list entry | bracketed | m3 |
| `]L` | Normal | last list entry | bracketed | m3 |
| `[t` | Normal | previous TODO comment | bracketed | m3 |
| `]t` | Normal | next TODO comment | bracketed | m3 |
| `[h` | Normal | previous git hunk | bracketed | m3 |
| `]h` | Normal | next git hunk | bracketed | m3 |
| `[H` | Normal | first git hunk | bracketed | m3 |
| `]H` | Normal | last git hunk | bracketed | m3 |
| `[c` | Normal | previous git change | bracketed | m3 |
| `]c` | Normal | next git change | bracketed | m3 |
| `[d` | Normal | previous diagnostic | bracketed | m3 |
| `]d` | Normal | next diagnostic | bracketed | m3 |

## Prefixes (g, z, [, ], CTRL-W, registers, marks, operators)

| keys | mode | action | plugin | source |
|---|---|---|---|---|
| `g` | Normal | +goto | core | vim |
| `gg` | Normal | first line | core | vim |
| `ge` | Normal | back to end of word | core | vim |
| `gE` | Normal | back to end of WORD | core | vim |
| `gi` | Normal | insert where insert stopped | core | vim |
| `gI` | Normal | insert at column 1 | core | vim |
| `gJ` | Normal | join lines without a space | core | vim |
| `gj` | Normal | down a screen line | core | vim |
| `gk` | Normal | up a screen line | core | vim |
| `g0` | Normal | start of screen line | core | vim |
| `g^` | Normal | first non-blank of screen line | core | vim |
| `g$` | Normal | end of screen line | core | vim |
| `gm` | Normal | middle of screen line | core | vim |
| `gM` | Normal | middle of the text line | core | vim |
| `go` | Normal | go to byte | core | vim |
| `gp` | Normal | put after, cursor after | core | vim |
| `gP` | Normal | put before, cursor after | core | vim |
| `gq` | Normal | format lines | core | vim |
| `gw` | Normal | format, keep cursor | core | vim |
| `gu` | Normal | lowercase | core | vim |
| `gU` | Normal | uppercase | core | vim |
| `g~` | Normal | swap case | core | vim |
| `g?` | Normal | rot13 | core | vim |
| `gv` | Normal | reselect visual | core | vim |
| `g;` | Normal | older change position | core | vim |
| `g,` | Normal | newer change position | core | vim |
| `ga` | Normal | ascii of character | core | vim |
| `g8` | Normal | utf-8 bytes of character | core | vim |
| `gf` | Normal | edit file under cursor | core | vim |
| `gn` | Normal | search match as selection | core | vim |
| `gN` | Normal | previous match as selection | core | vim |
| `g&` | Normal | repeat :s on all lines | core | vim |
| `g_` | Normal | last non-blank | core | vim |
| `g-` | Normal | older text state | core | vim |
| `g+` | Normal | newer text state | core | vim |
| `g*` | Normal | search word, no boundaries | core | vim |
| `g#` | Normal | search word backwards, no boundaries | core | vim |
| `gR` | Normal | virtual replace mode | core | vim |
| `gs` | Normal | sleep | core | vim |
| `gc` | Normal | +comment (gc{motion}, gcc) | comment | vim |
| `gcc` | Normal | toggle comment on the line | comment | vim |
| `z` | Normal | +view and folds | core | vim |
| `zt` | Normal | cursor line at top | core | vim |
| `zz` | Normal | cursor line at middle | core | vim |
| `zb` | Normal | cursor line at bottom | core | vim |
| `z<CR>` | Normal | top, first non-blank | core | vim |
| `z.` | Normal | middle, first non-blank | core | vim |
| `z-` | Normal | bottom, first non-blank | core | vim |
| `zh` | Normal | scroll right | core | vim |
| `zl` | Normal | scroll left | core | vim |
| `zH` | Normal | scroll half screen right | core | vim |
| `zL` | Normal | scroll half screen left | core | vim |
| `zs` | Normal | cursor to left edge | core | vim |
| `ze` | Normal | cursor to right edge | core | vim |
| `zf` | Normal | create fold | core | vim |
| `zF` | Normal | fold lines | core | vim |
| `zo` | Normal | open fold | core | vim |
| `zO` | Normal | open folds recursively | core | vim |
| `zc` | Normal | close fold | core | vim |
| `zC` | Normal | close folds recursively | core | vim |
| `za` | Normal | toggle fold | core | vim |
| `zA` | Normal | toggle fold recursively | core | vim |
| `zv` | Normal | open folds at cursor | core | vim |
| `zR` | Normal | open all folds | core | vim |
| `zM` | Normal | close all folds | core | vim |
| `zd` | Normal | delete fold | core | vim |
| `zD` | Normal | delete folds recursively | core | vim |
| `zE` | Normal | eliminate all folds | core | vim |
| `zj` | Normal | next fold | core | vim |
| `zk` | Normal | previous fold end | core | vim |
| `zn` | Normal | folds off | core | vim |
| `zN` | Normal | folds on | core | vim |
| `zi` | Normal | toggle fold enable | core | vim |
| `[` | Normal | +previous | core | vim |
| `]` | Normal | +next | core | vim |
| `[[` | Normal | previous section start | core | vim |
| `]]` | Normal | next section start | core | vim |
| `[]` | Normal | previous section end | core | vim |
| `][` | Normal | next section end | core | vim |
| `[{` | Normal | previous unmatched { | core | vim |
| `]}` | Normal | next unmatched } | core | vim |
| `[(` | Normal | previous unmatched ( | core | vim |
| `])` | Normal | next unmatched ) | core | vim |
| `['` | Normal | previous mark line | core | vim |
| `]'` | Normal | next mark line | core | vim |
| `[`` | Normal | previous mark | core | vim |
| `]`` | Normal | next mark | core | vim |
| `[<Space>` | Normal | add blank line above | core | vim |
| `]<Space>` | Normal | add blank line below | core | vim |
| `<C-w>` | Normal | +windows | core | vim |
| `<C-w>s` | Normal | split below | core | vim |
| `<C-w>v` | Normal | split right | core | vim |
| `<C-w>n` | Normal | new window | core | vim |
| `<C-w>c` | Normal | close window | core | vim |
| `<C-w>q` | Normal | quit window | core | vim |
| `<C-w>o` | Normal | only this window | core | vim |
| `<C-w>w` | Normal | next window | core | vim |
| `<C-w>W` | Normal | previous window | core | vim |
| `<C-w>p` | Normal | last window | core | vim |
| `<C-w>t` | Normal | top-left window | core | vim |
| `<C-w>b` | Normal | bottom-right window | core | vim |
| `<C-w>h` | Normal | window left | core | vim |
| `<C-w>j` | Normal | window below | core | vim |
| `<C-w>k` | Normal | window above | core | vim |
| `<C-w>l` | Normal | window right | core | vim |
| `<C-w>H` | Normal | move window far left | core | vim |
| `<C-w>J` | Normal | move window to the bottom | core | vim |
| `<C-w>K` | Normal | move window to the top | core | vim |
| `<C-w>L` | Normal | move window far right | core | vim |
| `<C-w>r` | Normal | rotate windows | core | vim |
| `<C-w>R` | Normal | rotate windows up | core | vim |
| `<C-w>x` | Normal | exchange window | core | vim |
| `<C-w>=` | Normal | equalize sizes | core | vim |
| `<C-w>+` | Normal | taller | core | vim |
| `<C-w>-` | Normal | shorter | core | vim |
| `<C-w><` | Normal | narrower | core | vim |
| `<C-w>>` | Normal | wider | core | vim |
| `<C-w>_` | Normal | maximize height | core | vim |
| `<C-w>\|` | Normal | maximize width | core | vim |
| `"` | Normal | +register | core | vim |
| `""` | Normal | unnamed register | core | vim |
| `"+` | Normal | system clipboard | core | vim |
| `"*` | Normal | selection clipboard | core | vim |
| `"_` | Normal | black hole | core | vim |
| `"0` | Normal | last yank | core | vim |
| `"1` | Normal | last delete | core | vim |
| `"a` | Normal | named register a (a-z) | core | vim |
| `".` | Normal | last inserted text | core | vim |
| `":` | Normal | last command line | core | vim |
| `"/` | Normal | last search | core | vim |
| `"%` | Normal | file name | core | vim |
| `'` | Normal | +jump to mark line | core | vim |
| ``` | Normal | +jump to mark | core | vim |
| `m` | Normal | +set mark | core | vim |
| `q` | Normal | +record macro | core | vim |
| `@` | Normal | +run macro | core | vim |
| `'a` | Normal | mark a (a-z, A-Z) | core | vim |
| `''` | Normal | previous position | core | vim |
| `'[` | Normal | start of changed text | core | vim |
| `']` | Normal | end of changed text | core | vim |
| `'<` | Normal | start of selection | core | vim |
| `'>` | Normal | end of selection | core | vim |
| `'.` | Normal | last change | core | vim |
| `'^` | Normal | last insert | core | vim |
| `d` | Normal | +delete | core | vim |
| `c` | Normal | +change | core | vim |
| `y` | Normal | +yank | core | vim |
| `<` | Normal | +dedent | core | vim |
| `>` | Normal | +indent | core | vim |
| `=` | Normal | +reindent | core | vim |
| `!` | Normal | +filter through a command | core | vim |
| `dd` | Normal | delete line | core | vim |
| `cc` | Normal | change line | core | vim |
| `yy` | Normal | yank line | core | vim |
| `<<` | Normal | dedent line | core | vim |
| `>>` | Normal | indent line | core | vim |
| `==` | Normal | reindent line | core | vim |
| `!!` | Normal | filter line through a command | core | vim |
| `K` | Normal | hover documentation (language server) | lsp | m3 |
| `gd` | Normal | go to definition (language server) | lsp | m3 |
| `grr` | Normal | references (language server) | lsp | m3 |
| `grn` | Normal | rename symbol (language server) | lsp | m3 |
| `gra` | Normal | code action (language server) | lsp | m3 |
| `gh` | Normal | +stage hunks (gh{motion}) | git | m3 |
| `gH` | Normal | +reset hunks (gH{motion}) | git | m3 |
| `ys` | Normal | +surround add (ys{motion}{char}) | surround | vim |
| `yss` | Normal | surround the line | surround | vim |
| `ds` | Normal | surround delete (ds{char}) | surround | vim |
| `cs` | Normal | surround change (cs{old}{new}) | surround | vim |
| `yS` | Normal | surround add, on own lines | surround | vim |

## Other

| keys | mode | action | plugin | source |
|---|---|---|---|---|
| `jk` | Insert | Insert mode: leave to Normal mode (:set nojk_escape turns it off) | core | config |
| `<Space>` | Normal | Normal mode: leader key | core | config |
| `<C-^>` | Normal | Normal mode: alternate buffer | core | vim |
| `<A-j>/<A-k>` | Normal | Normal and Visual: move the line or selection down / up | move | m3 |
| `<A-h>/<A-l>` | Normal | Normal and Visual: shift the line or selection left / right | move | m3 |
| `<C-q>` | Normal | Picker: send the marked (or all) entries to the list | finder | m3 |
| `<C-t>` | Normal | Picker: mark or unmark the entry | finder | m3 |
| `<Tab>` | Insert | Insert and Select mode: jump to the next snippet tabstop (an active snippet; nvim 0.11's default) | core | vim |
| `<S-Tab>` | Insert | Insert and Select mode: jump to the previous snippet tabstop (Insert mode types a Tab otherwise, as nvim does) | core | vim |
| `<Tab>` | Insert | Insert mode: expand the snippet whose prefix stands before the cursor (snippets.json, VS Code format, next to the keymap file) | core | m3 |
| `<C-Space>` | Insert | Insert mode: ask the language server for completions (a picker; with :set lspcomplete=auto the popup) | lsp | m3 |
| `<Tab>/<C-n>/<Down>` | Insert | Insert mode, completion popup open: select the next item (past the last one nothing is selected) | lsp | m3 |
| `<S-Tab>/<C-p>/<Up>` | Insert | Insert mode, completion popup open: select the previous item | lsp | m3 |
| `<C-y>/<CR>` | Insert | Insert mode, completion popup open: accept the selected item (<CR> with nothing selected is a line break) | lsp | m3 |
| `<C-e>` | Insert | Insert mode, completion popup open: close it and keep what was typed (<Esc> closes it and leaves Insert mode) | lsp | m3 |
| `Select` | Insert | Select mode (after a jump onto a placeholder): a typed character or <CR> replaces it, <BS> and <Del> remove it, <Esc> leaves, <C-g> turns it into Visual mode | core | vim |

## Built-in plugins

| plugin | what it does |
|---|---|
| core | keymap tree, which-key engine, :Plugins and :Keys |
| finder | fuzzy pickers: files, grep, buffers, recent, git, symbols |
| whichkey | popup of the keys that can follow a pending prefix (core; old name) |
| explorer | file tree sidebar (<Space>e, :Neotree) |
| git | gutter signs, hunk keys, :Git log show diff blame |
| surround | ys ds cs and visual S |
| comment | gc and gcc, language aware |
| autopairs | insert-mode bracket and quote pairing |
| statusline | mode, file, branch, diagnostics, filetype, position; tabline |
| bracketed | [b ]b [l ]l [d ]d [h ]h [t ]t [c ]c |
| harpoon | pinned files per project, <Space>1..9 |
| move | move a line or selection with Alt-h/j/k/l |
| jump | label jump: <Space>j, then a character, then a label |
| guides | indent guides |
| todo | highlight TODO FIXME HACK NOTE WARN |
| terminal | :terminal, <Space>t, a shell or command on a pty in a buffer |
| session | remember the cursor position of each file |
| lsp | language server client: diagnostics, K, gd, grr, grn, gra, :Lsp (DESIGN.md section 13) |
