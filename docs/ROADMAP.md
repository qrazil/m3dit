# Roadmap: 0.7.0 to 1.0.0

Written 2026-10-15 from DESIGN.md (sections 9, 11, 12, 13, 14), CHANGELOG.md, docs/KEYMAP.md,
`tests/oracles/known_divergences.txt`, `tests/oracles/pending/` and the open items of the 0.4.x line. The
0.5.0 (themes) and 0.6.0 (renderer diffing, animation, UX performance) releases are being built on other
branches and are not part of this queue; this queue starts at 0.7.0 and does not touch colour handling or the
renderer.

## 0. Ground rules (decisions that apply to every item)

| Rule | Reason |
|---|---|
| Vim semantics, checked against `nvim --headless -u NONE` where nvim can answer; Helix-like polish only where Vim is silent | The oracle is what makes the engine trustworthy; nothing else in the repo is as strong |
| m31 only; an item that needs something m31 lacks stops and is recorded in section 5 | Rule 1 of DESIGN.md |
| No tree-sitter, no embedded scripting language in 1.0 | G3, and a language is a second product |
| Extension is the keymap/ex file (`:map`, `:source`, `:autocmd`-lite) in 1.0; an external-process JSON-RPC protocol after 1.0 | Section 12: a process boundary costs a spawn per plugin and a second widget set; nothing needs it yet |
| Every behaviour item ships with its test in the same commit: nvim corpus case, unit test (`tests/t_*.m31`) or pty scenario (`tests/e2e.py`), in that order of preference | |
| Tests are macOS-safe: BSD `sed -i` needs a suffix, no `tac`, `cat -A`, GNU `timeout`, `date +%s%N`, no fixed `/tmp` paths | The owner builds on macOS |
| One commit per item; one version per shippable group; full engine oracle suite (about 15 minutes) at the end of each group | |
| Engine work lives in `engine/` and new modules; edits to `ui/MED_app.m31` are small, delimited hooks | Concurrent branches rebase cleanly |

Size: S = under a day, M = one to three days, L = a week or more.

## 1. State at 0.4.1: what DESIGN section 9 says versus what is true

Rows of the Helix table that are stale or still open, with the verdict used below.

| Row | Section 9 says | Truth now | Queue item |
|---|---|---|---|
| Mouse drag-select | Partial | Done: press, drag (Visual), wheel, window focus (`MED_app` mouse handler) | verify only (R1) |
| Signature help, inlay hints | "no signature help or inlay hints" | Done in 0.4.0 (`:Lsp signature`, `:Lsp hints`); hints are drawn at line end | inline hints stay a renderer item (smooth) |
| Git blame, stage / reset hunk | "later" | Done (0.1.0 plugin: `<Space>gs gr gp gb`) | 0.9.0 moves them in-process |
| Regex backreferences, lookaround (G6) | "no backreferences or lookaround" | Stale: `engine/MED_regex.m31` is the editor's own backtracking engine with `\1`, `\@=`, `\@<=`, `\zs`, `\%[]`, lazy repeats, multi-line (fuzzed against nvim, 186 pattern cases + 12 seeds); G6 concerns only the stdlib `regex` | docs fix in 0.7.0 |
| `gn` / `cgn` | "later" | Done: `gn gN` in Normal, Visual and as operator target (corpus 84) | verify `cgn` + `.` in 0.8.0 corpus |
| Folds | Partial | Manual only; `foldmethod`, `foldlevel`, `foldenable` stored but inert | 0.8.0 |
| Persistent undo | Partial | `undofile` option stored only | 0.7.0 |
| Auto-reload / auto-save | Partial | Auto-reload polls mtimes; `autowrite` stored only | 0.7.0 |
| Snippets | Later | LSP completion flattens snippets to defaults | 0.8.0 |
| `.` position after a typed burst | known gap | nvim typeahead batching artifact, see R2 | 0.7.0 (investigate, probably document) |
| `gq` leaves `.` one line higher | known gap | engine bug | 0.7.0 |
| macOS paths | pbcopy done; LSP "untested on mac" | clipboard picks pbcopy/pbpaste; LSP spawns servers via `proc` (portable); install.sh covers darwin | needs a mac smoke list (R3, owner) |
| Embedded terminal | line-oriented screen model | no alt screen, no cursor addressing | 0.11.0 |
| Soft wrap `linebreak` | later | option stored only | 0.8.0 |
| Config | `keymap.vim` only | no project settings, no editorconfig | 0.7.0 |
| Session restore | cursor + recent files | no buffer/layout restore | 0.7.0 |

## 2. The queue

> **0.10.0 shipped out of queue: the file finder** (drawing safety, hints, name-first ranking, relevance,
> frecency; docs/FINDER.md). The groups below keep their order; the one headed 0.10.0 is the next free minor
> after it (read it as 0.11.0, and each later heading one minor up).

Each row: scope; reference behaviour; test; dependencies; size; decision.

### 0.7.0 Persistence and project settings (engine-centred)

| # | Item | Reference | Test | Deps | Size | Decision and reason |
|---|---|---|---|---|---|---|
| 1 | Docs honesty pass: DESIGN section 9 / 11 / README refreshed (G6 solved, drag, signature help, git) | | `tests/t_keymap.m31` unchanged | | S | Do first so later rows build on true statements |
| 2 | `undofile`: write the undo tree beside the file, read it back on open when the file is unchanged | nvim `undofile` / `undodir` (own format) | unit (`tests/t_undofile.m31`: round trip, content-hash mismatch discards, truncated file ignored); nvim cannot read our format, so no oracle | none | M | Own text format in `~/.local/state/m3/undo/<hash>` (not beside the file: no litter in repos, `undodir` default of nvim is also a state dir). Keyed by canonical path, validated by a content hash, so a changed file discards history instead of corrupting it. Default on, because the owner's config has `undofile` |
| 3 | `.` and `gq` mark fixes | nvim `'.` after `gq`; after typed bursts | corpus rows moved out of known gaps | | S | `gq` fix is an engine bug and is fixed. The burst case is an artifact of nvim batching typeahead in `feedkeys`; if the real (interactive) behaviour already matches, record it in known_divergences with that reason instead of reproducing a harness artifact |
| 4 | Auto-save and auto-reload hardening | `autowrite`, `autowriteall`, `autoread`, `:checktime`, `FocusLost` | unit with temp files (macOS-safe) | | S | `autowrite` writes modified buffers before `:next`, `:b`, `:e`, `:make`, `:!`; add `autosave` (m3 option, seconds, default off) on the idle tick; reload only unmodified buffers, warn (W12) on modified ones |
| 5 | Project settings: `.editorconfig` and `.m3.toml` | EditorConfig spec (`indent_style`, `indent_size`, `tab_width`, `end_of_line`, `charset`, `trim_trailing_whitespace`, `insert_final_newline`, `max_line_length`); `.m3.toml` = `[options]` table of `:set` names plus `[languages.NAME]` | unit (`tests/t_editorconfig.m31`) | | M | Parse EditorConfig ourselves (glob rules `*`, `**`, `{a,b}`, `[seq]`); `.m3.toml` is a deliberately tiny TOML subset so the engine does not depend on the `toml` crate being importable. Precedence: defaults < user keymap file < editorconfig < `.m3.toml` < modeline. Applied at buffer open, never mid-edit |
| 6 | Session restore | `:mksession` idea, restricted | pty scenario | 2 | M | `m3` with no arguments in a directory with saved state reopens the last buffers, tab/window layout (the 0.4.0 window model already has a serialisable tree) and cursors; `m3 -S` / `:Session save|load|delete NAME`. Not Vim's `Session.vim` script: our own file under the state dir |

### 0.8.0 Editing depth

> Status (branch `next`, built from `822a0b0`): items 7 to 11 are done (7: indent and marker folds including jump
> levels such as `{{{3`, `foldlevel`, `foldlevelstart`, counted line operators over closed folds). See the Unreleased
> entries of CHANGELOG.md and `tests/oracles/known_divergences.txt`.

| # | Item | Reference | Test | Deps | Size | Decision and reason |
|---|---|---|---|---|---|---|
| 7 | Folds beyond manual: `foldmethod=indent|marker`, `foldlevel`, `foldminlines`, `zx zX zm zM zr zR zn zN zc zo` level semantics, `foldlevelstart`, `foldtext` default | nvim | nvim corpus (`pending/folds.txt` becomes real corpus, plus indent/marker fuzz) | | M | `expr` and `syntax` methods stay unsupported (need `expr`/syntax groups); `diff` arrives with a diff view, not here. Reason: indent and marker cover real use and are oracle-checkable |
| 8 | `linebreak` / `breakat` / `showbreak` / `breakindent` | nvim | corpus (wrap cases exist: 87, 95) | | M | Wrapping decision is in the engine's wrap model (`MED_view` computes rows); only the width function changes. If it needs the renderer from `feat/smooth`, split it and land it after the merge |
| 9 | Snippet engine | LSP snippet grammar (`$1 ${1:default} ${1|a,b|} $0 ${1/re/fmt/opts} $TM_FILENAME` etc.); user snippets file `~/.config/m3/snippets.json` (VS Code format, so existing collections work) | unit (parse, expand, tabstop navigation, nested placeholders, mirrors, choice), pty scenario for Tab / S-Tab | | L | Engine owns expansion state (session of tabstops that follow edits through the mark machinery); `<Tab>` / `<S-Tab>` jump while active, `<Esc>` ends. Minimal transform support: `${n/regex/format/flags}` via `MED_regex` with `\u \U \l \L \E`, `${n:/upcase|downcase|capitalize}`. Variables: `TM_FILENAME`, `TM_FILENAME_BASE`, `TM_DIRECTORY`, `TM_LINE_INDEX`, `TM_LINE_NUMBER`, `TM_SELECTED_TEXT`, `CLIPBOARD`, `CURRENT_YEAR`... no shell variables. LSP completion switches from `plain_snippet` to this engine |
| 10 | `cgn` / `dgn` `.` verification, `gn` with counts and `:set nowrapscan` | nvim | extend corpus 84 | | S | Probe, fix what differs |
| 11 | Tab commands: `:tab split`, `:tab {cmd}`, `:{N}tabnew`, tab-label click | nvim | `oracle_windows.py` cases for the window model; click is a unit test of the hit-test function | | S | Window-model part (modifier, placement) is engine/ui-window; the click needs the tab line geometry that `feat/smooth` may change, so the hit-test is written against `MED_window` data and wired last |

### 0.9.0 Git in-process (m31git as a library)

| # | Item | Reference | Test | Deps | Size | Decision and reason |
|---|---|---|---|---|---|---|
| 12 | Add the `m31git` library as a dependency; replace `git show HEAD:path` and `git blame --porcelain` subprocesses in `ui/MED_git.m31` with `GIT_object` / `GIT_hunks` / `GIT_blame` | gitsigns | existing `tests/t_git.m31` must pass unchanged; add a 100k-line timing check | **m31git tagged library release** (the repo is being renamed qrazil/m31git; `deps` needs a stable commit; the GIT_ modules are importable today) | M | Fall back to the subprocess when the library reports an error, so a repo layout the library does not understand (worktrees, partial clones, sha256 objects) still shows a gutter. Reason: no `git` binary needed, no spawn per refresh |
| 13 | `:Git` read commands over the library: log (file, line range), show, diff (HEAD, index, working), blame as a picker with preview | fugitive read side | pty scenario | 12 | M | Read only. Writes stay hunk stage/reset and `<Space>g` suspending into `gitui`/`mgit` for anything else (DESIGN row "fugitive: never in medit") |
| 14 | Hunk text objects `ih` / `ah`, `:Gitsigns`-style `:Hunk stage|reset|undo|preview` | gitsigns | unit | 12 | S | Cheap once hunks are in-process |

Status of items 12 to 14 (0.12.0): done. Decision D3 numbers (m31 v0.6.0, tui v0.11.0): the library adds 17.4 percent to the
binary and about 12 s to a clean build, inside the 30 percent and 40 s limits, so it is the default and there is no build
switch. `m31git` v0.27.1 pins the same `tui` and `syntax` as m3, which m31 requires (v0.27.0 pinned tui v0.8.0 and could
not be combined). Item 13's `-L` follows first parents; the library has no merge-aware line history. Item 14 uses `:Hunk
stage|reset|undo|preview` (`undo` unstages) and the objects `ih` / `ah`.

### 0.10.0 Language intelligence completion

| # | Item | Reference | Test | Deps | Size | Decision and reason |
|---|---|---|---|---|---|---|
| 15 | Completion popup that follows the cursor: trigger characters, as-you-type filtering, `completionItem/resolve` documentation, commit characters, snippets through item 9 | blink.cmp / nvim-cmp essentials | `tests/fake_lsp.py` scenarios + pty | 9 | L | Keep CTRL-Space picker as the explicit path; the popup is opt-in `:set completeopt`-style `lspcomplete=auto|manual` (default `auto` after 1.0 soak) |
| 16 | Incremental `didChange`, dynamic registration, format on save (`:set lspformat`), `$/cancelRequest`, `workspace/didChangeWatchedFiles` | LSP 3.17 | `fake_lsp.py` | | M | Incremental sync only when the server announces it; full sync stays the default |
| 17 | Semantic tokens (overlay on the lexical highlighter) | LSP 3.17 | fake server | `feat/themes` merged (class to colour map) | M | After themes; skipped if the theme engine has no overlay slot |
| 18 | DAP | | | 15, a UI for variables and frames | L | Post-1.0. Reason: the pipes exist, the UI does not, and it is a second protocol client |

### 0.11.0 Terminal

| # | Item | Reference | Test | Deps | Size | Decision and reason |
|---|---|---|---|---|---|---|
| 19 | `ui/MED_vt.m31` becomes a real VT emulator: cursor addressing, SGR, erase, scroll regions, alternate screen, wide characters, bracketed paste, resize through `proc` pty size | xterm subset (vttest) | `tests/t_vt.m31` with recorded byte streams (`ls --color`, `htop` frame, `vim` start-up) | m31 pty winsize call (check `proc.start_pty` API at 0.5.0) | L | A screen-model-first emulator, not a parser per application. If `proc` lacks a pty resize call this is blocked and recorded |

### 0.12.0 Multi-selection

| # | Item | Reference | Test | Deps | Size | Decision and reason |
|---|---|---|---|---|---|---|
| 20 | Multiple cursors by replay: a set of (cursor or selection) positions; every Normal / Insert key is fed once per cursor from the last to the first, as one undo block; `<C-n>` (vim-visual-multi) adds the next match of the word, `gn`-like add-all, `<Esc>` collapses | vim-visual-multi, Helix `C` / `s` | corpus: each case equals the same keys run per cursor by hand in nvim (oracle runs N headless sequences and merges) | | L | Replay on the existing engine keeps the whole Vim grammar free and avoids a Helix-style selection-first rewrite. Cost: commands that read the screen (`H`, `CTRL-D`) run on the primary only. **This is the one item with architectural risk** (see section 4, D1): it ships as experimental and is cut from 1.0 if replay fails the dot/undo semantics |

### 0.13.0 Markdown and prose

| # | Item | Reference | Test | Deps | Size | Decision and reason |
|---|---|---|---|---|---|---|
| 21 | List continuation: `formatoptions` `r` `o` with `comments`/`flp` for `- `, `* `, `1.`, `> `, `- [ ]`; `formatoptions` `n` and `a` | nvim `ftplugin/markdown` | corpus (`formatoptions` fuzz exists) | | M | Engine-side, oracle-checkable |
| 22 | Markdown preview in a split through the `tui-markdown` library (read only, follows the cursor, rendered at window width) | | pty scenario | tui-markdown tagged release | M | Library render, not a browser (DESIGN: markdown-preview "never" stays true for browsers) |
| 23 | Spell checking | | | a word list | L | **Never** in 1.0: needs dictionaries; revisit post-1.0 |

### 0.14.0 Extensibility without a language

| # | Item | Reference | Test | Deps | Size | Decision and reason |
|---|---|---|---|---|---|---|
| 24 | `:autocmd` / `:augroup` / `:doautocmd` subset: `BufRead BufNewFile BufWritePre BufWritePost BufEnter BufLeave InsertEnter InsertLeave FileType VimEnter VimLeavePre TextYankPost DirChanged`, pattern globs, `++once`, commands are ex lines | nvim | corpus for the ex semantics; unit for events | | M | The smallest thing that replaces most of what people write Lua for (format on save, per-filetype settings). Still ex lines, no scripting |
| 25 | `:command` user commands (`:command! -nargs=* Name ex-line with <args>`) and `:function`-less `:if/:else/:endif` in sourced files | nvim | corpus | | M | Conditions are needed to share one `keymap.vim` between machines (`has('mac')`, `executable(...)`, `exists(...)`) |
| 26 | ~~External-process JSON-RPC extension protocol~~ replaced by compiled-in m31 extension modules (D2) | docs/EXTENSIONS.md | `t_ext`, `ext_pty.py` | | L | API 0.1.0 done behind a build switch; the JSON-RPC protocol is not built |

### 0.15.0 Polish, packaging and docs

| # | Item | Reference | Test | Size | Decision and reason |
|---|---|---|---|---|---|
| 27 | `:help` topics (searchable, one file per area, shipped inside the binary) and a man page `m3.1` generated from the keymap table | | `tests/t_help.m31` (every `:help {topic}` in docs resolves) | M | Generated from the same tables as KEYMAP.md, so they cannot rot |
| 28 | Packaging: `install.sh` (done), musl (done), `SHA256SUMS` published and verified by `install.sh`, Homebrew formula and tap text, `.deb` and `.rpm` recipes documented | | pty smoke on the artifacts | S | Document `.deb`/`.rpm` only; the tap lives in a separate repo the owner creates |
| 29 | Startup and memory budget measured in `bench/bench.py`: start to first frame under 60 ms on a 1k-line file, under 120 MB RSS for a 100k-line file with 1000 edits; regressions fail CI nightly | DESIGN section 8 | bench | S | Budgets, not promises: they are set after the first measurement and then enforced |
| 30 | Accessibility: `:set screenreader` (no animation, cursor kept at the edit position, status messages on one stable row, no box-drawing in pickers), `NO_COLOR` honoured | | pty scenario | S | Terminal screen readers read the cursor row; the mode only has to keep the cursor honest |
| 31 | Config reference page generated from the option table (`engine/MED_option.m31`), flagging stored-only options | | unit | S | Honest list of what an option does |

### 1.0.0 acceptance bar

1.0.0 is tagged when all of these hold:

1. Engine: the full nvim oracle (corpora, fuzz seeds, window oracle, regex oracle) passes with every known divergence listed with a reason, none listed as "not yet implemented" except the command-line window.
2. Every option in the option table either changes behaviour or is listed in the config reference as stored-only.
3. Items 1 to 11 and 15, 16, 19, 24, 25, 27, 28 shipped. Items 12 to 14 shipped unless m31git has no tagged library release (then the subprocess path stays and is documented). Item 20 (multi-selection) is not required; if it shipped it is marked experimental.
4. Session restore, undofile, editorconfig and autocmds work together on both Linux and macOS (the mac smoke list in the README, run by the owner).
5. Startup and memory budgets of item 29 are met on the CI runner.
6. No panic or hang in a 1 hour pty fuzz of random keys, resize and mouse events (`tests/e2e.py --fuzz`, to be added in 0.15.0), and no leftover child process after quit with LSP and terminal open.
7. Documentation: README, KEYMAP, `:help`, `m3.1` and the config reference are generated or checked by tests; DESIGN section 9 has no stale row.
8. A stability promise: the keymap file syntax, the state-directory layout versioning and the editorconfig/.m3.toml keys do not change incompatibly within 1.x.

### Deliberately never in scope

Tree-sitter or any parse-tree feature (G3); an embedded scripting language (Lua, Vimscript beyond the listed ex subset); AI assistants inside the editor; a browser-based markdown preview; fugitive-style full git UI (that is `mgit`/`gitui`); devicons by default; neoscroll-style animation of buffer scrolling beyond what `feat/smooth` ships; netrw's remote file protocols; spell checking in 1.x; the command-line window `q:` (listed divergence); Vim9script.

## 3. Dependencies on other repos and releases

| Needed by | Needs | Status |
|---|---|---|
| 12 to 14 | `qrazil/m31git` (formerly gitui) as a pinned dependency exposing `GIT_object`, `GIT_hunks`, `GIT_blame`, `GIT_log` | modules exist, the rename is in flight, no library tag |
| 22 | `qrazil/tui-markdown` tagged release | branch work exists in `repo-extractions/tui-markdown` |
| 17 | `feat/themes` merged (0.5.0) | in progress |
| 11 (click), 8 | `feat/smooth` merged (0.6.0), only if the renderer geometry changed | in progress |
| 19 | `proc.start_pty` size change in m31 | to verify against 0.5.0 |
| 28 | A tap repository | owner creates |

## 4. Decided by the owner (2026-10-17)

| # | Decision | Answer |
|---|---|---|
| D1 | Multi-selection model | **Replay-based multi-cursor** on the Vim engine (item 20) |
| D2 | Extension story after 1.0 | **Not external-process JSON-RPC.** The recommendation was declined and no alternative was named: a bundled scripting language or no extension story are what is left. Nothing in the queue depends on it before 1.0, so it stays open until the owner picks |
| D3 | `m3` depends on `m31git` (item 12) | **Yes**, as a pinned git dependency. Measure binary size and build time as the work lands, and report them |
| D4 | Public name | **`m3`**. The binary is `m3`; README, man page and the Homebrew formula say `m3`; DESIGN's `medit` becomes `m3` in 0.15.0. Whether the `m3dit` repo is renamed is a separate ask |

D2 follow-up (extapi branch): the owner's pick is m31 modules compiled into the binary; the design is `docs/EXTENSIONS.md` and API 0.1.0 is implemented in `ext/`, off by default (it replaces item 26).
