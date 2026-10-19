#!/usr/bin/env python3
"""Differential oracle for the fold structure of 'foldmethod' marker: the m31 engine against `nvim --headless`.

    python3 tests/oracles/oracle_folds.py --runner BIN [--cases N] [--seed S] [--mode plain|simple|wild] [-v]

BIN is tests/t_fold_run.m31 built. Random texts of lines with fold markers ({{{ and }}} alone or in text; `simple` adds
levels such as {{{2 and }}}3, `wild` several markers per line) are loaded in both, and what is compared is which folds
are closed at 'foldlevel' 0 to 6 (foldclosed() / foldclosedend() with 'foldminlines' 0), which fixes the whole fold tree.
"""
import argparse
import concurrent.futures
import os
import random
import subprocess
import sys
import tempfile

NVIM = os.environ.get("NVIM", "nvim")

TOKENS = {
    "plain": ["{{{", "}}}", "a {{{", "b }}}"],
    "simple": ["{{{", "}}}", "{{{1", "{{{2", "{{{3", "}}}1", "}}}2", "}}}3", "a {{{", "b }}}"],
    "wild": ["{{{", "}}}", "{{{1", "{{{2", "{{{3", "}}}1", "}}}2", "}}}3", "a {{{", "b }}}", "{{{ }}}", "}}}{{{", "{{{2 }}}1",
             "{{{0", "}}}0", "{{{{{{", "}}}}}}"],
}


def random_text(rng, mode):
    lines = []
    for _ in range(rng.randint(2, 9)):
        count = rng.choice([0, 1, 1, 2]) if mode == "wild" else rng.choice([0, 0, 1, 1, 1])
        lines.append(" ".join(rng.choice(TOKENS[mode]) for _ in range(count)) or "y")
    return lines


def nvim_view(lines, method):
    work = tempfile.mkdtemp(prefix="m3-fold-")
    path = os.path.join(work, "t.txt")
    out = os.path.join(work, "out")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    script = ("set fdm=%s fml=0 | let r=[] | for k in range(0,7) | let &fdl=k | let l=1 | while l<=line('$') | "
              "let c=foldclosed(l) | if c>0 | call add(r, k.':'.c.'-'.foldclosedend(l)) | let l=foldclosedend(l)+1 | "
              "else | let l+=1 | endif | endwhile | endfor | call writefile([join(r,' ')], '%s')") % (method, out)
    subprocess.run([NVIM, "--headless", "-u", "NONE", "-i", "NONE", "-n", "-es", "+" + script, "+q", path],
                   capture_output=True, timeout=30, stdin=subprocess.DEVNULL)
    with open(out) as f:
        return f.read().strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runner", required=True)
    ap.add_argument("--cases", type=int, default=300)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--mode", default="simple", choices=sorted(TOKENS))
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    texts = [random_text(rng, args.mode) for _ in range(args.cases)]
    work = tempfile.mkdtemp(prefix="m3-fold-")
    case_file = os.path.join(work, "cases")
    with open(case_file, "w") as f:
        for lines in texts:
            f.write("\\n".join(lines) + "\n")
    ours = subprocess.run([args.runner, case_file, "marker"], capture_output=True, text=True, timeout=120,
                          stdin=subprocess.DEVNULL).stdout.split("\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(2, os.cpu_count() or 2)) as pool:
        theirs = list(pool.map(lambda lines: nvim_view(lines, "marker"), texts))
    failed = 0
    for lines, want, got in zip(texts, theirs, ours):
        if want != got.strip():
            failed += 1
            print("DIFF %r\n  nvim=%s\n  m3  =%s" % (lines, want, got.strip()))
        elif args.verbose:
            print("ok   %r %s" % (lines, got.strip()))
    print("%d cases (%s, seed %d), %d matched, %d failed" % (len(texts), args.mode, args.seed, len(texts) - failed, failed))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
