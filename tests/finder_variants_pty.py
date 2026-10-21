#!/usr/bin/env python3
"""The finder's typing sequence on terminals that measure text differently (docs/FINDER.md).

    python3 tests/finder_variants_pty.py ./m3 [--quick]

Linux emulators agreed with the renderer and real Macs did not, so this replays what m3 writes on
several kinds of terminal. Over a tree whose names hold what terminals disagree on (text emoji
with U+FE0F, keycaps, ZWJ sequences, flags, Devanagari, halfwidth katakana, arrows, Nerd Font
glyphs, emoji newer than a terminal's tables) it opens the finder (Space f f), types p, o, m,
erases, retypes, moves the selection, resizes, and after every step compares the screen each
terminal shows with the screen a from-scratch repaint gives on that same terminal (the repaint is
what a resize writes: it begins with a screen clear).

The terminals are pyte (xterm pending wrap, characters measured one code point at a time,
which is Terminal.app's way: a family is 6 columns, a text emoji with U+FE0F is 1) with
`pyte.screens.wcwidth` swapped for another table: pyte itself, ambiguous characters wide, private use
wide, emoji newer than the table narrow, old astral pictographs narrow, jamo added up, regional
indicators wide. Skips with a note when pyte is missing.
"""
import os
import sys
import tempfile
import shutil
import unicodedata

try:
    import pyte
    import pyte.screens
except ImportError:
    print("skip finder_variants_pty: pyte is not installed")
    sys.exit(0)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "bench"))
sys.path.insert(0, HERE)
import uxperf  # noqa: E402

ROWS, COLS = 30, 100

NAMES = [
    "pom.xml",
    "poxm.txt",
    "po_plain.txt",
    "warn_⚠️_pom.md",
    "heart_❤️_pom_✔️.md",
    "keycap_1️⃣_pom.txt",
    "family_\U0001f468‍\U0001f469‍\U0001f467_pom.txt",
    "flag_\U0001f1e9\U0001f1ea_pom.txt",
    "skin_\U0001f44d\U0001f3fd_pom.txt",
    "dev_कि_नमस्ते_pom.txt",
    "kana_ｶﾞ_pom.txt",
    "arrow_→_▸_pom.txt",
    "nerd___pom.txt",
    "new_\U0001faa8_\U0001fae8_pom.txt",
    "cjk_中文_한글_pom.txt",
    "combining_é_ä_pom.txt",
    "thai_สวัสดี_pom.txt",
    "a_very_long_name_pom_" + "x" * 90 + ".txt",
    "dir/inner/pom.xml",
    "dir/inner/" + "z" * 60 + "⚠️" * 8 + "_pom.txt",
]
for i in range(40):
    NAMES.append("src/ui/module_%02d.m31" % i)


def make_tree(root):
    for name in NAMES:
        path = os.path.join(root, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        body = ("line ⚠️ text ❤️ more \U0001f468‍\U0001f469‍\U0001f467 end\n" * 12
                + "plain line\n" * 8)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)


# --- the terminals -------------------------------------------------------------------------

_pyte_width = pyte.screens.wcwidth


def _ambiguous(ch):
    code = ord(ch)
    if 0x2500 <= code <= 0x259F:
        return False
    return unicodedata.east_asian_width(ch) == "A"


def width_ambiguous_wide(ch):
    return 2 if _ambiguous(ch) else _pyte_width(ch)


def width_private_wide(ch):
    return 2 if 0xE000 <= ord(ch) <= 0xF8FF else _pyte_width(ch)


def width_new_emoji_narrow(ch):
    return 1 if 0x1FA70 <= ord(ch) <= 0x1FAFF else _pyte_width(ch)


def width_astral_narrow(ch):
    w = _pyte_width(ch)
    return 1 if (0x1F300 <= ord(ch) <= 0x1F64F and w == 2) else w


def width_jamo_added(ch):
    return 2 if 0x1100 <= ord(ch) <= 0x11FF else _pyte_width(ch)


def width_regional_wide(ch):
    return 2 if 0x1F1E6 <= ord(ch) <= 0x1F1FF else _pyte_width(ch)


VARIANTS = [
    ("pyte (code points added up, text emoji 1 column)", _pyte_width),
    ("ambiguous-wide", width_ambiguous_wide),
    ("private-wide", width_private_wide),
    ("new-emoji-narrow", width_new_emoji_narrow),
    ("astral-narrow", width_astral_narrow),
    ("jamo-added", width_jamo_added),
    ("regional-wide", width_regional_wide),
]


class Screens:
    """One pyte screen per terminal, fed the same bytes."""

    def __init__(self, rows, cols):
        self.rows, self.cols = rows, cols
        self.items = []
        for name, width in VARIANTS:
            screen = pyte.Screen(cols, rows)
            self.items.append((name, width, screen, pyte.ByteStream(screen)))

    def feed(self, data):
        for name, width, screen, stream in self.items:
            pyte.screens.wcwidth = width
            try:
                stream.feed(data)
            finally:
                pyte.screens.wcwidth = _pyte_width

    def resize(self, rows, cols):
        self.rows, self.cols = rows, cols
        for name, width, screen, stream in self.items:
            screen.resize(rows, cols)


def cells(screen, rows, cols):
    buf = screen.buffer
    return [[(buf[y][x].data, buf[y][x].fg, buf[y][x].bg, buf[y][x].reverse) for x in range(cols)]
            for y in range(rows)]


def text(screen, rows, cols):
    buf = screen.buffer
    return ["".join(buf[y][x].data or " " for x in range(cols)) for y in range(rows)]


class Session:
    def __init__(self, binary, root, rows=ROWS, cols=COLS):
        self.ed = uxperf.Editor(binary, root, [], rows, cols, keymap="NONE")
        self.rows, self.cols = rows, cols
        self.screens = Screens(rows, cols)
        self.fed = 0
        self.settle()

    def take(self):
        data = bytes(self.ed.raw[self.fed:])
        self.fed = len(self.ed.raw)
        return data

    def settle(self, quiet=0.15):
        self.ed.settle(quiet, 6)
        self.screens.feed(self.take())

    def type(self, keys, quiet=0.15):
        self.ed.send(keys)
        self.settle(quiet)

    def resize(self, rows, cols):
        self.ed.resize(rows, cols)
        self.rows, self.cols = rows, cols
        self.screens.resize(rows, cols)
        self.settle(0.25)

    def repaint(self):
        """What a from-scratch repaint of the current state gives on each terminal: the bytes
        written after a resize away and back, applied to a new screen."""
        rows, cols = self.rows, self.cols
        self.ed.resize(rows + 1, cols)
        self.ed.settle(0.25, 6)
        self.take()
        self.ed.resize(rows, cols)
        self.ed.settle(0.25, 6)
        data = self.take()
        fresh = Screens(rows, cols)
        fresh.feed(data)
        return fresh

    def close(self):
        self.ed.close()


class Report:
    def __init__(self):
        self.failures = []
        self.checks = 0


def check(session, rep, label):
    """Compare every terminal's screen with its own repaint; then it becomes the repaint
    (that is what the terminal shows after one)."""
    rows, cols = session.rows, session.cols
    shown = {name: (cells(s, rows, cols), text(s, rows, cols)) for name, w, s, st in session.screens.items}
    fresh = session.repaint()
    rep.checks += 1
    # the wiggle left the terminals one row taller and back: use the repaint as the truth
    for name, width, screen, stream in fresh.items:
        got_cells, got_text = shown[name]
        want_cells = cells(screen, rows, cols)
        want_text = text(screen, rows, cols)
        if got_cells != want_cells:
            diff = []
            for y in range(rows):
                if got_text[y] != want_text[y]:
                    diff.append("row %d screen=%r repaint=%r" % (y, got_text[y].rstrip(), want_text[y].rstrip()))
                elif got_cells[y] != want_cells[y]:
                    xs = [x for x in range(cols) if got_cells[y][x] != want_cells[y][x]]
                    diff.append("row %d look differs at cols %s" % (y, xs[:6]))
            rep.failures.append("%s [%s]: %s" % (label, name, " | ".join(diff[:2])))
    session.screens = fresh


def scenario_typing(binary, root, rep, quick):
    session = Session(binary, root)
    try:
        session.type(" ff", 0.6)
        check(session, rep, "open")
        for key, label in (("p", "type p"), ("o", "type po"), ("m", "type pom"), ("\x7f", "backspace"),
                           ("m", "retype m"), ("\x0e", "down"), ("\x0e", "down"), ("\x10", "up"),
                           ("\x15", "clear"), ("p", "p again"), ("\x7f", "empty again")):
            session.type(key)
            check(session, rep, label)
            if quick and label == "backspace":
                break
        for q in ("warn", "heart", "dev", "kana", "new", "family", "nerd", "arrow"):
            if quick:
                break
            session.type("\x15")
            session.type(q)
            check(session, rep, "query %r" % q)
            session.type("\x0e")
            check(session, rep, "query %r, next" % q)
    finally:
        session.close()


def scenario_resize(binary, root, rep, quick):
    session = Session(binary, root)
    try:
        session.type(" ff", 0.6)
        session.type("pom")
        check(session, rep, "resize: before")
        for rows, cols in ([(30, 80), (20, 60), (30, 100)] if quick else [(30, 80), (20, 60), (12, 40), (30, 130), (30, 100)]):
            session.resize(rows, cols)
            session.type("\x0e")
            check(session, rep, "resized to %dx%d" % (rows, cols))
    finally:
        session.close()


def main():
    binary = os.path.abspath(sys.argv[1])
    quick = "--quick" in sys.argv
    root = tempfile.mkdtemp(prefix="m3variants")
    root = os.path.realpath(root)
    rep = Report()
    try:
        make_tree(root)
        scenario_typing(binary, root, rep, quick)
        scenario_resize(binary, root, rep, quick)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    for line in rep.failures[:30]:
        print("FAIL " + line)
    print("finder_variants_pty: %d checks on %d terminals, %d failed" % (rep.checks, len(VARIANTS), len(rep.failures)))
    sys.exit(1 if rep.failures else 0)


if __name__ == "__main__":
    main()
