# Core status

State of m3's core against the plan, 2026-11-01, on branch `core` from v0.17.0 (8452e31). Every row was checked by running the binary (pty probes through the helpers of tests/e2e.py and tests/core_pty.py) or by running the oracle, not by reading the docs.

How to read it: **done+tested** has a named test; **done untested** works but no test pins it; **partial** works in part, the rest is named; **missing** is not built; **deferred** is deliberately not built, with the reason.

Oracle: `nvim` 0.11.5 is installed here, so `tests/oracles/oracle_nvim.py` ran live (41.7k corpus cases, all equal or listed in `known_divergences.txt`). Where nvim cannot answer (pickers, popups, buffers, the terminal) the oracle is the golden screens (`tests/screen_pty.py`, recorded from 0.15.0) and the pty scenarios.

Counts: 94 rows: 73 done+tested, 2 done untested, 6 partial, 9 missing, 4 deferred.

## A. The core list (docs/CORE-AND-PLUGINS.md, decision record)

Each bullet of the CORE paragraph.

| item | state | evidence |
|---|---|---|
| Vim engine and ex subset | done+tested | tests/oracles corpus (70 files, 41.7k cases against nvim 0.11.5), `oracle_nvim.py --fuzz`, known_divergences.txt lists 54 cases, each with its reason |
| Window, buffer and tab-page model | done+tested | tests/oracles/oracle_windows.py, tests/t_window.m31, t_split_run, e2e `tab_pages`, `tab_click_and_modifier`, screen_pty `split_*` |
| Renderer, animation, glide, indent guides | done+tested | tests/t_anim.m31, anim_pty.py, screen_pty `indent_guides` `wrap_long_lines`, bench/uxperf.py |
| LSP client: completion popup, semantic tokens, format on save | done+tested | tests/t_lsp.m31, t_pum.m31, t_semtok.m31, lsp_pty.py (popup_*, sync_*, format_on_save, semantic_tokens), e2e `lsp_client` |
| LSP: hover, signature help, definition, references, rename, code action, inlay hints, diagnostics list | done+tested | e2e `lsp_client`, `lsp_signature_hints_close`; `:Lsp ...` in MED_app |
| LSP: document symbols and workspace symbols from the server | missing | `:Symbols` is a lexical outline (MED_sources.symbol_entries); textDocument/documentSymbol and workspace/symbol are not requested; also no typeDefinition, implementation, declaration, call hierarchy |
| Picker primitive and core sources (files, buffers, grep, lines, help/keys, commands, options, marks, registers, quickfix, themes, recent, symbols, todos) | done+tested | tests/t_picker.m31, t_sources.m31, finder_pty.py, finder_variants_pty.py, screen_pty `finder_*` `command_palette` `keys_browser`; `:Registers` is new: core_pty `registers_picker` |
| Directory buffer (`:Explore`, `m3 DIR`) | done+tested | screen_pty `explore_directory`; core_pty `directory_argument_and_clean` (new: `m3 .` opens the listing, it used to exit 1) |
| Generic list (was the quickfix list; docs/LIST.md) | done+tested (0.25.0) | `tests/t_list.m31`; e2e `finder_grep_and_quickfix`; core_pty `quickfix_commands` (the `:c*` aliases) |
| Location list (`:lopen` `:lnext` ...) | folded in (0.25.0) | `:lnext` `:lprev` `:lfirst` `:llast` `:lclear` work on the one list store; `:lopen` and a per-window list do not exist |
| Message ring and `:messages` | done+tested | core_pty `messages_ring` (new: `:messages` was a no-op; now a 200 line ring, `:messages clear`; messages and notices are logged once each) |
| Snippets (LSP grammar, user snippets file) | done+tested | tests/t_snippet.m31, t_snippet_run + oracle_snippet.py against nvim vim.snippet, e2e `snippets_tab_select` |
| Undo files | done+tested | tests/t_undofile.m31, e2e `undofile_persists` |
| Project settings (.editorconfig, .m3.toml) | done+tested | tests/t_projconf.m31, e2e `project_settings` |
| Auto-reload, autowrite, autosave | done+tested | e2e `disk_watch_autosave_autowrite` |
| Theme engine, 14 themes, transparency | done+tested | tests/t_theme.m31, test_transparent.sh, transparent_pty.py, screen_pty `theme_*` |
| Minimal statusline | done+tested | screen_pty `start` and every golden screen; e2e `statusline_tabline_guides` |
| Tab line / bufferline | done+tested | screen_pty `bufferline`, `tab_pages`; e2e `statusline_tabline_guides` |
| Mouse | done+tested | e2e `tab_click_and_modifier`, `terminal_pane`; `--no-mouse` in test_entry_cli.sh |
| Clipboard: tools (pbcopy, wl-copy, xclip, xsel) and OSC 52 fallback | done+tested | t_register.m31 (registers), core_pty `osc52_without_clipboard_tool` (new: copy reaches the terminal when no tool exists; M3_NO_OSC52=1 turns it off). Paste from the terminal is bracketed paste, below |
| Extension API and `:Plugins` | done+tested | tests/t_ext.m31, t_plugins.m31, ext_pty.py, plugins_pty.py, tests/core_only.sh |

## B. ROADMAP items (docs/ROADMAP.md)

Numbers are the roadmap's.

| item | state | evidence |
|---|---|---|
| 1 Docs honesty pass | done untested | docs only; this file and docs/OPTIONS.md are the new honest lists |
| 2 undofile | done+tested | t_undofile, e2e `undofile_persists` |
| 3 `.` and `gq` mark fixes | done+tested | corpus 107_format_dot, 114_dot_mark |
| 4 Auto-save and auto-reload | done+tested | e2e `disk_watch_autosave_autowrite`; option `autosave` |
| 5 editorconfig and .m3.toml | done+tested | t_projconf, e2e `project_settings` (the roadmap names t_editorconfig; the file is t_projconf) |
| 6 Session restore | done+tested | t_session, e2e `session_layout_restore`, `session_restore` |
| 7 Folds beyond manual | done+tested | corpus 101, 108, 110, 111, 113, oracle_folds.py (3 modes); 8 marker-fold cases are known divergences |
| 8 linebreak, breakat, showbreak, breakindent | done+tested | corpus 87, 95, 112; t_wrapmap |
| 9 Snippet engine | done+tested | see section A |
| 10 cgn / dgn with `.` | done+tested | corpus 84, 109 |
| 11 Tab commands | done+tested | oracle_windows.py, e2e `tab_pages` |
| 12 m31git in process | done+tested | t_git, t_gitlib, git_pty (becomes a plugin in the other branch) |
| 13 `:Git` read commands | done+tested | git_pty, e2e `git_signs_and_pickers` |
| 14 Hunk objects and `:Hunk` | done+tested | t_git, e2e `git_hunk_jumps_and_no_repo` |
| 15 Completion popup | done+tested | t_pum, lsp_pty `popup_*`, fake_lsp_complete.py |
| 16 Incremental didChange, dynamic registration, format on save, cancel | done+tested | lsp_pty `sync_*`, `dynamic_registration`, `cancel_*`, `format_on_save` |
| 17 Semantic tokens | done+tested | t_semtok, oracle_tokens.py, lsp_pty `semantic_tokens` |
| 18 DAP | deferred | post 1.0 by the roadmap |
| 19 VT emulator for the terminal pane | done+tested | t_vt.m31, e2e `terminal_pane` |
| 20 Multiple cursors by replay | missing | not built; the roadmap makes it optional for 1.0 and experimental |
| 21 List continuation (formatoptions r o, n, a) | partial | `fo+=a` and `w` are stored only (known divergences, corpus 116); r/o/n pass the corpus 107/98 |
| 22 Markdown preview | missing | needs the tui-markdown library release; not started |
| 23 Spell checking | deferred | never in 1.x by the roadmap |
| 24 `:autocmd` `:augroup` `:doautocmd` | done+tested | new: engine/MED_autocmd.m31, corpus 117 (43 cases equal nvim), core_pty `autocmds_user_commands_and_if_in_keymap`. Events: BufWritePre/Post, BufReadPost, BufNewFile, BufEnter, BufLeave (declared, not fired), FileType, InsertEnter/Leave, VimEnter, VimLeavePre, TextYankPost (declared, not fired) |
| 25 `:command` and `:if` in sourced files | done+tested | new: corpus 117, `has()` `exists()` `executable()` `getenv()` in MED_expr, run_script blocks; one-line `if x \| cmd \| endif` is not supported |
| 26 Extension modules (replaces JSON-RPC) | done+tested | t_ext, ext_pty |
| 27 `:help` topics and `m3.1` | partial | `:help` opens the keymap picker; there are no help topics and no man page |
| 28 Packaging | partial | install.sh and musl exist; no SHA256SUMS verification, no formula text (owner items) |
| 29 Startup and memory budgets | partial | bench/bench.py and uxperf.py measure; no enforced budget in CI; measurements in this branch below |
| 30 Accessibility (`screenreader`, `NO_COLOR`) | missing | neither exists (NO_COLOR is not read) |
| 31 Config reference from the option table | done+tested | new: docs/OPTIONS.md generated by scripts/options_doc.py; `tests/test_core.sh` fails when it is stale |

## C. Vim parity (apps/nox/VIM_PARITY.md and the brief's list)

m3 is held to nvim by the corpus, not by the table; every row of VIM_PARITY's Implemented list passes it.

| item | state | evidence |
|---|---|---|
| Motions: hjkl w b e W B E ge 0 $ ^ + - \| { } gg G H M L % f t F T ; , CTRL-D U F B E Y O I, zz zt zb | done+tested | corpus 00, 10, 70-73, 81, 93-96 |
| Search: / ? n N * # g* g#, offsets e s b +-N, `;` chains, `//`, wrapscan, ignorecase/smartcase | done+tested | corpus 40, 77, 85; new cases in 115 (60 search cases) |
| Operators d c y gu gU g~ g? > < = gq gw ! with counts, forced v V and CTRL-V (o_CTRL-V) | done+tested | corpus 73, 107; o_CTRL-V is new (corpus 115) |
| Registers: named, append, numbered shift, small delete, `"_`, `"=`, `"%`, `":`, `"/`, `".`, CTRL-R forms | done+tested | corpus 74, 106, 115 |
| Marks: a-z A-Z, `'` `` ` `` `[ ] < > . ^ "`, :marks, :delmarks, mark adjustment on line edits | done+tested | corpus 43, 106; the `"` mark default is new |
| Macros and `@:`, `@@`, recursive, with counts, `:normal @a`, `:let @a` | done+tested | corpus 51, 80, 115, 116 |
| Counts and dot repeat (after operators, inserts, visual, macros, `:s`, g&) | done+tested | corpus 80, 116 (about 100 new cases) |
| Ex: ranges, patterns as addresses, `;`, marks, offsets, :d :m :t :co :j :> :< :y :pu :normal :g :v :s with flags g c i I n e & r, :sort, :retab, :left/:right/:center, :z, :undo/:redo/:earlier/:later, :@ | done+tested | corpus 45-50, 78, 100, 115; `:retab` was missing and is new |
| `:substitute` flags and specials (`\=`, `\u \U \l \L \e \E`, `&`, `~`, `\r \n`, `:s` repeat forms `& && g&`, `:~`) | done+tested | corpus 46, 85, 115; the `c` flag's cursor column is fixed |
| Patterns: magic levels, `\zs \ze \%[]`, lookaround, backrefs, `\%V` `\%'m`, `\%23l`, classes | done+tested | oracle_regex.py (186 cases + 6000 fuzz); `\%V` and `\%'m` are new; `\%#` and `\%.l` are not supported |
| Text objects iw aw iW aW is as ip ap i( a( ib i{ iB i[ i< i" i' i` it at, counts, repeated v-selection growth | done+tested | corpus 10, 44, 115 |
| Visual v V CTRL-V, o O, gv, I A c r J u U ~ > p P, `$` blocks, short lines, tabs | done+tested | corpus 20, 76, 115 |
| Insert: CTRL-W U H T D R O V K A N P, abbreviations, textwidth, autoindent, smartindent, expandtab, sts, sta | done+tested | corpus 52, 79, 98, 102, 104, 105; CTRL-R CTRL-W (invalid in Insert) is fixed |
| Folds: manual, indent, marker, zf zF zd zD zE zo zO zc zC za zA zv zx zX zm zM zr zR zn zN zj zk [z ]z, in Visual | done+tested | corpus 101, 108, 110, 111, 113; `zf` in Visual is new |
| Jumplist, changelist, `g;` `g,` CTRL-O CTRL-I, `:jumps` `:changes` | done+tested | corpus 81, 106, 114, 115 |
| Undo tree: u CTRL-R U g- g+ :undo N :earlier :later, undo blocks, branches | done+tested | corpus 41, 49, 75, 116 |
| gi gv g& g8 ga gJ gp gP gn gN g_ go gm gM | done+tested | corpus 84, 109, 115, 116 (`gv` after a line opened above the Visual area is a known divergence) |
| Completion keys in Insert (CTRL-N CTRL-P CTRL-X ...) | done+tested | corpus 99_complete (gen_complete.lua) |
| Options: selection=exclusive/old, virtualedit=all/onemore, formatoptions a/w | partial | stored only; known divergences, corpus 116 |
| Vimscript expressions in `:put =`, `:let`, `:s/\=` | partial | numbers, strings, printf, a few functions; no lists, floats, variables beyond `:let`; known divergences (no embedded scripting language) |
| CTRL-A in the command line (completion of all matches) | missing | known divergence in corpus 115; the key is dropped |
| Command-line window `q:` | deferred | listed divergence since 0.4 |
| `:set` for every documented option, `opt?` `opt&` `opt!` `invopt` `noopt` `+= -= ^=` | done+tested | corpus 97_options_fuzz; core_pty `set_query_toggle_reset`; docs/OPTIONS.md lists 324 options (it was 220: 104 portable nvim options were rejected with E518) |

## D. Files, buffers, windows, robustness

The brief's section (b) and (c).

| item | state | evidence |
|---|---|---|
| Buffer lifecycle: hidden, modified guards (E37, E162), :wq :x :q! :qa! ZZ ZQ, :w!, file changed on disk (W12) | done+tested | e2e `disk_watch_autosave_autowrite`; probed by pty (`:q` refuses, `:x` `:wq` `ZZ` write, `:q!` `ZQ` do not); `:w!` on a read-only file is not possible, see E below |
| Swap, backup and recovery policy | done+tested | no swap files; new: a recovery file per modified buffer in the state directory (`recover/`), written when the user is quiet for 1.5 s, removed on `:w` and on a deliberate quit; after `kill -9` the next open says W325 and `:recover` loads it; core_pty `recovery_after_kill9`; option `recover` |
| Atomic write (write to a temporary file, rename) | missing | `:w` truncates and writes in place (as nvim with `nowritebackup` does); the recovery file covers a crash before `:w`; a crash during the write itself can still lose the file |
| Encoding, line endings, BOM | done+tested | new: CRLF files stay CRLF, a UTF-8 BOM stays, non-UTF-8 files open as Latin-1 and are written back as Latin-1 (`fileformat` `fileencoding` `bomb`, `:set ff=unix`, E513 when a character does not fit); core_pty `encoding_and_line_endings`. Other encodings (UTF-16, cp1252 ...) are not converted |
| Binary and unreadable files, directory argument, permission errors | done+tested | binary: opens as Latin-1 (was: refused, exit 1); unreadable: `m3: "f": permission denied` exit 1; read-only write: E212 reported; directory: opens the listing; core_pty `directory_argument_and_clean`, probes in this file's history |
| Large files: a 50 MB, 1M line file opens and scrolls | done+tested | measured: opens in 0.8 s, `G` and `/pattern` under 0.3 s (bench by pty probe, not a CI test: timings do not belong in the suite) |
| Long lines: one 1 MB or 5 MB line | done+tested | was 1.7 s to open and 50-60 percent of a core while idle (language and TODO scans of the whole line on every tick and frame); now 0.45 s and 0.1 percent; core_pty `long_line_idle_cpu` |
| Huge paste, bracketed paste | done+tested | probe: a 3 MB, 100k line bracketed paste in Insert lands in 0.6 s; e2e/screen golden cover small pastes (`surround_and_pairs` `insert_typing`) |
| Resize storm | done+tested | probe: 200 SIGWINCH with changing sizes, no crash, screen correct; screen_pty `narrow_*` `resize_while_split` |
| Terminal restored on the ordinary exit paths: `:q`, `ZZ`, `:qa!` | done+tested | TUI_app leave sequence on the normal and error return paths (e2e checks the screen after exit) |
| Terminal restored on SIGTERM, SIGHUP, SIGINT, kill, a trap | missing | blocked by m31: the runtime has no signal handler and no `on_trap` (docs/M31-ON-TRAP-REQUEST.md); tui's own FRICTION.md section 23 says the same. Probed: SIGTERM/SIGHUP leave the terminal in the alternate screen. The recovery file above means no text is lost |
| Crash breaker (plugins start off after an abnormal exit) | missing | planned in CORE-AND-PLUGINS 4.10; needs a plugin to protect and the m31 hook; not built |
| `:w!` on a read-only file you own | missing | needs `fs.chmod` in the m31 stdlib (verified: `fs` has no chmod); `:w!` reports E212 |
| Tabs, expandtab, shiftwidth, softtabstop, smarttab, retab, editorconfig indent keys | done+tested | corpus 79, 98, 115; t_projconf |

## E. Configuration and command line

The brief's section (d).

| item | state | evidence |
|---|---|---|
| Flat option names, `:set` accessor consistency | done+tested | MED_ex option_text/option_store for the fields the engine reads; the rest through `opts`; core_pty `set_query_toggle_reset` |
| Init file loading (`keymap.vim`, `$M3_KEYMAP`, `--keymap`), `source`, `if`/`else`, user commands, autocmds | done+tested | e2e `user_maps_in_which_key`, `cmd_and_buffer_maps`; core_pty `autocmds_user_commands_and_if_in_keymap` |
| `--clean` | done+tested | new; `--keymap NONE --no-session`; test_entry_cli.sh and core_pty |
| `--version`, `--help`, `--completions bash\|zsh\|fish`, short forms `--k`, Oro refusals, exit statuses 0/1/2 | done+tested | tests/test_entry_cli.sh (about 60 checks); the grammar is `args` from m31, the same as mgit/1git; deprecated `-u` `-v` `-h` still warn and work |
| Plugin options naming (`harpoon_max`) | done untested | plugins branch |

## Deliberate divergences from vim/nvim

m3 takes ideas from nvim and helix and does not copy their mistakes or their unwanted features. The nvim oracle corpus (`tests/oracles`) stays the
regression reference for the vi core, not a mandate. A divergence is listed here, and the oracle cases it changes are in
`tests/oracles/known_divergences.txt` with the reason: none is hidden. Every default below can be rebound.

| divergence | vim / nvim | m3 | oracle |
|---|---|---|---|
| `:l`, `:list` (0.25.0) | print lines unambiguously, as `:set list` shows them; with a range, the cursor goes to the last line | open the generic list (`:l NAME`); a range is ignored. The print is still shown by `:set list` | 7 corpus cases (`:list`, `:1,2l`, `:2l`, `:2,3l`) in known_divergences.txt, reason "intentional" |
| `:lnext` `:lprev` `:lfirst` `:llast` `:lclear`, `:List*` | the location list of the current window | the generic list (default name `quickfix`); `:lopen`, `:lolder`, `:lwindow` do not exist; `:ll` is `:llast` | none in the corpus |
| `[q` `]q` `[Q` `]Q` | nvim 0.11 maps quickfix prev / next / first / last | not mapped; `[l` `]l` `[L` `]L` walk the default list | none (keys are not in the corpus) |
| one list store | quickfix and per-window location lists | a single store of named lists | none |
| Select mode `gh` `gH` | Select-mode starters | git hunk operators (0.23.0) | none |
| `Q` | Ex mode (vim) / replay macro (nvim 0.11) | follows nvim 0.11; Ex mode is `gQ` | matches nvim |

Proposed for dropping (nothing removed; the owner decides): the `:z` and `:#` page printers, `:=`, the Ex-mode entry `gQ` / `:visual` dance, and
the remaining `[` / `]` chords that exist only for vi's C-source navigation. No part of m3's own design depends on them. The location-list commands
`:lopen :lwindow :lolder :lnewer` are not ported (no second store).

## Choices made without the owner

| choice | why |
|---|---|
| Recovery files instead of swap files | A swap file litters the project and is read by nobody; a state-directory copy written only when the buffer is modified and the user is quiet costs nothing while typing and answers the one question (what did I lose?) |
| Non-UTF-8 text opens as Latin-1 | It is the last entry of nvim's default `fileencodings` and the only single-byte encoding that round-trips every byte |
| `m3 DIR` opens the listing | nvim does (netrw); exiting 1 was the worse behaviour |
| OSC 52 is on when no clipboard tool exists | the terminal decides; `M3_NO_OSC52=1` turns it off; reading the clipboard through OSC 52 is never done |
| One list store, no per-window location list | m3 produces lists (picker CTRL-Q, `:grep`, LSP, hunks, plugins) and a second store would hold nothing the first cannot; the `:l*` commands are the generic list's (0.25.0) |
| User commands may be abbreviated when the prefix is unique, as in Vim | the corpus compares it |
| `:augroup!` removes nothing | nvim 0.11 keeps the deleted group's autocommands running; the corpus compares it |
| Options the engine does not read are accepted and stored, and docs/OPTIONS.md lists them | a `:set` in a user's init file must not stop at E518 because of an option m3 has no use for |

## What stays open

* Signals and traps leave the terminal raw (m31 runtime: a signal handler or `on_trap`; requests below).
* `fs.chmod` for `:w!` on read-only files (m31 stdlib request).
* A `recover`-style atomic write needs nothing from m31 (`fs.rename` exists) but changes ownership and links semantics; left as is.
* LSP document and workspace symbols, type definition, implementation, declaration, call hierarchy.
* `selection=exclusive|old`, `virtualedit=all|onemore`, `formatoptions` a and w, Vimscript lists and floats in `:put =`.
* Multi-cursor (20), markdown preview (22), help topics and man page (27), `NO_COLOR` and screenreader mode (30).

### Measured here (Linux x86-64, this machine)

| what | before | after |
|---|---|---|
| open a 1 MB single-line file | 1.7 s | 0.45 s |
| open a 5 MB single-line file | 6.4 s | 1.7 s |
| idle CPU, 1 MB single-line file | 58 percent of a core | 3 percent |
| open a 50 MB, 1M-line file | 0.84 s | 0.84 s (unchanged) |
| `G` in that file, `/needle` in it | under 0.3 s | under 0.3 s |
| start to first frame, 2000-line file (median of 6, pty) | 0.22 s | 0.23 s (noise) |
| 1000 typed characters in Insert, until the screen is quiet | 0.15 s | 0.15 s |
