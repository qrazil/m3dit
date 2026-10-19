#!/usr/bin/env python3
"""Latency and frame-quality harness for m3 (docs/UX-PERF.md).

    python3 bench/uxperf.py --m3d ./m3 [--rows 60 --cols 200] [--runs 30]
                            [--only key,hold,resize,storm,idle,wrap,pum] [--json OUT]
                            [--env M3_NO_ANIM=1] [--check] [--no-sync-reply]

Everything runs the real binary in a pty. A "frame" is one burst of output: the
bytes between two gaps of at least GAP seconds, or, when the editor wraps its
frames in synchronized-output markers (DEC mode 2026), the bytes between
`CSI ? 2026 h` and `CSI ? 2026 l`. The harness answers the editor's DECRQM
query (`CSI ? 2026 $ p`) like a terminal that supports the mode, unless
--no-sync-reply says otherwise.

Measured, per action, over --runs repetitions:

  first byte   key written -> first output byte
  first frame  key written -> end of the first frame
  settled      key written -> end of the last frame (animations: their length)
  frames       frames written for the key
  bytes        bytes of the first frame / all frames

and, for a held key (auto-repeat simulated at REPEAT_HZ), frames per second,
bytes per frame and the key-to-frame latency distribution.

Everything is printed as a markdown table; --json writes the raw numbers.
--check fails (exit 1) only on gross regressions (the budgets at the top of
this file are generous soft limits, see docs/UX-PERF.md for the real ones).

Portable: no /proc needed (idle CPU and wakeups are reported only where
/proc exists), no GNU tools, temporary files from tempfile.
"""
import argparse
import fcntl
import json
import os
import pty
import random
import re
import select
import signal
import statistics
import struct
import subprocess
import sys
import tempfile
import termios
import time

GAP = 0.004           # seconds of silence that end a frame (no sync markers)
REPEAT_HZ = 30        # simulated key auto-repeat
SYNC_BEGIN = b"\x1b[?2026h"
SYNC_END = b"\x1b[?2026l"
DECRQM = b"\x1b[?2026$p"

# Gross-regression limits for --check (seconds / bytes). Deliberately loose:
# machine noise must never fail a build; real budgets are in docs/UX-PERF.md.
GROSS = {
    "key_first_frame_p99": 0.100,
    "single_cell_bytes": 400,
    "hold_fps_min": 10,
    "idle_wakeups_per_s": 30,   # reported only
}


LIVE = []


def _watchdog(_sig, _frm):
    for pr in LIVE:
        try:
            os.killpg(os.getpgid(pr.pid), signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass
    print("uxperf: watchdog expired -- the run stalled", flush=True)
    os._exit(2)


def percentile(values, q):
    if not values:
        return float("nan")
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round(q * (len(ordered) - 1))))
    return ordered[index]


class Frames:
    """Output grouped into frames, with the time each frame ended."""

    def __init__(self):
        self.items = []     # (t_start, t_end, nbytes)
        self.total = 0

    def add(self, t0, t1, n):
        self.items.append((t0, t1, n))
        self.total += n


class Editor:
    def __init__(self, binary, cwd, args=(), rows=60, cols=200, env=None, keymap="NONE",
                 sync_reply=True, focus=False):
        self.rows, self.cols = rows, cols
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        full = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor", LANG="C.UTF-8",
                    HOME=cwd, XDG_CONFIG_HOME=os.path.join(cwd, ".config"),
                    XDG_STATE_HOME=os.path.join(cwd, ".state"))
        full.pop("M3_KEYMAP", None)
        full.pop("M3_NO_ANIM", None)
        if env:
            full.update(env)
        self.proc = subprocess.Popen([binary, "-u", keymap] + list(args), stdin=slave, stdout=slave,
                                     stderr=slave, cwd=cwd, env=full, start_new_session=True,
                                     close_fds=True)
        os.close(slave)
        # a blocking write into a full pty (macOS keeps about 1 KB) would hang the whole run
        fcntl.fcntl(master, fcntl.F_SETFL, fcntl.fcntl(master, fcntl.F_GETFL) | os.O_NONBLOCK)
        LIVE.append(self.proc)
        self.master = master
        self.sync_reply = sync_reply
        self.carry = b""
        self.raw = bytearray()
        self.saw_sync = False

    # -- reading ------------------------------------------------------------

    def _answer_queries(self, data):
        if self.sync_reply and DECRQM in data:
            try:
                os.write(self.master, b"\x1b[?2026;2$y")
            except OSError:
                pass

    def read_frames(self, deadline, quiet, t_key=None, min_frames=0):
        """Read until `quiet` seconds pass with no output (and at least min_frames frames
        were seen), or until `deadline`. Returns (Frames, first_byte_time or None)."""
        frames = Frames()
        first = None
        cur_start = None
        cur_bytes = 0
        last = None
        in_sync = False
        began = time.perf_counter()
        while True:
            now = time.perf_counter()
            if now >= deadline:
                break
            wait = GAP if (cur_start is not None and not in_sync) else min(quiet, deadline - now)
            wait = max(0.0003, min(wait, deadline - now))
            ready, _, _ = select.select([self.master], [], [], wait)
            if ready:
                try:
                    data = os.read(self.master, 1 << 20)
                except OSError:
                    break
                if not data:
                    break
                t = time.perf_counter()
                self.raw += data
                self._answer_queries(data)
                if first is None:
                    first = t
                if cur_start is None:
                    cur_start = t
                cur_bytes += len(data)
                last = t
                if SYNC_BEGIN in data:
                    self.saw_sync = True
                    in_sync = True
                if SYNC_END in data:
                    in_sync = False
                    frames.add(cur_start, t, cur_bytes)
                    cur_start, cur_bytes = None, 0
                continue
            t = time.perf_counter()
            if cur_start is not None and not in_sync and t - last >= GAP:
                frames.add(cur_start, last, cur_bytes)
                cur_start, cur_bytes = None, 0
            if cur_start is None and len(frames.items) >= min_frames:
                since = t - (last if last is not None else began)
                if since >= quiet:
                    break
        if cur_start is not None:
            frames.add(cur_start, last, cur_bytes)
        return frames, first

    def settle(self, quiet=0.25, limit=10.0):
        """Wait for the editor to go quiet; returns total bytes."""
        frames, _ = self.read_frames(time.perf_counter() + limit, quiet)
        return frames.total

    def wait_text(self, needle, pyte_screen, timeout=8.0):
        end = time.perf_counter() + timeout
        while time.perf_counter() < end:
            self.settle(0.1, 1.0)
            if needle in "\n".join(pyte_screen()):
                return True
        return False

    # -- writing --------------------------------------------------------------

    def send(self, data, limit=5.0):
        """Write `data` without ever blocking: drain the editor's output while the pty is full."""
        if isinstance(data, str):
            data = data.encode()
        end = time.perf_counter() + limit
        view = memoryview(data)
        while len(view) and time.perf_counter() < end:
            r, w, _ = select.select([self.master], [self.master], [], 0.05)
            if r:
                try:
                    got = os.read(self.master, 1 << 20)
                except OSError:
                    return
                self.raw += got
                self._answer_queries(got)
            if w:
                try:
                    view = view[os.write(self.master, view[:512]):]
                except (BlockingIOError, InterruptedError):
                    pass
                except OSError:
                    return

    def write(self, data, chunk=4096):
        if isinstance(data, str):
            data = data.encode()
        view = memoryview(data)
        while len(view):
            ready = select.select([self.master], [self.master], [], 1.0)
            if ready[0]:
                try:
                    got = os.read(self.master, 1 << 20)
                except OSError:
                    return
                self.raw += got
                self._answer_queries(got)
            if ready[1]:
                try:
                    n = os.write(self.master, view[:min(chunk, 512)])
                except (BlockingIOError, InterruptedError):
                    continue
                except OSError:
                    return
                view = view[n:]

    def key(self, keys, quiet=0.12, limit=3.0, min_frames=1):
        """Send `keys`, return a dict of measurements."""
        if isinstance(keys, str):
            keys = keys.encode()
        t0 = time.perf_counter()
        self.send(keys)
        frames, first = self.read_frames(t0 + limit, quiet, t_key=t0, min_frames=min_frames)
        out = {"frames": len(frames.items), "bytes_all": frames.total}
        out["first_byte"] = (first - t0) if first else None
        if frames.items:
            out["first_frame"] = frames.items[0][1] - t0
            out["first_frame_bytes"] = frames.items[0][2]
            out["settled"] = frames.items[-1][1] - t0
            out["gaps"] = [frames.items[i + 1][0] - frames.items[i][0] for i in range(len(frames.items) - 1)]
        else:
            out["first_frame"] = out["first_frame_bytes"] = out["settled"] = None
            out["gaps"] = []
        return out

    def resize(self, rows, cols):
        fcntl.ioctl(self.master, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        try:
            os.killpg(os.getpgid(self.proc.pid), signal.SIGWINCH)
        except OSError:
            pass
        self.rows, self.cols = rows, cols

    def cpu_stats(self):
        """(cpu seconds, voluntary context switches) from /proc, or None."""
        try:
            with open("/proc/%d/stat" % self.proc.pid) as f:
                fields = f.read().rsplit(")", 1)[1].split()
            ticks = int(fields[11]) + int(fields[12])
            hz = os.sysconf("SC_CLK_TCK")
            switches = 0
            with open("/proc/%d/status" % self.proc.pid) as f:
                for line in f:
                    if line.startswith(("voluntary_ctxt_switches", "nonvoluntary_ctxt_switches")):
                        switches += int(line.split()[1])
            return ticks / hz, switches
        except (OSError, ValueError, IndexError):
            return None

    def close(self):
        self.send(b"\x1b\x1b:qa!\r", limit=1.0)
        end = time.time() + 3
        while time.time() < end and self.proc.poll() is None:
            try:
                select.select([self.master], [], [], 0.05)
                os.read(self.master, 1 << 20)
            except OSError:
                break
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait()
        try:
            os.close(self.master)
        except OSError:
            pass


# -- fixtures -------------------------------------------------------------------

def make_source(path, lines, seed=1):
    rng = random.Random(seed)
    words = ["alpha", "beta", "gamma", "delta", "value", "index", "count", "result", "buffer", "needle_rare"]
    with open(path, "w") as f:
        for i in range(lines):
            indent = "    " * rng.randrange(0, 4)
            a, b, c = (rng.choice(words) for _ in range(3))
            if i % 97 == 7:
                f.write("%sunique_marker_%d = %s\n" % (indent, i, "needle_rare"))
            else:
                f.write("%sint %s_%d = %s(%s, %d); // %s\n" % (indent, a, i, b, c, rng.randrange(1000), "line"))


def make_wrapped(path, lines, width=340, seed=2):
    rng = random.Random(seed)
    words = ["lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit", "needle_rare"]
    with open(path, "w") as f:
        for i in range(lines):
            text = []
            while sum(len(w) + 1 for w in text) < width:
                text.append(rng.choice(words))
            f.write("%d: %s\n" % (i, " ".join(text)))


# -- scenarios -------------------------------------------------------------------

def stats(values):
    values = [v for v in values if v is not None]
    if not values:
        return {"n": 0}
    return {"n": len(values), "p50": statistics.median(values), "p99": percentile(values, 0.99),
            "max": max(values), "mean": statistics.fmean(values)}


def ms(v):
    return "-" if v is None or v != v else "%.1f" % (v * 1000.0)


def run_key_actions(binary, args, root):
    """Per-action latency and bytes. Each action is repeated args.runs times."""
    results = {}
    big = os.path.join(root, "big.txt")
    make_source(big, 3000)
    ed = Editor(binary, root, [big], args.rows, args.cols, env=args.env, sync_reply=args.sync_reply)
    try:
        ed.settle(0.4, 10)
        ed.key("500G", limit=2.0)       # somewhere in the middle
        ed.settle(0.4)

        def repeat(name, keys, undo=None, before=None, quiet=0.12, min_frames=1):
            samples = []
            for _ in range(args.runs):
                if before:
                    ed.key(before, quiet=0.1)
                    ed.settle(0.15)
                samples.append(ed.key(keys, quiet=quiet, min_frames=min_frames))
                if undo:
                    ed.key(undo, quiet=0.1)
                    ed.settle(0.15)
            results[name] = samples

        repeat("j (one line down)", "j", undo="k")
        repeat("k (one line up)", "k", undo="j")
        repeat("l (one cell right)", "l", undo="h")
        repeat("w (word)", "w", undo="b")
        repeat("type a char (insert x)", "ix", undo="\x1b", quiet=0.12)
        repeat("<C-d> half page", "\x04", undo="\x15")
        repeat("<C-f> page", "\x06", undo="\x02")
        repeat("zt", "zt", undo="zz")
        repeat("gg (to line 1)", "gg", undo="500G")
        repeat("G (to the end)", "G", undo="500G")
        repeat("/needle_rare<CR>", "/needle_rare\r", undo="500G", before=":noh\r")
        repeat("n (next match)", "n", undo="N")
        repeat("<Space>ff (open picker)", " ff", undo="\x1b", quiet=0.35)
        repeat(":vsplit", ":vsplit\r", undo=":q\r", quiet=0.15)
        repeat(":split", ":split\r", undo=":q\r", quiet=0.15)
        repeat("which-key (<Space>)", " ", undo="\x1b", quiet=0.9)
    finally:
        ed.close()
    return results


def run_pum(binary, args, root):
    """Key to frame with the completion popup open (`:set lspcomplete=auto`, the scripted server of
    tests/fake_lsp_complete.py): a typed character that narrows the list, a backspace that widens it, and
    <Tab> moving the selection (which also starts the documentation fetch)."""
    fake = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "fake_lsp_complete.py")
    path = os.path.join(root, "pum.py")
    with open(path, "w") as f:
        f.write("x = 1\n\n")
    env = dict(args.env or {}, PWD=root, GIT_CEILING_DIRECTORIES=os.path.dirname(root))
    ed = Editor(binary, root, [path], args.rows, args.cols, env=env, sync_reply=args.sync_reply)
    results = {}
    try:
        ed.settle(0.4, 10)
        ed.key(":Lsp server python python3 %s\r" % os.path.abspath(fake), quiet=0.2)
        ed.key(":set lspcomplete=auto\r", quiet=0.2)
        ed.key(":Lsp start\r", quiet=0.8)
        ed.key("jA", quiet=0.2)
        ed.key("hel", quiet=0.6)
        ed.settle(0.4)
        for name, keys, undo in (("popup open: type a char (narrows)", "l", "\x7f"),
                                 ("popup open: backspace (widens)", "\x7f", "l"),
                                 ("popup open: <Tab> (select next)", "\t", None)):
            samples = []
            for _ in range(args.runs):
                samples.append(ed.key(keys, quiet=0.12))
                if undo:
                    ed.key(undo, quiet=0.12)
            results[name] = samples
    finally:
        ed.close()
    return results


def run_hold(binary, args, root):
    """Hold a key with auto-repeat: frames/s, bytes/frame, key->frame latency."""
    out = {}
    big = os.path.join(root, "big2.txt")
    make_source(big, 5000)
    for name, key, setup in (("hold j", b"j", b"1000G"), ("hold <C-d>", b"\x04", b"gg"),
                             ("hold l (type-ahead)", b"l", b"1000G")):
        ed = Editor(binary, root, [big], args.rows, args.cols, env=args.env, sync_reply=args.sync_reply)
        try:
            ed.settle(0.4, 10)
            ed.key(setup.decode(), limit=2.0)
            ed.settle(0.4)
            n = int(REPEAT_HZ * args.hold_seconds)
            period = 1.0 / REPEAT_HZ
            frames = Frames()
            sent = []
            t_start = time.perf_counter()
            cur_start = None
            cur_bytes = 0
            last = None
            in_sync = False
            next_key = t_start
            sent_count = 0
            end = t_start + args.hold_seconds + 1.5
            while time.perf_counter() < end:
                now = time.perf_counter()
                if sent_count < n and now >= next_key:
                    ed.send(key, limit=0.5)
                    sent.append(now)
                    sent_count += 1
                    next_key += period
                wait = max(0.0, min(next_key - now, 0.002)) if sent_count < n else 0.002
                ready, _, _ = select.select([ed.master], [], [], wait)
                if ready:
                    try:
                        data = os.read(ed.master, 1 << 20)
                    except OSError:
                        break
                    t = time.perf_counter()
                    ed._answer_queries(data)
                    if cur_start is None:
                        cur_start = t
                    cur_bytes += len(data)
                    last = t
                    if SYNC_BEGIN in data:
                        in_sync = True
                    if SYNC_END in data:
                        in_sync = False
                        frames.add(cur_start, t, cur_bytes)
                        cur_start, cur_bytes = None, 0
                elif cur_start is not None and not in_sync and time.perf_counter() - last >= GAP:
                    frames.add(cur_start, last, cur_bytes)
                    cur_start, cur_bytes = None, 0
                if sent_count >= n and cur_start is None and last and time.perf_counter() - last > 0.4:
                    break
            if cur_start is not None:
                frames.add(cur_start, last, cur_bytes)
            held = [f for f in frames.items if f[0] < t_start + args.hold_seconds]
            span = (held[-1][1] - held[0][0]) if len(held) > 1 else args.hold_seconds
            lat = []
            fi = 0
            for ts in sent:     # key -> the first frame that ends after it
                while fi < len(frames.items) and frames.items[fi][1] < ts:
                    fi += 1
                if fi < len(frames.items):
                    lat.append(frames.items[fi][1] - ts)
            out[name] = {
                "keys": n, "frames": len(held),
                "fps": len(held) / max(span, 1e-6),
                "bytes_per_frame": statistics.fmean([f[2] for f in held]) if held else 0,
                "total_bytes": sum(f[2] for f in held),
                "latency": stats(lat),
                "settle_after": max(0.0, frames.items[-1][1] - sent[-1]) if frames.items and sent else None,
            }
        finally:
            ed.close()
    return out


def run_resize(binary, args, root):
    big = os.path.join(root, "big3.txt")
    make_source(big, 2000)
    ed = Editor(binary, root, [big], args.rows, args.cols, env=args.env, sync_reply=args.sync_reply)
    out = {}
    try:
        ed.settle(0.4, 10)
        # full-screen redraw cost: the first frame of a resize
        samples = []
        for i in range(max(5, args.runs // 3)):
            t0 = time.perf_counter()
            ed.resize(args.rows, args.cols - 10 - (i % 2) * 10)
            frames, first = ed.read_frames(t0 + 3.0, 0.3)
            if frames.items:
                samples.append({"first_byte": first - t0, "bytes": frames.total,
                                "frames": len(frames.items), "settled": frames.items[-1][1] - t0})
        out["resize"] = samples
        # the cost of one cell changing, for comparison
        out["one_cell"] = [ed.key("l", quiet=0.1) for _ in range(10)]
        # the same screen drawn after switching away and back: ":redraw!" style
        out["redraw"] = [ed.key("\x0c", quiet=0.15) for _ in range(5)]
    finally:
        ed.close()
    return out


def run_storm(binary, args, root):
    """Paste of 1 MB (bracketed) and an unbracketed key storm."""
    out = {}
    path = os.path.join(root, "paste.txt")
    make_source(path, 20)
    payload = ("".join("%d some pasted text, needle_rare and more words here\n" % i for i in range(20000)))[: 1 << 20]
    for name, body in (("paste 1 MB (bracketed)", b"\x1b[200~" + payload.encode() + b"\x1b[201~"),
                       ("1 MB of keys (unbracketed j/k)", (b"jk" * (1 << 19)))):
        ed = Editor(binary, root, [path], args.rows, args.cols, env=args.env, sync_reply=args.sync_reply)
        try:
            ed.settle(0.4, 10)
            if "paste" in name:
                ed.key("i", quiet=0.1)
            t0 = time.perf_counter()
            before_frames = 0
            ed.write(body)
            t_written = time.perf_counter()
            frames, first = ed.read_frames(t0 + 120, 0.5)
            nframes = len(frames.items)
            out[name] = {
                "seconds_to_quiet": (frames.items[-1][1] - t0) if frames.items else None,
                "seconds_to_write": t_written - t0,
                "frames": nframes,
                "bytes": frames.total + 0,
                "bytes_per_frame": frames.total / nframes if nframes else 0,
            }
            # the editor must still be alive and responsive
            r = ed.key("\x1b", quiet=0.2)
            out[name]["alive"] = ed.proc.poll() is None
        finally:
            ed.close()
    return out


def run_idle(binary, args, root):
    path = os.path.join(root, "idle.txt")
    make_source(path, 200)
    ed = Editor(binary, root, [path], args.rows, args.cols, env=args.env, sync_reply=args.sync_reply)
    try:
        ed.settle(0.5, 10)
        a = ed.cpu_stats()
        t0 = time.perf_counter()
        ed.read_frames(t0 + args.idle_seconds, 99.0)
        b = ed.cpu_stats()
        dt = time.perf_counter() - t0
        if a and b:
            return {"cpu_percent": 100.0 * (b[0] - a[0]) / dt, "wakeups_per_s": (b[1] - a[1]) / dt}
        return {"cpu_percent": None, "wakeups_per_s": None}
    finally:
        ed.close()


def run_wrap(binary, args, root):
    path = os.path.join(root, "wrapped.txt")
    make_wrapped(path, 1000)
    ed = Editor(binary, root, [path], args.rows, args.cols, env=args.env, sync_reply=args.sync_reply)
    res = {}
    try:
        ed.settle(0.4, 10)
        ed.key(":set wrap\r", quiet=0.15)
        ed.settle(0.3)
        for name, keys, undo in (("wrap: j", "j", "k"), ("wrap: <C-d>", "\x04", "\x15"),
                                 ("wrap: <C-f>", "\x06", "\x02"), ("wrap: G", "G", "gg"),
                                 ("wrap: type a char", "ix", "\x1b")):
            samples = []
            for _ in range(max(10, args.runs // 2)):
                samples.append(ed.key(keys, quiet=0.12))
                ed.key(undo, quiet=0.1)
                ed.settle(0.15)
            res[name] = samples
    finally:
        ed.close()
    return res


# -- reporting ---------------------------------------------------------------------

def table_key(results):
    lines = ["| action | first byte p50 / p99 (ms) | first frame p50 / p99 (ms) | settled p50 (ms) | frames | bytes first frame (p50) | bytes all frames (p50) |",
             "|---|---|---|---|---|---|---|"]
    for name, samples in results.items():
        fb = stats([s["first_byte"] for s in samples])
        ff = stats([s["first_frame"] for s in samples])
        st = stats([s["settled"] for s in samples])
        fr = stats([s["frames"] for s in samples])
        b1 = stats([s["first_frame_bytes"] for s in samples])
        ba = stats([s["bytes_all"] for s in samples])
        if not fb["n"]:
            lines.append("| %s | no output | | | 0 | 0 | 0 |" % name)
            continue
        lines.append("| %s | %s / %s | %s / %s | %s | %d | %d | %d |" % (
            name, ms(fb["p50"]), ms(fb["p99"]), ms(ff["p50"]), ms(ff["p99"]), ms(st["p50"]),
            round(fr["p50"]), round(b1["p50"]), round(ba["p50"])))
    return "\n".join(lines)


def table_hold(hold):
    lines = ["| held key (30 Hz repeat) | keys | frames | frames/s | bytes/frame | key->frame p50 / p99 / max (ms) | last frame after last key (ms) |",
             "|---|---|---|---|---|---|---|"]
    for name, h in hold.items():
        lat = h["latency"]
        lines.append("| %s | %d | %d | %.1f | %d | %s / %s / %s | %s |" % (
            name, h["keys"], h["frames"], h["fps"], h["bytes_per_frame"],
            ms(lat.get("p50")), ms(lat.get("p99")), ms(lat.get("max")), ms(h["settle_after"])))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m3d", required=True)
    ap.add_argument("--rows", type=int, default=60)
    ap.add_argument("--cols", type=int, default=200)
    ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--hold-seconds", type=float, default=2.0)
    ap.add_argument("--idle-seconds", type=float, default=4.0)
    ap.add_argument("--only", default="key,hold,resize,storm,idle,wrap")
    ap.add_argument("--json")
    ap.add_argument("--env", action="append", default=[], help="NAME=VALUE for the editor")
    ap.add_argument("--no-sync-reply", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--watchdog", type=int, default=300, help="abort the whole run after N seconds (0 = off)")
    args = ap.parse_args()
    if args.watchdog and hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, _watchdog)
        signal.alarm(args.watchdog)
    args.env = dict(e.split("=", 1) for e in args.env)
    args.sync_reply = not args.no_sync_reply
    binary = os.path.abspath(args.m3d)
    only = set(args.only.split(","))
    root = tempfile.mkdtemp(prefix="m3d-ux-")
    report = {"rows": args.rows, "cols": args.cols, "binary": binary, "env": args.env}
    failures = []
    try:
        if "key" in only:
            res = run_key_actions(binary, args, root)
            report["key"] = res
            print("### Key latency and bytes (%dx%d)\n" % (args.cols, args.rows))
            print(table_key(res))
            print()
            one = [s["first_frame_bytes"] for s in res.get("l (one cell right)", []) if s["first_frame_bytes"]]
            if one and statistics.median(one) > GROSS["single_cell_bytes"]:
                failures.append("one-cell move writes %d bytes" % statistics.median(one))
            for name in ("j (one line down)", "type a char (insert x)"):
                p = percentile([s["first_frame"] for s in res.get(name, []) if s["first_frame"] is not None], 0.99)
                if p == p and p > GROSS["key_first_frame_p99"]:
                    failures.append("%s: key->frame p99 %.0f ms" % (name, p * 1000))
        if "pum" in only:
            res = run_pum(binary, args, root)
            report["pum"] = res
            print("### Completion popup open (%dx%d)\n" % (args.cols, args.rows))
            print(table_key(res))
            print()
            for name, samples in res.items():
                p = percentile([s["first_frame"] for s in samples if s["first_frame"] is not None], 0.99)
                if p == p and p > GROSS["key_first_frame_p99"]:
                    failures.append("%s: key->frame p99 %.0f ms" % (name, p * 1000))
        if "hold" in only:
            res = run_hold(binary, args, root)
            report["hold"] = res
            print("### Held key\n")
            print(table_hold(res))
            print()
            for name, h in res.items():
                if h["fps"] < GROSS["hold_fps_min"] and "type-ahead" not in name:
                    failures.append("%s: only %.1f frames/s" % (name, h["fps"]))
        if "resize" in only:
            res = run_resize(binary, args, root)
            report["resize"] = res
            print("### Full-screen redraw (resize) and comparison\n")
            for key in ("resize", "one_cell", "redraw"):
                samples = res[key]
                b = stats([s.get("bytes", s.get("bytes_all")) for s in samples])
                f = stats([s.get("settled", s.get("first_frame")) for s in samples])
                fr = stats([s["frames"] for s in samples])
                if b["n"] and f["n"]:
                    print("- %s: %d bytes (p50), %d frame(s), done in %s ms (p50)" % (
                        key, round(b["p50"]), round(fr["p50"]), ms(f["p50"])))
            print()
        if "storm" in only:
            res = run_storm(binary, args, root)
            report["storm"] = res
            print("### Input storms\n")
            print("| input | to quiet (s) | frames | bytes written | bytes/frame | alive |")
            print("|---|---|---|---|---|---|")
            for name, r in res.items():
                print("| %s | %s | %d | %d | %d | %s |" % (
                    name, "-" if r["seconds_to_quiet"] is None else "%.2f" % r["seconds_to_quiet"],
                    r["frames"], r["bytes"], r["bytes_per_frame"], r["alive"]))
                if not r["alive"]:
                    failures.append("%s: the editor died" % name)
            print()
        if "idle" in only:
            res = run_idle(binary, args, root)
            report["idle"] = res
            print("### Idle\n")
            if res["cpu_percent"] is None:
                print("- /proc is not available here: idle CPU and wakeups not measured\n")
            else:
                print("- idle CPU %.2f %%, %.1f context switches/s (over %.0f s)\n" % (
                    res["cpu_percent"], res["wakeups_per_s"], args.idle_seconds))
                # reported, never failed: the wakeups come from the m31 runtime's own timers
                # (about 190 a second in each of its 14 worker threads), not from the editor
                if res["wakeups_per_s"] > GROSS["idle_wakeups_per_s"]:
                    print("  (the m31 runtime wakes this often when idle; see docs/UX-PERF.md)\n")
        if "wrap" in only:
            res = run_wrap(binary, args, root)
            report["wrap"] = res
            print("### 1000-line wrapped file\n")
            print(table_key(res))
            print()
    finally:
        import shutil
        shutil.rmtree(root, ignore_errors=True)
    if args.json:
        with open(args.json, "w") as f:
            json.dump(report, f, indent=1, default=str)
    if args.check and failures:
        print("GROSS REGRESSIONS:")
        for f in failures:
            print("  " + f)
        sys.exit(1)
    if failures:
        print("note (not failing without --check):", "; ".join(failures))


if __name__ == "__main__":
    main()
