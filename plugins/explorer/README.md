# explorer

Default plugin (0.24.0). The file tree sidebar: neo-tree's filesystem source in a terminal. It was `ui/MED_tree.m31` and about 600 lines of
`ui/MED_app.m31`; it now docks as a **panel** (API 0.6.0, `Registry.did_panel`, docs/PANEL-API.md): the host keeps the layout, the separator, the focus
and the drawing surface, the plugin keeps what the sidebar shows.

* `<Space>e` toggles it with the current file revealed (`legacy` and `nvim`: `<Space>e` toggle, `<Space>E` reveal); `:Neotree [toggle|show|focus|close|reveal|refresh|hidden|DIR]`
  (also spelled `:NeoTree`). Options: `treewidth`, `treeglyphs`, `treehidden`.
* In the tree: `j k gg G <C-d> <C-u>` move, `l <CR> o` open / expand, `h` collapse / parent, `s v t` open in a split, `a d r c m` add, delete, rename, copy,
  move (each opens the command line with the path typed), `y x p` yank, cut, paste, `H` hidden files, `/` filter, `R` refresh, `P` preview, `i` info, `.` set
  root, `u <BS> -` up, `z` collapse all, `q` close, `?` help. `<C-w>l` goes back to the windows.
* Git status letters (M A D R ? !) come from `git status` through `Ctx.run_in` every 5 s while the tree is open and the editor is in Normal mode.

Tests: `plugins/explorer/tests/t_tree.m31` (the model), the golden screens `file_tree` and `git_tree_letters`, core_pty `explorer_panel_and_switch`,
the e2e tree scenarios and the transparent surfaces "file tree".
