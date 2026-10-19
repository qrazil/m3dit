#!/usr/bin/env python3
"""What nvim's own LSP client makes of a server's semantic tokens at some positions.

    python3 tests/oracle_tokens.py LANG FILETYPE POINTS_JSON SOURCE CMD...

nvim (headless, `-u NONE`) starts the server on SOURCE (file name `a.LANG`), waits for semantic tokens and prints
`tokens: {"row,col": ["type", "modifier", ...]}` (rows and columns 0-based, bytes) from `vim.inspect_pos`. The pty
scenario `real_clangd_tokens` of tests/lsp_pty.py compares the type of the token and whether it is a declaration
with what m3's `:Lsp tokens` says. Exit 2 when nvim cannot get tokens.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

LUA = r'''
local cmd = vim.json.decode(os.getenv("ORACLE_CMD"))
local points = vim.json.decode(os.getenv("ORACLE_POINTS"))
vim.cmd("filetype on")
vim.cmd("edit " .. vim.fn.fnameescape(os.getenv("ORACLE_FILE")))
vim.bo.filetype = os.getenv("ORACLE_FT")
local client_id = vim.lsp.start({ name = "oracle", cmd = cmd, root_dir = os.getenv("ORACLE_ROOT") })
local ok = vim.wait(30000, function()
  local c = vim.lsp.get_client_by_id(client_id)
  return c and c.initialized
end, 100)
if not ok then io.stderr:write("no initialize\n") vim.cmd("cquit 2") end
local function collect()
  local out, found = {}, 0
  for _, p in ipairs(points) do
    local info = vim.inspect_pos(0, p[1], p[2], { syntax = false, treesitter = false, extmarks = false, semantic_tokens = true })
    local names = {}
    local kind
    for _, t in ipairs(info.semantic_tokens or {}) do
      local group = t.opts and t.opts.hl_group or ""
      local ty = group:match("^@lsp%.type%.(%w+)")
      if ty then kind = ty end
      local mod = group:match("^@lsp%.mod%.(%w+)")
      if mod then names[#names + 1] = mod end
    end
    if kind then
      found = found + 1
      table.insert(names, 1, kind)
      out[p[1] .. "," .. p[2]] = names
    end
  end
  return out, found
end
local out, found = {}, 0
for _ = 1, 40 do
  vim.wait(500)
  out, found = collect()
  if found == #points then break end
end
io.write("tokens: " .. vim.json.encode(out) .. "\n")
vim.cmd("qa!")
'''


def main():
    nvim = shutil.which("nvim")
    if not nvim:
        sys.exit(2)
    lang, ft, points, source = sys.argv[1:5]
    root = os.path.realpath(tempfile.mkdtemp(prefix="m3tokens"))
    try:
        path = os.path.join(root, "a." + lang)
        with open(path, "w") as f:
            f.write(source)
        script = os.path.join(root, "o.lua")
        with open(script, "w") as f:
            f.write(LUA)
        env = dict(os.environ, ORACLE_CMD=json.dumps(sys.argv[5:]), ORACLE_FILE=path, ORACLE_ROOT=root,
                   ORACLE_FT=ft, ORACLE_POINTS=points, XDG_STATE_HOME=root)
        out = subprocess.run([nvim, "--headless", "-u", "NONE", "-i", "NONE", "-l", script], env=env,
                             capture_output=True, text=True, timeout=150, cwd=root)
        sys.stdout.write(out.stdout)
        if out.returncode or os.environ.get("ORACLE_DEBUG"):
            sys.stderr.write(out.stderr)
        sys.exit(out.returncode)
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
