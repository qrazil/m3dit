# The docked panel API (0.6.0, for the `explorer` plugin)

Design for `Registry.did_panel` (docs/CORE-AND-PLUGINS.md section 10, item 12). The file tree sidebar (`ui/MED_tree.m31` and the 150 `tree.`
references in `ui/MED_app.m31`) becomes the `explorer` plugin; this API is the seam. Nothing here is new behaviour: it is what the sidebar does today,
named.

## What the host keeps

* The **layout**: the panel takes columns from the left of the screen (the windows share the rest), with a one-column separator. The host asks the
  panel for its width each time it lays out; 0 means closed.
* The **focus**: at most one panel is focused. `<C-w>h` from the leftmost window focuses it, `<C-w>l` and `<C-w>w` leave it, a click in its columns
  focuses it, `Esc` in the panel hands the focus back (the panel decides). While it is focused its keys come first, before the map table and the
  engine; the leader (`<Space>`), `:` and `<C-w>` stay the host's, as today.
* The **drawing surface**: a `Canvas`, which resolves a theme scope name to a style (so transparency and the 16-colour twin keep working) and clips
  to the panel's rectangle. A plugin never sees a `TUI_buffer`, a `Style` or an RGB value.
* The **mouse**: a press in the panel's columns focuses it and goes to the panel; the wheel scrolls it.

## What the plugin gives

```
pub interface Panel {
    /// Columns wanted on a screen `screen_width` wide, 0 when closed (the host never gives more than half the screen).
    int columns(int screen_width);
    /// Draw into the canvas (its size is the panel's rectangle without the separator); `is_focused` tells the cursor row to show.
    void draw(Canvas canvas, bool is_focused);
    /// A key typed while the panel is focused (the engine's key code, `MED_key` notation as in Ctx.feed). True: handled.
    bool key(Ctx context, int key);
    /// A press (`is_press`) or wheel turn (`button` 4 up, 5 down) at row `y`, column `x` of the panel. True: redraw.
    bool mouse(Ctx context, int x, int y, int button, bool is_press);
    /// About every TICK_MS while the panel is open and the editor is idle; True: redraw.
    bool tick(Ctx context, int elapsed_ms);
}

pub type Canvas {
    pub int width; pub int height;
    pub void text(int x, int y, str text, str scope, bool is_bold);   // clipped to the canvas
    pub void fill_row(int y, str scope);                              // the whole row in that style
}

Registry.did_panel(str name, Panel panel)        // one docked panel per plugin; the first plugin to ask owns the left side
Ctx.panel_open(str name, bool is_focus)          // Ctx.panel_close(name), Ctx.panel_toggle(name), Ctx.panel_focus(name)
Ctx.is_panel_focused(str name)
```

The plugin also needs, and the API has or gains additively: `Ctx.did_run_ex` (the prompts are ex lines: `:Neotree add NAME`), `Ctx.begin_command(text)`
(the command line opens with `text` typed), `Ctx.open_file_in(absolute, how)` (here, below, beside), `Ctx.show_text` (the help and the preview overlay),
`Ctx.run_in` for `git status`, and the file operations through `fs` (plugins may use the standard library except `proc`, `os` and `term`).

## Layout rules (as today)

* A screen narrower than `TREE_MIN_SCREEN` columns shares nothing: the panel is closed in effect (`columns` returns 0 there).
* The panel's rectangle is the area minus the tab line and the last row; its first row is the header and its last row the label ("TREE" / "TREE *").
* The separator is the column right of the panel, drawn by the host in `ui.window`.

## Miller columns (planned)

A second implementation of `Panel` (or a view mode of the same one) draws three columns; the API does not change except that `columns` may ask for
more than a third of the screen. `<Space>E` is its key.

## Tests that guard it

The golden screens `file_tree` and `git_tree_letters`, `t_tree` (the model, which moves with it), the e2e `tree` scenarios, `transparent_pty`
surfaces "file tree" and "file tree, focused row moved", and `core_only.sh` (a `--no-plugins` build has no sidebar, no `:Neotree`, no `<Space>e`).
