# Transparency

m3 can draw on a terminal with an opacity or blur setting (rio, Alacritty, kitty, Terminal.app, ...) so that the
desktop shows through every surface, not just the editor area.

    :set transparent             all surfaces       (:set notransparent, :set transparent!, :set transparent&)
    :set transparent=popups      popups, menus and the finder only
    m3 --transparent             for one run;  M3_TRANSPARENT=1|popups|0 m3
    transparent = true           in a theme file: that theme asks for it (`false`, `"popups"` also)

Off by default, and then nothing changes: `--dump-sample` of every built-in theme at 16, 256 and 24 bits is
byte-identical to 0.15.0 (`tests/golden/dump_sample_0.15.0.txt`). Precedence: the `--transparent` flag, then
`M3_TRANSPARENT`, then `:set` / the keymap file's `set transparent`, then the theme's own key, then off. The option
is a string: `""` (the default) means "ask the theme"; `:set notransparent` is an explicit `off`.

## Why a terminal needs this

A cell shows the desktop only when its background is the terminal's default (no SGR 48, or SGR 49). Any explicit
background, even one equal to the default colour, is painted opaque (kitty can be told otherwise, see below). So the
editor cannot "make the colour see-through": every cell it writes must leave the background alone. That is a rule
about styles, so it is applied where styles are made.

## The rule

`MED_theme.transparent_style(mode, scope, style)` is applied by `Theme.style`, through which every look, class look,
`over`, cursor and base the renderer asks for passes. No widget knows about it, so a new feature gets it for free
as long as it takes its colours from the theme (it must not build `Colour.Rgb` backgrounds itself).

| scope kind | examples | ALL | POPUPS |
|---|---|---|---|
| interactive highlight | `ui.selection`, `search.*`, `ui.cursor*` (cursor, cursor line / column), `ui.virtual.ruler`, `ui.menu.selected`, `ui.picker.selected`, `ui.picker.match`, `ui.text.focus` | keeps its background | same |
| selected row of a list without a text colour | `ui.picker.selected`, `ui.menu.selected`, `ui.text.focus` | keeps the background and gets near-black or near-white text, whichever reads on it | same |
| badge | `ui.statusline.normal/insert/select/visual/replace/command/terminal`, `ui.todo`, `ui.virtual.jump-label` | the block goes, its colour becomes the text colour (bold stays) | untouched |
| popup, menu, finder | `ui.popup*`, `ui.which-key*`, `ui.help*`, `ui.menu`, `ui.picker`, `.title`, `ui.prompt` | background dropped; `ui.background` is not laid under them | background dropped |
| anything else | `ui.background`, `ui.statusline`, `ui.bufferline*`, `ui.gutter`, `ui.linenr*`, syntax scopes, unknown scopes | background dropped | untouched |

A reversed style on a non-highlight scope loses its reversal (reverse video paints the terminal's text colour as an
opaque background), so the `term16-*` bars become plain, dim or bold text. The cursor keeps its reversal.

Surfaces are then told apart by what is left: their rounded border (finder, which-key), the text colour, bold, dim.
The completion menu, listings and the statusline have no border; what stands between them and the code is the
blank, background-less rectangle they clear and their text colours.

### Interactive highlights: what they look like on a light or a dark desktop

A highlight must stay visible, so it keeps an explicit background, the one its theme chose. The alternatives were
reverse video and a computed "semi-contrast" background. The references: tokyonight.nvim's `transparent` only stops
setting the main background (floats and sidebars are separate switches); lazygit has the selected line's background
as its own key whose default is computed from whether the terminal is dark or light, offers `reverse` for high
contrast and `default` for bold only; Helix themes with no `ui.background` keep their `bg` on `ui.selection` and
`ui.menu.selected`. All of them keep an explicit highlight colour rather than reading the desktop. m3 does the same
and adds only what is needed for legibility:

* the colour is the theme's, so a dark theme's highlight is dark and `default-light`'s is light: pick the theme that
  matches the desktop (`:set background=light|dark` switches the two default themes; `COLORFGBG` sets it at start);
* a selected row with a background and no text colour is given near-black or near-white text for that background, so
  it reads whatever the terminal's own text colour is;
* a theme that wants a highlight that follows the desktop writes `modifiers = ["reversed"]` (the terminal's two
  colours swapped: always legible, opaque) or `modifiers = ["bold"]` / `"underlined"` with no `bg`.

The limit: text drawn over a highlight keeps its own colour (syntax colours are chosen for the theme's polarity), so a
dark theme on a light desktop is unreadable with or without transparency.

### Colour blending without the desktop's colour

The popup fade and the yank / jump flash mixed backgrounds. The desktop colour cannot be known, so while transparent
they mix nothing: the fade draws the popup dim for its first half, the flash paints the highlight's colour (with
readable text) for its first half. No frame carries a background that is not a highlight's. There is no dimming of
inactive windows in m3.

## Per-surface behaviour (after)

| surface | ALL | POPUPS |
|---|---|---|
| text area, syntax, gutter, line numbers, git signs, diagnostics, folds, guides | no background; theme `fg` | as the theme |
| cursor line / column, colour column, selection, search, incsearch, cursor | explicit background of the theme (highlights) | same |
| TODO | text colour of the block | as the theme |
| statusline, tab line | text colour only; the mode name is its colour, bold | as the theme |
| command line, messages | text colour only | as the theme |
| command-line menu | none; selected item keeps its background | none; selected kept |
| listings, hover, signature, `:Hunk preview` | none | none |
| which-key, jump labels | none, border and text | same |
| finder box, input, list, preview, relevance column | none; border, text, dim | same; selected row and focus line keep their background |
| `:Git` / `:Hunk` / buffers / grep pickers | as the finder | as the finder |
| completion popup, doc panel | none; the selected row and the scroll thumb keep a background | same |
| file tree | none; focused row keeps a background | as the theme |
| terminal pane, scrollbar | none | none |
| theme preview (`:theme`, `<Space>fC`) | the previewed theme drawn transparent | same |
| fade, flash | see above | see above |

## Writing a theme for transparency

* Put `transparent = true` at the top of the file if the theme only makes sense on the terminal's background; the user
  can still turn it off (`:set notransparent`).
* Do not set `ui.background`; with it set, `transparent = "popups"` keeps it under the text.
* Give every surface a *foreground*; its background is optional and is dropped. A bar that is only a background
  (`{ bg = "panel" }`) becomes invisible text, so give it `fg`.
* Make mode names and badges `{ fg = "ink", bg = "accent" }`: transparent mode shows them as `accent` text.
* Give highlights a background that reads against both your text colour and a plain desktop; avoid `bg` equal to the
  desktop you expect.
* Borders carry popups: do not rely on a background to tell a popup from the code.
* Test it: `m3 --transparent --theme NAME --dump-sample` shows the screens without surface backgrounds.

## Terminal settings

Opacity makes the *default* background translucent; blur blurs what is behind the window. Cells with an explicit
background stay opaque, which is why the editor drops them.

* rio: `[window] opacity = 0.85`, `blur = true` (macOS / KDE).
* Alacritty: `[window] opacity = 0.85` (and `blur = true` where the compositor supports it).
* kitty: `background_opacity 0.85`, `background_blur 20`; `dynamic_background_opacity yes` allows changing it at run
  time. Recent kitty also has `transparent_background_colors`, which makes chosen explicit backgrounds translucent
  too: with it m3's default (non-transparent) themes can look right without this feature.
* Terminal.app: Profile, Window: the Background colour opacity and Blur sliders.

Opacity near 1.0 hides the problem; around 0.7-0.9 the opaque cells of a non-transparent theme stand out.
Check the exact option names against your version.

## Audit (m3 0.15.0, before the change)

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
