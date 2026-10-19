#!/usr/bin/env python3
"""Cross-check of the completion request/response shape against nvim's built-in LSP client.

    python3 tests/oracle_lsp.py CMD...      e.g. pyright-langserver --stdio

nvim (headless, `-u NONE`) starts the same server on the second line of a small file (ORACLE_LANG=python: `os.pa`, c: `prin`), asks `textDocument/completion` at the end of
line 2 and prints the labels. This is a check of the request/response shape, not of rendering: it prints
`labels: ["a","b"]` (JSON) and `isIncomplete: true|false`, and the pty scenario `real_pyright` of tests/lsp_pty.py requires every
label m3's popup shows to be in nvim's list. Exit 2 when nvim or the server is missing.
"""
import os
import shutil
import subprocess
import sys
import tempfile

LUA = r'''
local cmd = vim.json.decode(os.getenv("ORACLE_CMD"))
vim.cmd("filetype on")
vim.cmd("edit " .. vim.fn.fnameescape(os.getenv("ORACLE_FILE")))
vim.bo.filetype = os.getenv("ORACLE_FT")
local client_id = vim.lsp.start({ name = "oracle", cmd = cmd, root_dir = os.getenv("ORACLE_ROOT") })
local ok = vim.wait(30000, function()
  local c = vim.lsp.get_client_by_id(client_id)
  return c and c.initialized
end, 100)
if not ok then io.stderr:write("no initialize\n") vim.cmd("cquit 2") end
vim.wait(1500)
local line = vim.api.nvim_buf_get_lines(0, 1, 2, false)[1]
local labels, incomplete = {}, false
for _ = 1, 2 do
  local res = vim.lsp.buf_request_sync(0, "textDocument/completion",
    { textDocument = vim.lsp.util.make_text_document_params(), position = { line = 1, character = #line },
      context = { triggerKind = 1 } }, 20000)
  labels, incomplete = {}, false
  for _, r in pairs(res or {}) do
    local result = r.result or {}
    local items = result.items or result
    if result.isIncomplete then incomplete = true end
    for _, item in ipairs(items) do labels[#labels + 1] = item.label end
  end
  if #labels > 0 then break end
  vim.wait(500)
end
io.write("labels: " .. vim.json.encode(labels) .. "\n")
io.write("isIncomplete: " .. tostring(incomplete) .. "\n")
vim.cmd("qa!")
'''


PRESETS = {
    "python": ("a.py", "import os\nos.pa\n", "python"),
    "c": ("a.c", "#include <stdio.h>\nint main(void) { prin\n", "c"),
}


def main():
    nvim = shutil.which("nvim")
    if not nvim:
        print("no nvim")
        sys.exit(2)
    import json
    root = os.path.realpath(tempfile.mkdtemp(prefix="m3oracle"))
    try:
        name, text, ft = PRESETS[os.environ.get("ORACLE_LANG", "python")]
        path = os.path.join(root, name)
        with open(path, "w") as f:
            f.write(text)
        script = os.path.join(root, "o.lua")
        with open(script, "w") as f:
            f.write(LUA)
        env = dict(os.environ, ORACLE_CMD=json.dumps(sys.argv[1:]), ORACLE_FILE=path, ORACLE_ROOT=root, ORACLE_FT=ft,
                   XDG_STATE_HOME=root)
        out = subprocess.run([nvim, "--headless", "-u", "NONE", "-i", "NONE", "-l", script], env=env,
                             capture_output=True, text=True, timeout=120, cwd=root)
        sys.stdout.write(out.stdout)
        if out.returncode or os.environ.get('ORACLE_DEBUG'):
            sys.stderr.write(out.stderr)
        sys.exit(out.returncode)
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
