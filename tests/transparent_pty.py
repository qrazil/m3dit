#!/usr/bin/env python3
"""Transparency (docs/TRANSPARENCY.md): with `:set transparent`, no surface paints a background of its own.

    python3 tests/transparent_pty.py ./m3 [--quick] [--themes a,b] [--jobs N] [--no-lsp] [--worker]

A terminal shows the desktop through a cell only when the cell's background is the terminal's default,
so every surface the editor draws has to leave it alone. This drives the real binary in a pty (pyte is
the terminal; skipped with a note when it is missing), switches to every built-in theme with
`:theme NAME` after `:set transparent`, opens every surface (text with every kind of highlight, the
status, tab and command lines, the tree, folds, splits, the terminal pane, the which-key popup, the
jump labels, the finder in all its sources with and without a preview, the :Git and :Hunk lists, the
command-line menu, listings; and, through a scripted language server, the completion popup with its
documentation panel and the hover popup) and checks, after every frame the editor wrote:

  1. a cell may have a background only when it is an interactive highlight: its colour is one that
     the theme gives a highlight scope (selection, cursor line, search, menu / picker row, cursor),
     and the cells are where a highlight is (the text area for text surfaces; for a popup, at most
     the selected rows, the input line and a stray cell or two);
  2. the tab line and the status line have none, the command line only the cursor cell.

The same surfaces run again under `nobg-NAME`, a user theme that inherits NAME and takes the
background away from every highlight scope: the whole byte stream written from then on must contain
no background colour at all (SGR 40-48 and 100-107; only 49 may appear), the byte-level proof that
nothing but the highlights paints one. Popups also run with the animation on, so the frames of a
fading popup are checked. Finally the default mode is checked to be what it was: `:set transparent`
then `:set notransparent` leaves the screen, and a full repaint, exactly as never having touched it.

Work is spread over processes (`--jobs`, default 3), some themes each. macOS-safe: BSD tools only,
non-blocking pty writes, closed pipes tolerated, PWD and GIT_CEILING_DIRECTORIES set for every subprocess.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    import pyte
except ImportError:
    print("skip transparent_pty: pyte is not installed")
    sys.exit(0)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "bench"))
import uxperf  # noqa: E402

ROWS, COLS = 30, 100
SYNC_END = b"\x1b[?2026l"
FAKE = os.path.join(HERE, "fake_lsp_complete.py")

RUST = """// TODO: tidy up
use std::collections::HashMap;

/// Counts the words.
pub fn count(text: &str) -> HashMap<String, usize> {
    let mut seen = HashMap::new();
    for word in text.split_whitespace() {
        *seen.entry(word.to_lowercase()).or_insert(0) += 1; // 0x1F
    }
    seen
}

fn main() {
    let total = count("a b a");
    println!("{:?}", total);
    if total.len() > 1 {
        println!("many");
    }
}
"""

# the themes that also get the language server surfaces and the animated popups (the code paths are the
# same for every theme: the rest get every other surface)
DEEP = ("default", "default-light", "tokyonight", "gruvbox", "github-light", "term16-dark")

# the scopes whose background is the point of them (ui/MED_theme.m31 is_highlight)
HIGHLIGHT = re.compile(r"^(ui\.selection.*|ui\.highlight.*|ui\.cursor.*|ui\.virtual\.ruler|ui\.menu\.selected|"
                       r"ui\.picker\.selected|ui\.picker\.match|ui\.text\.focus.*|search.*)$")


# ---------------------------------------------------------------------------------- themes

def theme_names():
    return sorted(f[:-5] for f in os.listdir(os.path.join(ROOT, "themes")) if f.endswith(".toml"))


def read_theme(name, seen=()):
    """(palette, {scope: the rest of its line}) of a built-in theme file, inheritance followed."""
    palette, entries = {}, {}
    with open(os.path.join(ROOT, "themes", name + ".toml"), encoding="utf-8") as handle:
        text = handle.read()
    section = ""
    for raw in text.split("\n"):
        line = raw.strip()
        if line.startswith("#") or not line:
            continue
        if line.startswith("["):
            section = line.strip("[] ")
            continue
        m = re.match(r'^"?([A-Za-z0-9_.+-]+)"?\s*=\s*(.*)$', line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        if section == "palette":
            q = re.match(r'^["\']([^"\']*)["\']', value)
            if q:
                palette[key] = q.group(1)
        elif key == "inherits":
            parent = value.strip().strip('"')
            if parent not in seen:
                p_palette, p_entries = read_theme(parent, seen + (name,))
                p_palette.update(palette)
                palette = p_palette
                p_entries.update(entries)
                entries = p_entries
        else:
            entries[key] = value
    return palette, entries


def highlight_colours(name):
    """The background colours the highlight scopes of a theme use, as pyte spells them (rrggbb); None
    when a theme names one by index or by name (the 16-colour themes: any colour goes)."""
    palette, entries = read_theme(name)
    out = set()
    for scope, value in entries.items():
        if not HIGHLIGHT.match(scope):
            continue
        m = re.search(r'\bbg\s*=\s*"([^"]+)"', value)
        if not m:
            continue
        colour = m.group(1)
        for _ in range(8):
            if colour in palette:
                colour = palette[colour]
        if re.match(r"^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$", colour):
            out.add(colour[1:7].lower())
        elif re.match(r"^#[0-9a-fA-F]{3}$", colour):
            out.add("".join(c * 2 for c in colour[1:]).lower())
        else:
            return None
    return out


# every scope `is_highlight` knows, and the fallbacks themes use for them, without a background
NOBG_SCOPES = ["ui.selection", "ui.selection.primary", "ui.highlight", "ui.cursor", "ui.cursor.primary",
               "ui.cursor.primary.normal", "ui.cursor.primary.insert", "ui.cursor.primary.select",
               "ui.cursor.primary.replace", "ui.cursor.normal", "ui.cursor.insert", "ui.cursor.select",
               "ui.cursor.replace", "ui.cursor.match", "ui.cursorline", "ui.cursorline.primary",
               "ui.cursorline.secondary", "ui.cursorcolumn", "ui.cursorcolumn.primary", "ui.virtual.ruler",
               "ui.menu.selected", "ui.picker.selected", "ui.picker.match", "ui.text.focus", "search.match",
               "search.current"]


def write_nobg_theme(config_home, name):
    directory = os.path.join(config_home, "m3", "themes")
    os.makedirs(directory, exist_ok=True)
    lines = ['inherits = "%s"' % name]
    for scope in NOBG_SCOPES:
        lines.append('"%s" = { modifiers = ["underlined"] }' % scope)
    with open(os.path.join(directory, "nobg-%s.toml" % name), "w") as handle:
        handle.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------------- fixtures

def git(root, *args):
    env = dict(os.environ, PWD=root, HOME=root, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CEILING_DIRECTORIES=os.path.dirname(root), GIT_AUTHOR_NAME="A", GIT_AUTHOR_EMAIL="a@example.com",
               GIT_COMMITTER_NAME="C", GIT_COMMITTER_EMAIL="c@example.com")
    out = subprocess.run(["git"] + list(args), cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if out.returncode != 0:
        raise RuntimeError("git %r failed: %s" % (args, out.stderr))


def make_project(root):
    os.makedirs(os.path.join(root, "src"))
    with open(os.path.join(root, "src", "main.rs"), "w") as f:
        f.write(RUST)
    with open(os.path.join(root, "app.py"), "w") as f:
        f.write("import os\n\n\ndef run(x):\n    return x + 1\n")
    with open(os.path.join(root, "README.md"), "w") as f:
        f.write("# Title\n\nSome *text* and `code`.\n")
    git(root, "init", "-q", "-b", "main")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "first")
    with open(os.path.join(root, "src", "main.rs"), "w") as f:
        f.write(RUST.replace("    seen\n", "    seen.clone()\n").replace('println!("many");', 'println!("many");\n        println!("more");'))


# ---------------------------------------------------------------------------------- the terminal

SGR = re.compile(rb"\x1b\[([0-9;:]*)m")


def background_sets(data):
    """Every SGR parameter that sets a background colour (40-48, 100-107) in `data`."""
    found = []
    for m in SGR.finditer(data):
        params = [p for p in re.split(rb"[;:]", m.group(1)) if p != b""]
        i = 0
        while i < len(params):
            p = int(params[i])
            if p in (38, 48):
                width = 3
                if i + 1 < len(params) and params[i + 1] == b"2":
                    width = 5
                if p == 48:
                    found.append(b";".join(params[i:i + width]))
                i += width
                continue
            if 40 <= p <= 47 or 100 <= p <= 107:
                found.append(params[i])
            i += 1
    return found


class Term:
    """An editor in a pty and a pyte screen that is fed one frame at a time."""

    def __init__(self, binary, root, files, env=None, rows=ROWS, cols=COLS):
        base = {"PWD": root, "GIT_CEILING_DIRECTORIES": os.path.dirname(root), "SHELL": "/bin/sh"}
        base.update(env or {})
        self.ed = uxperf.Editor(binary, root, files, rows, cols, env=base)
        self.rows, self.cols = rows, cols
        self.screen = pyte.Screen(cols, rows)
        self.stream = pyte.ByteStream(self.screen)
        self.fed = 0
        self.hook = None
        self.frames = 0
        self.settle(0.5)
        # a loaded machine may not have drawn the first screen yet: wait for the status line and the tab line
        for _ in range(40):
            rows = self.text()
            if "NORMAL" in rows[-2] and (len(files) < 2 or "2 " in rows[0]):
                break
            self.settle(0.25)

    def mark(self):
        """From here on, frames are checked and their bytes kept."""
        self.start = len(self.ed.raw)

    def written(self):
        return bytes(self.ed.raw[self.start:])

    def settle(self, quiet=0.15):
        self.ed.settle(quiet, 8)
        data = bytes(self.ed.raw[self.fed:])
        self.fed = len(self.ed.raw)
        while data:
            cut = data.find(SYNC_END)
            if cut < 0:
                self.stream.feed(data)
                break
            piece, data = data[:cut + len(SYNC_END)], data[cut + len(SYNC_END):]
            self.stream.feed(piece)
            self.frames += 1
            if self.hook:
                self.hook(self.screen)

    def type(self, keys, quiet=0.15):
        self.ed.send(keys)
        self.settle(quiet)

    def text(self):
        buf = self.screen.buffer
        return ["".join(buf[y][x].data or " " for x in range(self.cols)) for y in range(self.rows)]

    def close(self):
        self.ed.close()


# ---------------------------------------------------------------------------------- the rules

class Rules:
    """What a frame may show. `kind` is "text" (highlights may be anywhere in the text area) or "popup"
    (a few rows and cells of one); `popup_rows` bounds the selected rows a popup may have."""

    def __init__(self, allowed):
        self.allowed = allowed          # a set of rrggbb, or None for "any colour"
        self.kind = "text"
        self.popup_rows = 2
        self.bar = False
        self.label = "start"
        self.problems = []
        self.checked = 0
        self.said = set()

    def say(self, message):
        key = (self.label, message.split(" ")[0])
        if key not in self.said and len(self.problems) < 40:
            self.said.add(key)
            self.problems.append("[%s] %s" % (self.label, message))

    def __call__(self, screen):
        self.checked += 1
        buf = screen.buffer
        rows, cols = screen.lines, screen.columns
        per_row = {}
        for y in range(rows):
            for x in range(cols):
                cell = buf[y][x]
                if cell.bg != "default":
                    per_row.setdefault(y, []).append((x, cell.bg))
        status_rows = (0, rows - 2, rows - 1)
        for y, cells in per_row.items():
            if y == 0 or (y == rows - 2 and not self.bar):
                self.say("row %d (tab or status line) has %d background cells, e.g. %r" % (y, len(cells), cells[0]))
            elif y == rows - 1 and len(cells) > 1:
                self.say("the command line has %d background cells" % len(cells))
            for x, colour in cells:
                if self.allowed is not None and colour not in self.allowed:
                    self.say("colour %s at (%d,%d) is not a highlight colour of the theme" % (colour, y, x))
        if self.kind == "popup":
            big = [y for y, cells in per_row.items() if len(cells) >= 3 and y not in status_rows]
            if len(big) > self.popup_rows:
                self.say("%d rows of a popup have a background (at most %d): rows %r" % (len(big), self.popup_rows, big[:6]))
            stray = sum(len(c) for y, c in per_row.items() if len(c) < 3 and y not in status_rows)
            if stray > 3:
                self.say("%d stray background cells" % stray)


# ---------------------------------------------------------------------------------- the surfaces

class Surface:
    def __init__(self, name, keys, leave="\x1b", kind="text", popup_rows=2, wait=0.2, bar=False, previews=False):
        self.name, self.keys, self.leave, self.kind = name, keys, leave, kind
        self.popup_rows, self.wait = popup_rows, wait
        self.previews = previews    # it shows other themes (their highlight colours are not this theme's)
        self.bar = bar          # the surface takes the status line's row: its selected item may have a background


def surfaces(quick):
    out = [
        Surface("plain text, gutter, git signs, statusline, tab line", "", ""),
        Surface("syntax, TODO highlight", "gg", ""),
        Surface("cursor line, cursor column, colour column, list, relative numbers, scrollbar",
                ":set cursorline cursorcolumn colorcolumn=30 list relativenumber scrollbar\r5G8l",
                ":set nocursorline nocursorcolumn colorcolumn= nolist norelativenumber noscrollbar\r"),
        Surface("hlsearch matches", "/seen\r", ":nohlsearch\r"),
        Surface("incsearch preview", "gg/tota", "\x1b"),
        Surface("visual selection", "5GVjj", "\x1b"),
        Surface("characterwise selection", "7Gwvee", "\x1b"),
        Surface("insert mode", "5GA", "\x1b"),
        Surface("replace mode", "5GR", "\x1b"),
        Surface("command line typing", ":set num", "\x1b"),
        Surface("error message", ":nosuchcommand\r", ""),
        Surface("folds", "7Gzfj", "zEgg"),
        Surface("splits, window separators, inactive statusline", ":vsplit\r:split\r", ":only\r"),
        Surface("file tree", " e", " e", wait=0.5),
        Surface("file tree, focused row moved", " ejj", " e", wait=0.5),
        Surface("command-line menu (wildmenu)", ":colorscheme t\t", "\x1b", bar=True),
        Surface("listing (:ls)", ":ls\r", "\r"),
        Surface("hunk preview", "gg:Hunk preview\r", "\r", wait=0.5),
        Surface("which-key", " ", "\x1b", kind="popup", popup_rows=0, wait=0.4),
        Surface("which-key, a sub-prefix", " f", "\x1b\x1b", kind="popup", popup_rows=0, wait=0.4),
        Surface("jump labels", " j", "\x1b", kind="popup", popup_rows=2, wait=0.4),
        Surface("finder: files", " ff", "\x1b", kind="popup", popup_rows=1, wait=0.5),
        Surface("finder: files, typed query, second row selected", " ffm\x0e", "\x1b", kind="popup", popup_rows=1,
                wait=0.5),
        Surface("finder: grep with preview", " fgseen", "\x1b", kind="popup", popup_rows=2, wait=0.8),
        Surface("finder: buffers", " fb", "\x1b", kind="popup", popup_rows=1),
        Surface("finder: commands", " fc", "\x1b", kind="popup", popup_rows=1),
        Surface("finder: themes (live preview)", " fC\x0e", "\x1b", kind="popup", popup_rows=1, wait=0.5, previews=True),
        Surface("finder: all keys", " ?", "\x1b", kind="popup", popup_rows=1),
        Surface("git: log with preview", ":Git log %\r", "\x1b", kind="popup", popup_rows=2, wait=0.8),
        Surface("git: blame list", ":Git blame\r", "\x1b", kind="popup", popup_rows=2, wait=0.8),
        Surface("git: changed files", " gg", "\x1b", kind="popup", popup_rows=2, wait=0.8),
        Surface("terminal pane", ":terminal\r", "\x1b\x1b:bd!\r", wait=0.8),
    ]
    if quick:
        keep = ("plain", "cursor line", "hlsearch", "visual", "folds", "file tree", "which-key", "finder: files",
                "finder: grep", "git: log", "command-line menu", "listing")
        out = [s for s in out if s.name.startswith(keep)]
    return out


def run_surfaces(term, rules, only_popups, quick, is_nobg):
    for surface in surfaces(quick):
        if only_popups and surface.kind != "popup":
            continue
        if is_nobg and surface.previews:
            # the picker puts the highlighted theme on: its own highlights are not removed by `nobg-`
            continue
        rules.label = surface.name
        rules.kind = surface.kind
        rules.popup_rows = surface.popup_rows
        rules.bar = surface.bar
        kept = rules.allowed
        if surface.previews:
            rules.allowed = None
        term.type(surface.keys, surface.wait)
        rules.allowed = kept
        rules.kind = "text"
        rules.popup_rows = 2
        rules.bar = False
        if surface.leave:
            term.type(surface.leave, 0.1)
    rules.label = "after the surfaces"
    term.type("\x1b\x1b", 0.15)


def run_lsp(term, rules):
    """The completion popup, its documentation panel and the hover popup, through a scripted server."""
    term.type(":Lsp server python python3 %s\r" % FAKE, 0.3)
    term.type(":set lspcomplete=auto\r", 0.3)
    term.type(":Lsp start\r", 1.0)
    rules.label = "completion popup"
    rules.kind = "popup"
    rules.popup_rows = 1
    term.type("jA", 0.3)
    term.type("hel", 0.8)
    rules.label = "completion popup, selected row, documentation panel"
    for _ in range(3):
        term.ed.send("\t")
    term.settle(0.8)
    term.type("\x1b", 0.3)
    rules.kind = "text"
    rules.popup_rows = 2
    rules.label = "hover popup"
    term.type(":Lsp hover\r", 1.0)
    term.type("\r", 0.2)
    rules.label = "after the language server"


# ---------------------------------------------------------------------------------- one theme

def one_run(binary, root, name, use_nobg, animated, quick, with_lsp, failures, counts):
    theme = ("nobg-" + name) if use_nobg else name
    label = theme + (" (animated)" if animated else "")
    rules = Rules(set() if use_nobg else highlight_colours(name))
    env = {} if animated else {"M3_NO_ANIM": "1"}
    streams = []
    sessions = [(["src/main.rs", "app.py"], lambda t: run_surfaces(t, rules, animated, quick, use_nobg))]
    if with_lsp:
        sessions.append((["app.py"], lambda t: run_lsp(t, rules)))
    for files, body in sessions:
        with open(os.path.join(root, "app.py"), "w") as f:
            f.write("import os\n\nx = 1\n\n" if body is not sessions[0][1] else "import os\n\n\ndef run(x):\n    return x + 1\n")
        term = Term(binary, root, files, env=env)
        try:
            term.type(":set transparent\r:theme %s\r" % theme, 0.4)
            if use_nobg and "theme: nobg-" not in " ".join(term.text()[-2:]):
                failures.append("[%s] `:theme %s` did not switch: %r" % (label, theme, term.text()[-2:]))
            term.mark()
            term.hook = rules
            rules.label = "start"
            rules(term.screen)
            body(term)
            streams.append(term.written())
        finally:
            term.close()
    counts["frames"] += rules.checked
    counts["runs"] += 1
    if use_nobg:
        for stream in streams:
            sets = background_sets(stream)
            if sets:
                failures.append("[%s] %d background colours in the byte stream, first %r" % (label, len(sets), sets[0]))
    for problem in rules.problems:
        failures.append("[%s] %s" % (label, problem))


def run_theme(binary, name, quick, with_lsp, failures, counts):
    root = os.path.realpath(tempfile.mkdtemp(prefix="m3tr"))
    try:
        make_project(root)
        write_nobg_theme(os.path.join(root, ".config"), name)
        deep = name in DEEP and with_lsp
        for use_nobg in (False, True):
            one_run(binary, root, name, use_nobg, False, quick, deep and not quick, failures, counts)
            if deep and not quick:
                one_run(binary, root, name, use_nobg, True, quick, False, failures, counts)
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ---------------------------------------------------------------------------------- default mode

def check_default_unchanged(binary, failures):
    """`:set transparent` then `:set notransparent` and `transparent&` is the default again: the same
    screen, and a full repaint after it writes the bytes a repaint of a never-touched editor writes."""
    root = os.path.realpath(tempfile.mkdtemp(prefix="m3tr"))
    try:
        make_project(root)
        shots = []
        for toggled in (False, True):
            term = Term(binary, root, ["src/main.rs", "app.py"], env={"M3_NO_ANIM": "1"})
            try:
                term.type(":theme tokyonight\r", 0.3)
                if toggled:
                    term.type(":set transparent\r", 0.3)
                    term.type(":set notransparent\r", 0.3)
                    term.type(":set transparent&\r", 0.3)
                term.type(" ff", 0.6)
                term.type("\x1b", 0.2)
                before = len(term.ed.raw)
                term.ed.resize(ROWS + 1, COLS)
                term.ed.settle(0.3, 6)
                term.ed.resize(ROWS, COLS)
                term.ed.settle(0.3, 6)
                data = bytes(term.ed.raw[before:])
                shots.append((term.text(), len(background_sets(data)), data))
            finally:
                term.close()
        if shots[0][0] != shots[1][0]:
            failures.append("default mode: the screen after set / unset transparent differs")
        if shots[0][1] == 0:
            failures.append("default mode: the full repaint of a theme with backgrounds has none (the check is vacuous)")
        if shots[0][2] != shots[1][2]:
            failures.append("default mode: a full repaint writes other bytes after set / unset transparent")
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ---------------------------------------------------------------------------------- main

def option(args, name, default=None):
    if name in args and args.index(name) + 1 < len(args):
        return args[args.index(name) + 1]
    return default


def main():
    args = sys.argv[1:]
    binary = os.path.abspath(args[0])
    quick = "--quick" in args
    with_lsp = "--no-lsp" not in args
    worker = "--worker" in args
    jobs = int(option(args, "--jobs", "3"))
    names = theme_names()
    if option(args, "--themes"):
        names = option(args, "--themes").split(",")
    elif quick:
        names = [n for n in names if n in ("default", "tokyonight", "gruvbox", "github-light", "term16-dark")]
    if not worker and jobs > 1 and len(names) > 1:
        sys.exit(spread(binary, names, jobs, quick, with_lsp))
    failures, counts = [], {"frames": 0, "runs": 0}
    for name in names:
        try:
            run_theme(binary, name, quick, with_lsp, failures, counts)
        except Exception as error:  # a crash is a failure with its theme named
            failures.append("[%s] crashed: %r" % (name, error))
    if not worker:
        check_default_unchanged(binary, failures)
    for line in failures[:60]:
        print("FAIL " + line)
    print("transparent_pty: %d themes, %d runs, %d frames checked, %d failed" % (len(names), counts["runs"],
                                                                                counts["frames"], len(failures)))
    sys.exit(1 if failures else 0)


def spread(binary, names, jobs, quick, with_lsp):
    """Run the themes in `jobs` worker processes of this script and add their reports up."""
    procs = []
    for i in range(jobs):
        group = names[i::jobs]
        if not group:
            continue
        cmd = [sys.executable, os.path.abspath(__file__), binary, "--worker", "--themes", ",".join(group)]
        if quick:
            cmd.append("--quick")
        if not with_lsp:
            cmd.append("--no-lsp")
        procs.append(subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=os.getcwd()))
    failures, frames, runs = [], 0, 0
    for proc in procs:
        out, _ = proc.communicate()
        for line in out.decode("utf-8", "replace").splitlines():
            m = re.match(r"transparent_pty: \d+ themes, (\d+) runs, (\d+) frames", line)
            if m:
                runs += int(m.group(1))
                frames += int(m.group(2))
            elif line.strip():
                failures.append(line)
        if proc.returncode not in (0, 1):
            failures.append("FAIL a worker exited with status %r" % proc.returncode)
    extra = []
    check_default_unchanged(binary, extra)
    failures += ["FAIL " + line for line in extra]
    failed = [f for f in failures if f.startswith("FAIL")]
    for line in failed[:60]:
        print(line)
    print("transparent_pty: %d themes, %d runs, %d frames checked, %d failed" % (len(names), runs, frames, len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    main()
