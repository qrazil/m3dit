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
