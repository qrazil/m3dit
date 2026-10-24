# Transparency audit (m3 0.15.0, before the change)

A terminal shows the desktop through a cell only when the cell's background is the terminal's **default** (no SGR
48, or SGR 49 after one). Any explicit background, even one equal to the default, is painted opaque. So a surface is
transparent only if every cell it writes leaves the background at the default.

## How the editor area is transparent today

The editor area is transparent when the *theme* has no `ui.background` scope (and no `bg` in `ui.text`): `Theme.base`
is then empty, `App.render` skips its `buffer.fill(full, " ", theme.base)`, and `look(scope)` starts from an empty
base. That is the case for `default`, `default-light`, `term16-dark` and `term16-light` (see their headers). The other
ten built-in themes (`tokyonight`, `nightfox`, `gruvbox`, `gruvbox-material`, `gruvbox-material-soft`,
`catppuccin-mocha`, `onedark`, `nord`, `dracula`, `github-light`) set `ui.background`, so they are opaque everywhere,
and user themes in Helix's format usually do. There was no option, flag or environment variable for it, and a
theme with no `ui.background` was *still* opaque on every surface that has a scope with a `bg`: the finder, popups,
bars. That is what the owner saw: "the editor works, the finder does not".

Two more leaks existed even in the transparent default theme, both animations that mix colours:

* the popup fade (`MED_anim.fade_in`) blends the background of the popup with the background behind it and writes
  the result as an explicit 24-bit background on every cell of the popup for about 100 ms (a default background is
  "guessed" as black or white);
* the yank / jump flash (`MED_glide`) mixes the background of the flashed cells towards the `search.match` colour
  starting from the same guess.

## The tui library (`tui` 0.15.0, `tui-wt/perf2`)

| piece | does it emit a background for a default-style cell? |
|---|---|
| `Block` / `Popup` / `WhichKey` / `Transient` (`TUI_widget`, `TUI_menu`) | fill their rectangle with the style given; the defaults are `Style()` (no colours) and `BOLD` for titles, so a default style fills with spaces and writes **no** SGR |
| `TUI_style.sgr` (the renderer) | writes a background only when the pen's background differs from the next cell's: nothing for default-on-default; `49` only for the cell after an explicit background; a frame starts from `\x1b[0m` |
| `TUI_diff` erase-to-end-of-line | used only for runs of plain (default) blanks, after putting the pen back to plain, so it never paints |
| `TUI_textarea.selection_style` | `bg = Indexed(4)` (a highlight, on purpose) |
| `highlight_style` of list, table, outline, jump list, tabs, chart hover, diff view | `REVERSE`: draws the terminal's text colour as the background, opaque but readable on any desktop |
| gauge | half-cell edge uses the style's two colours, default when not set |

Nothing in the library paints a background unless the program gives one. The renderer needs no change for m3.

## Surface table (before)

"Scope" is the theme scope the draw code asks for; "bg source" is where an explicit background comes from today.

| surface | scope(s) | bg source today |
|---|---|---|
| text area, empty cells | `ui.background`, `ui.text` | the base: `buffer.fill(full, ..., base)` and under every `look()` (only when the theme has `ui.background`) |
| syntax text | `class_look`, `ui.text` | base; cursor line / colour column variants add theirs |
| gutter, line numbers, sign column | `ui.gutter`, `ui.linenr(.selected)` | base plus the scope's own `bg` (gruvbox, nightfox, ...) |
| git signs, diagnostic letters in the gutter | `ui.gutter` + `diff.*`, `error`, ... | base, gutter `bg` |
| cursor line / cursor column | `ui.cursorline`, `ui.cursorcolumn` | scope `bg` (a highlight) |
| colour column | `ui.virtual.ruler` | scope `bg` (a highlight) |
| indent guides, list chars, inlay hints | `ui.virtual.*` | foreground only; the cell's own background |
| visual selection | `ui.selection` | scope `bg` (a highlight) |
| search matches, incsearch preview | `search.match`, `search.current` | scope `fg` + `bg` (highlights) |
| TODO / FIXME | `ui.todo` | ink on a coloured block |
| cursor | `ui.cursor.primary.*` | reverse, or `bg` (the cursor) |
| folds | `ui.text.inactive` | base |
| diagnostics | gutter letters, statusline counts, `diagnostic.*` underline | no virtual text exists; base only |
| snippet placeholders | none of their own (cursor, selection) | base |
| statusline (active, inactive) | `ui.statusline`, `.inactive` | scope `bg` (or reverse video in `term16-*`) |
| statusline mode name | `ui.statusline.normal` ... | block of colour: `fg = ink`, `bg = accent` |
| bufferline / tab line | `ui.bufferline`, `.active` | scope `bg` (or reverse) |
| window separators | `ui.window` | foreground only |
| command line, messages, notifications | `ui.text`, `error` | base |
| command-line menu (wildmenu) | `ui.menu`, `ui.menu.selected` | scope `bg` for both |
| listings (`:ls`, hover, signature, `:Hunk preview`) | `ui.popup`, `ui.prompt` | scope `bg` of `ui.popup` |
| which-key, jump labels | `ui.which-key`, `.title` | scope `bg`; rounded border |
| finder: box, input line, list rows | `ui.picker`, `.title`, `ui.prompt` | scope `bg` of `ui.picker`; rounded border |
| finder: selected row, matched characters | `ui.picker.selected`, `ui.picker.match` | `bg` of the selected row (a highlight); match is `fg` + bold |
| finder: preview pane, focus line | `ui.picker`, `ui.picker.selected` | same as the box |
| finder: relevance column | `ui.picker` + `ui.text.inactive` | foreground only on the box background |
| completion popup (pum) and doc panel | `ui.menu`, `ui.menu.selected`, `ui.popup` | scope `bg`; the selected row and the scroll thumb use `ui.menu.selected` |
| file tree | `ui.text`, `ui.menu.selected`, `ui.statusline` | base; focused row and footer take scope `bg` |
| scrollbar | dim glyph | none |
| terminal pane | the pane's text (program colours are dropped) | base |
| popup fade (which-key, finder) | blend of popup and underlying `bg` | **explicit RGB background invented from a guess**, even with no `ui.background` |
| yank / search flash | blend of cell `bg` towards `search.match` | **explicit RGB background invented from a guess** |
| `:Git log/blame/...`, `:Hunk` | finder pickers, overlay listing | as the finder and the listing |
| theme preview (`:theme`, `<Space>fC`) | the same draw code | as above, for whichever theme is highlighted |
