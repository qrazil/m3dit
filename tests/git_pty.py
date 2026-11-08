#!/usr/bin/env python3
"""pty scenarios of the in-process git: the `:Git` commands and the hunk commands in the real binary.

    python3 tests/git_pty.py M3_BINARY

The screen is read with pyte (skips with a note when it is missing); effects are read back with real git.
macOS-safe: the temp root is resolved with realpath and handed to the child as cwd and PWD, git is fenced off
with GIT_CEILING_DIRECTORIES and reads no user or system configuration, pty writes are non-blocking.
"""
import fcntl
import os
import pty
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
    print("skip git_pty: pyte is not installed")
    sys.exit(0)

COLS, ROWS = 110, 34


class Session:
    def __init__(self, binary, root, args):
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))
        env = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor", LANG="C.UTF-8", PWD=root,
                   HOME=root, XDG_CONFIG_HOME=os.path.join(root, ".config"),
                   XDG_STATE_HOME=os.path.join(root, ".state"), GIT_CONFIG_NOSYSTEM="1",
                   GIT_CONFIG_GLOBAL=os.devnull, GIT_CEILING_DIRECTORIES=os.path.dirname(root),
                   GIT_AUTHOR_NAME="A", GIT_AUTHOR_EMAIL="a@example.com", GIT_COMMITTER_NAME="C",
                   GIT_COMMITTER_EMAIL="c@example.com")
        env.pop("M3_KEYMAP", None)
        self.proc = subprocess.Popen([binary, "--keymap", "NONE"] + args, stdin=slave, stdout=slave,
                                     stderr=slave, cwd=root, env=env, start_new_session=True, close_fds=True)
        os.close(slave)
        self.master = master
        fcntl.fcntl(master, fcntl.F_SETFL, fcntl.fcntl(master, fcntl.F_GETFL) | os.O_NONBLOCK)
        self.screen = pyte.Screen(COLS, ROWS)
        self.stream = pyte.ByteStream(self.screen)

    def pump(self, seconds):
        end = time.time() + seconds
        while time.time() < end:
            ready, _, _ = select.select([self.master], [], [], 0.05)
            if ready:
                try:
                    data = os.read(self.master, 65536)
                except (BlockingIOError, InterruptedError):
                    continue
                except OSError:
                    return
                if not data:
                    return
                self.stream.feed(data)

    def send(self, keys, settle=0.5):
        data = keys.encode()
        end = time.time() + 5
        while data and time.time() < end:
            try:
                count = os.write(self.master, data)
                data = data[count:]
            except (BlockingIOError, InterruptedError):
                self.pump(0.02)
        self.pump(settle)

    def text(self):
        return "\n".join(self.screen.display)

    def close(self):
        try:
            self.send("\x1b\x1b:qa!\r", 0.2)
        except OSError:
            pass
        end = time.time() + 3
        while time.time() < end and self.proc.poll() is None:
            self.pump(0.05)
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait()
        os.close(self.master)


def git(root, *args):
    env = dict(os.environ, PWD=root, HOME=root, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CEILING_DIRECTORIES=os.path.dirname(root), GIT_AUTHOR_NAME="A", GIT_AUTHOR_EMAIL="a@example.com",
               GIT_COMMITTER_NAME="C", GIT_COMMITTER_EMAIL="c@example.com")
    out = subprocess.run(["git"] + list(args), cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert out.returncode == 0, (args, out.stderr)
    return out.stdout.decode()


def repository():
    root = os.path.realpath(tempfile.mkdtemp(prefix="m3-git-"))
    git(root, "init", "-q", "-b", "main")
    with open(os.path.join(root, "f.txt"), "w") as handle:
        handle.write("".join("line %d\n" % n for n in range(1, 31)))
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "first commit")
    with open(os.path.join(root, "f.txt"), "w") as handle:
        handle.write("".join(("line %d\n" % n) if n != 5 else "five\n" for n in range(1, 31)))
    git(root, "commit", "-q", "-am", "change five")
    return root


def scenario(binary, name, body):
    root = repository()
    try:
        body(binary, root)
        print("ok " + name)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def log_list_and_preview(binary, root):
    s = Session(binary, root, ["f.txt"])
    try:
        s.pump(1.0)
        s.send(":Git log %\r", 0.8)
        shown = s.text()
        assert "Git log f.txt" in shown, shown
        assert "change five" in shown and "first commit" in shown, shown
        assert "Author: A <a@example.com>" in shown, shown   # the preview is git show, in process
        s.send("\x1b", 0.3)
        assert "Git log f.txt" not in s.text()
    finally:
        s.close()


def blame_list_jumps(binary, root):
    s = Session(binary, root, ["f.txt"])
    try:
        s.pump(1.0)
        s.send(":Git blame\r", 0.8)
        shown = s.text()
        assert "Git blame f.txt" in shown, shown
        assert "5 " in shown and "five" in shown and "A, " in shown, shown
        s.send("\r", 0.5)
        assert "Git blame" not in s.text()
    finally:
        s.close()


def show_and_diff_scratch(binary, root):
    s = Session(binary, root, ["f.txt"])
    try:
        s.pump(1.0)
        s.send(":Git show\r", 0.8)
        assert "diff --git a/f.txt b/f.txt" in s.text() and "+five" in s.text(), s.text()
        s.send(":bdelete!\r", 0.5)
        s.send("2Gccedited\x1b:w\r", 0.8)
        s.send(":Git diff\r", 0.8)
        assert "+edited" in s.text(), s.text()
    finally:
        s.close()


def hunk_stage_and_undo(binary, root):
    with open(os.path.join(root, "f.txt"), "w") as handle:
        handle.write("".join(("line %d\n" % n) if n not in (5, 20) else "changed %d\n" % n for n in range(1, 31)))
    s = Session(binary, root, ["f.txt"])
    try:
        s.pump(1.0)
        s.send("20G", 0.3)
        s.send(":Hunk stage\r", 0.8)
        assert "Hunk staged" in s.text(), s.text()
        staged = git(root, "diff", "--cached", "-U0")
        assert "+changed 20" in staged and "changed 5" not in staged, staged
        assert git(root, "status", "--porcelain").strip() == "MM f.txt"
        s.send(":Hunk undo\r", 0.8)
        assert "Hunk unstaged" in s.text(), s.text()
        assert git(root, "diff", "--cached").strip() == ""
        s.send(":Hunk list\r", 0.8)       # the hunks are rows of the generic list
        assert "hunk 1" in s.text() and "hunk 2" in s.text(), s.text()
        s.send("\x1b", 0.3)
        s.send("gg:lnext\r", 0.5)
        s.send(":lnext\r", 0.5)
        assert "(2 of 2)" in s.text(), s.text()
        s.send("5G:Hunk preview\r", 0.6)
        assert "-five" in s.text() and "+changed 5" in s.text(), s.text()
        s.send("\x1b", 0.3)
        s.send("5Gdih:w\r", 0.8)       # the hunk is the one changed row
        assert "changed 5" not in open(os.path.join(root, "f.txt")).read()
        s.send("u:w\r", 0.8)
        s.send(":Hunk reset\r:w\r", 0.8)
        assert "changed 5" not in open(os.path.join(root, "f.txt")).read()
        assert "five" in open(os.path.join(root, "f.txt")).read()
    finally:
        s.close()


def gutter_and_plugin_switch(binary, root):
    with open(os.path.join(root, "f.txt"), "w") as handle:
        handle.write("".join(("line %d\n" % n) if n != 5 else "changed 5\n" for n in range(1, 31)))
    s = Session(binary, root, ["f.txt"])
    try:
        s.pump(1.0)

        def sign_of(needle):
            for line in s.screen.display:
                if needle in line:
                    return line[0]
            return None
        assert sign_of("changed 5") == "~", s.text()
        assert sign_of("line 6") == " ", s.text()
        assert "main" in s.text().split("\n")[-2], "the branch is on the status line:\n" + s.text()
        s.send(":PluginDisable git\r", 0.6)
        assert sign_of("changed 5") != "~", "the signs go with the plugin:\n" + s.text()
        s.send(":Hunk next\r", 0.5)
        assert "ext git is switched off" in s.text(), s.text()
        s.send(":PluginEnable git\r", 0.6)
        s.pump(0.8)
        assert sign_of("changed 5") == "~", "and come back:\n" + s.text()
        s.send(":SignsGit\r", 0.6)
        assert sign_of("changed 5") != "~", s.text()
    finally:
        s.close()


def hunk_operators_and_ends(binary, root):
    with open(os.path.join(root, "f.txt"), "w") as handle:
        handle.write("".join(("line %d\n" % n) if n not in (5, 20) else "changed %d\n" % n for n in range(1, 31)))
    s = Session(binary, root, ["f.txt"])
    try:
        s.pump(1.0)
        # ]H and [H: the last and the first change
        s.send("]H", 0.4)
        assert " 20:" in s.text().split("\n")[-2], s.text()
        s.send("[H", 0.4)
        assert " 5:" in s.text().split("\n")[-2], s.text()
        # ghs stages the hunk under the cursor, and the same key unstages it again
        s.send("5Gghs", 0.8)
        staged = git(root, "diff", "--cached", "-U0")
        assert "+changed 5" in staged and "changed 20" not in staged, staged
        assert "Hunk staged" in s.text(), s.text()
        s.send("5Gghs", 0.8)
        assert git(root, "diff", "--cached", "-U0").strip() == "", "ghs a second time must unstage"
        assert "Hunk unstaged" in s.text(), s.text()
        # ghd previews the hunk, ghl lists the hunks of the buffer in the generic list
        s.send("20Gghd", 0.6)
        assert "-line 20" in s.text() and "+changed 20" in s.text(), s.text()
        s.send("\x1b", 0.3)
        s.send("ghl", 0.8)
        assert "hunk 1" in s.text() and "hunk 2" in s.text(), s.text()
        s.send("\x1b", 0.3)
        # ghr resets the hunk under the cursor: line 20 goes back
        s.send("20Gghr", 0.8)
        s.send(":w\r", 0.6)
        body = open(os.path.join(root, "f.txt")).read()
        assert "changed 20" not in body and "changed 5" in body, body
        # Visual mode: ghs stages the hunks in the selected lines
        s.send("1GVGghs", 0.8)
        staged = git(root, "diff", "--cached", "-U0")
        assert "+changed 5" in staged, staged
        # ghS unstages the whole buffer when nothing is left to stage; ghR types the reset for the user to confirm
        s.send("ghS", 0.8)
        assert git(root, "diff", "--cached", "-U0").strip() == "", "ghS with nothing unstaged must unstage the file"
        s.send("ghR", 0.5)
        assert ":Hunk reset-buffer" in s.text(), s.text()
        s.send("\x1b", 0.3)
        assert "changed 5" in open(os.path.join(root, "f.txt")).read(), "Escape must leave the buffer alone"
        s.send("ghS", 0.8)
        staged = git(root, "diff", "--cached", "-U0")
        assert "+changed 5" in staged, staged
        # commit what is staged, from the command line (the job answers in the message line)
        s.send(":Git commit second commit\r", 1.5)
        s.pump(1.0)
        assert git(root, "log", "-1", "--format=%s").strip() == "second commit", git(root, "log", "-1", "--format=%s")
        s.send(":Git commit\r", 0.5)
        assert "message is needed" in s.text(), s.text()
        # push and pull against a local remote
        bare = tempfile.mkdtemp(prefix="m3-git-remote-")
        try:
            git(bare, "init", "-q", "--bare", "-b", "main")
            git(root, "remote", "add", "origin", bare)
            git(root, "push", "-q", "-u", "origin", "main")
            git(root, "commit", "-q", "--allow-empty", "-m", "local only")
            s.send(":Git push\r", 2.0)
            s.pump(1.0)
            assert git(bare, "log", "-1", "--format=%s").strip() == "local only", git(bare, "log", "-1", "--format=%s")
            s.send(":Git pull\r", 2.0)
            s.pump(0.8)
            assert "Git:" in s.text() or "up to date" in s.text().lower(), s.text()
        finally:
            shutil.rmtree(bare, ignore_errors=True)
    finally:
        s.close()


def main():
    binary = sys.argv[1]
    scenario(binary, ":Git log lists the history with a git show preview", log_list_and_preview)
    scenario(binary, ":Git blame is a list that jumps to the line", blame_list_jumps)
    scenario(binary, ":Git show and :Git diff open scratch buffers", show_and_diff_scratch)
    scenario(binary, ":Hunk stage, undo, preview, reset and dih", hunk_stage_and_undo)
    scenario(binary, "the gutter, the branch and the plugin switch", gutter_and_plugin_switch)
    scenario(binary, "ghs ghr ghS ghR ghd ghl, ]H [H, :Git commit", hunk_operators_and_ends)


main()
