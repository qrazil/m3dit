# The generic list (0.25.0)

One core service holds every list of places or rows the editor produces. It replaces the quickfix list as a store of its own. The idea is
the nox `nox-list` plugin (`apps/nox/plugins/nox-list`), cut down to what the editor itself needs.

## Model

A **list** has a name and rows. The default list is called `quickfix`; every command below that takes no name uses it. Since 0.27.0 the `:c*` commands (`:cnext`, `:copen`, `:cdo` ...) are gone; this is the only list API. A **row** is a
`MED_picker.Entry`: `text` (shown and matched), `path` + 0-based `line` + `column` (where it goes), `action` (an `ex:` / `picker:` / `keys:`
row for rows that are not places) and `detail` (what a plugin's preview provider understands). A list also remembers its **current row**
(the one `:lnext` last went to; none until one was visited). Replacing a list forgets the current row.

There is one store (`ui/MED_lists.m31`, `App.lists`). A location list is a list with another name; there is no per-window list.

## Who fills it

| source | list | notes |
|---|---|---|
| finder `<C-q>` | `quickfix` | the marked (or all) rows that have a position; the list opens |
| `:grep` `:vimgrep` `:make` | `quickfix` | the first row is jumped to (not with `!`); `:lgrep` `:lvimgrep` `:lmake` are gone |
| LSP references (`grr`, `:Lsp references`) | `quickfix` | the list opens |
| LSP diagnostics (`<Space>xx`, `<Space>xX`) | `diagnostics` | the list opens; `]d` `[d` still walk the diagnostics themselves |
| git hunks of the buffer (`:Hunk list`) | `quickfix` | the git plugin, through the plugin API |
| a plugin | any | `Ctx.list_set` / `list_add` / `list_clear` / `list_open` (extension API 0.7.0) |

`:ldo CMD` runs an ex line at each row of the default list and `:lfdo CMD` once for each file in it (at its first row); the first line that fails ends the run. Nothing is written: add `| update`.

## Commands

| command | does |
|---|---|
| `:l [NAME]`, `:list [NAME]`, `:List [NAME]` | open the list in the finder (with its preview); an empty list says so |
| `:lnext [NAME]`, `:ListNext` | go to the next row (wraps) |
| `:lprev [NAME]`, `:ListPrev` | the previous row (wraps) |
| `:lfirst [NAME]`, `:ListFirst` / `:llast [NAME]`, `:ListLast` | the first / last row |
| `:lclear [NAME]`, `:ListClear` | empty the list |
| `:lnext N` | go to row N of the default list |

Keys: `[l` `]l` previous / next, `[L` `]L` first / last row of the default list (the `bracketed` plugin). `[q` `]q` `[Q` `]Q` are not mapped
any more. The finder slots `<Space>sq` (default), `<Space>fq` (config), `<Space>xQ` and `<Space>xL` open the list; they are defaults, so
`:nmap` or `init.vim` can rebind them, and the `nvim` profile keeps its keys.

## What the UI is

The finder, in its list kind: the rows with fuzzy filtering, the preview of the row under the cursor, `<C-n>`/`<C-p>` or the arrows to browse (the preview
follows without closing), Enter to go there, Escape to close. `:lnext` and `]l` do not open anything: they move the cursor and put
`(2 of 7) text` in the message line.

nox-list's own floating window with its `n` / `p` keys is not ported as a second widget: the finder already is a floating list with a live
preview, and a second one would be two things to keep alike.

## Not done

* The current row is not updated when a row is chosen in the finder (only `:lnext` and friends move it).
* Lists are not saved with a session.
* No `:lolder` / `:lnewer` history of lists: a list is replaced, not stacked.
