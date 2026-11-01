# harpoon

Pin the files you keep returning to and jump to them by number.

| keys | command | does |
|---|---|---|
| `<Space>ha` | `:HarpoonAdd` | pin this file (the next number) |
| `<Space>hd` | `:HarpoonRemove` | unpin this file |
| `<Space>he` | `:HarpoonMenu` | the pinned files in the finder (Enter opens one) |
| `<Space>hn` `<Space>hp` | `:HarpoonNext` `:HarpoonPrev` | next, previous pinned file (wraps) |
| `<Space>1` .. `<Space>9` | `:Harpoon N` | pinned file N (`:Harpoon` alone is the menu) |

The list is per project and kept in m3's state directory (`$XDG_STATE_HOME/m3`, default `~/.local/state/m3`), file
`harpoon-PROJECT`: the file the core wrote before this became a plugin, so existing lists carry over. Without a state
directory (`HOME` unset, `--keymap NONE`) it says so and does nothing.

API used (0.3.0): `Ctx.state_lines` and `did_set_state_lines` (the state file), `absolute_path`, `relative_path`,
`open_file` and `say_later` (open a file, then show the message after the file's own), `pick_files` (the menu),
`Spec.groups` (the `+harpoon` label in which-key). Lazy: it activates when the first command runs.

Turn it off: `:PluginDisable harpoon`, `--without harpoon`, `--no-plugins`.

Tests: `tests/t_harpoon.m31` (pin, number, next and previous, wrap, remove, menu, `:PluginDisable`), the e2e scenario
`state_recent_harpoon_position`, the golden screen `harpoon_pin`.
