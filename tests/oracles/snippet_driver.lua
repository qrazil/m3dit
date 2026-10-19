-- One snippet case in nvim, run as (see oracle_snippet.py):
--   M3S_TEXT=hex M3S_BODY=hex M3S_POS=row,col M3S_KEYS=k,k,k nvim --headless -u NONE -i NONE -n \
--       --cmd "let g:m3s_out='OUT'" -c "luafile snippet_driver.lua"
-- The keys go in one at a time with a pause between them, as a person types, so that what nvim does later in the
-- event loop (select mode after a jump, the mirror update) has happened before the next key. Key 63300 expands the
-- body at the cursor. It writes one line (same fields as tests/t_snippet_run.m31) to OUT and quits.

vim.g.loaded_clipboard_provider = 1
local out_path = vim.g.m3s_out

local function unhex(s)
  return (s:gsub('..', function(c) return string.char(tonumber(c, 16)) end))
end
local function hex(s)
  return (s:gsub('.', function(c) return string.format('%02x', c:byte()) end))
end

local text = unhex(os.getenv('M3S_TEXT') or '')
local body = unhex(os.getenv('M3S_BODY') or '')
local row, col = (os.getenv('M3S_POS') or '0,0'):match('(%d+),(%d+)')
local keys = {}
for piece in string.gmatch(os.getenv('M3S_KEYS') or '', '[^,]+') do keys[#keys + 1] = tonumber(piece) end

local SPECIAL = {
  [63232] = '<Up>', [63233] = '<Down>', [63234] = '<Left>', [63235] = '<Right>',
  [63236] = '<Home>', [63237] = '<End>', [63238] = '<PageUp>', [63239] = '<PageDown>',
  [63240] = '<Del>', [63241] = '<Insert>',
}
local function key_string(k)
  if k == 63300 then return '<F2>' end
  if SPECIAL[k] then return SPECIAL[k] end
  if k == 127 then return '<BS>' end
  if k == 60 then return '<lt>' end
  if k == 0 then return '<Nul>' end
  if k == 22 then return '<C-v>' end
  if k == 16777225 then return '<S-Tab>' end
  return vim.fn.nr2char(k)
end

local lines = vim.split(text, '\n', { plain = true })
local tmp = os.tmpname()
vim.fn.writefile(lines, tmp)
vim.cmd('silent noautocmd edit! ' .. vim.fn.fnameescape(tmp))
vim.bo.undolevels = 1000
os.remove(tmp)
vim.api.nvim_win_set_cursor(0, { tonumber(row) + 1, tonumber(col) })
vim.keymap.set({ 'i', 'n', 's' }, '<F2>', function() pcall(vim.snippet.expand, body) end)

local function finish()
  local m = vim.fn.mode()
  local mode = 'n'
  if m:sub(1, 1) == 'i' then mode = 'i'
  elseif m == 's' or m == 'S' then mode = 's'
  elseif m == 'v' or m == 'V' or m == '\22' then mode = 'v' end
  local cur = vim.api.nvim_win_get_cursor(0)
  local vrow, vcol = '-', '-'
  if mode == 's' or mode == 'v' then
    local p = vim.fn.getpos('v')
    vrow, vcol = tostring(p[2] - 1), tostring(p[3] - 1)
  end
  local f = assert(io.open(out_path, 'w'))
  f:write(table.concat({
    '0', hex(table.concat(vim.api.nvim_buf_get_lines(0, 0, -1, false), '\n')), tostring(cur[1] - 1), tostring(cur[2]),
    mode, vrow, vcol, vim.snippet.active() and '1' or '0',
  }, '\t'), '\n')
  f:close()
  vim.cmd('qa!')
end

local n = 0
local function step()
  n = n + 1
  if n > #keys then
    vim.defer_fn(finish, 120)
    return
  end
  vim.api.nvim_feedkeys(vim.api.nvim_replace_termcodes(key_string(keys[n]), true, true, true), 't', false)
  vim.defer_fn(step, 45)
end
vim.defer_fn(step, 20)
