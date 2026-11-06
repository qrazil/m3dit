# git

Default plugin (0.21.0). It was the git half of `ui/MED_app.m31` and `ui/MED_git*.m31`.

* **Keys** (profile `default`): `<Space>gh` hunks (`ghs ghr ghp ghu ghb ghB`), `gL` log of this file, `gd` diff, `uG` toggle signs, `]h [h`; the `nvim` and `legacy` profiles keep `gs gr gp gu gl gd gm gB gt` and `]c [c`.
* **Signs** in the gutter: `+` added, `~` changed, `_` removed rows against the index (marks and diagnostics have the column first);
  `:SignsGit` (`<Space>gt`) toggles them, `:set nogitsigns` turns them off.
* **Hunks**: `:Hunk stage|reset|undo|preview|list|next|prev` (`:Hunk list` puts the buffer's hunks in the generic list, docs/LIST.md) (`<Space>gs gr gu gp`, `]h [h`, `]c [c`), the `ih` / `ah` text objects.
* **`:Git log [FILE|%] [-L A,B]`, `:Git show [REV]`, `:Git diff [working|index|head]`, `:Git blame`** (lists in the finder with a `git show`
  preview, or scratch buffers), `:Git line` (`<Space>gB`, the last change of the cursor line).
* The branch and hunk counts for the status line (`Ctx.status`), read again every 3 s.

Reads and staging go through the m31git library; `git` itself runs (`Ctx.run_in`) only where the library cannot answer (a version 4 index, a partial
clone). The plugin imports only `ext.*` and m31git. Modules: `MEDX_git` (events, commands, keys), `MEDX_git_hunk` (the diff and hunk operations),
`MEDX_git_lib` (the library calls), `MEDX_git_cmd` (what `:Git` shows).

Tests: `plugins/git/tests/` (`t_git`, `t_gitlib`, the runner of `tests/oracles/oracle_git.py`), `tests/git_pty.py`.
