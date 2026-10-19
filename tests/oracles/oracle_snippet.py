#!/usr/bin/env python3
"""Differential oracle for snippets: the m31 snippet engine against nvim's vim.snippet.

    python3 tests/oracles/oracle_snippet.py --runner BIN [--file CASES] [--case LINE ...] [-v]

BIN is tests/t_snippet_run.m31 built. A case line is

    TEXT<TAB>CURSOR<TAB>BODY<TAB>KEYS

TEXT and BODY use \\n \\t \\\\ escapes, CURSOR is "row,col" (0-based), KEYS is Vim key notation where <F2> expands BODY
at the cursor (in the mode the editor is in) and <S-Tab> is Shift-Tab. Tab jumps while a snippet is active, as in
nvim 0.11. The keys are typed one at a time with a pause between them (tests/oracles/snippet_driver.lua) so that
nvim's own deferred work (Select mode after a jump, mirror updates) is done before the next key. Compared: the text,
the cursor, the mode (n i s v), the Visual anchor when there is one, and whether a snippet is active.

Cases are in tests/oracles/snippet_cases.txt; lines starting with # are comments.
"""
import argparse
import concurrent.futures
import os
import random
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import oracle_nvim as base  # noqa: E402

DRIVER = os.path.join(HERE, "snippet_driver.lua")
EXPAND = 63300
SHIFT_TAB = 16777225


def parse_keys(notation):
    out = []
    for piece in re.split(r"(<F2>|<S-Tab>)", notation):
        if piece == "<F2>":
            out.append(EXPAND)
        elif piece == "<S-Tab>":
            out.append(SHIFT_TAB)
        elif piece:
            out.extend(base.parse_keys(piece))
    return out


class Case:
    def __init__(self, text, row, col, body, notation, source=""):
        self.text, self.row, self.col, self.body = text, row, col, body
        self.notation = notation
        self.keys = parse_keys(notation)
        self.source = source

    def line(self):
        return "%s\t%d,%d\t%s\t%s" % (base.escape_text(self.text), self.row, self.col, base.escape_text(self.body), self.notation)


def parse_case(line, source=""):
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 4:
        return None
    text = base.unescape_text(parts[0])
    row, col = 0, 0
    if parts[1].strip():
        r, c = parts[1].split(",")
        row, col = int(r), int(c)
    return Case(text, row, col, base.unescape_text(parts[2]), "\t".join(parts[3:]), source)


def load(path):
    cases = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.startswith("#") or not line.strip():
                continue
            case = parse_case(line, "%s:%d" % (os.path.basename(path), n))
            if case:
                cases.append(case)
    return cases


def run_nvim_case(case, tmp):
    out = os.path.join(tmp, "s%d_%d.txt" % (os.getpid(), random.getrandbits(32)))
    cmd = [base.NVIM, "--headless", "-u", "NONE", "-i", "NONE", "-n", "--cmd", "let g:m3s_out='%s'" % out,
           "-c", "luafile " + DRIVER]
    env = dict(os.environ, M3S_TEXT=base.hexs(case.text), M3S_BODY=base.hexs(case.body),
               M3S_POS="%d,%d" % (case.row, case.col), M3S_KEYS=",".join(str(k) for k in case.keys))
    proc = None
    timed_out = False
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                                env=env, start_new_session=True)
        base.CHILDREN.add(proc)
        try:
            proc.wait(timeout=30 + len(case.keys))
        except subprocess.TimeoutExpired:
            timed_out = True
            base.kill_child(proc, out)
        with open(out, encoding="utf-8") as f:
            line = f.read().rstrip("\n")
        os.unlink(out)
    except Exception:  # noqa
        return None
    finally:
        if proc is not None:
            base.kill_child(proc, out if timed_out else None)
            base.CHILDREN.discard(proc)
    return line.split("\t")


def run_engine_batch(runner, cases, tmp, timeout=120):
    path = os.path.join(tmp, "cases_%d.txt" % random.getrandbits(32))
    with open(path, "w", encoding="utf-8") as f:
        for i, c in enumerate(cases):
            f.write("\t".join([str(i), base.hexs(c.text), str(c.row), str(c.col), base.hexs(c.body),
                               ",".join(str(k) for k in c.keys)]) + "\n")
    try:
        done = subprocess.run([runner, path], capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return [None] * len(cases)
    results = {}
    for line in done.stdout.split("\n"):
        if line:
            fields = line.split("\t")
            results[int(fields[0])] = fields
    return [results.get(i) for i in range(len(cases))]


def run_engine(runner, cases, tmp):
    got = run_engine_batch(runner, cases, tmp)
    if all(g is not None for g in got):
        return got
    # a crash or a hang somewhere in the batch: run the missing cases one by one
    for i, c in enumerate(cases):
        if got[i] is None:
            got[i] = run_engine_batch(runner, [c], tmp, timeout=10)[0]
    return got


def show(fields):
    if fields is None:
        return "(no result)"
    return "text=%r cursor=%s,%s mode=%s anchor=%s,%s active=%s" % (
        base.unhexs(fields[1]), fields[2], fields[3], fields[4], fields[5], fields[6], fields[7])


def same(a, b):
    if a is None or b is None:
        return False
    if a[1:5] != b[1:5] or a[7] != b[7]:
        return False
    if a[4] in ("s", "v") and a[5:7] != b[5:7]:
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runner", required=True)
    ap.add_argument("--file", default=os.path.join(HERE, "snippet_cases.txt"))
    ap.add_argument("--case", action="append", default=[])
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    cases = [c for c in (parse_case(l, "arg") for l in args.case) if c] or load(args.file)
    tmp = tempfile.mkdtemp(prefix="m3-snip-")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(2, os.cpu_count() or 2)) as pool:
        theirs = list(pool.map(lambda c: run_nvim_case(c, tmp), cases))
    ours = run_engine(args.runner, cases, tmp)
    failed = 0
    for case, want, got in zip(cases, theirs, ours):
        if same(want, got):
            if args.verbose:
                print("ok   %s" % case.line())
            continue
        failed += 1
        print("DIFF %s\n  %s\n  nvim: %s\n  m3  : %s" % (case.source, case.line(), show(want), show(got)))
    print("%d cases, %d matched, %d failed" % (len(cases), len(cases) - failed, failed))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
