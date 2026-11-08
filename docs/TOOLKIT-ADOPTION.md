# Adopting the plugin toolkit (API 0.9.0)

The UI kit (floats, `MED_ui`, `MED_util`, docs/EXTENSIONS.md 0.7) lets a plugin stop writing its own drawing, key loop and open / close bookkeeping. This is the order in which the
shipped plugins would gain from it, with what each would drop. It is a list for whoever does the porting; nothing here has been ported, and a port is only done while the golden
screens and the plugin tests stay green. The sizes are the lines of the plugin's main module as of 0.31.1.

| order | plugin | what it would gain | what it drops |
|---|---|---|---|
| 1 | `notify` (175 lines) and the host's toast drawing (`App.draw_toasts`, `App.notify_user`) | one float per toast with `did_tick` for the expiry, stacked with `MED_ui.stack`/`divide` | the host-side toast list, its timers and its drawing; the plugin would own the whole feature |
| 2 | `harpoon` (147) | its menu is `MED_ui.select` over the pinned files | its own picker-list glue (`pick_list` entries and action strings) |
| 3 | `git` (733 + hunk, cmd, lib) | `:Git` output and `ghd` in `MED_ui.popup` (scrollable, titled); the commit message in `MED_ui.prompt` | `show_text` overlays that cannot scroll; the `:Git commit ` typed command-line trick |
| 4 | `explorer` (597 + tree 684) | its prompts (`add`, `rename`, `copy`, `move`, `delete`) as `MED_ui.prompt`, the preview and the help as floats; the tree stays a docked panel | `begin_command` prompts that carry a path and are parsed back; the `?` help drawing in the panel |
| 5 | `todo` (115) | the `Todo` list as a float with the kit's select menu where a finder is more than needed | little; it is mostly decorations |
| 6 | `terminal` (225 + vt) | the float and split variants are built on the kit from 0.32 on | nothing: it is the first user |
| 7 | `session`, `move`, `bracketed`, `statusline` | nothing to adopt | they have no windows of their own |

What does **not** move: the finder (a core picker with preview and fuzzy ranking, many sources), the which-key popup and the completion popup (the host draws them from engine state), and the
docked explorer column (a float would cover the text instead of sharing the screen). The finder preview stays a part of the finder.

Order of work: notify, harpoon, git, explorer prompts. Each is its own commit with its own golden screens re-recorded, so that a regression has one suspect.
