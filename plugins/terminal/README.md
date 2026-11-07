# terminal

Default plugin (0.29.0). `:terminal [command]` (and `<Space>t` / `<Space>tt` in the profiles that map it) runs a shell, or `sh -c command`, on a pty in a
new buffer. It was the `Term` type and about 300 lines of `ui/MED_app.m31`, plus `ui/MED_vt.m31`; the plugin now keeps what runs, over two host services
(API 0.8.0): **ptys** (`Ctx.pty_open`, `pty_write`, `pty_read`, `is_pty_open`, `pty_exit_code`) and **panes** (`Ctx.pane_open`, `pane_set`, `pane_input`,
`pane_busy`, `pane_size`, and the `PaneDriver` that takes the keys and the timer: `Registry.did_panes`). A plugin may not import `proc`, so the host
owns the ptys and the plugin names them by number.

* In the buffer the keys go to the program until `CTRL-\ CTRL-N`; in Normal mode `i` `a` `I` `A` give them back. The status line says TERMINAL while they do.
* When the program ends the buffer ends with `[Process exited N]`.
* The screen model (`MEDX_terminal_vt`) handles what line-oriented programs print (shells, build tools, `git`, `ls`): CR, LF, backspace, tab, erase,
  cursor movement, colours dropped. Full-screen programs (editors, pagers, htop) need a real emulator and are out of scope.
* `:terminal` is the one lowercase plugin command (nvim's name). With the plugin off (`:PluginDisable terminal`, `--without terminal`, `--no-plugins`) it is
  E492 / "switched off".

Tests: `plugins/terminal/tests/t_vt.m31` (the screen model), the e2e scenario `terminal_pane`, the core_pty scenario `terminal_plugin`.
