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
