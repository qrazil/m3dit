#!/usr/bin/env python3
"""Golden screens: the UI oracle of the core/plugins reorganisation (docs/CORE-AND-PLUGINS.md 7.5).

    python3 tests/screen_pty.py ./m3                      compare with tests/golden/screens.json
    python3 tests/screen_pty.py ./m3 --golden FILE        compare with FILE
    python3 tests/screen_pty.py ./m3 --record [FILE]      write FILE (default tests/golden/screens.json)
    python3 tests/screen_pty.py ./m3 --only name,name     run some scenarios
    python3 tests/screen_pty.py ./m3 --list               print the scenario names
    python3 tests/screen_pty.py ./m3 --raw                also compare the raw pty bytes (hash per scenario)
    python3 tests/screen_pty.py ./m3 --scratch DIR        keep the project directories under DIR

DESIGN says there is no nvim oracle for pickers, popups and buffers. The oracle for the front end is the old
build: the golden file was recorded from m3 0.15.0 (commit d24d514) before the reorganisation touched anything,
and every later build must reproduce it. About 30 scripted scenarios run the real binary in a pty, feed every
byte into the `pyte` emulator and compare, per scenario, the text of every row, a hash of every cell's style
(colour, bold, italic, underline, reverse), the cursor and the number of bytes the editor wrote. With --raw the
hash of the bytes themselves is compared too (the finder's streamed frames excepted; the animations are off, so the stream is deterministic on one
machine; terminal width probing is off because the harness is no terminal that answers it).

Margins: pty writes never block (uxperf.Editor), a dead child is tolerated, every wait is "until quiet" with
hundreds of milliseconds, the project directories are fixed-content and PWD and GIT_CEILING_DIRECTORIES are set,
so no outer repository is found. Skips with a note when pyte is missing; git scenarios skip without git.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

try:
    import pyte
except ImportError:
    print("skip screen_pty: pyte is not installed")
    sys.exit(0)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "bench"))
import uxperf  # noqa: E402

DEFAULT_GOLDEN = os.path.join(HERE, "golden", "screens.json")
ROWS, COLS = 30, 100
ESC = "\x1b"
WAIT = "wait"  # a step: pause for the which-key delay and settle


def make_project(root):
    """The fixed project every scenario starts in."""
    def put(path, body):
        full = os.path.join(root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(body)

    put("main.py", "import os\n\n# TODO: handle errors\ndef main(argv):\n    names = [a.upper() for a in argv]\n"
        "    for name in names:\n        print(name, 'ok')  # FIXME later\n    return 0\n\n\nif __name__ == '__main__':\n"
        "    main(os.sys.argv)\n")
    put("notes.md", "# Notes\n\nfirst paragraph with the word needle in it\n\n- item one\n- item two\n- item three\n\n"
        "second paragraph, wide: 日本語 and emoji \U0001f600 here\n")
    put("src/alpha.c", "#include <stdio.h>\n\nint main(void) {\n    printf(\"alpha\\n\");\n    return 0;\n}\n")
    put("src/beta.c", "int beta(int x) {\n    if (x > 1) {\n        return x * 2;\n    }\n    return x;\n}\n")
    put("docs/guide.txt", "guide line %d\n" * 1 % 1 + "".join("guide line %d needle\n" % i for i in range(2, 40)))
    put("long.txt", ("word " * 60 + "\n") * 6)
    put("numbers.txt", "".join("%d\n" % i for i in range(1, 121)))
    put("indent.txt", "top\n    one\n        two\n            three\n        two again\n    one again\ntop again\n")
    put("README", "readme\n")
    # fixed modification times: the finder ranks recent files first, so equal files must not tie by creation order
    stamp = 1700000000
    for base, _dirs, names in sorted(os.walk(root)):
        for name in sorted(names):
            stamp += 3600
            os.utime(os.path.join(base, name), (stamp, stamp))


def git(root, *args):
    env = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null", GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
               GIT_AUTHOR_DATE="2026-01-01T00:00:00Z", GIT_COMMITTER_DATE="2026-01-01T00:00:00Z",
               GIT_CEILING_DIRECTORIES=os.path.dirname(root), PWD=root)
    subprocess.run(["git", "-c", "init.defaultBranch=main", "-c", "gc.auto=0", "-c", "maintenance.auto=false",
                    "-c", "core.fsmonitor=false"] + list(args),
                   cwd=root, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def make_git(root):
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "init")
    with open(os.path.join(root, "main.py"), "a") as handle:
        handle.write("extra = 1\n")
    path = os.path.join(root, "numbers.txt")
    with open(path) as handle:
        lines = handle.read().split("\n")
    lines[9] = "ten changed"
    del lines[30:32]
    with open(path, "w") as handle:
        handle.write("\n".join(lines))


# (name, args, rows, cols, git?, steps). A step is keys to type, ("wait", seconds) or ("resize", rows, cols).
LEADER = " "
SCENARIOS = [
    ("start", [], ROWS, COLS, False, []),
    ("open_python", ["main.py"], ROWS, COLS, False, []),
    ("open_markdown_wide", ["notes.md"], ROWS, COLS, False, []),
    ("insert_typing", ["notes.md"], ROWS, COLS, False, ["GAnew line here", ESC]),
    ("visual_line", ["main.py"], ROWS, COLS, False, ["jjVj"]),
    ("visual_block", ["indent.txt"], ROWS, COLS, False, ["j\x16jjl"]),
    ("search_highlight", ["notes.md"], ROWS, COLS, False, ["/needle\r"]),
    ("pending_operator", ["main.py"], ROWS, COLS, False, ["2d"]),
    ("split_horizontal", ["main.py", "notes.md"], ROWS, COLS, False, [":split\r"]),
    ("split_vertical", ["main.py"], ROWS, COLS, False, [":vsplit notes.md\r"]),
    ("tab_pages", ["main.py"], ROWS, COLS, False, [":tabnew notes.md\r", ":tabnew long.txt\r", "gt"]),
    ("bufferline", ["main.py", "notes.md", "long.txt"], ROWS, COLS, False, []),
    ("explore_directory", [], ROWS, COLS, False, [":Explore\r"]),
    ("finder_files", [], ROWS, COLS, False, [LEADER + "ff", "numb"]),
    ("finder_query", [], ROWS, COLS, False, [LEADER + "ff", "alp"]),
    ("finder_grep", [], ROWS, COLS, False, [LEADER + "fg", "needle"]),
    ("finder_buffers", ["main.py", "notes.md"], ROWS, COLS, False, [":Buffers\r"]),
    ("command_palette", [], ROWS, COLS, False, [":Commands\r"]),
    ("which_key_leader", [], ROWS, COLS, False, [LEADER, (WAIT, 0.9)]),
    ("which_key_g", ["main.py"], ROWS, COLS, False, ["g", (WAIT, 0.9)]),
    ("which_key_bracket", ["main.py"], ROWS, COLS, False, ["]", (WAIT, 0.9)]),
    ("which_key_ctrl_w", ["main.py"], ROWS, COLS, False, ["\x17", (WAIT, 0.9)]),
    ("keys_browser", [], ROWS, COLS, False, [":Keys\r"]),
    ("file_tree", ["main.py"], ROWS, COLS, False, [LEADER + "e"]),
    ("plugins_list", [], ROWS, COLS, False, [":Plugins\r"]),
    ("plugin_disable", ["main.py"], ROWS, COLS, False, [":PluginDisable statusline\r"]),
    ("harpoon_pin", ["main.py"], ROWS, COLS, False, [LEADER + "ha", ":e notes.md\r", LEADER + "ha", LEADER + "1"]),
    ("fold_manual", ["main.py"], ROWS, COLS, False, [":set foldmethod=indent\r", "jzc"]),
    ("marks_sign", ["main.py"], ROWS, COLS, False, ["jjmajjmb"]),
    ("indent_guides", ["indent.txt"], ROWS, COLS, False, [":set shiftwidth=4\r"]),
    ("wrap_long_lines", ["long.txt"], ROWS, COLS, False, []),
    ("number_options", ["numbers.txt"], ROWS, COLS, False, [":set number relativenumber\r", "20j"]),
    ("scroll_half_page", ["numbers.txt"], ROWS, COLS, False, ["\x04\x04"]),
    ("theme_light", ["main.py"], ROWS, COLS, False, [":theme default-light\r"]),
    ("theme_tokyonight", ["main.py"], ROWS, COLS, False, [":theme tokyonight\r"]),
    ("error_message", [], ROWS, COLS, False, [":nosuchcommand\r"]),
    ("cmdline_substitute", ["notes.md"], ROWS, COLS, False, [":%s/item/ITEM/g\r"]),
    ("surround_and_pairs", ["notes.md"], ROWS, COLS, False, ["ysiw)", "o(a[b", ESC]),
    ("comment_toggle", ["main.py"], ROWS, COLS, False, ["jjjgcc"]),
    ("move_line", ["main.py"], ROWS, COLS, False, ["\x1bj"]),
    ("label_jump", ["main.py"], ROWS, COLS, False, [LEADER + "j", "o"]),
    ("narrow_40", ["main.py", "notes.md"], 24, 40, False, []),
    ("narrow_60_finder", [], 24, 60, False, [LEADER + "ff", "txt"]),
    ("wide_200", ["main.py", "notes.md"], 30, 200, False, [":vsplit notes.md\r"]),
    ("resize_while_split", ["main.py"], ROWS, COLS, False, [":vsplit notes.md\r", ("resize", 20, 70)]),
    ("git_gutter_status", ["main.py", "numbers.txt"], ROWS, COLS, True, [":e numbers.txt\r"]),
    ("git_hunk_jump", ["numbers.txt"], ROWS, COLS, True, ["]c"]),
    ("git_branches", [], ROWS, COLS, True, [":Branches\r"]),
    ("git_tree_letters", ["main.py"], ROWS, COLS, True, [LEADER + "e"]),
]


class Term:
    def __init__(self, binary, root, args, rows, cols, env):
        self.ed = uxperf.Editor(binary, root, args, rows, cols, env=env)
        self.rows, self.cols = rows, cols
        self.screen = pyte.Screen(cols, rows)
        self.stream = pyte.ByteStream(self.screen)
        self.fed = 0
        self.settle(0.4)

    def settle(self, quiet=0.25):
        self.ed.settle(quiet, 8)
        data = bytes(self.ed.raw[self.fed:])
        self.fed = len(self.ed.raw)
        self.stream.feed(data)

    def type(self, keys):
        self.ed.send(keys)
        self.settle()

    def resize(self, rows, cols):
        self.ed.resize(rows, cols)
        self.rows, self.cols = rows, cols
        self.screen.resize(rows, cols)
        self.settle(0.4)

    def snapshot(self):
        buf = self.screen.buffer
        text = []
        style = hashlib.sha1()
        for y in range(self.rows):
            row = []
            for x in range(self.cols):
                cell = buf[y][x]
                row.append(cell.data or " ")
                style.update(("%s|%s|%s|%d%d%d%d%d;" % (cell.fg, cell.bg, "", cell.bold, cell.italics, cell.underscore,
                                                       cell.reverse, cell.strikethrough)).encode())
            text.append("".join(row).rstrip())
        return {
            "text": text,
            "style": style.hexdigest(),
            "cursor": [self.screen.cursor.y, self.screen.cursor.x, bool(self.screen.cursor.hidden)],
            "bytes": len(self.ed.raw),
            "raw": hashlib.sha1(bytes(self.ed.raw)).hexdigest(),
        }

    def close(self):
        self.ed.close()


def run_scenario(binary, scratch, spec):
    name, args, rows, cols, is_git, steps = spec
    root = os.path.realpath(os.path.join(scratch, name))
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    make_project(root)
    if is_git:
        make_git(root)
    env = {"M3_NO_ANIM": "1", "TUI_WIDTH_PROBE": "off", "PWD": root, "GIT_CEILING_DIRECTORIES": os.path.dirname(root),
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
    term = Term(binary, root, args, rows, cols, env)
    try:
        for step in steps:
            if isinstance(step, tuple):
                if step[0] == WAIT:
                    term.ed.settle(step[1], 8)
                    term.settle(0.3)
                elif step[0] == "resize":
                    term.resize(step[1], step[2])
            else:
                term.type(step)
        term.settle(0.4)
        return term.snapshot()
    finally:
        term.close()


def is_loose(name):
    """The finder streams its results across frames: its screen is deterministic once it is quiet, its byte count
    and byte stream depend on where the frame boundaries fell. Everything else is compared byte for byte."""
    return name.startswith("finder_") or name.endswith("_finder")


def diff_text(old, new):
    out = []
    for y in range(max(len(old), len(new))):
        a = old[y] if y < len(old) else ""
        b = new[y] if y < len(new) else ""
        if a != b:
            out.append("    row %2d golden %r" % (y, a))
            out.append("           now    %r" % b)
    return out


def main():
    argv = sys.argv[1:]
    if not argv or argv[0].startswith("--"):
        if argv and argv[0] == "--list":
            print("\n".join(spec[0] for spec in SCENARIOS))
            return 0
        print(__doc__)
        return 2
    binary = os.path.abspath(argv[0])
    golden = DEFAULT_GOLDEN
    record = False
    raw = False
    only = None
    scratch = None
    rest = argv[1:]
    while rest:
        flag = rest.pop(0)
        if flag == "--record":
            record = True
            if rest and not rest[0].startswith("--"):
                golden = os.path.abspath(rest.pop(0))
        elif flag == "--golden":
            golden = os.path.abspath(rest.pop(0))
        elif flag == "--only":
            only = set(rest.pop(0).split(","))
        elif flag == "--raw":
            raw = True
        elif flag == "--scratch":
            scratch = os.path.realpath(rest.pop(0))
        elif flag == "--list":
            print("\n".join(spec[0] for spec in SCENARIOS))
            return 0
        else:
            print("unknown flag " + flag)
            return 2
    have_git = shutil.which("git") is not None
    own_scratch = scratch is None
    if own_scratch:
        scratch = os.path.realpath(tempfile.mkdtemp(prefix="m3screens"))
    os.makedirs(scratch, exist_ok=True)
    expected = {}
    if not record:
        if not os.path.exists(golden):
            print("no golden file: " + golden + " (record one with --record)")
            return 2
        with open(golden) as handle:
            expected = json.load(handle)["scenarios"]
    results = {}
    failures = 0
    checked = 0
    try:
        for spec in SCENARIOS:
            name = spec[0]
            if only is not None and name not in only:
                continue
            if spec[4] and not have_git:
                print("skip %s: git is not installed" % name)
                continue
            now = run_scenario(binary, scratch, spec)
            results[name] = now
            if record:
                continue
            checked += 1
            gold = expected.get(name)
            if gold is None:
                print("FAIL %s: not in the golden file" % name)
                failures += 1
                continue
            problems = []
            if gold["text"] != now["text"]:
                problems.append("text differs")
                problems.extend(diff_text(gold["text"], now["text"]))
            if gold["style"] != now["style"]:
                problems.append("cell styles differ")
            if gold["cursor"] != now["cursor"]:
                problems.append("cursor golden %s now %s" % (gold["cursor"], now["cursor"]))
            loose = is_loose(name)
            if not loose and gold["bytes"] != now["bytes"]:
                problems.append("pty bytes golden %d now %d" % (gold["bytes"], now["bytes"]))
            if raw and not loose and gold["raw"] != now["raw"]:
                problems.append("raw pty stream differs")
            if problems:
                failures += 1
                print("FAIL %s" % name)
                for line in problems:
                    print("  " + line if not line.startswith("    ") else line)
    finally:
        if own_scratch:
            shutil.rmtree(scratch, ignore_errors=True)
    if record:
        os.makedirs(os.path.dirname(golden), exist_ok=True)
        with open(golden, "w") as handle:
            json.dump({"recorded_from": os.path.basename(binary), "rows": ROWS, "cols": COLS, "scenarios": results},
                      handle, indent=1, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
        print("recorded %d scenarios in %s" % (len(results), golden))
        return 0
    print("screen_pty: %d scenarios, %d differ" % (checked, failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
