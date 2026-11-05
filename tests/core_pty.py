#!/usr/bin/env python3
"""Core-functionality checks of the real m3 binary in a pty (docs/CORE-STATUS.md names the scenario per row).

    python3 tests/core_pty.py ./m3 [--only NAME]

Reuses the Session of tests/e2e.py (pyte screen, temp HOME and XDG dirs, `-u NONE`). Every wait is "until the text
shows up" with seconds of margin; no fixed /tmp path, no directory-content dependence.
"""
import os
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import e2e  # noqa: E402
from e2e import Session  # noqa: E402

SCENARIOS = {}


def scenario(fn):
    SCENARIOS[fn.__name__] = fn
    return fn


def project():
    root = tempfile.mkdtemp(prefix="m3d-core-")
    with open(os.path.join(root, "a.txt"), "w") as f:
        f.write("one\ntwo\nthree\n")
    return root


@scenario
def messages_ring(binary, root):
    s = Session(binary, root, ["a.txt"])
    try:
        assert s.wait_for("one"), s.text()
        s.send(":echo 'first note'\r")
        s.send(":echo 'second note'\r")
        s.send(":nosuchcmd\r")
        s.send(":messages\r", settle=0.4)
        text = s.text()
        a, b, c = text.find("first note"), text.find("second note"), text.find("E492")
        assert 0 <= a < b < c, "ring order wrong:\n" + text
        s.send("\r")
        s.send(":messages clear\r")
        s.send(":echo 'only one'\r")
        s.send(":messages\r", settle=0.4)
        assert "first note" not in s.text() and "only one" in s.text(), s.text()
    finally:
        s.close()


def recovery_files(root):
    folder = os.path.join(root, ".state", "m3", "recover")
    return sorted(os.listdir(folder)) if os.path.isdir(folder) else []


def wait_until(check, seconds=10.0):
    end = time.time() + seconds
    while time.time() < end:
        if check():
            return True
        time.sleep(0.1)
    return False


@scenario
def recovery_after_kill9(binary, root):
    keymap = os.path.join(root, "empty.vim")
    open(keymap, "w").close()
    s = Session(binary, root, ["a.txt"], keymap=keymap)
    try:
        assert s.wait_for("one"), s.text()
        s.send("ggIRECOVER \x1b", settle=0.3)
        assert wait_until(lambda: recovery_files(root)), "no recovery file after the idle time"
        s.proc.kill()
        s.proc.wait()
        os.close(s.master)
    except BaseException:
        s.close()
        raise
    assert open(os.path.join(root, "a.txt")).read() == "one\ntwo\nthree\n", "kill -9 must not touch the file"
    second = Session(binary, root, ["a.txt"], keymap=keymap)
    try:
        assert second.wait_for("one"), second.text()
        assert second.wait_for("W325"), "no notice about the recovery file:\n" + second.text()
        second.pump(2.5)  # the idle tick must not delete the recovery file of a buffer that was only opened
        assert recovery_files(root), "the recovery file went away on its own"
        second.send(":recover\r", settle=0.4)
        assert "RECOVER one" in second.text(), second.text()
        second.send(":w\r", settle=0.4)
        assert open(os.path.join(root, "a.txt")).read().startswith("RECOVER one\n")
        assert wait_until(lambda: not recovery_files(root), 3.0), "the recovery file stays after :w"
        second.send("ix\x1b", settle=0.3)
        assert wait_until(lambda: recovery_files(root)), "no recovery file for the second edit"
        second.send(":q!\r", settle=0.5)
        second.pump(1.0)
        assert not recovery_files(root), "a deliberate :q! leaves a recovery file"
    finally:
        second.close()


def put_bytes(root, name, data):
    with open(os.path.join(root, name), "wb") as handle:
        handle.write(data)


def get_bytes(root, name):
    with open(os.path.join(root, name), "rb") as handle:
        return handle.read()


@scenario
def encoding_and_line_endings(binary, root):
    put_bytes(root, "crlf.txt", b"one\r\ntwo\r\nthree\r\n")
    put_bytes(root, "bom.txt", b"\xef\xbb\xbfhello\nworld\n")
    put_bytes(root, "lat.txt", b"caf\xe9\nx\n")
    put_bytes(root, "mixed.txt", b"one\r\ntwo\nthree\r\n")
    for name, edit, shown, expect in (
        ("crlf.txt", "Ax", "fileformat=dos", b"onex\r\ntwo\r\nthree\r\n"),
        ("bom.txt", "Ax", "bomb", b"\xef\xbb\xbfhellox\nworld\n"),
        ("lat.txt", "Ax", "fileencoding=latin1", b"caf\xe9x\nx\n"),
        ("mixed.txt", "Ax", "fileformat=unix", b"one\rx\ntwo\nthree\r\n"),
    ):
        s = Session(binary, root, [name])
        try:
            s.pump(0.5)
            key = {"crlf.txt": ":set ff?\r", "bom.txt": ":set bomb?\r", "lat.txt": ":set fenc?\r", "mixed.txt": ":set ff?\r"}[name]
            s.send(key, settle=0.4)
            assert shown in s.text(), "%s: %r not on screen:\n%s" % (name, shown, s.text())
            s.send("\x1b", settle=0.2)
            if name == "lat.txt":
                s.send("gg", settle=0.2)
                assert "caf\u00e9" in s.text(), s.text()
            else:
                s.send("gg", settle=0.2)
            s.send(edit + "\x1b", settle=0.3)
            s.send(":w\r", settle=0.5)
            assert "written" in s.text(), s.text()
            got = get_bytes(root, name)
            assert got == expect, "%s: wrote %r, wanted %r" % (name, got, expect)
        finally:
            s.close()
    # a character Latin-1 cannot hold is refused, the file stays as it was
    s = Session(binary, root, ["lat.txt"])
    try:
        s.pump(0.6)
        s.send("A\u65e5\x1b:w\r".encode("utf-8"), settle=0.5)
        assert "E513" in s.text(), s.text()
        assert get_bytes(root, "lat.txt") == b"caf\xe9x\nx\n"
        s.send(":set fenc=utf-8\r:w\r", settle=0.5)
        assert b"\xc3\xa9" in get_bytes(root, "lat.txt"), "fenc=utf-8 should write UTF-8"
    finally:
        s.close()


@scenario
def directory_argument_and_clean(binary, root):
    os.makedirs(os.path.join(root, "sub"))
    open(os.path.join(root, "sub", "inner.txt"), "w").write("inner\n")
    s = Session(binary, root, ["sub"])
    try:
        assert s.wait_for("inner.txt"), "m3 DIR should open the directory listing:\n" + s.text()
        s.send("\r", settle=0.5)
        assert s.wait_for("inner"), s.text()
    finally:
        s.close()
    # --clean: no state files are kept
    state = os.path.join(root, ".state")
    s = Session(binary, root, ["--clean", "a.txt"], keymap=os.path.join(root, "none.vim"))
    try:
        assert s.wait_for("one"), s.text()
        s.send("ggx:w\r", settle=0.4)
    finally:
        s.close()
    assert not os.path.exists(os.path.join(state, "m3", "recent")), "--clean must keep no state"


@scenario
def registers_picker(binary, root):
    s = Session(binary, root, ["a.txt"])
    try:
        assert s.wait_for("one"), s.text()
        s.send("yy", settle=0.2)
        s.send(":Registers\r", settle=0.6)
        assert s.wait_for("Registers"), s.text()
        assert "one" in s.text().split("Registers", 1)[1], s.text()
        s.send("\x1b", settle=0.3)
        assert s.wait_for("NORMAL"), s.text()
    finally:
        s.close()


@scenario
def set_query_toggle_reset(binary, root):
    s = Session(binary, root, ["a.txt"])
    try:
        assert s.wait_for("one"), s.text()
        for keys, shown in ((":set ts?\r", "tabstop=8"), (":set sw=3 sw?\r", "shiftwidth=3"), (":set sw&\r:set sw?\r", "shiftwidth=8"),
                            (":set invwrap wrap?\r", "nowrap"), (":set wrap!\r:set wrap?\r", "  wrap"), (":set fenc?\r", "fileencoding=utf-8"),
                            (":set inccommand?\r", "inccommand="), (":set nosuchopt\r", "E518")):
            s.send(keys, settle=0.4)
            assert shown in s.text(), "%r: %r not on screen:\n%s" % (keys, shown, s.text())
            s.send("\x1b", settle=0.2)
    finally:
        s.close()


@scenario
def osc52_without_clipboard_tool(binary, root):
    empty = os.path.join(root, "nobin")
    os.makedirs(empty)
    s = Session(binary, root, ["a.txt"], env={"PATH": empty})
    raw = []
    original = s.stream.feed
    s.stream.feed = lambda data: (raw.append(data), original(data))[1]
    try:
        assert s.wait_for("one"), s.text()
        s.send('"+yy', settle=0.6)
        got = b"".join(raw)
        assert b"\x1b]52;c;b25lCg==" in got, "no OSC 52 for 'one\\n': %r" % got[-300:]
        s.send('"+p', settle=0.3)
        assert s.text().count("one") >= 2, s.text()
    finally:
        s.close()
    # M3_NO_OSC52=1: nothing is written
    s = Session(binary, root, ["a.txt"], env={"PATH": empty, "M3_NO_OSC52": "1"})
    raw = []
    original = s.stream.feed
    s.stream.feed = lambda data: (raw.append(data), original(data))[1]
    try:
        assert s.wait_for("one"), s.text()
        s.send('"+yy', settle=0.6)
        assert b"]52;" not in b"".join(raw)
    finally:
        s.close()


def cpu_ticks(pid):
    """User plus system clock ticks of a process, or None where there is no /proc (macOS)."""
    try:
        with open("/proc/%d/stat" % pid) as handle:
            fields = handle.read().rsplit(")", 1)[1].split()
        return int(fields[11]) + int(fields[12])
    except (OSError, IndexError, ValueError):
        return None


@scenario
def long_line_idle_cpu(binary, root):
    """An idle editor on a one-line 1 MB file must not scan the line on every tick (it once cost 60 percent of a core)."""
    with open(os.path.join(root, "long.txt"), "w") as handle:
        handle.write("word " * 200000 + "\n")
    s = Session(binary, root, ["long.txt"])
    try:
        assert s.wait_for("word", timeout=30), s.text()
        if cpu_ticks(s.proc.pid) is None:
            print("     (no /proc here: idle CPU not measured)")
            return
        s.pump(2.0)
        before = cpu_ticks(s.proc.pid)
        s.pump(3.0)
        used = cpu_ticks(s.proc.pid) - before
        hz = os.sysconf("SC_CLK_TCK")
        assert used < 0.15 * 3.0 * hz, "idle for 3 s used %d ticks (%.0f percent of a core)" % (used, 100.0 * used / (3.0 * hz))
    finally:
        s.close()


@scenario
def quickfix_commands(binary, root):
    s = Session(binary, root, ["a.txt"])
    try:
        assert s.wait_for("one"), s.text()
        s.send(" fd", settle=0.8)
        assert s.wait_for("Lines"), s.text()
        s.send("\x11", settle=0.6)  # CTRL-Q: every entry to the quickfix list
        s.send("\x1b", settle=0.4)
        s.send(":clist\r", settle=0.5)
        text = s.text()
        assert "a.txt:1:" in text and "a.txt:3:" in text, "clist:\n" + text
        s.send("\r", settle=0.3)
        s.send(":cc 3\r", settle=0.5)
        assert "(3 of 3)" in s.text() and "3:1" in s.text(), s.text()
        s.send(":cc 1\r", settle=0.5)
        assert "(1 of 3)" in s.text(), s.text()
        s.send(":cwindow\r", settle=0.6)
        assert "Quickfix" in s.text(), s.text()
    finally:
        s.close()


@scenario
def autocmds_user_commands_and_if_in_keymap(binary, root):
    keymap = os.path.join(root, "k.vim")
    with open(keymap, "w") as handle:
        handle.write("\n".join([
            "augroup core",
            "  autocmd!",
            "  autocmd BufWritePre *.txt s/one/ONE/e",
            "  autocmd InsertLeave *.txt s/$/!/e",
            "  autocmd VimEnter * normal! G",
            "augroup END",
            "if has('nvim')",
            "  command! -nargs=1 Greet s/two/<args>/",
            "else",
            "  command! -nargs=1 Greet s/two/WRONG/",
            "endif",
            "if has('win32')",
            "  command! Never s/three/NEVER/",
            "elseif exists('$HOME')",
            "  command! Never s/three/THREE/",
            "endif",
            "if executable('sh')",
            "  command! HaveSh s/three/sh/",
            "endif",
            ""]))
    s = Session(binary, root, ["a.txt"], keymap=keymap)
    try:
        assert s.wait_for("three"), s.text()
        assert "3:1" in s.text(), "VimEnter should have run G:\n" + s.text()
        s.send("ix\x1b", settle=0.4)
        assert "xthree!" in s.text(), "InsertLeave autocmd did not run:\n" + s.text()
        s.send(":2\r:Greet hello\r", settle=0.4)
        assert "hello" in s.text(), s.text()
        s.send(":3\r:Never\r", settle=0.4)
        assert "THREE" in s.text() or "xTHREE" in s.text(), "if/elseif in the keymap file:\n" + s.text()
        s.send(":Greet\r", settle=0.4)
        assert "E471" in s.text(), s.text()
        s.send("gg:w\r", settle=0.6)
        assert "written" in s.text(), s.text()
    finally:
        s.close()
    with open(os.path.join(root, "a.txt")) as handle:
        body = handle.read()
    assert body.startswith("ONE"), "BufWritePre autocmd should have changed the text: %r" % body


@scenario
def vi_command_line_and_ex_mode(binary, root):
    with open(os.path.join(root, "b.txt"), "w") as f:
        f.write("beta\ngamma\n")
    with open(os.path.join(root, "tags"), "w") as f:
        f.write("gamma\tb.txt\t/^gamma$/;\"\tf\n")
    # -c runs an ex line after the files are read, +N goes to a line
    s = Session(binary, root, ["-c", "s/one/ONE/", "+3", "a.txt", "b.txt"])
    try:
        assert s.wait_for("ONE"), s.text()
        s.send("x", settle=0.3)
        assert "hree" in s.text() and "three" not in s.text(), "+3 should put the cursor on line 3:\n" + s.text()
        # the argument list: :next goes to the second file, :args shows both with the current one in brackets
        s.send(":w\r:next\r", settle=0.5)
        assert "beta" in s.text(), s.text()
        s.send(":args\r", settle=0.4)
        assert "a.txt [b.txt]" in s.text(), s.text()
        s.send(":prev\r", settle=0.4)
        assert "ONE" in s.text(), s.text()
        # Ex mode: the command line stays open; :visual leaves
        s.send("gQ", settle=0.3)
        s.send("2\r", settle=0.3)
        s.send("s/two/TWO/\r", settle=0.3)
        s.send("visual\r", settle=0.3)
        assert "TWO" in s.text(), s.text()
        s.send("ihi\x1b", settle=0.3)
        assert "hi" in s.text() and "-- INSERT --" not in s.text(), s.text()
    finally:
        s.close()
    # -t jumps to the tag
    s = Session(binary, root, ["-t", "gamma", "a.txt"])
    try:
        s.send("", settle=0.5)
        assert s.wait_for("gamma"), s.text()
        s.send(":pop\r", settle=0.4)
        assert "ONE" in s.text() or "three" in s.text() or "hree" in s.text(), s.text()
    finally:
        s.close()


def main():
    binary = os.path.abspath(sys.argv[1])
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    failed = 0
    for name, fn in SCENARIOS.items():
        if only and name != only:
            continue
        root = project()
        try:
            fn(binary, root)
            print("ok   %s" % name)
        except AssertionError as error:
            failed += 1
            print("FAIL %s: %s" % (name, error))
        except Exception as error:  # noqa
            failed += 1
            print("FAIL %s: %r" % (name, error))
        finally:
            shutil.rmtree(root, ignore_errors=True)
    print("core_pty: %d scenarios, %d failed" % (len(SCENARIOS) if not only else 1, failed))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
