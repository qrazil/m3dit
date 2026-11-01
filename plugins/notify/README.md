# notify

Toast notifications, and a history of them.

* Boxes stack in the top right corner of the text area, 3 seconds each (6 for an error), at most five, 44 columns of
  text wrapped, titled `Info`, `Warning` or `Error` in the theme's `info`, `warning` and `error` colours on the popup
  background (so a transparent theme stays transparent).
* What becomes one: language server messages (`window/showMessage`) and what plugins `Ctx.notify`. The editor's own
  messages and errors (`E486: ...`) stay in the message line, as in Neovim with nvim-notify.
* `:Notify [info|warn|error] TEXT` shows one by hand; `:Notifications` lists this session's in the finder, newest first;
  `:NotifyClear` dismisses the boxes.
* Every toast is also in the core's `:messages` ring (the ring is the core's; the plugin's `:Notifications` is the toast history).
* With the plugin off or not built in, a message goes to the message line as before.

API used (0.3.0): the `Message` event (`Info.text`, `Info.level`), `Ctx.notify` (for other plugins), `Ctx.set_toasts` with
`MED_ext.Toast` (the host draws), a `Tick` handler that ages the boxes, `Ctx.pick_lines`. Lazy: it activates at the
first message, so a session without any costs nothing but the stub.

Turn it off: `:PluginDisable notify`, `--without notify`, `--no-plugins`.

Tests: `tests/t_notify.m31`, `tests/screen_pty.py` scenario `notify_toast`, `tests/transparent_pty.py` (the box is
checked on transparent terminals).
