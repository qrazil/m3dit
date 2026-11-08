# Tree-sitter in m3: the feasibility spike

Status: **findings and a proposal, nothing built, no grammar vendored.** Written 2026-11-09 at m3 0.32. The owner's decision: tree-sitter is a must before 1.0 (Helix, Zed and nvim all depend on it); structural
text objects, indent, folds and injections have to work with no language server. This replaces the earlier "declined" in ROADMAP, DAILY-DRIVER and NORTH-STAR. The questions at the end are for the
owner; grammar vendoring starts only after they are answered.

## 1. Can an m31 program use the tree-sitter C runtime? (what the m31 sources say)

Read: `m31-wt/asmffi/docs/ffi-decision.md` and `stdlib-seam.md`, the release's `NOTES.txt` and `runtime/`, and m3's own `scripts/build.sh`.

* **Linking extra C is not the obstacle.** `m31c` only emits C (`-emit-c FILE --out FILE.c`); the C compiler is invoked by the project's own script. m3's `scripts/build.sh` and `tests/test.sh` already name the runtime sources
  on the `cc` line (`rt.c`, `scheduler.c`, the reactor, the context switch). Adding `lib.c` of tree-sitter (one translation unit, `lib/src/lib.c`), a glue file and the `parser.c` / `scanner.c` of the grammars is a change to that line.
  m3 controls it; no compiler support is needed for this half.
* **Calling C from m31 is the obstacle.** The only way out of the language is `prim "c"` (decided 2026-10-21): a bodiless declaration that the compiler turns into a checked call of a runtime function `rt_k_NAME`. Its limits:
  allowed only in modules that come from the standard library's `lib/` ("library code only", refused anywhere else, including dependency modules such as `tui` or `syntax`); the callee must be named `__k_...` and lives in the
  m31 runtime; arguments are integers (at most six) and byte or integer-array spans with a declared range; the result is an integer or void; **no pointers, no structs by value, no callbacks, no strings.**
  Tree-sitter's API is pointers (`TSParser *`, `TSTree *`) and a 24-byte struct passed by value (`TSNode`), so a direct binding is impossible; a C glue that keeps the objects in tables and speaks integers and byte buffers fits the limits.
* **So there are two ways in** (section 2): ask m31 to relax `prim "c"`, or do not call C from m31 at all.

## 2. Two designs

| | A. in process: glue plus `prim "c"` | B. a helper process: `m3-ts`, talked to over pipes |
|---|---|---|
| what | a C glue (`native/ts_glue.c`) holds parsers, trees, queries and node cursors in tables; m31 calls it through `prim "c"` with integer handles and byte buffers (sources in, packed spans out) | a small C program linked with the tree-sitter runtime and the grammars; m3 starts one per editor, sends edits and queries as length-prefixed binary messages, reads spans back, exactly as it already does for language servers |
| needs from m31 | **a compiler change**: `prim "c"` outside `lib/` (see the request below), or the binding living in m31's own `lib/` | **nothing** |
| parse on the key path | a parse is a blocking C call; it must run in a spawned task (a blocking-wrapped FFI call lets other tasks run, `docs/concurrency-decision.md`), and the result is copied or shared | never: the helper parses while the editor draws; results arrive as messages, stale spans are drawn until the new ones come, shifted by the edit |
| crash isolation | a bug or a hostile file in a grammar scanner takes the editor down | the helper dies, the editor keeps working (lexical fallback), the helper is restarted |
| memory, start-up | one binary; grammars linked in, which costs binary size and link time | two binaries (the release carries both); the helper starts lazily on the first file of a language |
| cost per edit | a call | one small message (the changed range and text) and the reply: well below a frame; to be measured |
| incremental parse | `ts_tree_edit` + `ts_parser_parse` with the old tree, natively | the same, inside the helper |
| tests | oracle against nvim's tree-sitter dumps (the `syntax` library has this harness: `syntax/docs/ORACLE.md`) | the same, plus a protocol test that needs no editor |

**Proposal: B first.** It needs nothing from m31, keeps parsing off the key path by construction, and survives a bad grammar. A stays possible later behind the same m3-side interface (`MED_ts` with `parse`, `edit`,
`highlights`, `objects`, `folds`, `indent`): the editor code does not know which one it talks to. If the owner prefers A, the request to m31 is below.

**Request to m31 (only for A).** (1) Allow `prim "c"` in a project's own and dependency modules, behind an explicit opt-in in the project file (e.g. a `native` line in `deps` naming the C files and include paths, which the
build script passes to `cc`), keeping every span and range check. (2) Let the callee prefix be the project's (`m31x_...`) so that m3 can supply `ts_glue.c` itself instead of living in m31's runtime. (3) Optional: a way to return
more than an integer (today a result is one `int`; the glue writes into an `out bytes` span, which is enough). (4) A statement on whether a blocking-wrapped `prim "c"` call runs on another OS thread (parallel with the editor loop) or
only yields the green thread.

## 3. The pieces, and what each must do

| piece | notes |
|---|---|
| runtime and parse | tree-sitter `lib/` (MIT), one translation unit; a parser per buffer with its language; the source is fed as the editor's lines joined, re-sent only on open; an edit sends `(start byte, old end, new end, new text)` and the helper does `ts_tree_edit` and an incremental re-parse |
| highlights | the language's `highlights.scm`, run over the viewport only (`ts_query_cursor_set_byte_range`); the captures map onto the `syntax` library's classes through `SYN_class.from_capture` (the mapping the oracle already uses); the spans replace the lexical ones for that buffer, and **injections** (markdown fences, html script and style, `markdown_inline`) come from `injections.scm` |
| text objects | `textobjects.scm` captures (`@function.outer`, `@function.inner`, `@class.*`, `@parameter.*`, `@block.*`, `@comment.*`, `@conditional.*`, `@loop.*`, `@call.*`) feeding the registry of 0.35; keys `af if ac ic aa ia` and `]f [f` between functions |
| indent | `indents.scm` for `=` and `o` / `O` / Enter where the lexical indent is wrong; falls back to the engine's rules |
| folds | `folds.scm` for `foldmethod=syntax`-like folds, computed lazily for the visible region and cached per tree |
| incremental selection | expand and shrink along the node chain (`ts_node_parent`), the Helix `Alt-o` / `Alt-i` idea, on keys the keymap audit assigns |
| large files | a size or long-line threshold (an option, `treesitter_maxfile`, in bytes) above which the buffer keeps the lexical `syntax` highlighter and no tree is built; parse budget enforced by the helper (a timeout per parse, `ts_parser_set_timeout_micros` / the progress callback), so one pathological file cannot stall anything |
| build option | the helper is optional: `--without treesitter` builds no helper and every buffer is lexical; at run time `:set notreesitter` |
| registry order | tree-sitter, then LSP ranges (`documentSymbol`, `foldingRange`, `selectionRange`), then the lexical fallback (`syntax` library, brackets, indent rules), then user-defined objects |

Budgets go in docs/UX-PERF.md when the helper exists: key-to-frame must not move (the parse is off the key path); a re-parse after a one-character edit; the first parse of a 1 MB file; the helper's resident size.
None of these has been measured; there is nothing to measure until the prototype exists.

## 4. Grammars

The first set (the owner's list): c, cpp, rust, go, python, javascript, typescript, tsx, java, kotlin, lua, bash, json, yaml, toml, html, css, markdown, markdown_inline, sql, dockerfile, make, diff. m31 itself has no
tree-sitter grammar (the language is new); it stays on the `syntax` library unless one is written.

Revisions to start from are those of the nvim-treesitter checkout on the owner's machine (`lockfile.json`, nvim-treesitter commit `cf12346a`, 2026-03-23), and compiled sizes of the same parsers there give the order of magnitude:

| language | revision | | language | revision |
|---|---|---|---|---|
| c | `2a265d69` | | json | `46aa487b` |
| cpp | `e5cea0ec` | | yaml | `18059174` |
| rust | `e86119bd` | | toml | `64b56832` |
| go | `5e73f476` | | html | `cbb91a0f` |
| python | `710796b8` | | css | `6e327db4` |
| javascript | `6fbef405` | | markdown, markdown_inline | `41328523` |
| typescript, tsx | `75b3874e` | | sql | `b9d10958` |
| java | `a7db5227` | | dockerfile | `971acdd9` |
| kotlin | `c4ddea35` | | make | `a4b91874` |
| lua | `db16e765` | | diff | `e42b8def` |
| bash | `0c46d792` | | | |

Compiled shared objects there: cpp 3.5 MB, sql 2.1, tsx 1.5, typescript 1.4, bash 1.4, rust 1.1, c 0.6, python 0.5, java 0.4; all 40 parsers installed there come to 18 MB. A static link of the 23 above is on the order of 12 to 15 MB of
machine code and several tens of MB of generated C (`parser.c` of C++ and TypeScript are several MB each); a clean build of them is minutes, so they are compiled once into a library, not on every m3 build.

**Licences.** The tree-sitter runtime is MIT. nvim-treesitter (its queries) is Apache-2.0 (checked: its `LICENSE` is the Apache 2.0 text); Helix's queries are MPL-2.0 (from memory, **to verify**: file-level copyleft, a vendored
Helix query file stays under MPL-2.0 with its notice). The grammars are separate repositories; every one on the list is expected to be MIT, but **that has not been checked from the sources and must be before anything is vendored**
(a script that reads the `LICENSE` of each pinned revision and fails on anything but a permissive licence belongs in the vendoring step). Queries are taken from nvim-treesitter where its licence allows, with the attribution and the
change notice Apache-2.0 asks for; `injections.scm` and `textobjects.scm` follow the same rule (textobjects come from the separate `nvim-treesitter-textobjects`, to be checked as well).

**Where they live (proposal).** A separate pinned repository, `qrazil/m3-grammars`: for each grammar the generated `src/parser.c`, `scanner.c` / `scanner.cc`, the `grammar.json` licence file and the query files, at the
pinned revision, plus a manifest (`grammars.lock`: name, upstream URL, revision, licence, query provenance) and the script that checks licences and rebuilds. m3's `deps` pins one commit of it, as it does tui and syntax; CI builds the
helper (design B) or the C archive (design A) from it. A vendored directory inside m3 would put tens of MB of generated C in every clone; a separate repository keeps m3 small and lets the grammars move on their own.

## 5. Milestones

| version | content |
|---|---|
| 0.33 | LSP navigation and the installer (written, parked on a branch while the toolkit and the terminal come first) |
| 0.34 | tree-sitter core: the helper (or the glue), the protocol, parse and incremental re-parse, highlights with injections, the large-file fallback, the build option; the first grammar set; docs/UX-PERF.md budgets |
| 0.35 | tree-sitter text objects, indent, folds and incremental selection, with the text-object registry (sources: tree-sitter, LSP ranges, lexical, user-defined) |
| then | project search and replace, virtual text, miller columns, `:diffthis` |

## 6. Questions for the owner

1. **A or B?** The helper process (no m31 change, parsing off the key path, crash isolation) or the in-process glue (one binary, needs the `prim "c"` change from m31)? The proposal is B.
2. **Static or on demand?** Link the first 23 grammars into the helper (a bigger release, nothing to install), or ship the helper small and fetch compiled grammars on first use like `:LspInstall` (nvim-treesitter's way; needs a download and a place for them)? Mixed is possible: a core handful static (c, python, lua, json, markdown, bash), the rest on demand.
3. **The language list.** Is the list of 23 right? Anything to add (m31 has no grammar; a project-specific language)?
4. **The grammar repository.** A separate pinned repo `qrazil/m3-grammars` as proposed, or a vendored directory in m3?
5. **Query policy.** May the queries be taken from nvim-treesitter (Apache-2.0, with attribution) and Helix (MPL-2.0 stays on those files), or should m3 write its own where the licence is awkward?
6. **Size budget.** How much larger may a release get (the estimate for the 23 static is 12 to 15 MB of code)?
7. **Does tree-sitter replace the `syntax` library for highlighting** wherever a grammar exists (the library stays for the large-file fallback and for languages without a grammar), or only add text objects, folds and indent while the lexical highlighter keeps colouring?
8. **Platforms.** Linux x86-64, Linux aarch64 and macOS, as now; the helper adds a C compiler to what CI already has. Is anything else required?
