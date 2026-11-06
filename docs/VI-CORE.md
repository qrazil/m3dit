# vi core requirements

What POSIX `vi` and `ex` (IEEE 1003.1 `vi` and `ex` utilities) require, checked against `nvim --headless -u NONE` (nvim 0.11.5) and
against m3. The owner's rule is "Vim commands behave exactly like nvim", so where vi and Vim differ, Vim (nvim) wins and the row says
**divergence kept on purpose**. The POSIX pages were not fetched (no network was used); the list is written from the spec's command and option tables from memory and
checked item by item against nvim, so an item the spec has and this file lacks is a gap in this file.

Status words: **done+tested** (an oracle corpus case or a unit/pty test exercises it), **partial**, **missing**, **divergence kept**.
Corpora: `tests/oracles/corpus/118_vi_core.txt` and `119_vi_options_ex.txt` (written for this file: 316 cases, all equal to nvim except
7 listed in `known_divergences.txt`, each a harness artifact: quitting, an unnamed buffer, abbreviation expansion in a typed `:unab`),
plus the 70 older corpus files (`docs/CORE-STATUS.md`). New behaviour has unit tests in `tests/t_vi.m31` and a pty scenario
`vi_command_line_and_ex_mode` in `tests/core_pty.py`.

## Command line

| item | status | note |
|---|---|---|
| `vi file ...` (argument list) | done+tested | `:args`, `t_vi` |
| `-c cmd`, `+cmd`, `+N`, `+` | done+tested | pty `vi_command_line_and_ex_mode`; `-c` is taken out before the Oro `args` grammar sees it |
| `-t tag` | done+tested | same scenario |
| `-r` (recover) | partial | `-r` runs `:recover` on the first file (m3 keeps a recovery file per modified buffer in its state directory, no swap file); `-r` alone does not list files |
| `-R` (read-only) | done+tested | `:set readonly` after the files are read |
| `-e`, `-E` / `ex` | done | starts in Ex mode (below); there is no `ex` binary name, `m3 -e` is it |
| `-s` (silent batch) | missing | m3 needs a terminal; there is no headless mode (a request for the editor, not for m31) |

## Motions

All of these are in the nvim oracle corpus (118) and match: `h j k l`, `0 ^ $ |`, `w W b B e E`, `( ) { } [[ ]] [] ][`, `% `, `H M L`,
`G`, `f F t T ; ,`, `/ ? n N` with offsets (`/pat/e`, `/pat/+1`), `* #`, `'x` `` `x `` `''` ` `` `, `+ - <CR> _`, counts.

| item | status | note |
|---|---|---|
| `{ }` and `[[ ]]` honour 'paragraphs' and 'sections' (nroff macros `.PP`, `.SH`) | done+tested (new) | was ignored; corpus 119 |
| `(` `)` sentences | done+tested | corpus 118 |
| `H M L` with a count, `z` positions | done+tested | corpus 118 |

## Operators and editing commands

`d c y < > ! =` with every motion, `x X D C s S r R J ~ p P u U . &` `Y yy dd cc`, `ZZ`, `ZQ`, `@x`, `"x` named buffers `a-z` and `A-Z` append, numbered
buffers `1-9` shifting, `"-` small delete, `"_` black hole: **done+tested** (corpus 118/119; the older corpora cover all of it in
depth). `U` (undo line) is a Vim command that nvim keeps; matches. Text objects of the vi subset (`w W s p ( ) b B { }`) done+tested.

## Insert mode

`i a I A o O`, counts (`3ix`), `CTRL-V`, `CTRL-W`, `CTRL-U`, `CTRL-H`, `CTRL-T`/`CTRL-D` (shift), `CTRL-R x`, 'autoindent', 'textwidth': done+tested.
**'wrapmargin' was stored only; it now acts** (`wm=N` breaks N columns before the window edge when 'textwidth' is 0; corpus 119).
'showmatch' stays **stored only** (a brief jump to the opening bracket in a terminal is a visual effect that nvim -u NONE also lacks in a headless run).

## Ex commands and addresses

Addresses `. $ % N 'x /pat/ ?pat? +N -N ;` and `,`: done+tested (corpus 119).

| command | status | note |
|---|---|---|
| `:a[ppend]`, `:i[nsert]`, `:c[hange]` | done+tested (new) | text read a line at a time up to a line with only `.`, Esc gives up; 'autoindent' copies the indent of the reference line like nvim; cases 110-112 of corpus 118 |
| `:ab[breviate]`, `:una[bbreviate]`, `:map`, `:unmap`, `:map!` | done+tested | corpus 118; one harness artifact in `known_divergences.txt` |
| `:ar[gs]`, `:n[ext]`, `:N[ext]`, `:prev[ious]`, `:fir[st]`, `:rew[ind]`, `:la[st]`, `:wn[ext]`, `:argadd`, `:argdelete` | done+tested (new) | `t_vi`; names are split at spaces, no glob |
| `:argdo`, `:windo`, `:tabdo`, `:bufdo` | done+tested (new, `bufdo` older) | `t_vi` |
| `:c[opy]` `:t` `:m[ove]` `:d[elete]` `:y[ank]` `:pu[t]` `:j[oin]` `:>` `:<` | done+tested | corpus 118, 119 |
| `:s` with `&` `~` `\1` `\u` `\U`, flags `g c`, `:&` `:&&` `:~` `g&` `&` | done+tested | corpus 119 |
| `:g`, `:v` (and `:g!`) | done+tested | corpus 118, 119 |
| `:k`, `:ma[rk]` | done+tested | corpus 118 |
| `:z`, `:=`, `:#`, `:nu`, `:p` (`:l` is the generic list since 0.25.0) | done+tested | corpus 119 (`:z+ - . ^ =` and counts) |
| `:r file`, `:r !cmd`, `:{range}!cmd` filters, `:!` | done+tested | corpus 118 |
| `:e!`, `:e #`, `:f[ile]` | done+tested (`:file` new) | `:file NAME` renames the buffer |
| `:@x`, `:*x` | done+tested | corpus 119 |
| `:u[ndo]`, `:red[o]`, `:ve[rsion]` | done+tested | corpus 118 (`u`); `:version` is in CORE-STATUS |
| `:w`, `:w!`, `:wq`, `:x`, `:q`, `:q!` | done+tested | `:x`/`:w`/`:q` are harness artifacts in the oracle (they end the process); unit and pty tests cover them |
| `:pre[serve]` | done (new) | writes the recovery files now; message "Preserved" |
| `:rec[over]` | done+tested | older; `-r` calls it |
| `:ta[g]`, `:ts[elect]`, `:tj[ump]`, `:tn[ext]`, `:tp[revious]`, `:tN`, `:tr[ewind]`, `:tl[ast]`, `:po[p]`, `:tags` | done+tested (new) | `t_vi`; see Tags |
| `:gr[ep]`, `:vim[grep]`, `:mak[e]` (and `l` forms) | done+tested (new) | fill the default list (docs/LIST.md); see below |
| `:vi[sual]`, `gQ` (Ex mode) | done+tested (new) | see Ex mode; vi's `Q` is **divergence kept** (below) |
| `:st[op]`, `:su[spend]`, `CTRL-Z` | missing | needs the terminal library to raise SIGTSTP and restore the screen on SIGCONT: **m31 request**: signals (`SIGTSTP`/`SIGCONT` handlers or `os.raise`), the same blocker as `docs/M31-ON-TRAP-REQUEST.md` |
| `:sh[ell]` | missing | would run `$SHELL` with the terminal handed over (needs a terminal suspend/resume in tui); the `terminal` plugin's `:terminal` is the m3 way |
| `:ex`, `:o[pen]` (open mode) | divergence kept | `:open` is a vi line-at-a-time visual mode; nvim has no open mode either |
| `:#!`/`:@` register execution | done+tested | corpus 119 |

## Tags

`:tag NAME`, CTRL-] (word under the cursor), CTRL-T and `:pop` (stack), `:tnext`/`:tprevious`/`:trewind`/`:tlast` over the matches of the last `:tag`,
`:tags` lists the stack, `-t NAME` at start-up. The files come from the 'tags' option (`./tags;,tags`: `./` is the directory of the current
file; the `;` upward search is read as the plain name, **partial**); format is ctags' (`NAME<TAB>FILE<TAB>ADDRESS;"<TAB>kind`, header lines
`!_TAG_...` skipped, address a line number or `/^...$/` literal search, `\/` escaped). 'ignorecase' folds the name. Not done: binary search of
sorted files (the files are scanned linearly), `tagcase`, `taglength`, `:tselect` as an interactive list (it jumps to the first match like `:tag`),
`CTRL-W ]`, `g]`. Module `engine/MED_tags.m31`, App glue `App.run_tag`. Divergence from vi: the stack keeps the file, row and column of the place left.

## Quickfix: `:grep`, `:vimgrep`, `:make`

`:make [args]` runs 'makeprg', `:grep args` runs 'grepprg' (`$*` is replaced by the arguments); the output is read as `file:line:col: text`,
`file:line: text` or `file(line,col): text` (`engine/MED_errfmt.m31`, **'errorformat' is not read**) and becomes the quickfix list; the first
entry is jumped to (not with `!`). `:vimgrep /pat/ files` searches the named files itself (smart-case, files as the shell expands them, no `**`).
`:lgrep`, `:lvimgrep`, `:lmake` are the same (there is one list store, docs/LIST.md; since 0.25.0 the list is the generic one and `:l` / `:lnext` ... walk it).

## Ex mode

`gQ` (and `m3 -e`) opens the command line; it opens again after each command until `:visual` (`:vi`). Vi's `Q` is **not** Ex mode here: nvim 0.11 makes `Q` replay the last recorded macro (checked with `nvim --headless`, corpus 118 has the cases) and Vim commands behave like nvim. Divergence: the line is the editor's
command line at the bottom of the screen, not a scrolling teletype; there is no `:` prompt character change. Esc closes the line and it comes back.

## Options

| option | status | note |
|---|---|---|
| autoindent | done+tested | |
| autowrite | done+tested | |
| ignorecase | done+tested | |
| list | done+tested | |
| magic | done+tested (new) | `nomagic` makes patterns start with `\M` (corpus 119); the replacement side of `:s` (`&`, `~`) is not switched, **partial** |
| number | done+tested | |
| paragraphs | done+tested (new) | read by `{ }` |
| readonly | done+tested | |
| remap | divergence kept | nvim has no 'remap' option (`:noremap` is the way); `:set remap` is accepted and ignored in both |
| report | done+tested | |
| scroll | done+tested (new) | `:set scroll=N` is the CTRL-D/CTRL-U amount |
| sections | done+tested (new) | read by `[[ ]]` and `{ }` |
| shell | done | `:!` and filters use it |
| shiftwidth | done+tested | |
| showmatch | partial | stored only (no visible effect) |
| showmode | partial | stored only (the mode is always shown) |
| slowopen | divergence kept | not an nvim option |
| tabstop | done+tested | |
| taglength | partial | stored only |
| tags | done+tested (new) | |
| term | divergence kept | not an nvim option; `$TERM` is read |
| terse | partial | stored only |
| warn | partial | stored only (`:!` after a change does not print "[No write since last change]") |
| wrapmargin | done+tested (new) | |
| wrapscan | done+tested | |
| writeany | partial | stored only |

## Other keys

| key | status | note |
|---|---|---|
| CTRL-G | done+tested | file name, position |
| CTRL-L | done+tested | redraw |
| CTRL-R (redo in nvim, not vi's "redraw") | divergence kept | Vim wins |
| CTRL-^ | done+tested | alternate file |
| CTRL-Z | missing | m31 request above |
| CTRL-] CTRL-T | done+tested (new) | |
| CTRL-V in insert, CTRL-W CTRL-U CTRL-H | done+tested | corpus 118 |
| `U` | done+tested | |
| `&` | done+tested | |

## Counts

Rows: see the tables. Items that the task text named and what happened: tags (done), args list (done), `:windo` (done), `:grep`/`:vimgrep`/`:make`
(done), Ex mode (done), `:preserve` and `-r` (done, `-r` partial), `:append`/`:insert`/`:change` (done), 'wrapmargin' 'scroll' 'sections'
'paragraphs' 'magic' (done), CTRL-Z / `:stop` / `:shell` (missing, m31 request), `-s` (missing).
