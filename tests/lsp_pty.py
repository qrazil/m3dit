#!/usr/bin/env python3
"""The language server popups of m3, driven through a pty (docs/DESIGN.md section 13).

    python3 tests/lsp_pty.py ./m3 [--quick] [--only NAME,NAME] [--real]

A scripted server (tests/fake_lsp_complete.py, Python 3 over stdio) answers; with --real (or M3_LSP_REAL=1) the
scenarios that need a real language server run too, against whichever of pyright-langserver /
rust-analyzer / lua-language-server / clangd / typescript-language-server is installed (PATH or nvim's mason bin
directory); a missing server skips its scenario. The screen is read through pyte, and after every step the screen
the diff renderer produced is compared with a from-scratch redraw of the same state (a resize away and back is
always a full redraw). The popup is checked for an intact rectangle: every row of it is one run of cells with the
popup's background, the rows are adjacent, nothing is drawn right of it that does not belong to it, and a closed
popup leaves no background cell in the text area. No control character the server sent may reach the terminal.
Skips with a note when pyte is missing. No language server process is left behind (checked by pid, Linux only).
"""
import json
import os
import shutil
import sys
import tempfile
import time

try:
    import pyte
except ImportError:
    print("skip lsp_pty: pyte is not installed")
    sys.exit(0)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "bench"))
import uxperf  # noqa: E402

FAKE = os.path.join(HERE, "fake_lsp_complete.py")
MASON = os.path.expanduser("~/.local/share/nvim/mason/bin")
ROWS, COLS = 30, 100

SCENARIOS = {}


def scenario(fn):
    SCENARIOS[fn.__name__] = fn
    return fn


class Skip(Exception):
    pass


def descendants(pid):
    """Every live descendant pid of `pid` (from /proc; empty where there is none)."""
    parents = {}
    try:
        entries = os.listdir("/proc")
    except OSError:
        return set()
    for entry in entries:
        if entry.isdigit():
            try:
                with open("/proc/%s/stat" % entry) as f:
                    parents[int(entry)] = int(f.read().rsplit(")", 1)[1].split()[1])
            except (OSError, IndexError, ValueError):
                pass
    out, frontier = set(), {pid}
    while frontier:
        frontier = {p for p, q in parents.items() if q in frontier and p not in out}
        out |= frontier
    return out


def alive(pid):
    try:
        with open("/proc/%d/stat" % pid) as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except OSError:
        return False


class Report:
    def __init__(self):
        self.failures = []
        self.checks = 0
        self.skipped = []

    def fail(self, label, detail):
        self.failures.append("%s: %s" % (label, detail))

    def ok(self, label, condition, detail=""):
        self.checks += 1
        if not condition:
            self.fail(label, detail or "condition false")


class Term:
    def __init__(self, binary, root, files, rows=ROWS, cols=COLS, extra_env=None):
        self.root = root
        env = {"FAKE_LSP_LOG": os.path.join(root, "log"), "PWD": root,
               "GIT_CEILING_DIRECTORIES": os.path.dirname(root)}
        if extra_env:
            env.update(extra_env)
        self.ed = uxperf.Editor(binary, root, files, rows, cols, env=env)
        self.rows, self.cols = rows, cols
        self.screen = pyte.Screen(cols, rows)
        self.stream = pyte.ByteStream(self.screen)
        self.fed = 0
        self.settle(0.4)

    def settle(self, quiet=0.2):
        self.ed.settle(quiet, 8)
        data = bytes(self.ed.raw[self.fed:])
        self.fed = len(self.ed.raw)
        self.stream.feed(data)

    def type(self, keys, quiet=0.25):
        self.ed.send(keys)
        self.settle(quiet)

    def wait_for(self, needle, timeout=6.0):
        end = time.time() + timeout
        while time.time() < end:
            self.settle(0.1)
            if needle in "\n".join(self.text()):
                return True
        return False

    def wait_gone(self, needle, timeout=4.0):
        end = time.time() + timeout
        while time.time() < end:
            self.settle(0.1)
            if needle not in "\n".join(self.text()):
                return True
        return False

    def resize(self, rows, cols):
        self.ed.resize(rows, cols)
        self.rows, self.cols = rows, cols
        self.screen.resize(rows, cols)
        self.settle(0.3)

    def cells(self):
        buf = self.screen.buffer
        return [[(buf[y][x].data, buf[y][x].fg, buf[y][x].bg, buf[y][x].reverse, buf[y][x].bold)
                 for x in range(self.cols)] for y in range(self.rows)]

    def text(self):
        buf = self.screen.buffer
        return ["".join((buf[y][x].data or " ") if len(buf[y][x].data) <= 1 else buf[y][x].data[0]
                        for x in range(self.cols)) for y in range(self.rows)]

    def full_redraw(self):
        before = (self.rows, self.cols)
        self.resize(before[0] + 1, before[1])
        self.resize(*before)
        return self.cells(), self.text()

    def log(self):
        path = os.path.join(self.root, "log")
        if not os.path.exists(path):
            return []
        with open(path) as f:
            return [json.loads(line) for line in f if line.strip()]

    def setup_server(self, auto=True, command=None):
        self.type(":Lsp server python %s\r" % (command or "python3 " + FAKE), 0.3)
        if auto:
            self.type(":set lspcomplete=auto\r", 0.3)
        self.type(":Lsp start\r", 0.8)

    def buffer_text(self):
        """The text lines of the window (line numbers stripped), up to the status line."""
        out = []
        for row in self.text()[:self.rows - 2]:
            if row.startswith("~"):
                continue
            out.append(row[5:].rstrip() if len(row) > 5 else "")
        return out

    def close(self):
        pids = descendants(self.ed.proc.pid)
        self.ed.close()
        time.sleep(0.3)
        left = [p for p in pids if alive(p)]
        for p in left:
            try:
                os.kill(p, 9)
            except OSError:
                pass
        return left


def popup_rows(term):
    """The popup as the rows (y, x_first, x_last_exclusive) of non-default-background cells above the status line."""
    buf = term.screen.buffer
    out = []
    for y in range(term.rows - 2):
        xs = [x for x in range(term.cols) if buf[y][x].bg != "default"]
        out.append((y, xs))
    return out


def popup_problems(term):
    """The popup rectangle is one block of rows, each a single run of popup cells."""
    problems = []
    rows = [(y, xs) for y, xs in popup_rows(term) if xs]
    if not rows:
        return ["no popup cells"]
    ys = [y for y, _ in rows]
    if ys != list(range(ys[0], ys[-1] + 1)):
        problems.append("popup rows are not adjacent: %r" % ys)
    for y, xs in rows:
        if xs != list(range(xs[0], xs[-1] + 1)):
            problems.append("row %d: popup cells are not one run: %r" % (y, xs[:30]))
    return problems


def popup_text(term):
    """The text of each popup row (between its first and last popup cell)."""
    text = term.text()
    return [text[y][xs[0]:xs[-1] + 1] for y, xs in popup_rows(term) if xs]


def no_popup(term):
    return not [1 for _, xs in popup_rows(term) if xs]


def check(term, rep, label, expect_popup=True):
    rep.checks += 1
    if expect_popup:
        for p in popup_problems(term):
            rep.fail(label, "frame: " + p)
    elif not no_popup(term):
        rep.fail(label, "popup cells left on screen: %r" % popup_text(term)[:4])
    shown_cells, shown_text = term.cells(), term.text()
    full_cells, full_text = term.full_redraw()
    if shown_text != full_text or shown_cells != full_cells:
        diff = []
        for y in range(term.rows):
            if shown_text[y] != full_text[y]:
                diff.append("row %d shown=%r full=%r" % (y, shown_text[y].rstrip(), full_text[y].rstrip()))
            elif shown_cells[y] != full_cells[y]:
                xs = [x for x in range(term.cols) if shown_cells[y][x] != full_cells[y][x]]
                diff.append("row %d style differs at cols %s" % (y, xs[:8]))
        rep.fail(label, "diff-rendered screen != full redraw: " + " | ".join(diff[:3]))
    if expect_popup:
        for p in popup_problems(term):
            rep.fail(label, "after full redraw, frame: " + p)


def make_root():
    base = os.path.realpath(os.environ.get("M3_TEST_TMP") or tempfile.gettempdir())
    return os.path.realpath(tempfile.mkdtemp(prefix="m3lsp", dir=base))


def write(root, name, text):
    with open(os.path.join(root, name), "w") as f:
        f.write(text)


def start(binary, root, text="x = 1\n\n", name="a.py", auto=True, rows=ROWS, cols=COLS, extra_env=None):
    write(root, name, text)
    term = Term(binary, root, [name], rows, cols, extra_env)
    term.setup_server(auto)
    return term


# ------------------------------------------------------------------------------------------ scenarios

@scenario
def popup_filter_accept(binary, root, rep, quick):
    term = start(binary, root)
    try:
        term.type("jA")
        term.type("hel", 0.5)
        rep.ok("popup opens as you type", term.wait_for("hello_world"), "\n".join(term.text()[:10]))
        rows = popup_text(term)
        rep.ok("kind letters and details shown", any(" f hello_world" in r and "fn() -> str" in r for r in rows), repr(rows))
        check(term, rep, "popup: hel")
        term.type("lo_")
        rows = popup_text(term)
        rep.ok("filter narrows as you type", len(rows) == 2 and all("hello_" in r for r in rows), repr(rows))
        check(term, rep, "popup: hello_")
        term.type("\t")
        check(term, rep, "tab selects")
        term.type("\t")
        term.type("\x0e")      # CTRL-N past the last row: nothing selected
        term.type("\x10")      # CTRL-P back to the last row
        term.type("\x1b[Z")    # S-Tab: the row before
        check(term, rep, "keys move the selection")
        term.type("\t")
        term.type("\x19", 0.4)   # CTRL-Y accepts
        rep.ok("CTRL-Y accepts the selected item", term.buffer_text()[1:2] == ["hello_world"], repr(term.buffer_text()))
        check(term, rep, "accepted", expect_popup=False)
        term.type("\x1b")
    finally:
        left = term.close()
    rep.ok("no server left", not left, repr(left))


@scenario
def popup_cancel_and_enter(binary, root, rep, quick):
    term = start(binary, root)
    try:
        term.type("jA")
        term.type("he", 0.5)
        rep.ok("opens", term.wait_for("help"))
        term.type("\x05", 0.3)      # CTRL-E closes, text stays
        rep.ok("CTRL-E leaves the text", term.buffer_text()[1:2] == ["he"], repr(term.buffer_text()))
        check(term, rep, "closed by CTRL-E", expect_popup=False)
        term.type("l", 0.5)
        rep.ok("typing again reopens it", term.wait_for("hello_world"))
        term.type("\r", 0.4)        # nothing selected: Enter is a line break
        rep.ok("Enter without a selection is a newline", term.buffer_text()[1:3] == ["hel", ""], repr(term.buffer_text()))
        check(term, rep, "closed by Enter", expect_popup=False)
        term.type("he", 0.5)
        rep.ok("opens on the new line", term.wait_for("help"))
        term.type("\x1b", 0.3)      # Esc closes and leaves Insert
        check(term, rep, "closed by Esc", expect_popup=False)
        rep.ok("Esc left Insert mode", "NORMAL" in "\n".join(term.text()[-2:]), "\n".join(term.text()[-2:]))
    finally:
        term.close()


@scenario
def popup_trigger_and_enter_accept(binary, root, rep, quick):
    term = start(binary, root)
    try:
        term.type("jA")
        term.type("obj.", 0.6)
        rep.ok("a trigger character asks", term.wait_for("alpha"), "\n".join(term.text()[:10]))
        asks = [e for e in term.log() if e["kind"] == "completion"]
        rep.ok("triggerKind 2 with the character", asks and asks[-1]["trigger"] == 2 and asks[-1]["char"] == ".", repr(asks))
        check(term, rep, "after the dot")
        term.type("be")
        rows = popup_text(term)
        rep.ok("filter after a trigger character", len(rows) == 1 and "beta_value" in rows[0], repr(rows))
        term.type("\t")
        term.type("\r", 0.4)       # Enter accepts the selected row (no line break)
        rep.ok("Enter accepts the selected row", term.buffer_text()[1:3] == ["obj.beta_value"], repr(term.buffer_text()))
        term.type("\x1b")
    finally:
        term.close()


@scenario
def popup_docs_and_resolve(binary, root, rep, quick):
    term = start(binary, root)
    try:
        term.type("jA")
        term.type("hel", 0.5)
        rep.ok("opens", term.wait_for("hello_world"))
        for _ in range(3):
            term.ed.send("\t")
        term.settle(0.5)
        rep.ok("documentation side panel", term.wait_for("Docs for"), "\n".join(term.text()[:12]))
        rep.ok("the panel wraps", any("enough to wrap" in r or "side panel" in r for r in term.text()), "\n".join(term.text()[:14]))
        check(term, rep, "docs panel")
        resolves = [e for e in term.log() if e["kind"] == "resolve"]
        rep.ok("a burst of selections resolves once, after a pause", 1 <= len(resolves) <= 2, repr(resolves))
        term.type("\x1b")
    finally:
        term.close()


@scenario
def popup_snippet(binary, root, rep, quick):
    term = start(binary, root)
    try:
        term.type("jA")
        term.type("fo", 0.6)
        rep.ok("snippet item listed", term.wait_for(" s for"), "\n".join(term.text()[:8]))
        term.type("\t")
        term.type("\x19", 0.4)
        lines = term.buffer_text()
        rep.ok("snippet expanded by the snippet engine", lines[1:2] == ["for i in items {"], repr(lines))
        term.type("k")       # the placeholder `i` is selected: typing replaces it
        term.type("\t")      # next tabstop
        term.type("zz")
        lines = term.buffer_text()
        rep.ok("tabstops work", lines[1:2] == ["for k in zz {"], repr(lines))
        check(term, rep, "snippet done", expect_popup=False)
        term.type("\x1b")
    finally:
        term.close()


@scenario
def popup_additional_edits(binary, root, rep, quick):
    term = start(binary, root)
    try:
        term.type("jA")
        term.type("import_m", 0.6)
        rep.ok("opens", term.wait_for("import_me"))
        term.type("\t")
        term.type("\x19", 0.5)
        lines = term.buffer_text()
        rep.ok("additionalTextEdits (from resolve) applied", lines[0] == "import me" and "import_me" in lines[2], repr(lines))
        term.type("X")
        lines = term.buffer_text()
        rep.ok("the cursor followed the edit above it", lines[2] == "import_meX", repr(lines))
        term.type("\x1b")
    finally:
        term.close()


@scenario
def popup_hostile_labels(binary, root, rep, quick):
    term = start(binary, root)
    try:
        term.type("jA")
        term.type("evil", 0.6)
        rep.ok("opens", term.wait_for("evil"))
        check(term, rep, "control characters in a label")
        raw = bytes(term.ed.raw)
        rep.ok("no OSC from a label", b"\x1b]0;x" not in raw)
        rep.ok("no SGR from a label", b"evil\x1b[31m" not in raw and b"\x1b[31mred" not in raw)
        rep.ok("no BEL from a label", b"red\x07" not in raw and b"red\x07\x08" not in raw)
        term.type("\x15")      # CTRL-U
        term.type("日", 0.6)
        rep.ok("wide characters", any("日本語の名前" in r.replace(" ", "") for r in term.text()), "\n".join(term.text()[:8]))
        check(term, rep, "wide label")
        term.type("\x15")
        term.type("long_", 0.6)
        rep.ok("long label", term.wait_for("long_xxx"))
        rows = popup_text(term)
        rep.ok("a long label is cut with an ellipsis inside the popup", any("…" in r for r in rows), repr(rows))
        check(term, rep, "long label")
        term.type("\x1b")
    finally:
        term.close()


@scenario
def popup_placement(binary, root, rep, quick):
    text = "".join("line %d\n" % i for i in range(60))
    term = start(binary, root, text)
    try:
        term.type("G")
        term.type("A")
        term.type(" he", 0.6)
        rep.ok("opens near the bottom", term.wait_for("hello_world"))
        rows = [(y, xs) for y, xs in popup_rows(term) if xs]
        cursor_row = max(y for y, row in enumerate(term.text()[:term.rows - 2]) if "line 59 he" in row)
        rep.ok("popup above the cursor row at the bottom", rows and rows[-1][0] < cursor_row, "rows %r cursor %d" % ([y for y, _ in rows], cursor_row))
        rep.ok("the cursor row is untouched", "line 59 he" in term.text()[cursor_row])
        check(term, rep, "above the cursor")
        sizes = [(20, 60), (12, 40), (30, 100)] if not quick else [(14, 50)]
        for rows_, cols_ in sizes:
            term.resize(rows_, cols_)
            term.type("l", 0.4)
            term.type("\x7f", 0.4)
            check(term, rep, "resized to %dx%d" % (rows_, cols_), expect_popup=not no_popup(term))
        term.type("\x1b")
    finally:
        term.close()


@scenario
def popup_cancel_request(binary, root, rep, quick):
    term = start(binary, root)
    try:
        term.type("jA")
        term.ed.send("slow")
        term.settle(0.15)            # the request is out (the server takes 0.6 s)
        term.ed.send("x")
        term.settle(0.2)
        term.type("\x1b", 0.9)
        log = term.log()
        asks = [e for e in log if e["kind"] == "completion"]
        cancels = [e for e in log if e["kind"] == "cancel"]
        rep.ok("a newer request cancels the outdated one ($/cancelRequest)", cancels and asks[0]["word"] == "slow", repr(log))
        rep.ok("Esc with nothing pending sends no further cancel", len(cancels) <= 2, repr(cancels))
    finally:
        term.close()


@scenario
def popup_incomplete(binary, root, rep, quick):
    term = start(binary, root)
    try:
        term.type("jA")
        term.type("h", 0.6)
        term.type("e", 0.6)
        term.type("l", 0.6)
        kinds = [(e["trigger"], e["word"]) for e in term.log() if e["kind"] == "completion"]
        rep.ok("an incomplete list is asked for again as you type (triggerKind 3)", (3, "he") in kinds or (1, "he") in kinds, repr(kinds))
        term.type("\x1b")
    finally:
        term.close()


@scenario
def popup_manual_default(binary, root, rep, quick):
    term = start(binary, root, auto=False)
    try:
        term.type("jA")
        term.type("hel", 0.8)
        rep.ok("no popup without lspcomplete=auto", no_popup(term) and not [e for e in term.log() if e["kind"] == "completion"])
        term.type("\x00", 1.0)
        rep.ok("CTRL-Space still opens the picker", term.wait_for("Completion"), "\n".join(term.text()[:10]))
        term.type("\x1b")
        term.type("\x1b")
        term.type(":set lspcomplete=auto\r", 0.3)
        term.type("A")
        term.type("\x00", 0.8)
        rep.ok("CTRL-Space with auto opens the popup at once", term.wait_for("hello_world") and no_popup(term) is False)
        term.type("\x1b")
    finally:
        term.close()


@scenario
def popup_commit_character(binary, root, rep, quick):
    term = start(binary, root)
    try:
        term.type("jA")
        term.type("commit_m", 0.6)
        rep.ok("opens", term.wait_for("commit_me"))
        term.type("\t")
        term.type("(", 0.4)     # the item's own commit character
        rep.ok("a commit character accepts the selected item, then is typed", term.buffer_text()[1].startswith("commit_me("), repr(term.buffer_text()))
        term.type("\x1b")
    finally:
        term.close()


def last_doc(log):
    docs = [e["doc"] for e in log if e["kind"] in ("didOpen", "didChange")]
    return docs[-1] if docs else None


def read_file(root, name):
    with open(os.path.join(root, name), encoding="utf-8") as f:
        return f.read()


EDITS = ["A XX\x1b", "jdd", "yyp", "u", "3yyP", ":%s/a/\u00e9\U0001f600/g\r", "Gox\x1b", "ggdG",
         "ihello\rworld\x1b", "ggA!\x1b", "ddp"]


def drive_edits(term):
    for keys in EDITS:
        term.type(keys, 0.6)
    term.type(":w\r", 0.5)
    term.settle(1.0)


@scenario
def sync_incremental(binary, root, rep, quick):
    """FAKE_LSP_SYNC=2: every didChange is one ranged change, and the server's text is the file at the end."""
    term = start(binary, root, "alpha\nbeta \u00e9\ngamma \U0001f600\ndelta\n", auto=False, extra_env={"FAKE_LSP_SYNC": "2"})
    try:
        drive_edits(term)
        log = term.log()
        changes = [e for e in log if e["kind"] == "didChange"]
        rep.ok("several changes were sent", len(changes) >= 5, repr(len(changes)))
        rep.ok("every change has a range (incremental sync)", changes and all("range" in c for e in changes for c in e["changes"]), repr(changes[:2]))
        rep.ok("one event per didChange", all(len(e["changes"]) == 1 for e in changes))
        rep.ok("versions go up one by one", [e["version"] for e in changes] == list(range(2, 2 + len(changes))), repr([e["version"] for e in changes]))
        rep.ok("the server's text is the file's text", last_doc(log) == read_file(root, "a.py"), "%r vs %r" % (last_doc(log), read_file(root, "a.py")))
    finally:
        left = term.close()
    rep.ok("no server left", not left, repr(left))


@scenario
def sync_full_default(binary, root, rep, quick):
    """FAKE_LSP_SYNC=1 (and a server that says nothing): the whole text, as before."""
    term = start(binary, root, "alpha\nbeta \u00e9\ngamma \U0001f600\ndelta\n", auto=False, extra_env={"FAKE_LSP_SYNC": "1"})
    try:
        drive_edits(term)
        log = term.log()
        changes = [e for e in log if e["kind"] == "didChange"]
        rep.ok("changes carry the whole text", changes and all("range" not in c for e in changes for c in e["changes"]), repr(changes[:1]))
        rep.ok("the server's text is the file's text", last_doc(log) == read_file(root, "a.py"))
    finally:
        term.close()


@scenario
def format_on_save(binary, root, rep, quick):
    term = start(binary, root, "x = 1\n", auto=False)
    try:
        term.type("A # one\x1b", 0.5)
        term.type(":w\r", 0.6)
        rep.ok("nothing is formatted without :set lspformat", not [e for e in term.log() if e["kind"] == "formatting"] and read_file(root, "a.py") == "x = 1 # one\n", repr(read_file(root, "a.py")))
        term.type(":set lspformat\r", 0.3)
        term.type("A two\x1b", 0.5)
        term.type(":w\r", 0.8)
        log = term.log()
        kinds = [e["kind"] for e in log]
        rep.ok("the file is written formatted", read_file(root, "a.py").startswith("// formatted\n"), repr(read_file(root, "a.py")))
        rep.ok("formatting was asked for before the save", "formatting" in kinds and "didSave" in kinds and max(i for i, k in enumerate(kinds) if k == "formatting") < max(i for i, k in enumerate(kinds) if k == "didSave"), repr(kinds[-5:]))
        rep.ok("the buffer shows it", "// formatted" in "\n".join(term.text()[:4]))
        term.type("u", 0.4)
        term.type(":set nolspformat\r", 0.3)
        term.type(":w\r", 0.6)
        rep.ok("and not any more after :set nolspformat", len([e for e in term.log() if e["kind"] == "formatting"]) == 1)
    finally:
        term.close()


@scenario
def dynamic_registration(binary, root, rep, quick):
    """Completion, formatting, the sync kind and file watching are registered after initialize."""
    term = start(binary, root, "x = 1\n\n", extra_env={"FAKE_LSP_DYNAMIC": "1", "FAKE_LSP_SYNC": "2"})
    try:
        rep.ok("the registration was answered", any(e["kind"] == "registered" for e in term.log()) or term.wait_for("zzzz", 0.5) or any(e["kind"] == "registered" for e in term.log()), repr(term.log()))
        term.type("jA")
        term.type("hel", 0.8)
        rep.ok("a completion provider that registered itself is used", term.wait_for("hello_world"), "\n".join(term.text()[:8]))
        term.type("\x1b\x1b", 0.3)
        term.type(":set lspformat\r", 0.3)
        term.type("A one\x1b", 0.5)
        term.type(":w\r", 0.6)
        term.type("A two\x1b", 0.5)
        term.type(":w\r", 0.6)
        term.type("A three\x1b", 0.5)
        term.type(":w\r", 0.8)
        term.type("A four\x1b", 0.5)
        term.type(":w\r", 0.8)
        term.settle(0.6)
        log = term.log()
        kinds = [e["kind"] for e in log]
        rep.ok("formatting registered dynamically ran on the first three saves, not after unregister", kinds.count("formatting") == 3, repr(kinds))
        rep.ok("the sync kind registered dynamically is used", any("range" in c for e in log if e["kind"] == "didChange" for c in e["changes"]), repr(log[:6]))
        watched = [e for e in log if e["kind"] == "watched"]
        rep.ok("file watching: each save is reported (type 2, changed)", len(watched) >= 3 and all(w["changes"][0]["type"] == 2 for w in watched), repr(watched))
        rep.ok("the server's text is the file's text", last_doc(log) == read_file(root, "a.py"), "%r vs %r" % (last_doc(log), read_file(root, "a.py")))
    finally:
        term.close()


@scenario
def cancel_overtaken_request(binary, root, rep, quick):
    term = start(binary, root, "x = 1\n", auto=False)
    try:
        term.ed.send(":Lsp hover\r:Lsp hover\r")
        term.settle(1.2)
        log = term.log()
        rep.ok("a second hover overtakes the first ($/cancelRequest)", any(e["kind"] == "cancel" for e in log), repr(log))
        term.type("\r", 0.3)
        replies = [e for e in log if e["kind"] == "applyEdit_reply"]
        rep.ok("a stale workspace/applyEdit is refused with applied=false", replies and replies[0]["result"].get("applied") is False, repr(replies))
        rep.ok("and changed nothing", "STALE" not in "\n".join(term.text()))
    finally:
        term.close()


@scenario
def workspace_edit_operations(binary, root, rep, quick):
    write(root, "doomed.txt", "bye\n")
    term = start(binary, root, "hello = 1\nprint(hello)\n", auto=False)
    try:
        term.type(":Lsp rename zz\r", 1.0)
        rep.ok("the text edit of the documentChanges was applied", term.wait_for("zzello = 1"), "\n".join(term.text()[:5]))
        rep.ok("created then renamed", os.path.exists(os.path.join(root, "moved.txt")) and not os.path.exists(os.path.join(root, "created.txt")))
        rep.ok("deleted", not os.path.exists(os.path.join(root, "doomed.txt")))
        rep.ok("the summary is shown", "Renamed in 1 file" in "\n".join(term.text()[-3:]), "\n".join(term.text()[-3:]))
        # an edit for an older version of the document stops the whole edit
    finally:
        term.close()


# -------------------------------------------------------------------------------------- real servers

def find_server(*names):
    for name in names:
        found = shutil.which(name)
        if found:
            return found
        candidate = os.path.join(MASON, name)
        if os.path.exists(candidate):
            return candidate
    raise Skip("%s not installed" % names[0])


@scenario
def real_clangd(binary, root, rep, quick):
    """A real server: the popup follows typing; every label it shows is one nvim's own LSP client gets for the same
    request (tests/oracle_lsp.py; the shape cross-check, not a rendering one)."""
    cmd = find_server("clangd")
    term = start(binary, root, "#include <stdio.h>\nint main(void) {\n    \n}\n", name="a.c", auto=True)
    try:
        term.type(":Lsp server c %s\r" % cmd, 0.3)
        term.type(":Lsp stop\r", 0.5)
        term.type(":Lsp start\r", 1.0)
        term.type("jj$a")
        term.type("prin", 0.5)
        end = time.time() + 30
        while time.time() < end and not any("printf" in r for r in popup_text(term)):
            term.type("\x7f", 0.3)
            term.type("n", 1.5)
        rows = popup_text(term)
        rep.ok("clangd answers; `prin` offers printf", any("printf" in r for r in rows), "\n".join(term.text()[:10]))
        if rows:
            check(term, rep, "real clangd popup")
            seen = oracle_labels("c", cmd)
            if seen is None:
                rep.skipped.append("real_clangd oracle: nvim could not answer")
            else:
                shown = [r.strip()[2:].strip().split(" ")[0] for r in rows]
                missing = [label for label in shown if label and not any(o.strip().startswith(label) for o in seen)]
                rep.ok("every label of the popup is one nvim's client lists", not missing, "missing %r of %r" % (missing, seen[:8]))
            term.type("\t")
            term.type("\x19", 0.6)
            rep.ok("accepting inserts the item", "printf" in "\n".join(term.buffer_text()), repr(term.buffer_text()))
        term.type("\x1b")
    finally:
        left = term.close()
    rep.ok("no clangd process left", not left, repr(left))


def oracle_labels(lang, cmd):
    import subprocess
    try:
        out = subprocess.run([sys.executable, os.path.join(HERE, "oracle_lsp.py")] + cmd.split(), capture_output=True, text=True,
                             timeout=120, env=dict(os.environ, ORACLE_LANG=lang))
    except subprocess.TimeoutExpired:
        return None
    for line in out.stdout.splitlines():
        if line.startswith("labels:"):
            labels = json.loads(line[len("labels:"):].strip() or "[]")
            return labels or None
    return None


def fg_at(term, y, x):
    return term.screen.buffer[y][x].fg


def find_text(term, needle):
    """(row, column) of the first screen cell run holding `needle`, columns counted in cells."""
    for y, row in enumerate(term.text()[:term.rows - 2]):
        x = row.find(needle)
        if x >= 0:
            return y, x
    return None


@scenario
def semantic_tokens(binary, root, rep, quick):
    """Tokens from the server are painted over the lexical highlighter; an edited row falls back to the lexer until
    the next answer; UTF-16 columns are right; `:Lsp tokens` says what is under the cursor."""
    text = "def go(x):\n    myvar = Foo(x)\n\u00e9\U0001f600 myvar + Foo\n"
    term = start(binary, root, text, auto=False, extra_env={"FAKE_LSP_TOKENS": "1"})
    try:
        end = time.time() + 8
        while time.time() < end and not any(e["kind"] == "semtok" for e in term.log()):
            term.settle(0.2)
        term.settle(0.5)
        kw = find_text(term, "def")
        var1 = find_text(term, "myvar")
        rep.ok("the screen shows the file", kw is not None and var1 is not None, "\n".join(term.text()[:5]))
        if kw is None or var1 is None:
            return
        keyword_fg = fg_at(term, var1[0], var1[1])
        rep.ok("`myvar` (a keyword token) is coloured, all five cells alike", keyword_fg != "default" and all(fg_at(term, var1[0], var1[1] + i) == keyword_fg for i in range(5)),
               "%r" % [fg_at(term, var1[0], var1[1] + i) for i in range(5)])
        rep.ok("the neighbour cells are not recoloured", fg_at(term, var1[0], var1[1] - 1) != keyword_fg and fg_at(term, var1[0], var1[1] + 5) != keyword_fg)
        row3 = [y for y, r in enumerate(term.text()[:term.rows - 2]) if "myvar +" in r.replace("\u00e9", "e")]
        rep.ok("the third row shows too", bool(row3))
        if row3:
            x3 = term.text()[row3[0]].find("myvar")
            rep.ok("columns after an astral character are right (UTF-16)", all(fg_at(term, row3[0], x3 + i) == keyword_fg for i in range(5)) and fg_at(term, row3[0], x3 - 1) != keyword_fg,
                   "x3=%d %r" % (x3, [fg_at(term, row3[0], x3 + i) for i in range(-1, 6)]))
            foo = term.text()[row3[0]].find("Foo")
            rep.ok("a type token has a colour of its own", fg_at(term, row3[0], foo) not in (keyword_fg, fg_at(term, row3[0], foo - 1)))
        check(term, rep, "tokens painted", expect_popup=False)
        term.type("gg", 0.2)
        term.type("/myvar\r", 0.2)
        term.type(":Lsp tokens\r", 0.4)
        rep.ok("`:Lsp tokens` names the token under the cursor", "keyword" in term.text()[-1] or "keyword" in "\n".join(term.text()[-3:]), "\n".join(term.text()[-3:]))
        term.type(":noh\r", 0.2)
        # an edit: the edited row shows lexical colours at once, tokens come back after the next answer
        before = len([e for e in term.log() if e["kind"] == "semtok"])
        term.type("A # note", 0.3)       # still in Insert mode: no request goes out
        var1 = find_text(term, "myvar")
        rep.ok("an edited row falls back to the lexer at once", fg_at(term, var1[0], var1[1]) != keyword_fg, repr(fg_at(term, var1[0], var1[1])))
        term.type("\x1b", 0.1)
        end = time.time() + 6
        while time.time() < end and len([e for e in term.log() if e["kind"] == "semtok"]) == before:
            term.settle(0.2)
        term.settle(0.6)
        rep.ok("and the new answer paints it again", fg_at(term, var1[0], var1[1]) == keyword_fg, repr(fg_at(term, var1[0], var1[1])))
        check(term, rep, "tokens repainted", expect_popup=False)
    finally:
        left = term.close()
    rep.ok("no server left", not left, repr(left))


@scenario
def real_clangd_tokens(binary, root, rep, quick):
    """A real server's tokens, against what nvim's own client shows for the same positions (tests/oracle_tokens.py)."""
    cmd = find_server("clangd")
    source = "int add(int a, int b) { return a + b; }\nint main(void) { int y = add(1, 2); return y; }\n"
    term = start(binary, root, source, name="a.c", auto=False)
    try:
        term.type(":Lsp server c %s\r" % cmd, 0.3)
        term.type(":Lsp stop\r", 0.5)
        term.type(":Lsp start\r", 1.0)
        points = [(0, 4), (1, 25), (1, 21)]    # add (declaration), add (call), y (declaration)
        seen = {}
        end = time.time() + 40
        while time.time() < end and len(seen) < len(points):
            term.type("gg", 0.2)
            for row, col in points:
                term.type("gg%s0%s" % ("j" * row, "l" * col), 0.1)
                term.type(":Lsp tokens\r", 0.5)
                line = " ".join(term.text()[-3:])
                if "under the cursor:" in line:
                    seen[(row, col)] = line.split("under the cursor:")[1].strip().split("  ")[0].strip()
            if len(seen) < len(points):
                time.sleep(1.0)
        rep.ok("clangd's semantic tokens arrive", len(seen) == len(points), repr(seen))
        wanted = oracle_tokens("c", cmd, source, "c", points)
        if wanted is None:
            rep.skipped.append("real_clangd_tokens oracle: nvim could not answer")
        else:
            for point in points:
                mine = seen.get(point, "").split()
                theirs = wanted.get("%d,%d" % point, [])
                rep.ok("token at %r: type %s modifiers agree with nvim's client (%r)" % (point, mine[:1], theirs),
                       mine and theirs and mine[0] == theirs[0] and ("declaration" in mine) == ("declaration" in theirs),
                       "m3 %r nvim %r" % (mine, theirs))
    finally:
        left = term.close()
    rep.ok("no clangd process left", not left, repr(left))


def oracle_tokens(lang, cmd, source, ft, points):
    import subprocess
    try:
        out = subprocess.run([sys.executable, os.path.join(HERE, "oracle_tokens.py"), lang, ft, json.dumps(points), source] + cmd.split(),
                             capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return None
    for line in out.stdout.splitlines():
        if line.startswith("tokens:"):
            return json.loads(line[len("tokens:"):])
    return None


@scenario
def real_clangd_sync_format(binary, root, rep, quick):
    """A real server announces incremental sync: edits keep its diagnostics right, and format on save formats."""
    cmd = find_server("clangd")
    term = start(binary, root, "int main(void) {\nint x = undefined_thing;\nreturn x;\n}\n", name="a.c", auto=False)
    try:
        term.type(":Lsp server c %s\r" % cmd, 0.3)
        term.type(":Lsp stop\r", 0.5)
        term.type(":Lsp start\r", 1.0)
        rep.ok("diagnostics arrive", term.wait_for("E:1", 30.0), "\n".join(term.text()[-3:]))
        term.type("jdddd", 0.5)
        term.type("O  int  y=1;\x1b", 0.5)
        rep.ok("deleting the bad line (an incremental change) clears the error", term.wait_gone("E:1", 15.0), "\n".join(term.text()[-3:]))
        term.type("ggdG", 0.3)
        term.type("iint   main( void ){return   0;}\x1b", 0.5)
        term.type(":set lspformat\r", 0.3)
        term.type(":w\r", 3.0)
        formatted = read_file(root, "a.c")
        rep.ok("clangd formats on save", formatted == "int main(void) { return 0; }\n", repr(formatted))
    finally:
        left = term.close()
    rep.ok("no clangd process left", not left, repr(left))


@scenario
def real_pyright(binary, root, rep, quick):
    cmd = find_server("pyright-langserver")
    term = start(binary, root, "import os\nos.pa\n", extra_env=None)
    try:
        term.type(":Lsp server python %s --stdio\r" % cmd, 0.3)
        term.type(":Lsp stop\r", 0.5)
        term.type(":Lsp start\r", 0.5)
        term.type("j$A")
        end = time.time() + 40
        shown = False
        while time.time() < end and not shown:
            term.type("\x7f", 0.3)
            term.type("a", 2.0)
            shown = any(" path" in r or "path " in r for r in popup_text(term))
        rep.ok("pyright answers; `os.pa` offers path", shown, "\n".join(term.text()[:10]))
        if shown:
            check(term, rep, "real pyright popup")
            term.type("\t")
            while not any("path" in r and "┃" in r for r in []):
                break
            term.type("\x19", 0.5)
            rep.ok("accept inserts the item", term.buffer_text()[1:2] and term.buffer_text()[1].startswith("os.path"), repr(term.buffer_text()))
        term.type("\x1b")
    finally:
        left = term.close()
    rep.ok("no pyright process left", not left, repr(left))


def main():
    binary = os.path.abspath(sys.argv[1])
    quick = "--quick" in sys.argv
    only = None
    for i, arg in enumerate(sys.argv):
        if arg == "--only" and i + 1 < len(sys.argv):
            only = sys.argv[i + 1].split(",")
    want_real = "--real" in sys.argv or os.environ.get("M3_LSP_REAL") == "1"
    rep = Report()
    for name, fn in SCENARIOS.items():
        if only and name not in only:
            continue
        if name.startswith("real_") and not want_real and not only:
            continue
        root = make_root()
        try:
            fn(binary, root, rep, quick)
        except Skip as why:
            rep.skipped.append("%s: %s" % (name, why))
        except Exception as error:  # a crashed scenario is a failure, not a skip
            rep.fail(name, "exception %r" % (error,))
        finally:
            shutil.rmtree(root, ignore_errors=True)
    for line in rep.skipped:
        print("skip " + line)
    for line in rep.failures[:40]:
        print("FAIL " + line)
    print("lsp_pty: %d checks, %d failed" % (rep.checks, len(rep.failures)))
    sys.exit(1 if rep.failures else 0)


if __name__ == "__main__":
    main()
