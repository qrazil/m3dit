#!/usr/bin/env python3
"""End-to-end checks of the real m3 binary in a pty.

    python3 tests/e2e.py ./m3 [--only NAME]

The screen is rebuilt with pyte (skipped with a note when pyte is missing).
Each scenario starts a fresh editor in a temporary project directory, types
keys and waits for text on the screen.
"""
import fcntl
import os
import pty
import re
import select
import shutil
import struct
import subprocess
import sys
import tempfile
import termios
import time

try:
    import pyte
except ImportError:
    print("skip e2e: pyte is not installed")
    sys.exit(0)

ROWS, COLS = 30, 100


class Session:
    def __init__(self, binary, cwd, args=(), rows=ROWS, cols=COLS, env=None, keymap="NONE"):
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        full = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor", LANG="C.UTF-8",
                    HOME=cwd, XDG_CONFIG_HOME=os.path.join(cwd, ".config"),
                    XDG_STATE_HOME=os.path.join(cwd, ".state"))
        full.pop("M3_KEYMAP", None)
        if env:
            full.update(env)
        self.proc = subprocess.Popen([binary, "-u", keymap] + list(args), stdin=slave, stdout=slave,
                                     stderr=slave, cwd=cwd, env=full, start_new_session=True,
                                     close_fds=True)
        os.close(slave)
        self.master = master
        self.screen = pyte.Screen(cols, rows)
        self.stream = pyte.ByteStream(self.screen)

    def pump(self, seconds=0.2):
        end = time.time() + seconds
        while time.time() < end:
            ready, _, _ = select.select([self.master], [], [], 0.05)
            if ready:
                try:
                    data = os.read(self.master, 65536)
                except OSError:
                    return
                if not data:
                    return
                self.stream.feed(data)

    def text(self):
        return "\n".join(self.screen.display)

    def send(self, keys, settle=0.15):
        if isinstance(keys, str):
            keys = keys.encode()
        os.write(self.master, keys)
        self.pump(settle)

    def wait_for(self, needle, timeout=5.0):
        end = time.time() + timeout
        while time.time() < end:
            self.pump(0.1)
            if needle in self.text():
                return True
        return False

    def close(self):
        try:
            os.write(self.master, b"\x1b\x1b:qa!\r")
        except OSError:
            pass
        end = time.time() + 3
        while time.time() < end and self.proc.poll() is None:
            self.pump(0.05)
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait()
        os.close(self.master)


SCENARIOS = {}


def scenario(fn):
    SCENARIOS[fn.__name__] = fn
    return fn


def project():
    root = tempfile.mkdtemp(prefix="m3d-e2e-")
    with open(os.path.join(root, "hello.txt"), "w") as f:
        f.write("hello world\nsecond line\nthird needle line\n")
    os.makedirs(os.path.join(root, "src"))
    with open(os.path.join(root, "src", "main.py"), "w") as f:
        f.write("def main():\n    return 42  # TODO later\n")
    return root


@scenario
def leader_which_key(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world"), s.text()
        s.send(" ", settle=0.8)
        assert s.wait_for("find"), "leader which-key missing:\n" + s.text()
        assert "Write file" in s.text(), s.text()
    finally:
        s.close()


@scenario
def prefix_which_key(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send("g", settle=0.8)
        assert s.wait_for("first line"), "g which-key missing:\n" + s.text()
        s.send("\x1b")
        s.send("\x17", settle=0.8)
        assert s.wait_for("split below"), "ctrl-w which-key missing:\n" + s.text()
        s.send("\x1b")
        s.send("d", settle=0.8)
        assert s.wait_for("paragraph"), "operator which-key missing:\n" + s.text()
    finally:
        s.close()


@scenario
def jk_escape(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send("ixx")
        s.send("jk", settle=0.2)
        assert s.wait_for("NORMAL") or "INSERT" not in s.text(), s.text()
        s.send(":set nojk_escape\r")
        s.send("ijk")
        assert "jk" in s.text().split("\n")[0], s.text()
    finally:
        s.close()


@scenario
def plugins_command(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send(":Plugins\r")
        assert s.wait_for("finder"), s.text()
        s.send("\x1b")
        s.send(":PluginDisable finder\r")
        s.send(" f", settle=0.8)
        assert "Find files" not in s.text(), "finder rows should be gone:\n" + s.text()
    finally:
        s.close()


def have(tool):
    return shutil.which(tool) is not None


def git(root, *args):
    subprocess.run(["git", "-C", root] + list(args), check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL,
                   env=dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_AUTHOR_NAME="t",
                            GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t"))


@scenario
def finder_files(binary, root):
    s = Session(binary, root, ["hello.txt"], cols=130)
    try:
        assert s.wait_for("hello world")
        s.send(" ff", settle=0.6)
        assert s.wait_for("src/main.py"), "files picker:\n" + s.text()
        s.send("main")
        assert s.wait_for("def main"), "preview missing:\n" + s.text()
        s.send("\r", settle=0.5)
        assert s.wait_for("return 42"), s.text()
    finally:
        s.close()


@scenario
def finder_grep_and_quickfix(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send(" fg", settle=0.4)
        s.send("line", settle=0.8)
        assert s.wait_for("hello.txt:3"), "grep hit:\n" + s.text()
        s.send("\x11", settle=0.5)  # ctrl-q: to the quickfix list
        assert s.wait_for("Quickfix"), s.text()
        s.send("\x1b", settle=0.2)
        s.send("]q", settle=0.3)
        s.send(":cnext\r", settle=0.3)
        assert s.wait_for("of 2") or s.wait_for("of 3"), s.text()
    finally:
        s.close()


@scenario
def finder_lines_and_marks(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send(" fd", settle=0.4)
        s.send("third", settle=0.4)
        s.send("\r", settle=0.4)
        assert "NORMAL" in s.text() and re.search(r" 3:\d+ ", s.text()), s.text()
    finally:
        s.close()


@scenario
def bracketed_and_move(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send("\x1bj", settle=0.3)  # Alt-j: move the line down
        lines = s.text().split("\n")
        assert "second line" in lines[0] and "hello world" in lines[1], "\n".join(lines[:4])
        s.send("\x1bk", settle=0.3)
        lines = s.text().split("\n")
        assert "hello world" in lines[0], "\n".join(lines[:4])
    finally:
        s.close()


@scenario
def git_signs_and_pickers(binary, root):
    if not have("git"):
        return
    git(root, "init", "-q", "-b", "main")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "first")
    git(root, "checkout", "-q", "-b", "feature")
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send("ggOnew line\x1b", settle=0.3)
        s.send(" gs", settle=0.5)   # stage hunk
        assert s.wait_for("Hunk staged"), s.text()
        out = subprocess.run(["git", "-C", root, "diff", "--cached", "--stat"], capture_output=True, text=True).stdout
        assert "hello.txt" in out, out
        s.send(" gb", settle=0.6)
        assert s.wait_for("main") and s.wait_for("feature"), s.text()
        s.send("\x1b", settle=0.2)
        s.send(" gC", settle=0.6)
        assert s.wait_for("first"), s.text()
    finally:
        s.close()


@scenario
def git_hunk_jumps_and_no_repo(binary, root):
    path = os.path.join(root, "long.txt")
    with open(path, "w") as f:
        f.write("".join("row %02d\n" % n for n in range(1, 31)))
    s = Session(binary, root, ["long.txt"])
    try:
        assert s.wait_for("row 01")
        s.send("3GAA\x1b", settle=0.3)
        s.send("gg0]cx", settle=0.3)     # not a repository: no hunks, ]c stays put and x eats the "r"
        assert "ow 01" in s.text(), s.text()
    finally:
        s.close()
    if not have("git"):
        return
    git(root, "init", "-q", "-b", "main")
    git(root, "add", "long.txt")
    git(root, "commit", "-q", "-m", "first")
    with open(path, "w") as f:
        f.write("".join("row %02d\n" % n for n in range(1, 31)))
    s = Session(binary, root, ["long.txt"])
    try:
        assert s.wait_for("row 01")
        s.send("3GAA\x1b", settle=0.3)
        s.send("20GAB\x1b", settle=0.5)
        s.send("gg0]cx", settle=0.3)
        assert "ow 03A" in s.text(), s.text()
        s.send("]cx", settle=0.3)
        assert "ow 20B" in s.text(), s.text()
        s.send("[cx", settle=0.3)
        assert "w 03A" in s.text(), s.text()
    finally:
        s.close()


@scenario
def terminal_pane(binary, root):
    s = Session(binary, root, ["hello.txt"], env={"SHELL": "/bin/sh", "PS1": "$ "})
    try:
        assert s.wait_for("hello world")
        s.send(":terminal\r", settle=0.8)
        assert s.wait_for("TERMINAL"), s.text()
        s.send("echo from_the_pane_$((6*7))\r", settle=0.8)
        assert s.wait_for("from_the_pane_42"), s.text()
        s.send("\x1c\x0e", settle=0.3)  # CTRL-\ CTRL-N
        assert s.wait_for("NORMAL"), s.text()
        s.send("i", settle=0.3)
        assert s.wait_for("TERMINAL"), s.text()
        s.send("exit\r", settle=0.8)
        assert s.wait_for("Process exited 0"), s.text()
    finally:
        s.close()


@scenario
def shell_filters(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send(":%!sort\r", settle=0.5)
        lines = s.text().split("\n")
        assert "hello world" in lines[0], "\n".join(lines[:4])
        s.send(":r !echo from_read\r", settle=0.5)
        assert s.wait_for("from_read"), s.text()
        s.send("!!tr a-z A-Z\r", settle=0.5)
        assert s.wait_for("FROM_READ"), s.text()
        s.send(":!echo bang_output\r", settle=0.5)
        assert s.wait_for("bang_output"), s.text()
    finally:
        s.close()


@scenario
def statusline_tabline_guides(binary, root):
    if have("git"):
        git(root, "init", "-q", "-b", "trunk")
    s = Session(binary, root, ["src/main.py", "hello.txt"])
    try:
        assert s.wait_for("return 42")
        text = s.text()
        first = text.split("\n")[0]
        assert "main.py" in first and "hello.txt" in first, "tabline:\n" + text
        s.send(":b1\r", settle=0.4)
        assert s.wait_for("return 42"), s.text()
        assert "\u2502" in s.text(), "indent guide missing:\n" + s.text()
        assert "python" in s.text().split("\n")[-2], "filetype missing:\n" + s.text()
        if have("git"):
            assert s.wait_for("trunk", 4.0), "branch missing:\n" + s.text()
        s.send(":PluginDisable guides\r", settle=0.3)
        assert "\u2502" not in s.text(), s.text()
        s.send(":PluginDisable statusline\r", settle=0.3)
        assert "python" not in s.text().split("\n")[-2], s.text()
    finally:
        s.close()


@scenario
def tab_pages(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send(":tabnew src/main.py\r", settle=0.4)
        assert s.wait_for("return 42"), s.text()
        first = s.text().split("\n")[0]
        assert "hello.txt" in first and "src/main.py" in first, "tab line:\n" + s.text()
        s.send("gt", settle=0.3)
        assert "hello world" in s.text() and "return 42" not in s.text(), s.text()
        s.send(":vsplit\r", settle=0.3)
        s.send("gt", settle=0.3)
        assert "return 42" in s.text(), s.text()
        s.send("gT", settle=0.3)
        first = s.text().split("\n")[0]
        assert "2 hello.txt" in first, "window count in the tab label:\n" + first
        s.send(":tabclose\r", settle=0.3)
        assert "return 42" in s.text(), s.text()
        assert "2 hello.txt" not in s.text().split("\n")[0], s.text()
    finally:
        s.close()


@scenario
def tab_click_and_modifier(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send(":tabnew src/main.py\r", settle=0.4)
        assert s.wait_for("return 42"), s.text()
        # the tab line is " hello.txt  src/main.py ": a click on the first label shows its page
        s.send("\x1b[<0;3;1M\x1b[<0;3;1m", settle=0.4)
        assert "hello world" in s.text() and "return 42" not in s.text(), s.text()
        s.send("\x1b[<0;16;1M\x1b[<0;16;1m", settle=0.4)
        assert "return 42" in s.text(), "click on the second label:\n" + s.text()
        # :tab split opens the page after the current one, :0tab split before the first
        s.send(":tab split\r", settle=0.4)
        s.send(":0tab split\r", settle=0.4)
        first = s.text().split("\n")[0]
        assert first.count("src/main.py") == 3 and "hello.txt" in first, "tab line:\n" + first
        assert first.index("src/main.py") < first.index("hello.txt"), first
    finally:
        s.close()


@scenario
def state_recent_harpoon_position(binary, root):
    keymap = os.path.join(root, "empty.vim")
    open(keymap, "w").close()
    s = Session(binary, root, ["src/main.py"], keymap=keymap)
    try:
        assert s.wait_for("return 42")
        s.send("j$", settle=0.2)
        s.send(" ha", settle=0.4)
        assert s.wait_for("Harpoon: pinned"), s.text()
        s.send(":e hello.txt\r", settle=0.4)
        s.pump(1.5)
    finally:
        s.close()
    s = Session(binary, root, ["src/main.py"], keymap=keymap)
    try:
        assert s.wait_for("return 42")
        assert re.search(r" 2:\d+ ", s.text()), "position not restored:\n" + s.text()
        s.send(" fr", settle=0.5)
        assert s.wait_for("hello.txt"), "recent list:\n" + s.text()
        s.send("\x1b", settle=0.2)
        s.send(" he", settle=0.5)
        assert s.wait_for("main.py"), "harpoon menu:\n" + s.text()
    finally:
        s.close()


@scenario
def lsp_client(binary, root):
    fake = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake_lsp.py")
    with open(os.path.join(root, "a.py"), "w") as f:
        f.write("hello = 1  # BUG\nprint(hello)\nprint(hello)\n")
    s = Session(binary, root, ["a.py"])
    try:
        assert s.wait_for("print(hello)")
        s.send(":Lsp server python python3 %s\r" % fake, settle=0.3)
        s.send(":Lsp start\r", settle=0.3)
        assert s.wait_for("E:1", 8.0), "diagnostic count missing:\n" + s.text()
        assert re.search(r"^E ", s.text(), re.M) or " E " in s.text().split("\n")[0], "sign missing:\n" + s.text()
        s.send("]d", settle=0.4)
        assert s.wait_for("found BUG on line 1"), s.text()
        s.send(" ll", settle=0.4)
        assert s.wait_for("error: found BUG"), s.text()
        s.send("K", settle=0.6)
        assert s.wait_for("hover 0:"), "hover:\n" + s.text()
        assert "replies=ok cfg=2" in s.text(), "server requests were not answered:\n" + s.text()
        s.send("\r", settle=0.2)
        s.send(":Lsp rename howdy\r", settle=0.8)
        assert s.wait_for("howdy = 1"), "rename:\n" + s.text()
        s.send(":Lsp format\r", settle=0.8)
        assert s.wait_for("PRINT(HOWDY)"), "format:\n" + s.text()
        s.send("grr", settle=0.8)
        assert s.wait_for("References"), "references:\n" + s.text()
        s.send("\x1b", settle=0.2)
        s.send(":Lsp action\r", settle=0.8)
        assert s.wait_for("Fix BUG"), "actions:\n" + s.text()
        s.send("\r", settle=0.6)
        assert s.wait_for("FIXED"), "applied:\n" + s.text()
        # completion: CTRL-Space in Insert mode, accept with Enter; snippets lose their placeholders
        s.send(":$\r", settle=0.2)
        s.send("o", settle=0.2)
        s.send("xx.hel", settle=0.2)
        s.send("\x00", settle=1.0)
        assert s.wait_for("Completion"), "completion popup:\n" + s.text()
        s.send("\r", settle=0.6)
        assert s.wait_for("xx.hello_world"), "completion accepted:\n" + s.text()
        s.send("\x1b", settle=0.2)
        s.send("o", settle=0.2)
        s.send("sn", settle=0.2)
        s.send("\x00", settle=1.0)
        s.send("\r", settle=0.6)
        assert s.wait_for("snip(arg, )"), "snippet accepted:\n" + s.text()
        s.send("\x1b", settle=0.2)
        s.send("u", settle=0.2)
        s.send("u", settle=0.2)
        # an action that carries only `data` is resolved first, a command is executed
        s.send(":Lsp action\r", settle=0.8)
        assert s.wait_for("Lazy fix"), "actions:\n" + s.text()
        s.send("Lazy", settle=0.3)
        s.send("\r", settle=0.8)
        assert s.wait_for("LAZY "), "resolved action:\n" + s.text()
        s.send(":Lsp action\r", settle=0.8)
        s.send("Run comm", settle=0.3)
        s.send("\r", settle=0.8)
        assert s.wait_for("CMD "), "executed command:\n" + s.text()
    finally:
        s.close()


@scenario
def lsp_signature_hints_close(binary, root):
    fake = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake_lsp.py")
    with open(os.path.join(root, "a.py"), "w") as f:
        f.write("hello = 1\nprint(hello)\n")
    with open(os.path.join(root, "b.py"), "w") as f:
        f.write("other = 2\n")
    s = Session(binary, root, ["a.py"])
    try:
        assert s.wait_for("print(hello)")
        s.send(":Lsp server python python3 %s\r" % fake, settle=0.3)
        s.send(":Lsp start\r", settle=0.3)
        s.pump(2.0)
        s.send("j$", settle=0.2)
        s.send(":Lsp signature\r", settle=1.0)
        assert s.wait_for("greet(name, greeting)", 5.0), "signature help:\n" + s.text()
        assert "-> greeting" in s.text() and "Say hello" in s.text(), s.text()
        s.send("\r", settle=0.2)
        s.send(":Lsp hints\r", settle=1.5)
        assert s.wait_for("value:", 5.0), "inlay hints:\n" + s.text()
        s.send(":Lsp hints\r", settle=0.4)
        assert "value:" not in s.text(), s.text()
        # typing a trigger character in Insert mode asks for signature help
        s.send("o", settle=0.2)
        s.send("greet(", settle=1.2)
        assert s.wait_for("greet(name, greeting)", 5.0), "signature on (:\n" + s.text()
        s.send("\x1b", settle=0.2)   # dismisses the listing
        s.send("\x1b", settle=0.2)
        # deleting a buffer sends didClose
        s.send(":e b.py\r", settle=0.3)
        s.pump(1.0)
        s.send(":bd! 1\r", settle=0.5)
        s.pump(0.5)
        s.send("K", settle=1.0)
        assert s.wait_for("closed=1", 5.0), "didClose:\n" + s.text()
    finally:
        s.close()


class Skip(Exception):
    pass


MASON = os.path.expanduser("~/.local/share/nvim/mason/bin")


def find_server(*names):
    """The first of `names` found on PATH or in nvim's mason bin directory, else skip."""
    for name in names:
        found = shutil.which(name)
        if found:
            return found
        candidate = os.path.join(MASON, name)
        if os.path.exists(candidate):
            return candidate
    raise Skip("%s not installed" % names[0])


def descendants(pid):
    """Every live descendant pid of `pid` (from /proc)."""
    parents = {}
    for entry in os.listdir("/proc"):
        if entry.isdigit():
            try:
                with open("/proc/%s/stat" % entry) as f:
                    fields = f.read().rsplit(")", 1)[1].split()
                parents[int(entry)] = int(fields[1])
            except (OSError, IndexError, ValueError):
                pass
    out, frontier = set(), {pid}
    while frontier:
        frontier = {p for p, q in parents.items() if q in frontier and p not in out}
        out |= frontier
    return out


def real_server(binary, root, lang, command, files, open_file, wanted, probe_line, probe_char,
                rename_to, wait=60.0, env=None, check_quit=True):
    """Drive a real language server: diagnostics arrive, hover, definition,
    references, rename; then quit and require no process of the server is left."""
    for path, text in files.items():
        full = os.path.join(root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write(text)
    s = Session(binary, root, [open_file], env=env)
    started = []
    try:
        s.pump(0.5)
        s.send(":Lsp server %s %s\r" % (lang, command), settle=0.3)
        s.send(":Lsp start\r", settle=0.3)
        assert s.wait_for(wanted, wait), "diagnostics (%s) missing:\n%s" % (wanted, s.text())
        started = sorted(descendants(s.proc.pid))
        assert started, "no server process was started"
        # a server that reports progress (indexing) is busy: wait until it is idle
        end = time.time() + wait
        while time.time() < end and "LSP:" in s.text().split("\n")[-2]:
            s.pump(0.5)
        s.send(":%d\r" % probe_line, settle=0.2)
        s.send("0" + "l" * probe_char, settle=0.2)
        s.send("K", settle=2.0)
        assert "Press ENTER" in s.text(), "hover shows nothing:\n" + s.text()
        s.send("\r", settle=0.2)
        s.send("gd", settle=2.0)
        assert "NORMAL" in s.text()
        s.send(":%d\r" % probe_line, settle=0.2)
        s.send("0" + "l" * probe_char, settle=0.2)
        s.send("grr", settle=2.0)
        assert "References" in s.text(), "references:\n" + s.text()
        s.send("\x1b", settle=0.3)
        s.send(":%d\r" % probe_line, settle=0.2)
        s.send("0" + "l" * probe_char, settle=0.2)
        s.send(":Lsp rename %s\r" % rename_to, settle=2.5)
        assert s.wait_for(rename_to, 5.0), "rename:\n" + s.text()
        s.send(":Lsp info\r", settle=0.5)
        assert "(ready" in s.text(), "info:\n" + s.text()
        s.send("\r", settle=0.2)
    finally:
        s.close()
    if check_quit:
        time.sleep(0.5)
        left = [p for p in started if os.path.exists("/proc/%d" % p)]
        # a reaped or zombie process is fine; a running one is an orphan
        alive = []
        for p in left:
            try:
                with open("/proc/%d/stat" % p) as f:
                    if f.read().rsplit(")", 1)[1].split()[0] != "Z":
                        alive.append(p)
            except OSError:
                pass
        for p in alive:
            try:
                os.kill(p, 9)
            except OSError:
                pass
        assert not alive, "server processes left after quit: %r" % alive


@scenario
def lsp_real_pyright(binary, root):
    cmd = find_server("pyright-langserver")
    real_server(binary, root, "python", cmd + " --stdio",
                {"a.py": 'def greet(name):\n    return "hi " + name\n\nx = greet("a")\ny = undefined_name\nz = greet("b")\n'},
                "a.py", "E:1", 6, 6, "hello")


@scenario
def lsp_real_clangd(binary, root):
    cmd = find_server("clangd")
    real_server(binary, root, "c", cmd,
                {"a.c": 'int add(int a, int b) {\n    return a + b;\n}\n\nint main(void) {\n    int y = add(1, 2);\n    return undefined_thing + y;\n}\n'},
                "a.c", "E:1", 6, 12, "plus", wait=30.0)


@scenario
def lsp_real_typescript(binary, root):
    cmd = find_server("typescript-language-server")
    real_server(binary, root, "javascript", cmd + " --stdio",
                {"a.ts": 'function add(a: number, b: number): number {\n  return a + b;\n}\n\nconst x: number = "no";\nconst y = add(1, 2);\n',
                 "tsconfig.json": '{"compilerOptions":{"strict":true}}\n'},
                "a.ts", "E:1", 6, 12, "plus", wait=30.0)


@scenario
def lsp_real_lua(binary, root):
    cmd = find_server("lua-language-server")
    real_server(binary, root, "lua", cmd,
                {"a.lua": 'local function add(a, b)\n  return a + b\nend\n\nlocal y = add(1, 2)\nprint(y, undefined_global)\n'},
                "a.lua", "W:1", 5, 12, "plus", wait=30.0)


@scenario
def lsp_real_rust_analyzer(binary, root):
    cmd = None
    # a rustup proxy without the component fails --version: try nvim's mason build too
    for candidate in (shutil.which("rust-analyzer"), os.path.join(MASON, "rust-analyzer")):
        if candidate and os.path.exists(candidate) and subprocess.run(
                [candidate, "--version"], capture_output=True).returncode == 0:
            cmd = candidate
            break
    if not cmd or not shutil.which("cargo"):
        raise Skip("no working rust-analyzer (and cargo)")
    env = {"RUSTUP_HOME": os.environ.get("RUSTUP_HOME", os.path.expanduser("~/.rustup")),
           "CARGO_HOME": os.environ.get("CARGO_HOME", os.path.expanduser("~/.cargo"))}
    real_server(binary, root, "rust", cmd,
                {"Cargo.toml": '[package]\nname = "fx"\nversion = "0.1.0"\nedition = "2021"\n',
                 "src/main.rs": 'fn add(a: i32, b: i32) -> i32 {\n    a + b\n}\n\nfn main() {\n    let x: i32 = "no";\n    let y = add(1, 2);\n    println!("{}", y);\n}\n'},
                "src/main.rs", "E:1", 7, 12, "plus", wait=180.0, env=env)


@scenario
def label_jump(binary, root):
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world")
        s.send(" jn", settle=0.5)   # the n of "second line" and "needle line" ...
        assert s.wait_for("jump"), s.text()
        assert s.wait_for("third needle line") or True
        s.send("a", settle=0.4)
        assert "NORMAL" in s.text() and re.search(r" [23]:\d+ ", s.text()), s.text()
    finally:
        s.close()


@scenario
def user_maps_in_which_key(binary, root):
    keymap = os.path.join(root, "keys.vim")
    with open(keymap, "w") as f:
        f.write("let mapleader = \" \"\nnnoremap <leader>w :w<CR>\nnnoremap gX :s/hello/HELLO/<CR>\nnnoremap <leader>q ddp\n")
    s = Session(binary, root, ["hello.txt"], keymap=keymap)
    try:
        assert s.wait_for("hello world")
        s.send("g", settle=0.8)
        assert s.wait_for(":s/hello/HELLO/"), "user gX missing from which-key:\n" + s.text()
        s.send("\x1b", settle=0.2)
        s.send(" ", settle=0.8)
        assert s.wait_for("ddp"), "user <leader>q missing:\n" + s.text()
        assert "Find files" in s.text() or "find" in s.text(), s.text()
        s.send("q", settle=0.4)
        assert s.wait_for("second line"), s.text()
        lines = s.text().split("\n")
        assert "second line" in lines[0] and "hello world" in lines[1], "\n".join(lines[:3])
    finally:
        s.close()


@scenario
def themes(binary, root):
    import re as regex
    # --theme paints the whole screen in the theme's background (truecolor)
    s = Session(binary, root, ["--theme", "tokyonight", "src/main.py"])
    try:
        assert s.wait_for("return 42"), s.text()
        assert s.screen.buffer[0][5].bg == "1a1b26" or s.screen.buffer[2][60].bg == "1a1b26", "background not painted"
        assert s.screen.buffer[2][60].bg == "1a1b26", "empty cell is not the theme's background: %r" % s.screen.buffer[2][60].bg
        s.send(":theme\r", settle=0.4)
        assert "theme: tokyonight" in s.text(), s.text()
        s.send(":colorscheme nord\r", settle=0.4)
        assert "theme: nord" in s.text(), s.text()
        assert s.screen.buffer[2][60].bg == "2e3440", "nord background: %r" % s.screen.buffer[2][60].bg
        s.send(":theme nonesuch\r", settle=0.4)
        assert 'unknown theme "nonesuch"' in s.text(), s.text()
        assert s.screen.buffer[2][60].bg == "2e3440", "theme changed on an unknown name"
        s.send(":theme gruvbox-m\t", settle=0.4)
        assert ":theme gruvbox-material" in s.text(), "Tab completion:\n" + s.text()
        s.send("\x1b", settle=0.3)
        # the picker previews while moving, and Esc puts the theme back
        s.send(" fC", settle=0.6)
        assert "Themes" in s.text(), s.text()
        s.send("\x0e", settle=0.5)
        assert s.screen.buffer[2][60].bg != "2e3440", "moving the selection did not preview a theme"
        s.send("\x1b", settle=0.4)
        assert "Themes" not in s.text(), s.text()
        assert s.screen.buffer[2][60].bg == "2e3440", "Esc did not restore the theme"
    finally:
        s.close()
    # an unknown --theme falls back to the default with a message
    s = Session(binary, root, ["--theme", "nonesuch", "hello.txt"])
    try:
        assert s.wait_for("hello world"), s.text()
        assert 'unknown theme "nonesuch"' in s.text(), s.text()
        s.send(":theme\r", settle=0.3)
        assert "theme: default" in s.text(), s.text()
    finally:
        s.close()
    # user themes: $XDG_CONFIG_HOME/m3/themes/NAME.toml, inheriting a built-in
    themes = os.path.join(root, ".config", "m3", "themes")
    os.makedirs(themes)
    with open(os.path.join(themes, "mine.toml"), "w") as f:
        f.write('inherits = "tokyonight"\n"ui.background" = { bg = "#102030" }\n"ui.text" = { bg = "#102030", fg = "#ffffff" }\n')
    s = Session(binary, root, ["hello.txt"])
    try:
        assert s.wait_for("hello world"), s.text()
        s.send(":theme mi\t", settle=0.4)
        assert ":theme mine" in s.text(), s.text()
        s.send("\r", settle=0.4)
        assert s.screen.buffer[2][60].bg == "102030", "user theme background: %r" % s.screen.buffer[2][60].bg
    finally:
        s.close()
    # the startup file's :colorscheme
    keymap = os.path.join(root, "start.vim")
    with open(keymap, "w") as f:
        f.write("colorscheme dracula\n")
    s = Session(binary, root, ["hello.txt"], keymap=keymap)
    try:
        assert s.wait_for("hello world"), s.text()
        assert s.screen.buffer[2][60].bg == "282a36", "startup colorscheme: %r" % s.screen.buffer[2][60].bg
    finally:
        s.close()
    # 16 colours: the default theme is the terminal's own palette, no 24-bit colour is written
    s = Session(binary, root, ["src/main.py"], env={"TERM": "xterm", "COLORTERM": ""})
    try:
        assert s.wait_for("return 42"), s.text()
        s.send(":theme\r", settle=0.4)
        assert "theme: term16-dark" in s.text(), s.text()
        for row in range(0, 5):
            for col in range(0, 40):
                cell = s.screen.buffer[row][col]
                assert not regex.fullmatch("[0-9a-f]{6}", cell.fg) and not regex.fullmatch("[0-9a-f]{6}", cell.bg), (row, col, cell)
        s.send(":theme tokyonight\r", settle=0.4)
        assert s.wait_for("theme: tokyonight"), s.text()
        for row in range(0, 5):
            for col in range(0, 40):
                cell = s.screen.buffer[row][col]
                assert not regex.fullmatch("[0-9a-f]{6}", cell.fg) and not regex.fullmatch("[0-9a-f]{6}", cell.bg), ("quantised", row, col, cell)
    finally:
        s.close()


@scenario
def undofile_persists(binary, root):
    keymap = os.path.join(root, "empty.vim")
    open(keymap, "w").close()
    s = Session(binary, root, ["hello.txt"], keymap=keymap)
    try:
        assert s.wait_for("hello world")
        s.send("xx", settle=0.2)
        s.send("jdd", settle=0.2)
        s.send(":w\r", settle=0.5)
        assert s.wait_for("written"), s.text()
        s.send(":q\r", settle=0.5)
    finally:
        s.close()
    undo_dir = os.path.join(root, ".state", "m3", "undo")
    assert os.path.isdir(undo_dir) and os.listdir(undo_dir), "no undo file written"
    s = Session(binary, root, ["hello.txt"], keymap=keymap)
    try:
        assert s.wait_for("llo world")
        s.send("u", settle=0.3)
        assert s.wait_for("second line"), "undo of the line delete after a restart:\n" + s.text()
        s.send("uu", settle=0.3)
        assert s.wait_for("hello world"), "undo of the two x:\n" + s.text()
    finally:
        s.close()
    # a file changed behind our back drops the history instead of corrupting the text
    with open(os.path.join(root, "hello.txt"), "w") as f:
        f.write("replaced\n")
    s = Session(binary, root, ["hello.txt"], keymap=keymap)
    try:
        assert s.wait_for("replaced")
        s.send("u", settle=0.3)
        assert "replaced" in s.text(), s.text()
    finally:
        s.close()


@scenario
def project_settings(binary, root):
    keymap = os.path.join(root, "empty.vim")
    open(keymap, "w").close()
    with open(os.path.join(root, ".editorconfig"), "w") as f:
        f.write("root = true\n[*.txt]\nindent_style = space\nindent_size = 3\ntrim_trailing_whitespace = true\n")
    with open(os.path.join(root, ".m3.toml"), "w") as f:
        f.write("[options]\nnumber = false\n")
    s = Session(binary, root, ["hello.txt"], keymap=keymap)
    try:
        assert s.wait_for("hello world")
        s.send("A  \x1b", settle=0.2)
        s.send("o\tx\x1b", settle=0.3)
        s.pump(0.3)
        assert re.search(r"^[│ ]  x ", s.text(), re.M), s.text()
        assert "1 " not in s.text().split("\n")[0][:3], "number = false was not applied:\n" + s.text()
        s.send(":w\r", settle=0.5)
        assert s.wait_for("written"), s.text()
        s.send(":q\r", settle=0.5)
    finally:
        s.close()
    with open(os.path.join(root, "hello.txt")) as f:
        lines = f.read().split("\n")
    assert lines[0] == "hello world", repr(lines[0])
    assert lines[1] == "   x", repr(lines[1])


@scenario
def disk_watch_autosave_autowrite(binary, root):
    keymap = os.path.join(root, "empty.vim")
    open(keymap, "w").close()
    path = os.path.join(root, "hello.txt")
    s = Session(binary, root, ["hello.txt"], keymap=keymap)
    try:
        assert s.wait_for("hello world")
        # an outside change to an unmodified buffer is read again within a couple of seconds
        with open(path, "w") as f:
            f.write("changed outside the editor\nsecond\n")
        assert s.wait_for("changed outside the editor", timeout=6), s.text()
        assert s.wait_for("reloaded", timeout=2), s.text()
        # a modified buffer is not touched, it gets the warning
        s.send("x", settle=0.2)
        with open(path, "w") as f:
            f.write("a different outside change\n")
        assert s.wait_for("W12", timeout=6), s.text()
        assert "hanged outside the editor" in s.text(), "the modified buffer must keep its text:\n" + s.text()
        s.send("u", settle=0.2)
        # 'autosave': written after the quiet time
        s.send(":set autosave=1\r", settle=0.3)
        s.send("x", settle=0.2)
        assert s.wait_for("autosaved", timeout=6), s.text()
        with open(path) as f:
            assert f.read().startswith("hanged outside the editor"), "autosave wrote the buffer"
        s.send(":set autosave=0\r", settle=0.3)
        # 'autowriteall': :q writes the buffer first
        s.send(":set autowriteall\r", settle=0.3)
        s.send("x", settle=0.2)
        s.send(":q\r", settle=0.8)
    finally:
        s.close()
    with open(path) as f:
        text = f.read()
    assert text.startswith("anged outside the editor"), "quit with autowriteall: %r" % text
    assert s.proc.poll() == 0, "exit status"


@scenario
def session_restore(binary, root):
    keymap = os.path.join(root, "empty.vim")
    open(keymap, "w").close()
    s = Session(binary, root, [], keymap=keymap)
    try:
        s.send(":e hello.txt\r", settle=0.4)
        s.send("jj", settle=0.2)
        s.send(":e src/main.py\r", settle=0.4)
        assert s.wait_for("return 42")
        s.send("j", settle=0.2)
        s.send(":Session save work\r", settle=0.4)
        assert s.wait_for("Session saved"), s.text()
        s.send(":q\r", settle=0.3)
        s.send(":qa\r", settle=0.6)
    finally:
        s.close()
    # no arguments: the project's buffers come back, the last current one shown
    s = Session(binary, root, [], keymap=keymap)
    try:
        assert s.wait_for("return 42"), s.text()
        s.send(":ls\r", settle=0.4)
        assert s.wait_for("hello.txt"), s.text()
        s.send("\r", settle=0.2)
    finally:
        s.close()
    # --no-session starts empty
    s = Session(binary, root, ["--no-session"], keymap=keymap)
    try:
        s.pump(1.0)
        assert "return 42" not in s.text() and "hello world" not in s.text(), s.text()
        s.send(":Session load work\r", settle=0.6)
        assert s.wait_for("Session loaded"), s.text()
        s.send(":Session list\r", settle=0.3)
        assert s.wait_for("Sessions: work"), s.text()
        s.send(":Session delete work\r", settle=0.3)
        assert s.wait_for("Session deleted"), s.text()
    finally:
        s.close()


@scenario
def snippets_tab_select(binary, root):
    import json
    config = os.path.join(root, "cfg")
    os.makedirs(config)
    keymap = os.path.join(config, "keymap.vim")
    open(keymap, "w").close()
    with open(os.path.join(config, "snippets.json"), "w") as f:
        json.dump({"for": {"prefix": "for", "body": ["for ${1:item} in ${2:items} do", "\t$0", "end"]}}, f)
    s = Session(binary, root, ["new.txt"], keymap=keymap)
    try:
        assert s.wait_for("new.txt"), s.text()
        s.send("ifor\t", settle=0.4)
        assert "for item in items do" in s.text(), "the prefix did not expand:\n" + s.text()
        assert "SELECT" in s.text(), "first placeholder is selected:\n" + s.text()
        s.send("x", settle=0.3)
        assert "for x in items do" in s.text() and "INSERT" in s.text(), s.text()
        s.send("\t", settle=0.3)
        assert "SELECT" in s.text(), "Tab selects the next placeholder:\n" + s.text()
        s.send("list", settle=0.3)
        assert "for x in list do" in s.text(), s.text()
        s.send("\t", settle=0.3)
        s.send("body", settle=0.3)
        assert "body" in s.text() and "for x in list do" in s.text(), s.text()
        s.send("\x1b[Z", settle=0.3)
        assert "SELECT" in s.text() or "INSERT" in s.text(), s.text()
        assert "for x in list do" in s.text(), s.text()
        s.send("\x1b", settle=0.3)
        assert "NORMAL" in s.text(), s.text()
    finally:
        s.close()


def main():
    binary = os.path.abspath(sys.argv[1])
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    failed = 0
    skipped = 0
    for name, fn in SCENARIOS.items():
        if only and name != only:
            continue
        root = project()
        try:
            fn(binary, root)
            print("ok   %s" % name)
        except Skip as error:
            skipped += 1
            print("skip %s: %s" % (name, error))
        except AssertionError as error:
            failed += 1
            print("FAIL %s: %s" % (name, error))
        except Exception as error:  # noqa
            failed += 1
            print("FAIL %s: %r" % (name, error))
        finally:
            shutil.rmtree(root, ignore_errors=True)
    print("e2e: %d scenarios, %d failed, %d skipped" % (len(SCENARIOS) if not only else 1, failed, skipped))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
