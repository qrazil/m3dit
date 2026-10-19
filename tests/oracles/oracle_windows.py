#!/usr/bin/env python3
"""Differential oracle for window layouts: the m31 App against `nvim --headless`.

    python3 tests/oracles/oracle_windows.py --runner BIN [--case KEYS ...] [-v]

BIN is tests/t_split_run.m31 built. Every case is a key string (Python escapes:
CTRL-W is \\x17, Enter is \\r); the same keys are typed in nvim (80x24, a
30-line file, laststatus=2) and in the App, and the window rectangles
(row, column, width, height without the status line), the active window and
the tab page are compared. Without --case the built-in list runs.
"""
import argparse
import binascii
import json
import os
import subprocess
import sys
import tempfile

NVIM = os.environ.get("NVIM", "nvim")
CW = "\x17"
CR = "\r"

CASES = [
    ":split" + CR, ":vsplit" + CR, ":new" + CR, ":vnew" + CR,
    ":split" + CR + ":split" + CR, ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR,
    ":split" + CR + ":vsplit" + CR, ":vsplit" + CR + ":split" + CR,
    ":split" + CR + ":vsplit" + CR + ":split" + CR,
    ":vsplit" + CR + ":split" + CR + ":vsplit" + CR,
    ":split" + CR + CW + "j" + ":vsplit" + CR,
    ":only" + CR, ":split" + CR + ":only" + CR, ":split" + CR + ":vsplit" + CR + ":only" + CR,
    ":split" + CR + ":close" + CR, ":vsplit" + CR + ":vsplit" + CR + ":close" + CR,
    ":split" + CR + ":vsplit" + CR + CW + "c",
    ":split" + CR + ":vsplit" + CR + CW + "o",
    ":split" + CR + CW + "q",
    ":split" + CR + ":split" + CR + CW + "x",
    ":split" + CR + ":split" + CR + CW + "j" + CW + "x",
    ":vsplit" + CR + ":vsplit" + CR + CW + "x",
    ":vsplit" + CR + ":vsplit" + CR + CW + "l" + CW + "x",
    ":split" + CR + ":split" + CR + CW + "r",
    ":split" + CR + ":split" + CR + CW + "R",
    ":vsplit" + CR + ":vsplit" + CR + CW + "r",
    ":vsplit" + CR + ":vsplit" + CR + CW + "R",
    ":split" + CR + ":split" + CR + CW + "H",
    ":split" + CR + ":split" + CR + CW + "L",
    ":split" + CR + ":split" + CR + CW + "K",
    ":split" + CR + ":split" + CR + CW + "J",
    ":vsplit" + CR + ":vsplit" + CR + CW + "J",
    ":vsplit" + CR + ":vsplit" + CR + CW + "K",
    ":vsplit" + CR + ":vsplit" + CR + CW + "H",
    ":vsplit" + CR + ":vsplit" + CR + CW + "L",
    ":split" + CR + ":vsplit" + CR + CW + "H",
    ":split" + CR + ":vsplit" + CR + CW + "J",
    ":split" + CR + ":vsplit" + CR + CW + "K",
    ":split" + CR + ":vsplit" + CR + CW + "L",
    ":vsplit" + CR + ":split" + CR + CW + "H",
    ":vsplit" + CR + ":split" + CR + CW + "L",
    ":split" + CR + CW + "_",
    ":split" + CR + CW + "j" + CW + "_",
    ":split" + CR + ":split" + CR + CW + "_",
    ":split" + CR + CW + "5_",
    ":split" + CR + CW + "10+",
    ":split" + CR + CW + "3-",
    ":split" + CR + CW + "+",
    ":split" + CR + CW + "-",
    ":split" + CR + CW + "|",
    ":vsplit" + CR + CW + "|",
    ":vsplit" + CR + CW + "20|",
    ":vsplit" + CR + CW + "10<",
    ":vsplit" + CR + CW + "10>",
    ":vsplit" + CR + CW + ">",
    ":vsplit" + CR + CW + "<",
    ":vsplit" + CR + CW + "l" + CW + "10<",
    ":vsplit" + CR + ":vsplit" + CR + CW + "20|",
    ":vsplit" + CR + ":vsplit" + CR + CW + "20|" + CW + "=",
    ":split" + CR + CW + "5_" + CW + "=",
    ":split" + CR + ":split" + CR + CW + "=",
    ":split" + CR + ":resize 5" + CR,
    ":split" + CR + ":resize +3" + CR,
    ":split" + CR + ":resize -3" + CR,
    ":split" + CR + ":resize" + CR,
    ":split" + CR + ":resize 100" + CR,
    ":split" + CR + ":resize 0" + CR,
    ":split" + CR + CW + "j" + ":resize 3" + CR,
    ":vsplit" + CR + ":vertical resize 20" + CR,
    ":vsplit" + CR + ":vertical resize +5" + CR,
    ":vsplit" + CR + ":vertical resize -5" + CR,
    ":vsplit" + CR + ":vertical resize 100" + CR,
    ":split" + CR + ":split" + CR + ":resize 4" + CR + CW + "j" + ":resize 4" + CR,
    ":split" + CR + ":split" + CR + CW + "j" + ":resize 5" + CR + CW + "j" + ":resize 5" + CR,
    ":split" + CR + CW + "w", ":split" + CR + CW + "W", ":split" + CR + CW + "p",
    ":split" + CR + CW + "t", ":split" + CR + CW + "b",
    ":split" + CR + ":vsplit" + CR + CW + "j", ":split" + CR + ":vsplit" + CR + CW + "k",
    ":split" + CR + ":vsplit" + CR + CW + "h", ":split" + CR + ":vsplit" + CR + CW + "l",
    ":split" + CR + ":vsplit" + CR + CW + "t" + CW + "j",
    ":split" + CR + ":vsplit" + CR + CW + "w" + CW + "w",
    ":split" + CR + ":vsplit" + CR + CW + "b" + CW + "k",
    CW + "s", CW + "v", CW + "n", CW + CW,
    CW + "s" + CW + "v" + CW + "s",
    ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR,
    ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR + ":split" + CR,
    ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR + ":vsplit" + CR,
    # tab pages: each keeps its own layout
    ":tabnew" + CR, ":tabnew" + CR + ":split" + CR, ":split" + CR + ":tabnew" + CR + ":vsplit" + CR + "gt",
    ":split" + CR + ":tabnew" + CR + "gt", ":split" + CR + ":tabnew" + CR + "gT",
    ":tabnew" + CR + ":tabnew" + CR + "gt", ":tabnew" + CR + ":tabnew" + CR + "2gt",
    ":tabnew" + CR + ":tabnew" + CR + ":tabfirst" + CR, ":tabnew" + CR + ":tabnew" + CR + ":tablast" + CR,
    ":tabnew" + CR + ":tabclose" + CR, ":tabnew" + CR + ":tabnew" + CR + ":tabclose" + CR,
    ":tabnew" + CR + ":tabnew" + CR + "gg" + ":tabclose" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":tabonly" + CR,
    ":split" + CR + ":tabnew" + CR + ":q" + CR, ":tabnew" + CR + ":split" + CR + ":q" + CR,
    ":tabnew" + CR + ":tabprev" + CR + ":tabnext" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":tabmove 0" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":tabmove" + CR + "gT",
    ":tabnew" + CR + ":split" + CR + ":tabnew" + CR + ":vsplit" + CR + "gt" + CW + "j",
    ":tabnew" + CR + CW + "T",
    ":split" + CR + CW + "T",
    # :tab {cmd} opens the window the command makes in a new tab page; a count says where; :{N}tabnew too
    ":tab split" + CR, ":tab vsplit" + CR, ":tab new" + CR, ":tab vnew" + CR, ":tab sp" + CR, ":tab vs" + CR,
    ":split" + CR + ":tab split" + CR, ":vsplit" + CR + ":tab split" + CR, ":split" + CR + ":vsplit" + CR + ":tab vsplit" + CR,
    ":tab split" + CR + ":vsplit" + CR, ":tab split" + CR + ":tab split" + CR, ":tab split" + CR + "gt", ":tab split" + CR + "gT",
    ":0tab split" + CR, ":1tab split" + CR, ":2tab split" + CR, ":$tab split" + CR, ":.tab split" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":0tab split" + CR, ":tabnew" + CR + ":tabnew" + CR + ":1tab split" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":2tab vsplit" + CR, ":tabnew" + CR + ":tabnew" + CR + ":$tab split" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":.tab split" + CR, ":tabnew" + CR + ":tabnew" + CR + ":-tab split" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":+tab split" + CR, ":0tabnew" + CR, ":1tabnew" + CR, ":2tabnew" + CR,
    ":tabnew" + CR + ":0tabnew" + CR, ":tabnew" + CR + ":1tabnew" + CR, ":tabnew" + CR + ":2tabnew" + CR, ":tabnew" + CR + ":3tabnew" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":1tabnew" + CR, ":tabnew" + CR + ":tabnew" + CR + ":$tabnew" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":.tabnew" + CR, ":tabnew" + CR + ":tabnew" + CR + ":0tabedit hello" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":1tabedit hello" + CR, ":tabnew" + CR + ":tabnew" + CR + ":2tabnext" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":$tabnext" + CR, ":tabnew" + CR + ":tabnew" + CR + ":1tabnext" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":tabnext 1" + CR, ":tabnew" + CR + ":tabnew" + CR + ":2tabclose" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":$tabclose" + CR, ":tabnew" + CR + ":tabnew" + CR + ":1tabclose" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":tabclose 2" + CR, ":tabnew" + CR + ":tabnew" + CR + ":2tabonly" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":tabonly" + CR, ":tabnew" + CR + ":tabnew" + CR + ":1tabprevious" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":2tabprevious" + CR, ":tabnew" + CR + ":tabnew" + CR + ":tabprevious 2" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":tabNext 1" + CR, ":tab edit hello" + CR, ":tab enew" + CR, ":tab close" + CR,
    ":tab tabnew" + CR, ":tabnew" + CR + ":tab only" + CR, ":tab split" + CR + ":tab only" + CR,
    ":tab split | vsplit" + CR, ":tab split|vsplit" + CR, ":tab new | split" + CR, ":tab tabnew | split" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":99tabnew" + CR, ":tabnew" + CR + ":tabnew" + CR + ":99tab split" + CR,
    ":tabnew" + CR + ":tabnew" + CR + ":tabnew" + CR + "2gt", ":tabnew" + CR + ":tabnew" + CR + "9gt",
]


def nvim_run(path, keys, size=None):
    script = """
local keys = vim.fn.getenv('M3_KEYS')
vim.cmd('set laststatus=2 lines=24 columns=80 splitbelow splitright')
vim.cmd('edit ' .. vim.fn.getenv('M3_FILE'))
vim.api.nvim_feedkeys(keys, 'tx', false)
local size = vim.fn.getenv('M3_SIZE')
if size ~= vim.NIL and size ~= '' then
  local r, c = size:match('(%d+),(%d+)')
  vim.cmd('set lines=' .. r .. ' columns=' .. c)
end
local wins = vim.api.nvim_tabpage_list_wins(0)
local rects = {}
local current = vim.api.nvim_get_current_win()
local cur = ''
for _, w in ipairs(wins) do
  local pos = vim.api.nvim_win_get_position(w)
  local r = string.format('%d,%d,%d,%d', pos[1], pos[2], vim.api.nvim_win_get_width(w), vim.api.nvim_win_get_height(w))
  table.insert(rects, {pos[1], pos[2], r})
  if w == current then cur = r end
end
table.sort(rects, function(a, b) if a[1] ~= b[1] then return a[1] < b[1] end return a[2] < b[2] end)
local parts = {}
for _, r in ipairs(rects) do table.insert(parts, r[3]) end
local out = table.concat(parts, ';') .. '|' .. cur .. '|' .. vim.fn.tabpagenr() .. '/' .. vim.fn.tabpagenr('$')
local bottom = 0
for _, w in ipairs(wins) do local p = vim.api.nvim_win_get_position(w); local b = p[1] + vim.api.nvim_win_get_height(w) + 1; if b > bottom then bottom = b end end
-- (nvim 0.11 counts the tab line in a window's position, so the windows always end just above the command line)
if vim.o.cmdheight ~= 1 or bottom ~= vim.o.lines - 1 then out = 'cmdheight' end
io.stdout:write(out .. '\\n')
"""
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
        f.write(script)
        lua = f.name
    env = dict(os.environ, M3_KEYS=keys, M3_FILE=path, M3_SIZE=size or '')
    try:
        out = subprocess.run([NVIM, "--headless", "-u", "NONE", "-n", "-i", "NONE", "--cmd", "set shortmess+=I",
                              "-c", "luafile " + lua, "-c", "qa!"], env=env, capture_output=True, text=True, timeout=30)
    finally:
        os.unlink(lua)
    text = out.stdout + out.stderr
    if "E36" in text or "E5113" in text:
        return "cmdheight"   # nvim refused (not enough room) and stopped feeding the keys
    lines = [l for l in text.split("\n") if ("|" in l and "," in l) or l == "cmdheight"]
    return lines[-1].strip() if lines else "nvim: " + (out.stdout + out.stderr).strip()[:200]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runner", required=True)
    ap.add_argument("--case", action="append", default=[])
    ap.add_argument("--fuzz", type=int, default=0, help="this many random command sequences")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    cases = [c.encode().decode("unicode_escape") for c in args.case] or CASES
    sizes = {}
    if args.fuzz:
        import random
        rng = random.Random(args.seed)
        pieces = [":split" + CR, ":vsplit" + CR, ":new" + CR, ":vnew" + CR, CW + "s", CW + "v", ":close" + CR,
                  CW + "c", CW + "o", CW + "w", CW + "W", CW + "p", CW + "t", CW + "b", CW + "j", CW + "k", CW + "h",
                  CW + "l", CW + "x", CW + "r", CW + "R", CW + "H", CW + "J", CW + "K", CW + "L", CW + "=",
                  CW + "_", CW + "|", CW + "+", CW + "-", CW + "<", CW + ">", CW + "5_", CW + "7|", CW + "3+",
                  CW + "4-", CW + "6<", CW + "9>", ":resize 6" + CR, ":resize +2" + CR, ":resize -2" + CR,
                  ":vertical resize 30" + CR, ":vertical resize +4" + CR, ":only" + CR,
                  ":tabnew" + CR, "gt", "gT", CW + "T", ":tab split" + CR, ":0tab split" + CR, ":1tab vsplit" + CR,
                  ":$tabnew" + CR, ":0tabnew" + CR, ":tab new" + CR, ":1tabclose" + CR, ":2tabnext" + CR]
        cases = []
        for _ in range(args.fuzz):
            keys = "".join(rng.choice([":split" + CR, ":vsplit" + CR]) for _ in range(rng.randint(1, 3)))
            keys += "".join(rng.choice(pieces) for _ in range(rng.randint(2, 9)))
            cases.append(keys)
            if rng.random() < 0.5:
                sizes[keys] = "%d,%d" % (rng.randint(8, 40), rng.randint(30, 140))
    work = tempfile.mkdtemp(prefix="m3-win-")
    text = os.path.join(work, "t.txt")
    with open(text, "w") as f:
        f.write("".join("line %d\n" % n for n in range(1, 31)))
    case_file = os.path.join(work, "cases")
    with open(case_file, "w") as f:
        for c in cases:
            f.write(binascii.hexlify(c.encode()).decode() + ("\t" + sizes[c] if c in sizes else "") + "\n")
    ours = subprocess.run([args.runner, text, case_file], capture_output=True, text=True, timeout=300)
    mine = {}
    for line in ours.stdout.split("\n"):
        if "\t" in line:
            key, value = line.split("\t", 1)
            mine[key] = value
    failed = 0
    skipped = 0
    for c in cases:
        expected = nvim_run(text, c, sizes.get(c))
        if expected == "cmdheight":
            skipped += 1   # nvim made the command line taller (resizing the only window)
            continue
        got = mine.get(binascii.hexlify(c.encode()).decode(), "missing")
        if expected != got:
            failed += 1
            print("DIFF %r %s\n  nvim=%s\n  m3  =%s" % (c, sizes.get(c, ""), expected, got))
        elif args.verbose:
            print("ok   %r %s" % (c, got))
    print("%d cases, %d matched, %d failed, %d skipped (nvim resized the command line or ran out of room)" % (len(cases), len(cases) - failed - skipped, failed, skipped))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
