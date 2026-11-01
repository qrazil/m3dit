# whichkey

After a pause, the keys that can follow what you typed.

* `<Space>` shows the leader menu; each further key narrows it (it stays once shown).
* `g`, `z`, `[`, `]`, `<C-w>`, `"`, `'` and the operators (`d`, `c`, `y`, `<`, `>`, `=`, `!`, `gu` ...) show the prefix help.
* The delay is 400 ms after the last key. `:set nowhichkey` turns the prefix help off (not the leader menu, as before).
* The popup lists the core's keys, the keys the plugins registered (with their `desc` and `Spec.groups` labels) and your own
  maps (their right-hand side as the label).

How it works: the host sends `PendingKeys` on every tick while keys are pending, with the time since the last key; this
plugin answers `Ctx.show_key_help()` once it is 400 ms. The keymap tree and the popup widget (`TUI_menu.WhichKey`, theme
scope `ui.which-key`) are the core's, so without the plugin the keys are the same and no popup appears. Eager (it only
registers one handler).

Turn it off: `:PluginDisable whichkey`, `--without whichkey`, `--no-plugins`.

Tests: `tests/t_whichkey.m31` (delays, stays while narrowing, `nowhichkey`, `:PluginDisable`), the golden screens
`which_key_leader`, `which_key_g`, `which_key_bracket`, `which_key_ctrl_w`, `tests/anim_pty.py` (the fade) and
`tests/transparent_pty.py` (the popup on a transparent terminal).
