# session

m3 remembers where you were.

* The **cursor position** of each file is put back when the file is opened (a file you opened with `:e`, or on the command
  line). A cursor already moved by a restored `:Session` is left alone.
* The **recent files** list (`$XDG_STATE_HOME/m3/recent`, 200 files) feeds `<Space>fr` and `:Recent`.
* Each file in front counts as a **visit** for the finder's frecency ordering (`<Space>ff` lists often and recently used
  files first).

It writes within 250 ms of a change (a `Tick` handler notes the file in front and its cursor row), when a buffer is closed
and when the editor quits. The state files are the ones the core wrote before this was a plugin (`recent`, `positions`),
so nothing is lost on upgrade; without a state directory (`HOME` unset, `--keymap NONE`) it does nothing. `:Session`
(named sessions of the buffers, tab pages and layout, and the project session saved on exit) stays in the core.

API used (0.4.0): `Ctx.global_state_lines` and `did_set_global_state_lines` (user state, not per project),
`Ctx.note_visit`, `Ctx.set_cursor` (which now also remembers the column for `j` and `k`), `Event.BufferOpen`,
`BufferClose`, `Tick` and `Shutdown`.

Differences from the core version: the old timer ran every second and wrote the position when the file was switched with
`activate`; the plugin's Tick is 250 ms and a buffer switch is noticed on the next Tick, so a buffer left within 250 ms of its
last cursor move keeps the previous row (`BufferClose` and `Shutdown` still write). A file is restored to row 0 only if it
was saved at a row above 0.

Turn it off: `:PluginDisable session`, `--without session`, `--no-plugins` (no recent files, no restored cursors).

Tests: `tests/t_session_plugin.m31`, the e2e scenario `state_recent_harpoon_position`.
