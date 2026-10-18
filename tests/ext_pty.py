#!/usr/bin/env python3
"""pty checks of the extension API with the sample extension (MEDX_trim_whitespace).

    python3 tests/ext_pty.py WITH_EXT_BINARY DEFAULT_BINARY

Needs no pyte: results are read from the files the editor writes. macOS-safe: the project directory is
resolved with realpath and handed to the child as both cwd and PWD, git is fenced off with
GIT_CEILING_DIRECTORIES, pty writes are non-blocking, no GNU-only tools.
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


class Session:
    def __init__(self, binary, root, args):
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 30, 100, 0, 0))
        env = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor", LANG="C.UTF-8", PWD=root,
                   HOME=root, XDG_CONFIG_HOME=os.path.join(root, ".config"),
                   XDG_STATE_HOME=os.path.join(root, ".state"),
                   GIT_CEILING_DIRECTORIES=os.path.dirname(root))
        env.pop("M3_KEYMAP", None)
        self.proc = subprocess.Popen([binary, "--keymap", "NONE"] + args, stdin=slave, stdout=slave,
                                     stderr=slave, cwd=root, env=env, start_new_session=True,
                                     close_fds=True)
        os.close(slave)
        self.master = master
        fcntl.fcntl(master, fcntl.F_SETFL, fcntl.fcntl(master, fcntl.F_GETFL) | os.O_NONBLOCK)
        self.seen = b""

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
                self.seen += data

    def send(self, keys, settle=0.4):
        data = keys.encode()
        end = time.time() + 5
        while data and time.time() < end:
            try:
                count = os.write(self.master, data)
                data = data[count:]
            except (BlockingIOError, InterruptedError):
                self.pump(0.02)
        self.pump(settle)

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


def read(path):
    with open(path, "rb") as handle:
        return handle.read()


def scenario(binary, name, body):
    root = os.path.realpath(tempfile.mkdtemp(prefix="m3-ext-"))
    try:
        body(binary, root)
        print("ok " + name)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def trim_on_write(binary, root):
    path = os.path.join(root, "a.txt")
    with open(path, "w") as handle:
        handle.write("one  \ntwo\t\nthree\n")
    s = Session(binary, root, ["a.txt"])
    try:
        s.pump(1.0)
        s.send(":w\r", 0.8)
    finally:
        s.close()
    assert read(path) == b"one\ntwo\nthree\n", read(path)


def untouched_by_default(binary, root):
    path = os.path.join(root, "a.txt")
    with open(path, "w") as handle:
        handle.write("one  \ntwo\t\n")
    s = Session(binary, root, ["a.txt"])
    try:
        s.pump(1.0)
        s.send(":w\r", 0.8)
    finally:
        s.close()
    assert read(path) == b"one  \ntwo\t\n", read(path)


def command_undo_and_dot(binary, root):
    path = os.path.join(root, "a.txt")
    with open(path, "w") as handle:
        handle.write("ab  \ncd  \n")
    s = Session(binary, root, ["a.txt"])
    try:
        s.pump(1.0)
        s.send("x", 0.3)             # "b  "
        s.send(":TrimTrailing\r", 0.6)  # "b"
        s.send(".", 0.3)             # dot still repeats x: ""
        s.send(":w\r", 0.8)
        assert read(path) == b"\ncd\n", read(path)
        s.send("u", 0.3)             # undoes the dot
        s.send("u", 0.3)             # undoes the trim as ONE step (line 2 as well)
        s.send(":w\r", 0.8)
    finally:
        s.close()
    # the write trims again, so only the text before the trim is visible through undo of x: "b" + "cd"
    assert read(path) == b"b\ncd\n", read(path)


def main():
    with_ext, default = sys.argv[1], sys.argv[2]
    scenario(with_ext, "trim on write (ext build)", trim_on_write)
    scenario(default, "default build leaves the file alone", untouched_by_default)
    scenario(with_ext, "command, one undo step, dot unchanged", command_undo_and_dot)


main()
