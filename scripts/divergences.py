#!/usr/bin/env python3
"""The divergences from vim/nvim, from tests/oracles/divergences.tsv (the single source).

    python3 scripts/divergences.py --write FILE    replace the generated block of FILE
    python3 scripts/divergences.py --check FILE    exit 1 when the block of FILE is out of date
    python3 scripts/divergences.py --selectors     print "id<TAB>mode<TAB>regex" for the oracle runner

The block sits between the lines `<!-- divergences:begin -->` and `<!-- divergences:end -->`.
Columns of the tsv: id, vim behaviour, m3 behaviour, reason, oracle (`skip`: the matching corpus cases are not
compared; `flip`: they must differ, and are reported when they start to match; `doc`: no corpus case is affected),
selector (a Python regular expression searched in the key notation of a corpus case; empty for `doc`).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "..", "tests", "oracles", "divergences.tsv")
BEGIN = "<!-- divergences:begin -->"
END = "<!-- divergences:end -->"


def rows():
    out = []
    with open(TSV) as handle:
        lines = handle.read().split("\n")
    for line in lines[1:]:
        if not line.strip() or line.startswith("#"):
            continue
        cells = line.split("\t")
        cells += [""] * (6 - len(cells))
        out.append(cells[:6])
    ids = [r[0] for r in out]
    if len(set(ids)) != len(ids):
        sys.exit("divergences.tsv: duplicate id")
    for r in out:
        if r[4] not in ("skip", "flip", "doc"):
            sys.exit("divergences.tsv: %s: oracle must be skip, flip or doc" % r[0])
        if (r[4] == "doc") != (r[5] == ""):
            sys.exit("divergences.tsv: %s: a selector goes with skip and flip only" % r[0])
    return out


def block():
    lines = [BEGIN, "", "Generated from `tests/oracles/divergences.tsv` by `python3 scripts/divergences.py --write docs/CORE-STATUS.md`; edit the tsv, not this table.", "",
             "| id | vim / nvim | m3 | reason | oracle |", "|---|---|---|---|---|"]
    for ident, vim, mine, reason, oracle, selector in rows():
        how = {"skip": "cases skipped", "flip": "cases must differ", "doc": "no case affected"}[oracle]
        lines.append("| `%s` | %s | %s | %s | %s |" % (ident, vim, mine, reason, how))
    lines += ["", END]
    return "\n".join(lines)


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--selectors":
        for ident, vim, mine, reason, oracle, selector in rows():
            if oracle != "doc":
                print("%s\t%s\t%s" % (ident, oracle, selector))
        return 0
    if len(sys.argv) != 3 or sys.argv[1] not in ("--write", "--check"):
        print(__doc__)
        return 2
    path = sys.argv[2]
    with open(path) as handle:
        text = handle.read()
    if BEGIN not in text or END not in text:
        sys.exit("%s has no divergences block" % path)
    head, rest = text.split(BEGIN, 1)
    tail = rest.split(END, 1)[1]
    fresh = head + block() + tail
    if sys.argv[1] == "--check":
        if fresh != text:
            print("%s is out of date: run python3 scripts/divergences.py --write %s" % (path, path))
            return 1
        return 0
    with open(path, "w") as handle:
        handle.write(fresh)
    return 0


if __name__ == "__main__":
    sys.exit(main())
