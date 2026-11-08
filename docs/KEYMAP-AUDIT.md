# Keymap audit (0.30.0)

The owner's principle: **prefer toggles and combined keys over paired keys.** One key flips a state (stage and unstage, show and hide); fewer keys with an obvious
meaning beat many near-duplicates. This audit went through `docs/KEYMAP.md` and the four profiles. Vim motions, operators and the `[` `]` pairs are untouched (next and
previous are natural pairs there); the `nvim` profile follows the owner's config and is changed only where m3 itself added a duplicate. Any key can still be
rebound in the user's keymap file, which is read after the defaults.

Decisions: **keep**, **merge into X** (the action stays on the key named), **toggle**, **drop** (the action has another key, or the key's only job was to be a second spelling).

## The `default` profile, leader tree (`<Space>`)

| key | was | decision | reason |
|---|---|---|---|
| `<Space><Space>` | find files | drop | `<Space>ff` is the same picker |
| `<Space>,` | switch buffer | drop | `<Space>fb` |
| `<Space>/` | live grep (project) | drop | `<Space>sg` |
| `<Space>:` | commands | drop | `<Space>sC`; `:` itself opens the command line |
| `<Space>?` | all keys | keep | the one help key; `sh` and `sk` were the same picker |
| `<Space>sh`, `<Space>sk` | help / keymaps | merge into `?` | three spellings of one picker |
| `<Space>fG` | live grep (project) | merge into `sg` | |
| `<Space>sb` | lines of this buffer | merge into `fg` | `fg` is the owner's locked key for it |
| `<Space>sd`, `<Space>x` group (`xx xX xQ xL`) | diagnostics, buffer diagnostics, list | merge into `D` group and `sq` | the `D` group (`Dd` workspace, `Db` buffer) is the diagnostics key; `sq` opens the generic list; `xQ` and `xL` opened the same list as `sq` |
| `<Space>Dl`, `<Space>Ds` | diagnostic at cursor, symbols | merge into `cd`, `ss` | |
| `<Space>cs` | symbols | merge into `ss` | symbols are a search |
| `<Space>bn`, `<Space>bp` | next / previous buffer | drop | `]b` and `[b` (a natural pair) |
| `<Space>bl` | list buffers | drop | `fb` is the list, with a preview |
| `<Space>ws`, `<Space>wv` | split below / right | merge into `-` and `\|` | |
| `<Space>gs`, `<Space>gf` | changed files | merge into `gg` | three keys for one picker |
| `<Space>tt` | terminal (a group of one) | merge into `<Space>t` | one key opens a terminal |
| `<Space>e` | file tree | keep (a toggle) | opens with the file revealed, closes when open |
| `<Space>uh` | toggle inlay hints | keep (a toggle) | |
| `<Space>uG` | toggle git signs | keep (a toggle) | |
| `<Space>uC` | colour schemes | keep | a picker, not a switch |
| `<Space>ff fr fb fg fe fn`, `sg sw so sm ss sq sC sp sn`, `bb bd br`, `wd wo w=`, `gg gb gl gn gR`, `cr ca cf cd`, `Dd Db`, `j`, `n`, `-`, `\|`, `qq qa` | | keep | one key each |

There were no pairs of on and off keys for an option in the `default` tree, so no `<Space>t*` switches needed turning into toggles: the `u` group already has one key per switch.

## Plugin keys of the `default` profile

| key | was | decision | reason |
|---|---|---|---|
| `<Space>ha he hn hp hx`, `<Space>1`..`9` | harpoon | keep | `hn` / `hp` are a natural pair |
| `<Space>gp`, `<Space>gP`, `<Space>gc` | pull, push, commit | keep | different actions |
| `<Space>ghs` `ghu` | stage hunk / unstage hunk | **toggle** (planned, 0.31) | one key stages an unstaged hunk and unstages a staged one |
| `<Space>ghr`, `ghp`, `ghb`, `ghB`, `gL`, `gd` | reset, preview, blame line, blame list, file log, diff | keep for now; the git milestone (0.31) replaces the hunk family by the `gh*` set the owner chose (`ghs ghr ghS ghR ghd ghD ghb ghl`) and drops `ghp` and `<Space>gB` | |
| `[h ]h [H ]H`, `[b ]b [B ]B`, `[l ]l [L ]L`, `[t ]t`, `[d ]d` | motions | keep | natural pairs |
| `<Space>st` | TODO list | keep | |

## The `nvim` and `legacy` profiles

The leader tree here is the owner's own config plus m3 extras. Rows from his config are kept as they are, including `xQ` and `xL` (both open the generic list; they were two keys in his config). Only a
row m3 itself added as a second spelling was dropped:

| key | was | decision | reason |
|---|---|---|---|
| `<Space>fk` | keymaps | drop | `<Space>fh` is the same picker |

The root keys `<Space><Space> , / :` of these two profiles are kept: they are the muscle memory of the config the profile reproduces. The `nvim` profile will be re-checked against his keymap file when it is supplied.

## Vim chords

Not touched: motions, operators, text objects, registers, marks, `g` `z` `[` `]` `CTRL-W`. Divergence from vim applies to defaults that are mistakes, not to the editing grammar (the removals
of 0.27.0 are in docs/DIVERGENCE-AUDIT.md).

## The `gh` hunk keys (0.31.0)

`gh` is now only a prefix; the final set is `ghs` (stage, or unstage if staged; Visual: the selected lines), `ghr` (reset; Visual: the selected lines), `ghS` (stage or unstage the whole buffer),
`ghR` (reset the buffer to the index: the command line is typed, Enter confirms), `ghd` (inline diff of the hunk), `ghD` (the buffer against the index), `ghb` (blame the line), `ghl` (the hunks in the
generic list), with `]h [h` for the motions. `gh{motion}` and `gH{motion}` (0.23.0) are gone: they would have made `ghb` and `ghl` mean "the hunks from the cursor back a word" and "one character right";
Visual mode (`ghs`, `ghr`) covers a range of lines, and `ih` / `ah` stay as text objects (`vihghs`). `<Space>gh*`, `<Space>gB` and `ghp` are gone.

## Migration

One line per removed key is in CHANGELOG.md (0.30.0).
