#!/usr/bin/env python3
"""Plugins end to end: builds that contain the fixture plugins (tests/fixtures/plugins), in a pty.

    python3 tests/plugins_pty.py LAZY_BINARY EAGER_BINARY DEFAULT_BINARY

  LAZY_BINARY     built with `--plugin-dir tests/fixtures/plugins --plugins hello`
  EAGER_BINARY    built with `--plugin-dir tests/fixtures/plugins --plugins greeter` (requires hello)
  DEFAULT_BINARY  the plain build, which must know nothing of either

Checked: `:Plugins` lists the compiled plugins with their state (lazy, then active after the first `:Hello`); the
lazy plugin's command, key and write hook work and wake it; `:PluginDisable` unmaps its key and silences the
command and `:PluginEnable` brings both back; the eager plugin activated at start-up, after the plugin it requires,
and exactly once (greeter.log); the default build has no `Hello` command and no plugin section in `:Plugins`.
Skips with a note when pyte is missing. macOS-safe: non-blocking pty writes (uxperf.Editor), every wait is
"until quiet" with hundreds of milliseconds, the project directory is resolved with realpath and handed over as
cwd and PWD, git is fenced off with GIT_CEILING_DIRECTORIES.
"""
import os
import shutil
import sys
import tempfile

try:
    import pyte
except ImportError:
    print("skip plugins_pty: pyte is not installed")
    sys.exit(0)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "bench"))
import uxperf  # noqa: E402

ROWS, COLS = 30, 110
failures = []
checks = 0


def check(name, condition, detail=""):
    global checks
    checks += 1
    if not condition:
        failures.append("%s %s" % (name, detail))
        print("FAIL " + name + (": " + detail if detail else ""))


class Session:
    def __init__(self, binary, root):
        env = {"PWD": root, "GIT_CEILING_DIRECTORIES": os.path.dirname(root), "M3_NO_ANIM": "1",
               "TUI_WIDTH_PROBE": "off"}
        self.ed = uxperf.Editor(binary, root, ["a.txt"], ROWS, COLS, env=env)
        self.screen = pyte.Screen(COLS, ROWS)
        self.stream = pyte.ByteStream(self.screen)
        self.fed = 0
        self.settle(0.5)

    def settle(self, quiet=0.3):
        self.ed.settle(quiet, 6)
        self.stream.feed(bytes(self.ed.raw[self.fed:]))
        self.fed = len(self.ed.raw)

    def type(self, keys, quiet=0.3):
        self.ed.send(keys)
        self.settle(quiet)

    def text(self):
        return "\n".join(line.rstrip() for line in self.screen.display)

    def close(self):
        self.ed.close()


def project(parent, name):
    root = os.path.realpath(os.path.join(parent, name))
    os.makedirs(root)
    with open(os.path.join(root, "a.txt"), "w") as handle:
        handle.write("alpha\nbeta\n")
    return root


def main():
    lazy_bin, eager_bin, default_bin = [os.path.abspath(a) for a in sys.argv[1:4]]
    parent = os.path.realpath(tempfile.mkdtemp(prefix="m3plugins"))
    try:
        # the lazy plugin
        root = project(parent, "lazy")
        term = Session(lazy_bin, root)
        term.type(":Plugins\r")
        text = term.text()
        check("lazy: the plugin section is there", "Compiled plugins (api 0.2.0):" in text, text)
        check("lazy: the plugin waits", "lazy  hello  fixture: a lazy command, a key and a write hook" in text, text)
        check("lazy: the core features are still listed", "on   core  keymap tree" in text)
        term.type("\x1b:Hello world\r")
        check("lazy: the command woke the plugin and ran", "hello world" in term.text(), term.text())
        term.type(":Plugins\r")
        check("lazy: now active", "active  hello" in term.text(), term.text())
        term.type("\x1b\\zh")
        check("lazy: the key runs the command", "hello keyed" in term.text(), term.text())
        term.type(":w\r")
        log = os.path.join(root, "hello.log")
        check("lazy: the write hook ran", os.path.exists(log) and open(log).read().startswith("wrote ") and open(log).read().rstrip().endswith("a.txt"), term.text())
        term.type(":PluginDisable hello\r")
        term.type("\\zh")
        check("lazy: disabled, the key does nothing", "hello keyed" not in term.text().split("\n")[-1], term.text())
        term.type(":Hello again\r")
        check("lazy: disabled, the command says so", "ext hello is switched off" in term.text(), term.text())
        term.type(":Plugins\r")
        check("lazy: :Plugins shows it off", "off  hello" in term.text(), term.text())
        term.type("\x1b:PluginEnable hello\r")
        term.type(":Hello back\r")
        check("lazy: enabled again", "hello back" in term.text(), term.text())
        term.close()

        # the eager plugin, and the plugin it requires
        root = project(parent, "eager")
        term = Session(eager_bin, root)
        log = os.path.join(root, "greeter.log")
        check("eager: activated at start-up, once", os.path.exists(log) and open(log).read() == "ready\n")
        term.type(":Plugins\r")
        text = term.text()
        check("eager: both are active, the dependency first",
              text.find("active  hello") >= 0 and text.find("active  greeter") > text.find("active  hello"), text)
        term.close()

        # the plain build knows neither
        root = project(parent, "plain")
        term = Session(default_bin, root)
        term.type(":Hello x\r")
        check("plain: no Hello command", "E492" in term.text() or "Not an editor command" in term.text(), term.text())
        term.type(":Plugins\r")
        check("plain: no plugin section", "Compiled plugins" not in term.text(), term.text())
        term.close()
    finally:
        shutil.rmtree(parent, ignore_errors=True)
    print("plugins_pty: %d checks, %d failed" % (checks, len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
