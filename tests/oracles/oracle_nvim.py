#!/usr/bin/env python3
"""Differential oracle: the m31 editing engine against `nvim --headless`.

    python3 tests/oracles/oracle_nvim.py --runner BIN [--corpus] [--fuzz]
                                         [--seed N] [--cases N] [--only TEXT] [-v]

A case is a starting text, a cursor and a key sequence. The same case is run
in nvim (one process per case, in a pool, driven by nvim_driver.lua) and in
the engine (one process for the whole batch, BIN is tests/t_oracle_run.m31
built). What is compared: the buffer text, the cursor, the mode, the Visual
anchor, and the registers. Everything runs on temporary files.

Corpus files (tests/oracles/corpus/*.txt) hold one case per line:

    TEXT<TAB>CURSOR<TAB>KEYS

TEXT uses \\n \\t \\\\ escapes; CURSOR is "row,col" (0-based) or empty; KEYS is
Vim key notation (<Esc>, <C-v>, <CR> ...). Lines starting with # are comments,
except `#plugins: NAME...`, which loads those vim plugins (surround, repeat,
auto-pairs) in nvim for the cases that follow in the file (the engine has them
built in). They are looked for in $M3D_PLUGINS (default ~/.vim/plugged); a file
whose plugins are missing is skipped with a note.

known_divergences.txt holds cases the engine knowingly does not match, each
preceded by a `# reason` comment. A known case that starts to match is
reported, so the list cannot rot.

divergences.tsv is the list of deliberate divergences from vim/nvim (docs/CORE-STATUS.md is generated
from it by scripts/divergences.py). A row with `skip` and a selector (a regular expression searched in the
key notation) takes the matching corpus cases out of the comparison; they are counted and listed with -v.
A row with `flip` keeps them in and expects them to differ, like known_divergences.txt.

The fuzzer (--fuzz) builds random cases from a vocabulary of key chunks over
small texts that include combining marks, wide characters and tabs, from a
seed (--seed), so a failure reproduces. A failing fuzz case is shrunk and
printed as a corpus line.
"""
import argparse
import atexit
import binascii
import concurrent.futures
import glob
import os
import random
import re
import signal
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
NVIM = os.environ.get("NVIM", "nvim")


def unpack_appimage(binary):
    """An AppImage nvim mounts a FUSE filesystem per run, which is slow and leaves
    a helper process behind whenever a run is killed. Unpack it once and run the
    real binary; any other nvim is used as it is."""
    import shutil
    import tempfile
    found = shutil.which(binary) or binary
    try:
        with open(found, "rb") as f:
            head = f.read(16)
    except OSError:
        return binary
    if head[8:11] != b"AI\x02":
        return binary
    target = tempfile.mkdtemp(prefix="medit_nvim_")
    try:
        subprocess.run([found, "--appimage-extract"], cwd=target, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=120, stdin=subprocess.DEVNULL)
    except Exception:  # noqa
        shutil.rmtree(target, ignore_errors=True)
        return binary
    inner = os.path.join(target, "squashfs-root", "usr", "bin", "nvim")
    if not os.path.exists(inner):
        shutil.rmtree(target, ignore_errors=True)
        return binary
    atexit.register(shutil.rmtree, target, True)
    return inner


NVIM = unpack_appimage(NVIM)
DRIVER = os.path.join(HERE, "nvim_driver.lua")

PLUGIN_ROOT = os.environ.get("M3D_PLUGINS", os.path.expanduser("~/.vim/plugged"))
PLUGIN_DIRS = {"surround": "vim-surround", "repeat": "vim-repeat", "auto-pairs": "auto-pairs"}

NAMED = {
    "esc": 27, "cr": 13, "enter": 13, "return": 13, "nl": 10, "tab": 9,
    "bs": 127, "backspace": 127, "space": 32, "lt": 60, "bar": 124,
    "bslash": 92, "nul": 0, "up": 63232, "down": 63233, "left": 63234,
    "right": 63235, "home": 63236, "end": 63237, "pageup": 63238,
    "pagedown": 63239, "del": 63240, "delete": 63240, "insert": 63241,
}


def parse_keys(notation):
    """Vim key notation to the engine's integer keys (MED_key.parse)."""
    out = []
    i = 0
    while i < len(notation):
        ch = notation[i]
        if ch == "<":
            j = notation.find(">", i + 1)
            if 0 < j - i <= 16:
                inner = notation[i + 1:j]
                low = inner.lower()
                if low in NAMED:
                    out.append(NAMED[low])
                    i = j + 1
                    continue
                if len(inner) == 3 and inner[:2].lower() == "c-" and (inner[2].isalpha() or inner[2] in "@[\\]^_"):
                    c = inner[2]
                    out.append(ord(c.lower()) - 96 if c.isalpha() else ord(c) & 31)
                    i = j + 1
                    continue
        out.append(ord(ch))
        i += 1
    return out


def unescape_text(text):
    out = []
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\\" and i + 1 < len(text):
            n = text[i + 1]
            if n == "n":
                out.append("\n")
            elif n == "t":
                out.append("\t")
            elif n == "\\":
                out.append("\\")
            else:
                out.append(c + n)
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def escape_text(text):
    return text.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t")


class Case:
    def __init__(self, text, row, col, notation, source=""):
        self.plugins = ""
        self.text = text
        self.row = row
        self.col = col
        self.notation = notation
        self.keys = parse_keys(notation)
        self.source = source

    def line(self):
        cur = "" if (self.row, self.col) == (0, 0) else "%d,%d" % (self.row, self.col)
        return "%s\t%s\t%s" % (escape_text(self.text), cur, self.notation)

    def ident(self):
        return self.line()


def parse_case_line(line, source=""):
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 3:
        return None
    text = unescape_text(parts[0])
    row, col = 0, 0
    if parts[1].strip():
        r, c = parts[1].split(",")
        row, col = int(r), int(c)
    return Case(text, row, col, "\t".join(parts[2:]), source)


def load_cases_file(path):
    cases = []
    reasons = []
    with open(path, encoding="utf-8") as f:
        pending = ""
        plugins = ""
        for n, line in enumerate(f, 1):
            if line.startswith("#plugins:"):
                plugins = line[len("#plugins:"):].strip()
                missing = [p for p in plugins.split() if not os.path.isdir(os.path.join(PLUGIN_ROOT, PLUGIN_DIRS[p]))]
                if missing:
                    print("skip %s: plugin(s) not found in %s: %s" % (os.path.basename(path), PLUGIN_ROOT, " ".join(missing)), file=sys.stderr)
                    return [], []
                continue
            if line.startswith("#"):
                pending = line[1:].strip()
                continue
            if not line.strip():
                continue
            case = parse_case_line(line, "%s:%d" % (os.path.basename(path), n))
            if case:
                case.plugins = plugins
                cases.append(case)
                reasons.append(pending)
    return cases, reasons


def hexs(text):
    return binascii.hexlify(text.encode("utf-8")).decode("ascii")


def unhexs(digits):
    # nvim keeps a key with no character in a register as the bytes 0x80 0xXX
    # 0xYY (K_SPECIAL); the engine's text is UTF-8, so it writes U+0080 and
    # U+00FD there. Compare both the same way.
    text = binascii.unhexlify(digits).decode("utf-8", "surrogateescape")
    text = text.replace("\udc80", "\u0080").replace("\udcfd", "\u00fd")
    return text.encode("utf-8", "replace").decode("utf-8")


def case_hex_line(index, case):
    return "\t".join([str(index), hexs(case.text), str(case.row), str(case.col),
                      ",".join(str(k) for k in case.keys), ",".join(case.plugins.split())])


CHILDREN = set()
CASE_TIMEOUT = float(os.environ.get("ORACLE_NVIM_TIMEOUT", "20"))


def kill_marked(marker):
    """Kill, by pid, any process still holding `marker` on its command line.

    An AppImage nvim runs a FUSE helper in its own session; killing the nvim
    process group leaves the helper behind, and only the case's unique output
    path names it. Linux only (needs /proc)."""
    if not marker or not os.path.isdir("/proc"):
        return
    for entry in os.listdir("/proc"):
        if not entry.isdigit() or int(entry) == os.getpid():
            continue
        try:
            with open("/proc/%s/cmdline" % entry, "rb") as f:
                text = f.read()
        except OSError:
            continue
        if marker.encode() in text:
            try:
                os.kill(int(entry), signal.SIGKILL)
            except OSError:
                pass


def kill_child(proc, marker=None):
    """Kill a spawned nvim (and its process group) by pid, then reap it."""
    try:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    try:
        proc.wait(timeout=5)
    except Exception:  # noqa
        pass
    kill_marked(marker)


def kill_all_children(*_args):
    for proc in list(CHILDREN):
        kill_child(proc)


atexit.register(kill_all_children)
for _sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
    signal.signal(_sig, lambda num, frame: (kill_all_children(), os._exit(128 + num)))


def run_nvim_case(case, tmp):
    out = os.path.join(tmp, "n%d_%d.txt" % (os.getpid(), random.getrandbits(32)))
    cmd = [NVIM, "--headless", "-u", "NONE", "-i", "NONE", "-n", "-l", DRIVER, out,
           hexs(case.text), str(case.row), str(case.col), ",".join(str(k) for k in case.keys),
           case.plugins]
    proc = None
    did_time_out = False
    try:
        # own session so the whole process group can be killed; always reaped in finally
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                stdin=subprocess.DEVNULL, start_new_session=True)
        CHILDREN.add(proc)
        try:
            proc.wait(timeout=CASE_TIMEOUT)
        except subprocess.TimeoutExpired:
            did_time_out = True
            kill_child(proc, out)
        with open(out, encoding="utf-8") as f:
            line = f.read().rstrip("\n")
        os.unlink(out)
    except Exception as e:  # noqa
        return None
    finally:
        if proc is not None:
            kill_child(proc, out if did_time_out else None)
            CHILDREN.discard(proc)
    return line.split("\t")


def run_nvim(cases, tmp):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(2, os.cpu_count() or 2)) as pool:
        return list(pool.map(lambda c: run_nvim_case(c, tmp), cases))


def run_engine_batch(runner, cases, tmp, timeout=60):
    path = os.path.join(tmp, "cases_%d.txt" % random.getrandbits(32))
    with open(path, "w", encoding="utf-8") as f:
        for i, c in enumerate(cases):
            f.write(case_hex_line(i, c) + "\n")
    try:
        done = subprocess.run([runner, path], capture_output=True, timeout=timeout, text=True,
                              stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return None
    if done.returncode != 0:
        return None
    results = {}
    for line in done.stdout.split("\n"):
        if not line:
            continue
        fields = line.split("\t")
        results[int(fields[0])] = fields
    if len(results) != len(cases):
        return None
    return [results[i] for i in range(len(cases))]


def run_engine(runner, cases, tmp):
    got = run_engine_batch(runner, cases, tmp)
    if got is not None:
        return got
    # a crash or a hang somewhere in the batch: find it case by case
    out = []
    for c in cases:
        r = run_engine_batch(runner, [c], tmp, timeout=5)
        out.append(r[0] if r else None)
    return out


def describe(fields):
    if fields is None:
        return "<no result>"
    text = unhexs(fields[1])
    regs = {}
    if len(fields) > 7 and fields[7]:
        for entry in fields[7].split(";"):
            # the name is one character and may be ":" itself
            name, kind, content = entry[0], *entry[2:].split(":", 1)
            regs[name] = (kind, unhexs(content))
    return {"text": text, "cursor": (int(fields[2]), int(fields[3])), "mode": fields[4],
            "anchor": (fields[5], fields[6]), "regs": regs,
            "top": fields[8] if len(fields) > 8 else "0",
            "left": fields[9] if len(fields) > 9 else "0"}


def diff(want, got, case=None):
    """Why two result lines differ ("" when they match)."""
    if want is None or got is None:
        return "no result (nvim=%s engine=%s)" % (want is not None, got is not None)
    a, b = describe(want), describe(got)
    if case is not None and any(k >= 63232 for k in parse_keys(case.notation)):
        # nvim stores special keys in the "." register as internal byte
        # sequences; known divergence class, not compared.
        a["regs"].pop(".", None)
        b["regs"].pop(".", None)
    notes = []
    if a["text"] != b["text"]:
        notes.append("text: nvim=%r engine=%r" % (a["text"], b["text"]))
    if a["cursor"] != b["cursor"]:
        notes.append("cursor: nvim=%s engine=%s" % (a["cursor"], b["cursor"]))
    if a["mode"] != b["mode"]:
        notes.append("mode: nvim=%s engine=%s" % (a["mode"], b["mode"]))
    if a["top"] != b["top"]:
        notes.append("top line: nvim=%s engine=%s" % (a["top"], b["top"]))
    if a["left"] != b["left"]:
        notes.append("left column: nvim=%s engine=%s" % (a["left"], b["left"]))
    if a["mode"] != "n" and a["anchor"] != b["anchor"]:
        notes.append("anchor: nvim=%s engine=%s" % (a["anchor"], b["anchor"]))
    for name in sorted(set(a["regs"]) | set(b["regs"])):
        if a["regs"].get(name) != b["regs"].get(name):
            notes.append("reg %s: nvim=%r engine=%r" % (name, a["regs"].get(name), b["regs"].get(name)))
    return "; ".join(notes)


def compare_cases(runner, cases, tmp):
    want = run_nvim(cases, tmp)
    got = run_engine(runner, cases, tmp)
    return [diff(w, g, c) for w, g, c in zip(want, got, cases)]


# ------------------------------------------------------------------- fuzzing

TEXT_LINES = [
    "", "a", "foo bar", "foo  bar baz", "  indented line", "\ttabbed", "one two three four",
    "x.y(z); w", "foo(bar, baz)", "if (a) { b }", "end.", "héllo wörld", "e\u0301a\u0301 x",
    "日本語 text", "a日b", "trailing   ", "   ", "word1 word2", "a-b_c d", "12 345", "x 0x1f -7 0b101 007 9", "-5 0xFE 99",
    "[x] {y} (z)", "Hello. World! How are you? Fine.", "say \"hi there\" ok", "<b>x</b> <i>y</i>",
    "<div><p>a</p></div>", "f(a, [1], {k})", "Mr. Smith (see.) Ok", "it's 'q' `c`", "a.  b.   c",
    "snake_case here", "A B C", "UPPER lower", "x\ty", "!!", "😀 smile",
]

MOTIONS = ["h", "l", "j", "k", "w", "W", "b", "B", "e", "E", "ge", "gE", "0", "^", "$", "_", "G", "gg",
           "{", "}", "fa", "Fa", "ta", "Ta", ";", ",", "fo", "to", "f ", "|", "+", "-", "g_", "gj", "gk",
           "3l", "2w", "2b", "3e", "2j", "2k", "0", "fe", "Fe", "5|", "2G"]
PAIR_MOTIONS = ["%", "(", ")", "[(", "])", "[{", "]}"]
OBJECTS = ["iw", "aw", "iW", "aW", "ip", "ap", "i(", "a(", "ib", "i{", "a{", "i[", "i\"", "a\"", "i'", "is", "as",
           "i<", "a<", "it", "at", "iB", "aB", "a]", "a)", "ab", "i`", "a'", "a`", "i>", "a>", "i]", "2iw", "2aw",
           "2as", "2is", "2i(", "2a\"", "2ap", "3iw", "iW", "2it", "2at", "i)", "a}", "i}"]
OPERATORS = ["d", "c", "y", ">", "<", "g~", "gu", "gU", "g?"]
SIMPLE = ["x", "X", "D", "p", "P", "u", "<C-r>", ".", "J", "gJ", "~", "rx", "r<CR>", "3x", "2p", "xp", "ddp",
          "yyp", "yyP", "dd", "yy", "cc", "Y", "gp", "gP", "2J", "3~", "2dd", "u.", "..", "ra", "xu", "dwu",
          "qaxq", "@a", "@@", "\"ayy", "\"ap", "\"Ayy", "\"add", "\"1p", "\"-p", "\"_dd", "\"_x", "yl", "yh",
          "yw", "ylp", "\"0p", "2yy", "3\"ayy", "\"bdw", "\"cx", "S", "s", "C"]
INSERTS = ["i", "a", "I", "A", "o", "O", "gI", "gi", "R", "3i", "2a", "2o", "cw", "ciw", "cc", "S", "s", "C", "cb",
           "ce", "c$", "c0", "cl", "2cw", "c2w", "cj", "ck", "caw", "ci(", "ca\"", "3s"]
TYPED = ["foo", "x", "Hello", "a b", " ", "\t", "<CR>", "<BS>", "<C-w>", "<C-u>", "<Left>", "<Right>",
         "<Del>", "é", "日", "<BS><BS>", "ab<BS>c", "<CR><CR>", "  ", "{<CR>}", "<C-r>\"", "<C-r>a", "<C-r>0",
         "<Home>", "<End>", "<Up>", "<Down>", "(x)", "foo bar<C-w>"]
VISUAL = ["v", "V", "<C-v>"]
VISUAL_OPS = ["d", "c", "y", ">", "<", "~", "u", "U", "J", "gJ", "x", "X", "D", "r_", "p", "P", "o", "O", "gv",
              "iw", "aw", "ip", "i(", "a(", "i\"", "<Esc>", "S", "s", "Y", "C", "g?", "gU", "gu", "g~", "IX<Esc>", "AX<Esc>", "<C-a>", "<C-x>", "g<C-a>", "g<C-x>", "2<C-a>"]
SEARCH = ["/a<CR>", "/foo<CR>", "?o<CR>", "n", "N", "*", "#", "/\\<w<CR>", "/b\\|c<CR>", "/[aeiou]<CR>",
          "/o\\+<CR>", "/^<CR>", "/$<CR>", "d/a<CR>", "d?o<CR>", "c/b<CR>x<Esc>", "/e\\zsl<CR>", "y/o<CR>",
          "dn", "dN", "d*", "/.<CR>", "/\\d<CR>", "/\\s<CR>", "/\\k\\+<CR>", "/o/e<CR>", "/o/e+1<CR>",
          "/o/s-1<CR>", "/o/b+1<CR>", "/a/+1<CR>", "/a/-1<CR>", "?o?e<CR>", "?a?+1<CR>", "//<CR>", "?<CR>",
          "/o/;/a/<CR>", "2/o<CR>", "3n", "2N", "g*", "g#", "d/o/e<CR>", "y/a/+1<CR>", "c/o<CR>X<Esc>",
          "d/$<CR>", "/\\n<CR>", "/o\\|$<CR>", "/\\(o\\)\\1<CR>", "d#", "dg*", "/\\cO<CR>", "/O<CR>", "dn.", "n."]
EX = [":s/a/b/<CR>", ":s/o/0/g<CR>", ":%s/ /_/g<CR>", ":2d<CR>", ":1,2d<CR>", ":d<CR>", ":%d<CR>", ":2,3j<CR>",
      ":j<CR>", ":><CR>", ":g/a/d<CR>", ":v/a/d<CR>", ":g/o/s/o/0/<CR>", ":2<CR>", ":$<CR>", ":1<CR>",
      ":.,+1d<CR>", ":%s/\\(o\\)\\(.\\)/\\2\\1/g<CR>", ":s/\\s\\+$//<CR>", ":%norm Ax<CR>", ":y<CR>", ":pu<CR>",
      ":t.<CR>", ":m0<CR>", ":m$<CR>", ":2,3><CR>", ":normal dw<CR>", ":%s/o/&&/g<CR>", ":s/x*//g<CR>",
      ":g/^/m0<CR>", ":%j<CR>", ":2,$d<CR>", ":%s/\\<./\\u&/g<CR>", ":&&<CR>", ":%s/a\\|b/X/g<CR>",
      ":g/e/j<CR>", ":g/^/j<CR>", ":2,3m0<CR>", ":g/e/normal dd<CR>", ":undo<CR>", ":redo<CR>", "@:", ":earlier 1f<CR>",
      ":later 1f<CR>", "g-", "g+", ":2ka<CR>", ":'a,.d<CR>", ":g/e/t.<CR>", ":.,+2>><CR>", ":2,3y x<CR>", ":$put x<CR>"]
MISC = ["m", "ma", "'a", "`a", "mb", "'b", "`b", "d'a", "d`a", "y'a", "''", "``", "`[", "`]", "'[", "']",
        "<C-a>", "<C-x>", "5<C-a>", "3<C-x>", "<C-a>.", "<C-x>."]


def chunks(vocab):
    """The key chunks the fuzzer may use; `vocab` switches optional groups on:
    objects, visual, search, ex, misc, pairs, registers."""
    motions = list(MOTIONS)
    if "pairs" in vocab:
        motions += PAIR_MOTIONS
    c = []
    c += motions * 3
    c += [o + m for o in OPERATORS for m in motions[:30]]
    simple = [s for s in SIMPLE if "registers" in vocab or '"' not in s]
    c += simple * 2
    if "objects" in vocab:
        c += [o + m for o in OPERATORS for m in OBJECTS]
    for ins in INSERTS:
        if ("objects" not in vocab) and ins[-1:] in "()\"" and len(ins) > 2:
            continue
        c.append(ins + random.choice(TYPED) + random.choice(TYPED) + "<Esc>")
    if "visual" in vocab:
        for v in VISUAL:
            c.append(v + random.choice(motions) + random.choice(VISUAL_OPS))
    if "search" in vocab:
        c += SEARCH
    if "ex" in vocab:
        c += EX
    if "misc" in vocab:
        c += MISC
    return c


def random_text(rng):
    n = rng.choice([1, 1, 2, 2, 3, 4, 5])
    return "\n".join(rng.choice(TEXT_LINES) for _ in range(n))


def random_case(rng, vocab):
    text = random_text(rng)
    lines = text.split("\n")
    row = rng.randrange(len(lines))
    col = 0
    if lines[row]:
        # a grapheme start: pick a character index and convert, combining marks ignored
        chars = [i for i, ch in enumerate(lines[row]) if not (0x300 <= ord(ch) <= 0x36F)]
        idx = rng.choice(chars)
        col = len(lines[row][:idx].encode("utf-8"))
    pool = chunks(vocab)
    n = rng.choice([1, 1, 2, 2, 3, 4, 5, 6])
    parts = []
    for _ in range(n):
        part = rng.choice(pool)
        if rng.random() < 0.12 and part[:1].isalpha():
            part = rng.choice(["2", "3", "4"]) + part
        parts.append(part)
    return Case(text, row, col, "".join(parts))


def split_parts(notation):
    """Split key notation into chunks the shrinker can drop: one key at a time."""
    parts = []
    i = 0
    while i < len(notation):
        if notation[i] == "<":
            j = notation.find(">", i)
            if 0 < j - i <= 8:
                parts.append(notation[i:j + 1])
                i = j + 1
                continue
        parts.append(notation[i])
        i += 1
    return parts


def shrink(runner, case, tmp, fails):
    """Drop keys and lines while the case keeps failing."""
    best = case
    changed = True
    while changed:
        changed = False
        parts = split_parts(best.notation)
        for i in range(len(parts)):
            cand = Case(best.text, best.row, best.col, "".join(parts[:i] + parts[i + 1:]))
            if cand.notation and fails(cand):
                best = cand
                changed = True
                break
        if changed:
            continue
        lines = best.text.split("\n")
        if len(lines) > 1:
            for i in range(len(lines)):
                rest = lines[:i] + lines[i + 1:]
                row = best.row - 1 if i < best.row else best.row
                if i == best.row:
                    continue
                cand = Case("\n".join(rest), row, best.col, best.notation)
                if fails(cand):
                    best = cand
                    changed = True
                    break
    return best


# ---------------------------------------------------------------------- main

def load_divergences():
    """The skip and flip rules of divergences.tsv: (id, mode, compiled selector)."""
    rules = []
    path = os.path.join(HERE, "divergences.tsv")
    if not os.path.exists(path):
        return rules
    with open(path) as handle:
        lines = handle.read().split("\n")
    for line in lines[1:]:
        cells = line.split("\t")
        if len(cells) >= 6 and cells[4] in ("skip", "flip") and cells[5]:
            rules.append((cells[0], cells[4], re.compile(cells[5])))
    return rules


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runner", required=True)
    ap.add_argument("--corpus", action="store_true", help="run tests/oracles/corpus/*.txt")
    ap.add_argument("--fuzz", action="store_true")
    ap.add_argument("--case", action="append", default=[], help="an ad hoc case line TEXT<TAB>CURSOR<TAB>KEYS (repeatable)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--cases", type=int, default=300)
    ap.add_argument("--vocab", default="", help="extra fuzz vocabulary: search,ex,misc")
    ap.add_argument("--only", default="", help="only corpus cases whose line contains this")
    ap.add_argument("--file", default="", help="only corpus files whose name contains this")
    ap.add_argument("--no-shrink", action="store_true")
    ap.add_argument("--max-report", type=int, default=12, help="shrink and print at most this many fuzz failures")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    if not (args.corpus or args.fuzz or args.case):
        args.corpus = True

    with tempfile.TemporaryDirectory(prefix="medit_oracle_") as tmp:
        known = {}
        kpath = os.path.join(HERE, "known_divergences.txt")
        if os.path.exists(kpath):
            kc, kr = load_cases_file(kpath)
            for c, r in zip(kc, kr):
                known[c.ident()] = r

        total = matched = divergent = failed = 0
        stale = []
        rules = load_divergences()
        skipped = {}

        if args.corpus:
            cases = []
            for path in sorted(glob.glob(os.path.join(HERE, "corpus", "*.txt"))):
                if args.file and args.file not in os.path.basename(path):
                    continue
                cs, _ = load_cases_file(path)
                cases += cs
            if args.only:
                cases = [c for c in cases if args.only in c.line()]
            kept = []
            for c in cases:
                rule = None
                for candidate in rules:
                    if candidate[2].search(c.notation):
                        rule = candidate
                        break
                if rule and rule[1] == "skip":
                    skipped[rule[0]] = skipped.get(rule[0], 0) + 1
                    continue
                if rule:
                    known[c.ident()] = "divergences.tsv: " + rule[0]
                kept.append(c)
            cases = kept
            diffs = compare_cases(args.runner, cases, tmp)
            for c, d in zip(cases, diffs):
                total += 1
                if not d:
                    matched += 1
                    if c.ident() in known:
                        stale.append(c)
                elif c.ident() in known:
                    divergent += 1
                    if args.verbose:
                        print("known divergence (%s): %s" % (known[c.ident()], c.line()))
                else:
                    failed += 1
                    print("FAIL %s\n  %s\n  %s" % (c.source, c.line().replace("\t", "  |  "), d))

        if args.case:
            cases = [parse_case_line(line, "--case") for line in args.case]
            diffs = compare_cases(args.runner, cases, tmp)
            for c, d in zip(cases, diffs):
                total += 1
                if not d:
                    matched += 1
                else:
                    failed += 1
                    print("DIFF %s\n  %s" % (c.line().replace("\t", "  |  "), d))

        if args.fuzz:
            rng = random.Random(args.seed)
            vocab = set(v for v in args.vocab.split(",") if v)
            cases = [random_case(rng, vocab) for _ in range(args.cases)]
            diffs = compare_cases(args.runner, cases, tmp)
            fuzz_failed = []
            for c, d in zip(cases, diffs):
                total += 1
                if not d:
                    matched += 1
                elif c.ident() in known:
                    divergent += 1
                else:
                    fuzz_failed.append((c, d))
            seen = set()
            unreported = max(0, len(fuzz_failed) - args.max_report)
            fuzz_failed.sort(key=lambda cd: len(cd[0].notation))
            for c, d in fuzz_failed[:args.max_report]:
                if not args.no_shrink:
                    def fails(cand):
                        return bool(compare_cases(args.runner, [cand], tmp)[0])
                    c = shrink(args.runner, c, tmp, fails)
                    d = compare_cases(args.runner, [c], tmp)[0]
                if c.ident() in seen or c.ident() in known:
                    continue
                seen.add(c.ident())
                failed += 1
                print("FUZZ (seed %d)\n  %s\n  %s" % (args.seed, c.line().replace("\t", "  |  "), d))
                print("  corpus line: %s" % c.line())
            failed += unreported
            if unreported:
                print("(%d more failing fuzz cases not shown)" % unreported)

        for c in stale:
            print("STALE known divergence now matches: %s" % c.line())
        if skipped and args.verbose:
            for ident in sorted(skipped):
                print("skipped by divergences.tsv (%s): %d cases" % (ident, skipped[ident]))
        print("%d cases, %d matched, %d known divergences, %d skipped (divergences.tsv), %d failed" % (total, matched, divergent, sum(skipped.values()), failed))
        return 1 if failed or stale else 0


if __name__ == "__main__":
    sys.exit(main())
