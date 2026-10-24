# m3: a small core and first-party plugins on a stable API

Status: design proposal, 2026-10-23, written against m3 0.15.0 (commit d24d514, branch `arch`). Documentation only:
nothing in this change touches code. It reorganises m3 the way the owner already organised his earlier editor `nox`
(a Helix fork with a Vim engine in Rust and a Lua plugin platform), under the one constraint that differs: m31
compiles ahead of time, so **there is no runtime plugin loading**. A plugin is an m31 module compiled into the
binary and chosen at build time.

How to read it. Section 0 is the whole proposal in one page. Sections 1 to 9 follow the brief: (1) what nox
decided, (2) principles, (3) feature-by-feature table, (4) API 0.2, (5) registration metadata and build switches,
(6) repo layout, (7) migration plan, (8) what the API must not do, (9) open questions with a recommendation each.
Claims about the code were checked by reading it; where I did not check something, the text says so.

Sources read. nox: `apps/nox/NOX_API.md`, `VIM_PARITY.md`, `README.md` (the stock Helix readme), `helix-lua/src/lib.rs`
and `nox_plugin.lua`, `helix-term/src/commands/vim.rs`, `helix-term/src/handlers/nox_events.rs`,
`helix-view/src/tree.rs` and `document.rs`, the 17 plugins in `apps/nox/plugins/*/init.lua`, the standalone
repos `nox-*.git` in the hoard server, `nox-config.git` (`init.lua`) and the Neomem node
`MASTER - nox editor` (id 68b6f1ed, namespace homelab). m3: `README.md`, `DESIGN.md`, `docs/ROADMAP.md`,
`docs/EXTENSIONS.md`, `docs/FINDER.md`, `docs/UX-PERF.md`, `CHANGELOG.md`, and the code in `engine/`, `ui/`,
`ext/`, `scripts/`, `tests/`, `bench/`. m31: `docs/modules-decision.md`, `module-state-decision.md`,
`stdlib-decision.md`, `reference.md` (facts quoted in section 4.1).

---

## Owner decisions

Final, 2026-10-23. The owner delegated all of section 9 to the architect, and the answer is: **every
recommendation in section 9 is accepted as written**. Where the list below differs from the text of section 9,
the recommendation in section 9 wins. Items 13, 16 and 17 were not named in the owner's message; they are
accepted on the same rule (recommendation as written).

| # | Decision |
|---|---|
| Q1 | Monorepo `plugins/` until API 1.0, then read-only mirrors `m3-<name>` |
| Q2 | The checked-in registry (`ext/MED_ext_enabled.m31`) is generated from the `default` profile, guarded by a test |
| Q3 | `:PluginEnable` and `:PluginDisable` stay a run-time switch on top of build-time selection |
| Q4 | The LSP client stays in core, behind a facade so a later `--no-lsp` is possible |
| Q5 | surround and autopairs leave the engine as the LAST step (S17) only, and only with the oracle corpora green |
| Q6 | Indent guides stay core |
| Q7 | The 0.1.0 events are renamed to the nox names, without aliases |
| Q8 | Byte columns in the API, with conversion helpers |
| Q9 | The explorer is built on the widget/Canvas API (identical output) |
| Q10 | API 1.0 is tagged with m3 1.0; until then 0.2.x is additive |
| Q11 | The crash breaker is accepted; an `on_trap` request for m31 is written up |
| Q12 | Message history in core (`:messages`); toasts are the `notify` plugin, in `full` first |
| Q13 | A source SDK tarball per release (recommendation as written) |
| Q14 | The 10 non-default themes move to the data plugin `themes` (S3) |
| Q15 | `colors` is built (S16) and stays out of `default`; colors are off by default |
| Q16 | `trouble` deferred until the docked widget exists (S13) |
| Q17 | First-party plugin versions equal the editor's |
| Q18 | Plugin options are flat and prefixed (`harpoon_max`) |

Scope of the first implementation task: S0 and S1 of section 7, then stop.

---

## 0. The proposal on one page

1. **Core** is what the Vim engine, the window and buffer model, the renderer, the LSP client, the picker
   *primitive* and the extension API need to exist. It is checked by the nvim oracle (about 40,000 cases) and must
   stay a complete modal editor without any plugin (section 2.3 defines "complete" and a test).
2. **First-party plugins** are the features the owner installs as plugins in nvim or that nox ships as plugins:
   which-key popup, statusline extras, finder sources, file tree, git gutter and commands, harpoon, move, label
   jump, bracketed pairs, TODO highlight, terminal pane, session restore, extra themes; later surround and
   autopairs. They live in `plugins/<name>/`, are built in **by default**, and compile out with one switch
   (`scripts/build.sh --no-plugins`, `--without NAME`, `--plugins LIST`).
3. A plugin talks to the editor **only through `ext/` API 0.2** (an extension of today's `MED_ext` 0.1.0). Core
   never imports a plugin. The first-party plugins dogfood the API: if a plugin needs something, the API grows
   first. This is nox decision N1 (section 1).
4. nox's plugin manager (lazy `event` / `cmd` / `keys` / `ft`, `dependencies`, `opts`) becomes **registration
   metadata** (`MED_ext.Spec`, plain m31 data) evaluated at start-up. Laziness here saves runtime initialisation
   (state files, caches, process spawns), not code loading, and says so.
5. nox's API choices carry over where they make sense: hybrid handles plus namespaced services, one options
   accessor, an event bus, split decoration calls, real floating windows outside the layout, buffer-local keymaps,
   no callbacks in a restricted context, a versioned API that never reuses a symbol. Where m31 differs, the
   difference is stated: **traps are fatal**, so the contract is "return `Result`, never trap" and error isolation
   is weaker than nox's (section 4.10).
6. Migration is a list of **behaviour-preserving steps** (section 7), cheapest first: foundation (registry
   metadata, build profiles, golden-screen baseline), then `move`, `themes`, `bracketed`, `harpoon`, decorations and
   `todo`, statusline, which-key, `git`, `finder`, `explorer`, `terminal`, `session`, last `surround` and
   `autopairs` (they are entangled with `MED_vim`). Each step moves code, changes no user-visible behaviour, keeps
   the oracle and the pty suites green and is checked with `bench/uxperf.py`.
7. Acceptance of the whole design is the **core-only build**: `scripts/build.sh --no-plugins` must pass the core gate
   defined in section 7.4 and be a daily-usable Vim with LSP.

Decisions needed from the owner are in section 9 (18 items, one line each). The three that matter most: where LSP
and guides sit (core, recommended), whether surround and autopairs leave the engine (yes, last), and whether
explorer gets a widget API or is rewritten on a buffer as nox did (widget API, to stay identical).

---

## 1. What nox decided, and why

nox = Helix 25.07.1 fork at `apps/nox` (branch `nox`): the Vim modal engine is written from scratch in Rust
(`helix-term/src/commands/vim.rs`, 1,847 lines), plugins are Lua on LuaJIT via mlua (`helix-lua`, 4,504 lines in
`lib.rs` plus a 479-line plugin manager in `nox_plugin.lua`). The decisions below come from `NOX_API.md`, its
"Design notes", the code, the plugin headers and the Neomem master (`api_model_locked_2026_07_24`,
`design_decisions`, `architecture`). The owner's mandate (Neomem): "We are doing something new, we should do it
right. Avoid ALL the pitfalls" of Neovim; greenfield, clean design wins over muscle memory, ship a stable API.

### 1.1 The locked decisions

| # | Decision | What it means | Why (as recorded) | Where |
|---|---|---|---|---|
| N1 | Small core, first-party features as plugins on the public API | M9 built the plugin manager **and** which-key, statusline, file tree (two flavours) as plugins "to dogfood the API"; 17 plugins in the repo | An API nobody uses internally rots; friction found by plugins is fixed in the API | `plugins/*/init.lua`, Neomem `design_decisions` |
| N2 | Hybrid API: stateful **handles** are objects (`buf:set_lines`, `buf.name`), stateless **services** are namespaced functions (`nox.events.on`, `nox.keymap.set`, `nox.opt`) | `.` is state, `:` is action (Textadept convention) | nvim threads `buf` ids through every call only because of its RPC boundary; in-process nox has no RPC, so no tax | `NOX_API.md` Conventions; `lib.rs:444` (`Buffer`), `:1313` (`Window`), `:1395` (`Selection`) |
| N3 | Error contract: contract violations (wrong type, closed handle, unknown option) raise `error()`; expected failures return `nil, err`; the host wraps every callback so one bad plugin callback is logged and isolated | Two classes of failure, never silently dropped input | PIL 8.3; nvim silently drops unknown keys | `NOX_API.md` Conventions; `nox_plugin.lua:170` (`finish_load` pcall) |
| N4 | **One options accessor** `nox.opt.name = v`, symmetric types, dotted names reach nested config, unknown name or wrong type errors | Applied live through the canonical `:set` path | nvim has about 11 divergent option accessors (issue 29314) | `NOX_API.md` Options; Neomem `options` |
| N5 | **Event bus replaces autocmd**: `events.on(name, fn, opts?) -> id`, `off(id)`, `emit(name, payload?)`, snake_case names, `ev = {event, buf}` | Names: `ready buffer_open buffer_close buffer_leave buffer_write_pre buffer_write_post insert_enter insert_leave mode_changed cursor_moved diagnostic_changed`; clean break, no autocmd alias | Not lite-xl style monkeypatching; handler errors isolated | `NOX_API.md` Events; `nox_events.rs` (the whole bridge, 82 lines) |
| N6 | **No fast-context trap**: callbacks always run on the main loop with a live editor | `schedule`, `defer_fn`, `system` marshal back through the job queue | nvim E5560 and issues 21052, 35071 | `NOX_API.md` Async; Neomem `M5_events_async` |
| N7 | **Decorations are distinct calls** (virtual text, sign, highlight), namespace scoped, named `{text=, hl=}` chunks, 0-indexed, one clear path | Not nvim's omnibus `set_extmark` with 30 options | Readability, one documented priority | `NOX_API.md` Decorations; `lib.rs:675-790`; `document.rs:158-169` |
| N8 | **Stable, versioned API; never reuse a symbol for a new signature**; typed option tables that error on unknown keys; deprecations announced to plugin authors; the surface is stabilised before 1.0, not during | Anti-churn guarantee; changes logged in `NOX_API.md` | A plugin ecosystem is a promise | `NOX_API.md` status and design notes |
| N9 | **The Vim engine owns the selection model.** Helix's `Selection` is demoted to a transient tool inside one command cycle; one choke point (`normalize_cursor`) with zero exceptions | Lua sees `head`, `anchor`, `text`; plugins cannot set arbitrary multi-ranges | "Vim engine front-facing, Helix selection as a tool, second" (owner) | `vim.rs:1616`; Neomem `M5_7_vim_cursor_model` |
| N10 | **Plugins dogfood the API**; friction is recorded in the plugin's own footer and turns into API work | `FRICTION` and `MISSING PRIMITIVE` notes | see N1 | `nox-ui/init.lua:1019`, `nox-indent/init.lua:279`, `nox-colors/init.lua:17` |
| N11 | **Lazy loading** by `event`, `cmd`, `keys`, `ft`; eager when no trigger. A `cmd` trigger installs a stub `:Cmd` that loads the plugin and re-dispatches; a `keys` trigger binds a stub | Cheap start-up | lazy.nvim model | `nox_plugin.lua:275` (`register_lazy`) |
| N12 | **Plugin dependencies** are loaded and configured before the dependent; load-once guard set *before* dependencies, which prevents cycles and re-entrancy | `dependencies = {...}` | | `nox_plugin.lua:249` (`load`) |
| N13 | `opts` and `config`: `config(opts)` runs on load; else `module.setup(opts)` runs only if `opts` was given; with neither, the module is merely required | Declarative configuration | | `nox_plugin.lua:170` |
| N14 | **Floats are real windows outside the tiling**: a float is a `View` node in `tree.nodes` that is in no container, so tiling never touches it; second render pass; clamp to the screen (a resize once panicked); `resize` in place keeps buffer, selection and keymaps; tier 1 non-editable, tier 2 `editable` | One window model, not a second UI system | Input routing needed no change: editing resolves the view from `tree.focus` | `helix-view/src/tree.rs:8-30,138-196`; Neomem `post_M9_floats` |
| N15 | **Buffer-local keymaps** (`opts.buffer`), checked first, single-key in Normal/Select in v1; user and Lua bindings take **precedence** over the engine, unbound keys fall through to Vim | Sidebars and float menus drive themselves | | `editor.rs:1162` (`nox_buffer_keymaps`); Neomem `keymap_first_model` |
| N16 | **Statusline is push-based**: a plugin recomputes on events and calls `statusline.set`; the renderer draws the last value; with no plugin the built-in line renders unchanged | No per-frame callback into the plugin | Frame budget | `NOX_API.md` Statusline; `editor.rs:1079` |
| N17 | Plugin acquisition: a spec names a local `dir` (dev) or a `git` repo (cloned to the data dir, async), config helper `plugin(name, repo)` prefers the local checkout; plugins are bundled in the repo **and** published as standalone `nox-*` repos | One config on a dev box and on a fresh machine | | `nox-config/init.lua:14-30`; `nox_plugin.lua:196` |
| N18 | The leader keymap is **plugin `opts`**: which-key takes a nested table of keys, names and actions; groups drill in | Keys are data owned by the plugin that shows them | | `nox-config/init.lua` (which-key block) |
| N19 | Native subsystems are wrapped **read-only first** (`diagnostic.get/count`, `treesitter.query/node_at`, `lsp.*` through `exec`); setters deferred | Reading is the 90% need | | `NOX_API.md` Native subsystem wrappers |
| N20 | **Keep the platform substrates** (Helix LSP, tree-sitter, pickers, theme engine with 172 themes); add the Vim engine and the Lua layer; do not rewrite what works | "Retained Helix theme engine" | Merge hygiene with upstream; internal crate names kept | Neomem `design_decisions` |
| N21 | Sequential API slices (each slice touches `lib.rs`), hardening per milestone, QA findings fixed by an overhaul, not bolt-on patches | | | Neomem `design_decisions` |

`VIM_PARITY.md` shows the other half of nox's discipline: the Vim engine is tracked by hand (done, partial, remaining,
and a list of features **intentionally skipped** with a reason: sentence motions, `R`, `gq`). m3 has the same
list in `DESIGN.md` and `known_divergences.txt`, and an automated oracle instead of a hand-kept table; that is the
one place m3 is ahead, and the reason core (T2) is defined by the oracle.

### 1.2 The nox plugin set (what "first-party" meant there)

| Plugin (dir, repo) | Lines | What | Built on | Depends on |
|---|---|---|---|---|
| `nox-ui` (`nox-ui`) | 1,028 | nui-style library: `line`, `split`, `tree`, `menu`, `input`, `popup`, `animate`, `devicon` | float, keymap, defer_fn | none; **dependency of 6 plugins** |
| `statusline` (`nox-statusline`) | 136 | mode, file, filetype, diagnostics, position | `statusline.set` + events | none |
| `which-key` (`nox-which-key`) | 247 | focused non-editable float per prefix, one buffer-local key per entry | float, buffer-local keymap | none |
| `mini-files` (`nox-mini-files`) | 159 | picker-based explorer (`:Files`) | `ui.select`, `fs.read_dir` | none |
| `neo-tree` (`nox-neo-tree`) | 650 | sidebar tree, `a r d` file ops | `create_buffer`, `open_in_split`, keymap | nox-ui |
| `files` (`nox-files`) | 573 | miller-columns explorer, 3 floats resized in place | floats | nox-ui |
| `nox-notify` | 339 | sliding corner notification stack, levels, `:Notify` | floats, `screen_size`, animate | nox-ui |
| `nox-git` | 927 | lazygit-style two-pane dashboard, `:Git`, stage/commit/push/pull | floats, `system`, `ui.input` | nox-ui |
| `nox-gitsigns` | 406 | `git diff -U0` to gutter signs, `]c [c` | `set_sign`, `system` | none |
| `nox-list` | 518 | generic quickfix: named lists, items with `file/line/action` | floats, preview | nox-ui |
| `nox-trouble` | 294 | diagnostics and grep sources feeding `nox-list` | `diagnostic.get`, `system` | nox-list |
| `nox-todo` | 389 | TODO highlight in comments, `:TodoList` | `set_highlight`, `system` | nox-list |
| `nox-move` | 244 | move line or selection, `<A-j/k/h/l>` | `buf:set_lines`, keymap | none |
| `nox-surround` | 304 | add/change/delete pairs, a Lua engine on the selection API | selection, `set_lines` | none |
| `nox-scroll` | 224 | smooth half/full page scrolling via `scroll_down` steps on a timer | `exec`, `defer_fn` | nox-ui (optional) |
| `nox-indent` | 294 | enables native indent guides, scope overlay | `nox.opt`, `set_highlight` | none |
| `nox-colors` | 354 | colour-literal preview | `set_highlight` | none |

All 17 exist both as directories under `plugins/` and as standalone hoard repos `nox-*.git` (checked with
`ls-tree`; the three I opened, `nox-ui`, `nox-notify`, `nox-gitsigns`, hold only `init.lua`, plus a README for
`nox-ui`). The nox config is 100 lines: a `plugin()` helper and one `nox.plugins({...})` call.

### 1.3 Friction the nox plugins recorded (the API gaps m3 must not repeat)

| Friction | Recorded in | Consequence for m3 API 0.2 |
|---|---|---|
| No insert-mode buffer-local keymaps, so an editable float cannot confirm on `<CR>` | `nox-ui:1019` | `MapSpec` has all modes and a buffer scope (4.3) |
| No inline virtual text anchored at a column, so indent guides cannot be a plugin | `nox-indent:279` | `set_inline_text(ns, Pos, chunks)` (4.4) |
| `hl` must be a theme scope; no arbitrary RGB, no way to add a scope; unknown scopes silently skipped | `nox-colors:17` | `Hl` is a scope or an RGB; `did_scope` registers scopes with fallbacks (4.4) |
| `open_in_split` ignores width; Helix even-splits | Neomem `open_threads` | docked panels use a window-local `winfixwidth` (Vim has it) (4.5) |
| No float `set_title`, no float area getter | Neomem `open_threads` | `Float.set_title`, `Float.area()` |
| `set_lines(0, -1, ...)` collapses the selection; fixed once in `nox-ui` | `neo-tree:286` | `Buf.set_lines` keeps the cursor and says how (4.2) |
| Runtime keymap changes apply on a later tick, so a lazy `keys` stub must also carry the action | `nox_plugin.lua:323` | m3's `MED_map` is synchronous; triggers are data, which-key sees lazy keys (5.1) |
| Async work enqueued on a throwaway job queue is dropped (LSP replies) | Neomem `M8` | All callbacks go through the one tick loop (4.7) |
| Dev dir names and repo names diverge (`statusline` vs `nox-statusline`, `neo-tree` vs `nox-neo-tree`) and the config needs a `plugin()` shim | `nox-config/init.lua` | One naming rule (6.2) |
| Plugins carry a "headless smoke test" getter but no committed tests | `nox-gitsigns:316`, `nox-list:479` | Every m3 plugin owns tests (6.1) |
| Networked plugin manager has an operational cost: after the hoard server change the clone URLs are marked UNCERTAIN in Neomem | Neomem `open_threads` | Not needed: m3 plugins are compiled from the tree |

### 1.4 What carries over to m3 and what cannot

| nox idea | In m3 | Because |
|---|---|---|
| Lua tables, `pcall`, closures | m31 values, `Result`, lambdas capturing objects | m31 has interfaces, lambdas, generics, no downcast, no module variables, no `recover` |
| `error()` for contract violations | `Err(text)` and a recorded problem, never a trap | A trap kills the process (EXTENSIONS section 5) |
| Runtime clone of plugins from git | **dropped**; source comes with the tree, selection is build time | No runtime loading (D2) |
| `config = function(opts)` | **dropped**; options are registered data set by `:set` in `keymap.vim` | No code in user configuration |
| Lua `require("nox-list")` between plugins | typed **service slots** owned by core, implemented by a plugin | No interface downcast in m31, so a registry cannot hold arbitrary service types |
| nox-ui as a plugin library | its parts become core API (float, `select`, `input`, tween); devicons optional later | m3 already has the picker, popups and `MED_anim` |
| Helix `Selection` as a tool | m3's engine has one cursor plus Visual anchor/kind, and multi-cursor by replay (D1) | The Vim engine owns selection by construction |

---

## 2. Principles for m3

### 2.1 Vocabulary

* **Core** (C): in every build, including `--no-plugins`.
* **First-party plugin** (P): lives in `plugins/<name>/`, built in by default, compiled out by a switch, registered
  through the extension API only.
* **Engine plugin** (E): a P whose hooks are *engine* hooks (they run inside the headless `Editor`, with no UI):
  surround, autopairs. They need hooks core does not offer yet (API slice E) and are oracle-tested.
* **Data plugin** (D): a P that only registers data (extra themes).
* **Split** (S): the feature has a mechanism in core and policy or content in a plugin.
* **New** (N): nox has it, m3 does not.

### 2.2 The test for deciding (apply in order, first match wins)

| # | Question | If yes |
|---|---|---|
| T1 | **Substrate.** Does the extension API itself, or another core feature, need it to exist (picker widget, window and float model, decoration store, statusline host, job runner, key and option tables, LSP client)? | Core |
| T2 | **Oracle.** Is it Vim or nvim built-in behaviour that the nvim oracle checks (not a plugin that nvim loads separately)? | Core |
| T3 | **Removal.** Does `m3 --no-plugins` stop being a complete modal editor without it (checklist in 2.3, gate in 7.4)? | Core |
| T4 | **Plugin.** Would the owner install it as a plugin in nvim (DESIGN section 1 audit), or is it a plugin in nox, **and** can it be written on the public API plus declared API additions? | Plugin (P, E or D) |
| T5 | **Split.** Does one module mix a mechanism (T1) with content or policy (T4)? | Split at the data boundary: core keeps the mechanism and an interface, the plugin supplies content |

Two corollaries. A feature that needs a **frame-level hook** (the renderer would have to call it each frame)
stays core, because 0.1.0 decided "no draw hook, by design" (EXTENSIONS section 7): smooth scroll (glide), indent
guides, yank flash and popup fade are renderer features with options. A feature whose **only blocker is a missing
API** is a plugin with a prerequisite step, not a core feature (todo, jump, harpoon).

### 2.3 What "complete modal editor" means (the core-only contract)

`scripts/build.sh --no-plugins` must give, with no plugin compiled in and no file but the user's own:

1. The whole Vim grammar the oracle covers: motions, operators including `gc`, text objects, counts, registers
   (including `"+` `"*` and the expression register), marks, macros, dot repeat, Visual char/line/block, folds,
   snippets and Select mode, abbreviations, digraphs, `<C-a>`, `gn`.
2. Search and regex (`/ ? n N * #`, `:s`, `:g`, the Vim regex engine), the ex subset (`:normal :sort :put :m :t`,
   `:!` filters, `:r !`), `:set` and the options table, `:map` family and `let mapleader` in the keymap file,
   `:source`, `:let`, command-line completion and history.
3. Buffers, windows and tab pages (nvim frame sizes), the mouse, soft wrap, scrolling with glide, the quickfix
   list (`:copen :cnext` ...), netrw-style directory buffers (`:Explore`, `:e dir`).
4. Files: read and write, `.editorconfig` and `.m3.toml`, undo files, outside-change reload, `autowrite`,
   `autosave`.
5. Rendering: lexical syntax highlighting (`syntax` library), themes (the four default ones), minimal statusline
   and tab line, sign column (marks, diagnostics), cursor shapes, animation.
6. The **LSP client**: start by language, document sync, diagnostics (store, signs, count), hover, definition,
   references, rename, code actions, format and `lspformat`, completion (CTRL-Space picker and the popup),
   signature help, inlay hints, semantic tokens, `:Lsp`.
7. The **picker primitive**: `MED_picker` and its view, `MED_fuzzy`, and the core sources buffers, commands (the
   palette), options, themes, keys, quickfix. No file walker, grep or git source.
8. The extension API and `:Plugins` (an empty list).

It does **not** have: leader menu rows other than the ten core rows, which-key popup, file finder and grep,
git, file tree, terminal pane, harpoon, move, jump, bracketed, TODO, session restore, extra themes, branch and
hunk counts in the statusline; and, at the end state, surround and autopairs.

### 2.4 Rules that keep it small

| Rule | Mechanism |
|---|---|
| R1 Core never imports a plugin; plugin builds put `plugins/` out of the compiler's reach for `--no-plugins` | The minimal build runs on a scratch tree without `plugins/` (5.2): an import from core is a compile error |
| R2 A plugin imports only `ext.*`, `engine.*` **value types** (`MED_buffer.Pos`, `MED_key`), the m31 stdlib minus `proc`/`os`/`term`, and its own modules | `scripts/check_plugins.sh` greps imports; part of the gate |
| R3 A plugin never reaches `App` internals or `context.editor` | Same script; `Ctx.editor` stays public for 0.1.0 compatibility but is deprecated in 0.2 |
| R4 First-party plugins have no private API; need something, add it to `ext/` first | Review rule (N1, N10) |
| R5 A migration step changes no behaviour of the default build | Golden screens, oracle, pty suites, `uxperf` bytes (7.4) |
| R6 Each plugin owns its tests and docs; core tests do not import a plugin | 6.1 |
| R7 Registration is cheap and idle events cost one list read | Budget in 5.3 |
| R8 No runtime loading and no scripting language (D2) | Section 8 |

---

## 3. Feature-by-feature classification

Legend: C core, P plugin, E engine plugin (hooks in the Editor), D data plugin, S split, N new. "nox" names the
nox counterpart. Lines are from `wc -l` at d24d514. `MED_plugin` is today's runtime on/off registry (18 names);
the last column of table 3.3 maps it.

### 3.1 `engine/` (headless, no terminal): 37 modules, about 30,700 lines

| Module (lines) | Responsibility (verified) | Class | Rationale | nox |
|---|---|---|---|---|
| MED_buffer (190), MED_text (459), MED_key (424), MED_num (33), MED_case (68), MED_charclass (52) | line array and `splice`; cluster boundaries and widths; key codes and notation; helpers; generated case and class tables | C | T1 substrate | helix-core Rope, graphemes |
| MED_editor (1,476) | `Editor` state, transactions, undo tree, cursor clamping | C | T1; T2 | `Document` + Vim state |
| MED_vim (8,532) | the whole command layer: motions, operators, insert, Visual, dot, macros | C | T2; **contains** the autopair and surround call sites (9 option-guarded sites, listed in S17) that step S17 cuts | `vim.rs` (engine as core, N9) |
| MED_parse (403), MED_motion (570), MED_textobj (1,314), MED_nrfmt (438), MED_screen (137), MED_wrapmap (258), MED_view (933), MED_digraph (177) | stateless key parser; motions; objects; `<C-a>`; `gj gk`; wrap model; window onto the buffer (scroll commands); digraphs | C | T2, oracle corpora | `vim.rs` |
| MED_search (1,185), MED_regex (1,915) | `/ ? n N * #`, `%`; the Vim regex engine | C | T2 | Helix regex (PCRE, deliberately not Vim) |
| MED_ex (4,278), MED_expr (954), MED_listing (142), MED_shell (217) | ex lines, ranges, `:s :g :normal`; `\=` evaluator; `:marks :registers :jumps :changes`; child processes for filters | C | T2. `is_ui_command` (a hard-coded list of 75 names) is the seam where ex meets the front end; step 0 turns it into registry data | `typed.rs` hooks `:s` `:g` |
| MED_register (333), MED_map (353), MED_option (265) | register file; `:map` tables; the option table (Neovim names, kinds, defaults) | C | T1: plugins add options and maps through these | `nox.opt`, keymap |
| MED_fold (340), MED_autofold (624) | manual and indent/marker folds | C | T2 | Helix has none |
| MED_snippet (1,464), MED_snipops (309) | LSP snippet grammar, sessions, Select mode hook | C | T2 (checked against `vim.snippet`); LSP completion needs it (T1) | none |
| MED_complete (426), MED_complete_data (152) | command-line completion, generated from nvim | C | T2 | none |
| MED_hl (75), MED_semtok (214) | adapter to the `syntax` library; LSP semantic-token overlay | C | T1 renderer substrate; LSP half of T3 | tree-sitter (core in nox) |
| MED_undofile (227), MED_projconf (561) | undo tree as text and back; `.editorconfig`, `.m3.toml` | C | T2 (nvim has `undofile` and EditorConfig built in) | none |
| **MED_surround (800)** | port of surround.vim: `ys ds cs`, Visual `S` | **E** | T4: a plugin in nvim and in nox. Oracle corpora 88 to 90 (2,155 cases) load the real plugin. Entangled: `MED_ex.drain` handles `\x04surround` sentinels, `Editor` carries `sur_*` fields | `nox-surround` |
| **MED_autopair (356)** | port of auto-pairs 2.0.0 decisions | **E** | T4. Corpora 91 and 92 (758 cases). Called in the insert path of `MED_vim` per key (4662-4744) | none (Helix has autopairs in core) |
| `gc` / `gcc` (inside MED_vim) | comment toggle, language aware | C | T2: nvim 0.11 has `gc` built in (corpus 62, 75 cases); stays behind `:set comment` | none |

### 3.2 `ui/` (front end): 28 modules, about 24,500 lines, plus `ext/` (840)

| Module (lines) | Responsibility (verified) | Class | Rationale | nox |
|---|---|---|---|---|
| **MED_app (9,665)** | the `App`: loop, key routing, buffers, windows, tabs, mouse, rendering, plus **everything below** (LSP glue about 1,300 lines, window and tab commands 1,080, picker glue 700, tree 515, popup 350, session 280, git 230, terminal 230, listing 190, ext hooks 290) | C, to be **cut down** | The god object. Target: loop, input routing, buffers/windows/tabs, text rendering, command line. Everything else leaves through the API or moves (table 7.2) | `Application` + `EditorView` |
| MED_window (1,362) | layout tree with nvim frame sizes, pages, neighbours | C | T1/T2 (`oracle_windows.py`) | `tree.rs` |
| MED_picker (534), MED_picker_view (325), MED_fuzzy (1,184) | picker state machine, drawing, scorer | **C (primitive)** | T1. **Coupling to cut:** `MED_picker` imports `MED_frecency` (`boost_of`, line 196); becomes a `BoostFn` supplied by the finder | helix pickers (core) |
| MED_files (129), MED_ignore (212), MED_grep (187), MED_frecency (222), MED_sources (253) | project walk, `.gitignore`, grep corpus, frecency, source command lines and parsers | **P `finder`** (S) | T5: content and policy over the picker. `project_root()` (called at 5 sites in `App`, among them the LSP result handler and the git command) moves to core | `mini-files` (picker explorer) |
| MED_tree (551) | neo-tree model: rows, git letters, file ops | **P `explorer`** | T4. Imports `MED_files` and `MED_git` (soft dependency on `git`) | `neo-tree` |
| MED_git (744), MED_gitlib (1,113), MED_gitcmd (372) | gutter diff, in-process git over m31git, `:Git` read commands | **P `git`** | T4. m31git is 17.4% of the binary and about 12 s of build (ROADMAP D3): a `--no-plugins` build drops both | `nox-gitsigns`, `nox-git` |
| MED_lsp (1,541), MED_pum (770) | JSON-RPC client over `proc` pipes; completion popup | C | T3 (owner requires the LSP client in core), T1 (diagnostics feed signs and the API) | Helix LSP (core in nox, N20) |
| MED_keymap (417) | the keymap table as data: leader tree, prefix help, palette rows, `docs/KEYMAP.md` generator | **S** | Core keeps the table for its own keys (10 core rows plus `g z [ ] <C-w>` prefix help); plugin rows move into plugins and register as `MapSpec` | `which-key` opts |
| MED_theme (975), MED_sample (121) | theme engine (Helix TOML), `--dump-sample` | C | T1 renderer | Helix theme engine kept (N20) |
| MED_theme_data (2,130) | 14 built-in themes embedded as m31 string lists (generated) | **S / D** | Core keeps `default`, `default-light`, `term16-dark`, `term16-light`; the other 10 become data plugin `themes` | Helix `runtime/themes` |
| MED_anim (407), MED_glide (476) | pure animation scheduler; scroll glide, yank flash, popup fade | C | Corollary of 2.2 (frame-level) | `nox-scroll` (a plugin there because Helix had none) |
| MED_vt (225) + terminal code in App (about 230) | VT screen model; `:terminal` pane over `proc.start_pty` | **P `terminal`** | T4 (floaterm in nvim). Needs pty and raw-key capture in the API | none |
| MED_session (220), MED_state (111), MED_persist (78) | session files, recent files and last cursor positions, undo-file paths | **S** | `MED_persist` (undo paths) and the state directory stay core; `:Session` and the restore of layout, `MED_session`, `remember_position` become `session` | none |
| MED_clip (139) | `"+` `"*` through pbcopy, wl-clipboard, xclip | C | T2 | clipboard |
| MED_plugin (53) | runtime registry of 18 names | replaced | by `MED_ext` registry metadata; `:Plugins`, `:PluginEnable`, `:PluginDisable` keep their behaviour | `:NoxPlugins` |
| `ext/` MED_ext (788), MED_ext_enabled (10), MEDX_trim_whitespace (42) | extension API 0.1.0, generated registry, sample | C | T1 | `helix-lua` |

### 3.3 User-visible features, one row each

Today's switch name is `MED_plugin` (`:PluginDisable NAME`); "core switch" means the feature stays core and keeps
its option.

| Feature (today) | Where it lives today | Class | New home | nox counterpart | Notes |
|---|---|---|---|---|---|
| Statusline: mode, file, `[+]`, position | `App.draw_status` | C | core minimal line | built-in line | stays so `--no-plugins` has a status line |
| Statusline extras: branch, hunk counts, E/W counts, filetype, LSP status | `draw_status` gated by `is_plugin_on("statusline")` | P | `statusline` | `statusline` | reads diagnostics and git through services; segments with priorities |
| Bufferline (two or more buffers) | `draw_tabline`, `statusline` switch | P | `statusline` | none | tab-page line stays core |
| Tab line (tab pages) | `draw_tabline`, `MED_window` pages | C | core | none | |
| Which-key popup | `App.prefix_typed`, `prefix_table`, `TUI_menu.WhichKey`, switch `whichkey` | S | popup in `whichkey`; pending-key state and the descriptions table stay core | `which-key` | `:Keys` and `<Space>?` browser remain core (palette-like picker over the table) |
| Leader tree (`<Space>` groups) | `MED_keymap.defaults()` | S | 10 core rows stay; the rest registered by the plugin that owns them | which-key `opts` | fixes 0.1.0 caveat: a user `<Space>` map hides the whole menu |
| Command palette, `:Commands`, `<Space>fc` | `MED_picker` over `MED_keymap` rows | C | core source `commands` | none | |
| File finder `<Space>ff`, grep, recent, lines, quickfix, options, marks, symbols, word, TODOs | `MED_picker`, `MED_files`, `MED_grep`, `MED_frecency`, `MED_sources`, `App.load_*` | S | `finder` owns files/grep/recent/lines/symbols/word; `buffers`, `commands`, `options`, `marks`, `keys`, `quickfix`, `themes` sources are core | `mini-files`, nvim fzf-lua | FINDER.md ranking moves with it unchanged |
| Directory buffer `:Explore`, `:e dir`, `R D % d gh` | `MED_files.list_directory`, `App.*listing*`, `MED_listing` | C | core | netrw | nvim ships netrw (T2) |
| File tree sidebar `:Neotree`, `<Space>e` | `MED_tree`, `App.tree_*` (515 lines), mouse | P | `explorer` (needs docked widget, API slice D) | `neo-tree` | miller columns (`nox files`) not built (N) |
| Picker explorer `<Space>fe` | picker source | P | `finder` | `mini-files` | |
| Git gutter `+ ~ _`, `]c [c`, `ih ah`, `:Hunk` | `MED_git`, `App.draw_sign`, `run_hunk_command` | P | `git` | `nox-gitsigns` | sign priority: marks above diagnostics above git (today's order) |
| Git blame, `:Git log/show/diff/blame`, branches/commits/changed pickers | `MED_gitcmd`, `MED_gitlib` | P | `git` | `nox-git` | nox-git's lazygit dashboard (stage, commit, push) is deliberately not built: DESIGN says never, `mgit`/`gitui` do it |
| Surround | `MED_surround` + `MED_vim` + `MED_ex.drain` | E | `surround` (last) | `nox-surround` | Plugin alias `<Space>sa sd sr` rows move with it |
| Autopairs | `MED_autopair` + `MED_vim` insert path | E | `autopairs` (last) | none | |
| Comment `gc` | `MED_vim` | C | core, `:set comment` | none | T2 |
| Smooth scroll, glide, yank flash, popup fade, scrollbar | `MED_anim`, `MED_glide` | C | core renderer, `:set animate*` | `nox-scroll` | renderer feature (2.2); a `Tween` helper is exposed to plugins |
| Snippets (`<Tab>`, `snippets.json`) | `MED_snippet`, `MED_snipops`, `App.load_snippets` | C | core | none | |
| LSP client | `MED_lsp`, `App.lsp_*`, `server_*` (about 1,300 lines in App) | C | core (T3); later extraction candidate behind a facade | Helix LSP | the acceptance in the brief requires it in core |
| Completion popup (`lspcomplete`) | `MED_pum`, `App.pum_*` | C | core | Helix completion | |
| Semantic tokens | `MED_semtok` | C | core | tree-sitter | |
| Format on save (`lspformat`) | `App.lsp_format_before_write` | C | core option | none | must run inside the write path, before `BufferWritePre` handlers |
| Diagnostics: signs, `]d [d`, `<Space>ll`, picker | `App.diagnostic_*`, `draw_sign` | S | signs and store core; `]d [d` rows in `bracketed`; picker source in `finder` | `nox-trouble` | |
| Bracketed pairs `[b ]b [q ]q [d ]d [h ]h [t ]t` | `App.did_bracketed` | P | `bracketed` | none | soft dependencies on `git`, `todo`, diagnostics |
| Harpoon `<Space>ha he hn hp hd 1..9` | `App.harpoon_*`, `MED_state` | P | `harpoon` | none | per-project state file |
| Move line/selection `<A-j/k/h/l>` | `App.did_alt_move` | P | `move` | `nox-move` | needs no new API (section 7, step 2) |
| Label jump `<Space>j` | `App.handle_jump_key` | P | `jump` | none | needs key capture and an overlay |
| Indent guides | `App.draw_line` (4736), `:set noindentguides` | C | core renderer option | `nox-indent` | per cell, on blank lines; nox itself kept native guides in core and only toggled them (`nox-indent:3-17`). Optional later plugin `indentscope` for the scope overlay (N) |
| TODO highlight, `]t`, `<Space>ft` | `App.draw_line` (4746), `MED_sources` | P | `todo` | `nox-todo` | needs decorations (slice B) |
| Terminal pane `:terminal`, `<Space>t` | `MED_vt`, `App.start_terminal`, `Term` | P | `terminal` | none | needs pty, raw input, a buffer kind |
| Session: `:Session`, buffers, layout, cursors, last position | `MED_session`, `App.apply_session_*`, `remember_position` | P | `session` | none | needs a layout read/write API |
| Undo files, project settings, auto-reload, autowrite | `MED_persist`, `MED_projconf`, `App.check_disk` | C | core | none | T2 |
| Themes, `:theme`, picker with live preview | `MED_theme`, `MED_theme_data` | S | engine core; 10 themes in data plugin `themes` | Helix themes | |
| Quickfix list `:copen :cnext`, `<C-q>` from pickers | `App.send_to_quickfix`, `go_quickfix` | C | core | `nox-list` | the generic named-list idea becomes `Ctx.set_list(name, items)` on the same store |
| Messages | command-line message, `:messages` is accepted and ignored (`MED_ex` line 1683) | C | add a message ring and `:messages` to core (a Vim command) | `nox-notify` | the toast stack is the plugin |
| Mouse, clipboard, cursor shape, focus reporting | `App.handle_mouse`, `MED_clip` | C | core | | |

### 3.4 What nox's plugin set has that m3 lacks

| nox plugin | m3 today | Plan |
|---|---|---|
| `nox-notify` (toast stack, levels, message history) | one message line; `:messages` is a no-op | **N**: message ring in core (`:messages`), `Message` event; `notify` plugin draws toasts (needs Float, Tween). Step 11 |
| `nox-trouble` (diagnostics, grep, todo in one panel) | diagnostics picker `<Space>xx fx`, quickfix picker | **N**, deferred: a persistent panel needs the docked widget (slice D). Until then `finder` covers it |
| `nox-list` (generic named lists, items with actions, preview) | quickfix (core), pickers with preview | Covered. Add `Ctx.set_list(name, items)` so plugins can fill the quickfix store |
| `nox-todo` (highlight + `:TodoList`) | both exist, hard-wired in `draw_line` and `MED_sources` | Migration, not new (step 6) |
| `nox-move` | exists (`did_alt_move`) | Migration (step 2) |
| `nox-indent` (guides, scope overlay) | guides yes, scope overlay no | Guides stay core; `indentscope` optional later |
| `nox-colors` (colour-literal preview) | none | **N**: new plugin `colors`, possible because `Hl` carries RGB (fixes the nox finding); not in the default profile |
| `nox-scroll` | glide, richer | none |
| `nox-ui` (components, devicons, animate) | components exist in core; no devicons ("never by default") | Parts become API; optional `icons` plugin, off by default |
| `files` (miller columns), `mini-files` | picker explorer, tree, netrw | miller columns not planned |
| `nox-git` dashboard (stage, commit, push) | none, by decision | not planned |
| `which-key`, `statusline`, `neo-tree`, `nox-gitsigns`, `nox-surround` | exist, core today | Migration steps |

---

## 4. Extension API 0.2

### 4.1 Constraints from m31 that shape the API

Verified in the m31 docs (`modules-decision.md`, `module-state-decision.md`, `stdlib-decision.md`,
`reference.md` 3.4) and in `ext/MED_ext.m31`:

* Import cycles are forbidden. Layering is a DAG: `engine/` <- `ext/` <- `plugins/`, and `ui/` imports `ext/`.
  Hooks that the engine must call (slice E) therefore live in a module under `engine/` that `ext/` fills in.
* There are **no mutable module variables**. State lives in objects a program holds; a plugin keeps state in
  objects its lambdas capture.
* Interfaces are structural (a value with matching methods satisfies one) and there is **no downcast**. A registry
  cannot hold arbitrary service types; core therefore defines typed service interfaces (4.8).
* Lambdas capture; `Result<T, str>` and `Option<T>` exist; `const` data is limited to literals and collections, so
  a `Spec` is built by a function, not declared `const`.
* **A trap is fatal.** There is no `recover` (EXTENSIONS section 5). The API must never trap on caller input.
* Naming lint: a function that answers yes or no starts `is_`, `has_`, `can_` or `did_`; names are `snake_case` of
  three letters or more; module names take an upper-case prefix (`MEDX_` for in-repo plugins).

Signatures below are the intended API in m31 syntax, written for review. They are not code that builds today.

### 4.2 What exists in 0.1.0, and what 0.2 adds

| Capability | nox | MED_ext 0.1.0 (verified in `ext/MED_ext.m31`) | 0.2 |
|---|---|---|---|
| Identify, version check | `nox.plugins` spec | `did_declare(name, summary, major, minor)`, exact match while 0.x | `Spec` (5.1); check: major and minor equal, plugin patch <= host patch |
| Events | 11 events, `on/off/emit` | 10 events: `Startup Shutdown BufOpen BufWritePre BufWritePost BufClose ModeChanged CursorMoved TextChanged Tick`; `did_hook`, no `off`, no `emit` | nox names, 9 more events, ids, `once`, `emit` (4.3) |
| Ex commands | `command.add(name, fn)` with `args/fargs` | `did_command(name, summary, CommandFn)`; capital first letter; first come first kept | `CommandSpec` with bang, range, completion, `fargs` |
| Key maps | `keymap.set(mode, lhs, rhs, {buffer})`, `del` | `did_map(mode, keys, command, summary)` modes `n`, `x` only; installed as `:nnoremap` before the user file | all modes, `Cmd` or function action, buffer-local, `did_unmap`, groups (4.3) |
| Options | `nox.opt`, unknown errors | read-only: `option(name)`, `is_option_on(name)`; no plugin options | option registry (4.3) |
| Buffer read | handle methods | `line_count line(row) text() cursor() mode() file directory()` on `Ctx` | `Buf` handles (4.2.1) |
| Buffer write | `set_lines`, `insert`, `write` | `did_replace`, `did_set_line`, `set_cursor`; one undo step per handler | same plus `Buf` methods, `write` |
| Registers | via exec | `register(name)`, `did_set_register` | unchanged |
| Windows, selection | `Window`, `Selection` | none | `Win`, `Sel` (4.2.2) |
| Decorations | virt text, sign, highlight, namespaces | none; `set_segment` only | namespaces, 4 calls, viewport event (4.4) |
| Floats | `open_in_float`, handle | none; `pick` opens the finder | `Float` (4.5) |
| `select`, `input` | `nox.ui.*` | `pick(title, entries)` only | `Ctx.select`, `Ctx.input` (4.5) |
| Statusline | `statusline.set` regions | `set_segment(name, text)`, plain text, order of first set | slots, priorities, chunks with `Hl` (4.6) |
| Notifications | `nox.notify` | `say(text)` | levels, message ring, `Message` event (4.6) |
| Async | `schedule`, `defer_fn`, `system` | `run` (blocks, 1000 ms cap), `background` + `did_job`, no exit code, 250 ms tick | `schedule`, `defer`, `system` with exit code and cwd (4.7) |
| Read access to LSP, diagnostics, syntax | `diagnostic.get/count`, `treesitter.*` | none | `diagnostics()`, `lsp_state()`, `syntax_at()` (4.9) |
| Services between plugins | Lua `require` | none | typed service slots (4.8) |
| Utilities | `nox.util/path/fs` | `directory()`, `file` | `cwd`, `project_root`, `state_dir`, `config_dir`; m31 stdlib `fs`, `path` directly |
| Stability, errors | contract above | `Result<bool,str>`, three failures switch an extension off; no `off`/`once`; major/minor exact | section 4.10 |

Not in 0.1.0 and still not planned: runtime loading, a scripting layer, `BufEnter`-style autocmd patterns (the
event list replaces them), and anything that lets a plugin draw on a frame callback.

#### 4.2.1 Buffer handles

A handle holds an id and a reference to the host; every call resolves it live. A closed buffer is an `Err`, never
a trap (N2, N3 adapted).

```m31
pub type Buf {
    pub int id;                       // stable for the session, never reused (the `:ls` number)
    // private: the host reference
}
pub Option<Buf> Ctx.buf(int id)       // None when closed
pub Buf Ctx.current_buf()

pub bool Buf.is_valid()
pub int Buf.line_count()
pub str Buf.name()                    // path, or "" for an unnamed buffer
pub str Buf.filetype()                // the syntax library's language, "" when unknown
pub bool Buf.is_modified()
pub bool Buf.is_scratch()
pub Result<List<str>, str> Buf.get_lines(int from, int stop)    // rows [from, stop), stop < 0 means to the end
pub Result<bool, str> Buf.set_lines(int from, int stop, List<str> lines)  // one undo step per handler
pub Result<bool, str> Buf.insert(MED_buffer.Pos at, str text)
pub Result<bool, str> Buf.write()
pub Result<Buf, str> Ctx.create_buffer(BufOpts opts)   // scratch: name, modifiable, filetype
pub Result<bool, str> Buf.set_modifiable(bool flag)
```

Positions are `MED_buffer.Pos(row, col)`: **0-indexed row, byte column on a grapheme boundary**, the type the
engine and the oracle already use. nox uses 0-indexed character columns; byte columns are kept because every
oracle comparison and every LSP conversion in m3 already works in bytes. `Buf.col_to_display` and
`display_to_col` convert. `set_lines` keeps the cursor of every window on the buffer clamped and, unlike nox's
first version, never collapses a Visual selection of another window (nox needed a fix for this, N10).

Edits go through `editor.change`, as 0.1.0 does, so marks, the change list, the `U` line and the highlighter's
dirty row stay right, and everything one handler did is **one undo step**. An edit is refused with `Err` while an
undo block belongs to a command or insert session (the 0.1.0 rule, unchanged).

#### 4.2.2 Windows and the selection

```m31
pub Win Ctx.current_win()
pub Option<Win> Ctx.win(int id)
pub List<Win> Ctx.wins()                           // tiled windows of the current page, then floats by z
pub Buf Win.buf()
pub MED_buffer.Pos Win.cursor()
pub Result<bool, str> Win.set_cursor(MED_buffer.Pos at)   // clamped off the line end like a motion
pub bool Win.is_float()
pub TUI_geometry.Rect Win.area()                   // includes borders for floats
pub Result<bool, str> Win.set_option(str name, str value)  // window-local: winfixwidth, number, wrap...
pub Option<Sel> Win.selection()                    // None unless Visual
pub List<Sel> Win.selections()                     // one element today; the list shape is for multi-cursor (D1)

pub enum SelKind { Char; Line; Block; }
pub type Sel {
    pub MED_buffer.Pos anchor;
    pub MED_buffer.Pos head;
    pub SelKind kind;
}
pub str Sel.text()
pub Result<bool, str> Win.select(MED_buffer.Pos anchor, MED_buffer.Pos head, SelKind kind)
pub MED_buffer.Pos Ctx.screen_size()   // (rows, columns) of the whole editor area, unaffected by splits (nox.screen_size)
```

**The engine owns the selection model** (N9). A plugin can read it and ask the engine to enter Visual mode over a
range (`Win.select` goes through the same entry as `v`, `V`, `<C-v>`), but cannot build arbitrary range sets;
multi-cursor (D1, replay) will appear as more elements of `selections()`.

### 4.3 Events, keymaps, commands, options

**Events.** The bus replaces the 0.1.0 `Event` enum values and keeps the one-thread, registration-order,
coalescing and no-re-entrancy rules of EXTENSIONS section 2. Names are nox's (N5); the enum is PascalCase for
m31, the string is the stable name used in specs, `:Plugins` and `emit`.

| Enum (string) | nox | 0.1.0 | Info fields | Note |
|---|---|---|---|---|
| `Ready` ("ready") | `ready` | `Startup` | | after the keymap file; eager plugins activate here |
| `Shutdown` ("shutdown") | none | `Shutdown` | | normal exit only |
| `BufferOpen` ("buffer_open") | yes | `BufOpen` | buf | each command-line file, every later buffer |
| `BufferClose` ("buffer_close") | yes | `BufClose` | buf | before `:bdelete` |
| `BufferEnter` ("buffer_enter") | none | none | buf | new: active buffer changed |
| `BufferLeave` ("buffer_leave") | yes (focus lost) | none | buf | new |
| `BufferWritePre` ("buffer_write_pre") | yes | `BufWritePre` | buf | text may change; wraps `:w :wall` autowrite autosave; runs after LSP format |
| `BufferWritePost` ("buffer_write_post") | yes | `BufWritePost` | buf | only after a write without error |
| `InsertEnter`, `InsertLeave` | yes | via `ModeChanged` | buf | new |
| `ModeChanged` ("mode_changed") | yes | yes | mode_before, mode_after | |
| `CursorMoved` ("cursor_moved") | yes | yes | buf, pos | coalesced per frame (nox does the same, `nox_events.rs:18`) |
| `TextChanged` ("text_changed") | none | yes | buf, first_row | |
| `DiagnosticChanged` ("diagnostic_changed") | yes | none | buf | new |
| `FiletypeSet` ("filetype_set") | emulated by `buffer_open` + check | none | buf | makes the `ft` trigger exact |
| `ViewportChanged` ("viewport_changed") | none | none | buf, first_row, last_row, version | **new, the decoration driver**: fires at most once per frame when the visible rows or the text version changed; handlers set decorations for those rows; the renderer reads stored data (no draw hook) |
| `YankPost` ("yank_post") | none | none | buf, register, range | the flash is core; plugins may react |
| `OptionSet` ("option_set") | none | none | name, value | |
| `PendingKeys` ("pending_keys") | none | none | pending text | which-key; fires 400 ms after a prefix (the `WHICH_KEY_MS` rule moves into the event) |
| `Message` ("message") | none | none | level, text | the toast plugin; every `say`/`notify` |
| `DirChanged`, `FocusGained`, `FocusLost`, `Resize` | none | none | | optional |
| `Tick` ("tick") | none | yes, 250 ms | elapsed_ms | unchanged |
| custom | `events.emit(name, payload)` | none | payload `Map<str,str>` | `Registry.emit(name, Map<str,str>)`; `did_hook_named(name, Hook)` |

```m31
pub Result<int, str> Registry.hook_with(Event event, Hook hook, HookOpts opts)   // opts.once, opts.priority; returns an id
pub bool Registry.did_hook(Event event, Hook hook)       // 0.1.0 form, kept as sugar
pub bool Registry.did_unhook(int id)
```

**Keymaps.** Maps are *data in the spec* so which-key can show them before a lazy plugin activates (nox's `keys`
stub could not). They land in the engine's own `MED_map` tables, synchronously. User maps still win over plugin
maps and plugin maps over defaults (the 0.1.0 rule). Two engine prerequisites are Vim features with oracle corpora,
not plugin features: `<Cmd>` mappings (EXTENSIONS open question 3) and `<buffer>` maps (today E474 in
`DESIGN.md` 2.3).

```m31
pub enum MapMode { Normal; Visual; Insert; OperatorPending; Command; }   // n x i o c
pub enum Action { Command(str); Call(KeyFn); }       // ":Name args" or a function
pub interface KeyFn { Result<bool, str> run(Ctx context); }
pub type MapSpec {
    pub MapMode mode;
    pub str keys;                       // Vim notation: "<Space>gs", "<M-j>"
    pub Action action;
    pub str desc;                       // the which-key and `:Keys` label
    pub str group = "";                 // "git": a prefix group label registered once
    pub int buffer = 0;                 // 0 = global; else a Buf.id (buffer-local, shadows global)
    pub bool is_silent = true;
}
pub bool Registry.did_map(MapSpec spec)
pub bool Registry.did_unmap(MapMode mode, str keys, int buffer)
pub bool Registry.did_group(str prefix, str label)   // "<Space>g" = "git"
```

**Commands.**

```m31
pub type CommandSpec {
    pub str name;                       // capital first letter, letters and digits
    pub str summary;
    pub bool is_bang = false;
    pub bool is_range = false;
    pub int args_min = 0;  pub int args_max = -1;   // -1 = any
    pub CompleteFn complete;            // optional; None-like empty implementation by default
}
pub type CommandCall { pub str args; pub List<str> fargs; pub bool is_bang; pub int line1; pub int line2; pub int count; }
pub interface CommandFn2 { Result<bool, str> run(Ctx context, CommandCall call); }
```

`MED_ex.is_ui_command` (a hard-coded list of 75 names, `MED_ex.m31:1055`) becomes the registry's command table;
built-in names win, as now (`MED_ex.is_builtin_command`).

**Options registry** (N4). A plugin registers options; they join `:set`, `:set name?`, completion, `.m3.toml`
`[options]`, EditorConfig where mapped, and the generated config reference (ROADMAP item 31).

```m31
pub enum OptionKind { Bool; Int; Str; }
pub enum OptionScope { Global; Buffer; Window; }
pub type OptionSpec { pub str name; pub OptionKind kind; pub str default; pub OptionScope scope; pub str summary; }
pub bool Registry.did_option(OptionSpec spec)      // name rule: <plugin>_<what> in lower case, e.g. harpoon_max
pub str Ctx.option(str name)                       // exists in 0.1.0; now also reads plugin options
```

Reads return the registered kind (a Bool option is `true` or `false` text through `is_option_on`). An unknown name
in `:set` is E518 as in Vim (nox: unknown option errors, N4); the engine side needs `Editor.plugin_options`, an
`Option` table next to the const `SPECS`.

### 4.4 Namespaces and decorations (N7)

Distinct calls, namespace scoped, one clear path. A namespace is an int handle from `namespace`, taken at
registration (no per-call string lookup).

```m31
pub type Ns { pub int id; }
pub Result<Ns, str> Registry.namespace(str name)

pub enum HlKind { Scope; Rgb; }
pub type Hl { pub HlKind kind; pub str scope = ""; pub int fg = -1; pub int bg = -1; pub int attrs = 0; }
pub Hl scope(str name)                              // a theme scope, with fallbacks
pub Hl rgb(int fg, int bg, int attrs)               // closes the nox-colors gap
pub bool Registry.did_scope(str name, str fallback, Hl default_style)   // register a scope plugins draw with
pub type Chunk { pub str text; pub Hl hl; }

pub enum VtPos { EndOfLine; RightAlign; Inline; }
pub type Sign { pub str text; pub Hl hl; pub int priority = 10; }   // one cell wide
pub type Range { pub MED_buffer.Pos start; pub MED_buffer.Pos stop; }  // end exclusive, like nox

pub Result<bool, str> Buf.set_virtual_text(Ns ns, int row, List<Chunk> chunks, VtPos where)
pub Result<bool, str> Buf.set_inline_text(Ns ns, MED_buffer.Pos at, List<Chunk> chunks)  // column anchored (nox-indent gap)
pub Result<bool, str> Buf.set_sign(Ns ns, int row, Sign sign)             // one sign per (ns, row); replaces
pub Result<bool, str> Buf.set_highlight(Ns ns, Range range, Hl hl, int priority)
pub Result<bool, str> Buf.clear_namespace(Ns ns, int from_row, int to_row)   // all kinds for the ns; to_row < 0 = end
```

* The sign column is one cell wide today. Resolution per row: highest `priority` wins. The existing order
  (marks, then diagnostics, then git; `App.draw_sign`) becomes priorities 40, 30, 10, so the `git` migration is
  invisible.
* Decorations are stored per buffer and namespace, anchored to text (they move with edits like marks) and read by
  the renderer. **There is no draw callback.** A plugin whose decorations depend on the viewport (todo, colors,
  guides-like overlays) listens to `ViewportChanged` and writes only the visible rows; core clears a namespace
  region before the handler runs if the plugin asks (`HookOpts.clears_viewport`).
* Priority and layering are documented once: syntax class, then semantic token, then plugin highlights by
  ascending priority, then search, then Visual (nox: "overlays after syntax and diagnostics, before focused").
* Core features that are decorations today (marks letters, diagnostic signs, git signs, inlay hints) keep working
  as they are; moving them to namespaces is optional and must stay byte-identical.

### 4.5 Windows outside the layout, `select`, `input`

**Floats are real windows outside the tiling** (N14), not a second UI system. A float is a `Win` with
`is_float() == true` in a z-ordered list that `MED_window`'s layout never walks; navigation and `<C-w>` commands
skip it; the renderer draws a second pass; the editing pipeline targets the focused window, so a focused float
needs no special input routing; `close` restores the previous focus; area is clamped to the screen on every resize
(nox once panicked here).

```m31
pub type FloatOpts {
    pub int row; pub int col; pub int width; pub int height;    // outer area, 0-indexed
    pub bool has_border = true; pub str title = "";
    pub bool is_enter = true;       // focus it; false for toasts and previews
    pub bool is_editable = false;   // tier 1: not editable; tier 2: insert mode allowed
    pub int z = 50;
}
pub Result<Float, str> Ctx.open_float(Option<Buf> buf, FloatOpts opts)   // None makes a scratch buffer
pub type Float { pub Buf buf; pub Win win; }
pub bool Float.is_valid()
pub bool Float.did_focus()
pub void Float.close()
pub Result<bool, str> Float.resize(FloatOpts opts)       // in place: buffer, selection, maps survive
pub Result<bool, str> Float.set_title(str title)
```

Docked panels (a sidebar) are an ordinary split with a window-local `winfixwidth` and a width, so the window
oracle and equalising keep working: `Ctx.open_split(buf, SplitOpts{side, width})` and `Win.set_option("winfixwidth",
"1")`. A panel whose content is not text (the file tree today) needs the **widget** form in slice D: a window whose
content is an object implementing

```m31
pub interface Widget {
    void draw(Canvas canvas);                          // Canvas: size(), put(x, y, text, Hl), fill(rect, Hl), theme(scope)
    Result<bool, str> on_key(Ctx context, int key);
    Result<bool, str> on_mouse(Ctx context, MouseEvent event);
}
```

`Canvas` is a thin facade over `TUI_buffer`, so plugins do not import `tui`. Whether to build the widget form or
rewrite the explorer on a buffer as nox's neo-tree did is open question 9.

**`select` and `input`** (nox `ui.select`, `ui.input`): callback style, cancel is distinguishable.

```m31
pub type SelectItem { pub str text; pub str detail = ""; pub str path = ""; pub int row = -1; }
pub interface SelectFn { Result<bool, str> run(Ctx context, Option<int> index); }   // None = cancelled
pub Result<bool, str> Ctx.select(List<SelectItem> items, SelectOpts opts, SelectFn done)
pub interface InputFn { Result<bool, str> run(Ctx context, Option<str> text); }      // None = cancelled
pub Result<bool, str> Ctx.input(InputOpts opts, InputFn done)                       // prompt, default
```

Both ride on the core picker and command-line prompt, so they are modal in 0.2 (as nox's were until insert-mode
buffer-local keymaps and editable floats landed). The existing `Ctx.pick(title, entries)` stays and is the
file-location form; **streaming pickers** (the finder sources) use

```m31
pub interface PickSource { Result<List<MED_picker.Entry>, str> next(Ctx context, str query, int budget); bool is_done(); }
pub type PickSpec { pub str title; pub PickSource source; pub PreviewFn preview; pub List<PickAction> actions; pub BoostFn boost; }
pub Result<bool, str> Ctx.pick_stream(PickSpec spec)
```

with `PickAction` for the keys `<C-q>` (to quickfix), `<C-t>`, `<C-s>`, `<C-v>` and `BoostFn` for frecency, which
removes the `MED_picker` to `MED_frecency` import.

### 4.6 Statusline, bars, notifications

Push-based like nox (N16): the plugin computes on events and stores; the renderer draws stored text.

```m31
pub enum Slot { Left; Center; Right; }
pub type SegmentSpec { pub str name; pub Slot slot; pub int priority; }       // lower priority is dropped first
pub bool Registry.did_segment(SegmentSpec spec)
pub void Ctx.set_segment(str name, List<Chunk> chunks)                       // empty list removes; 0.1.0 text form stays
```

Core draws mode, file, `[+]` and the ruler. Segments of equal slot are ordered by priority and dropped, lowest
first, when the line is too narrow (the rule `draw_status` follows today, which the `statusline` migration must
reproduce exactly). `Ctx.set_bar(Bar bar, List<Chunk> chunks)` serves the top row when there is a single tab page
(bufferline); core keeps the tab page line when there are two or more pages.

```m31
pub enum Level { Debug; Info; Warn; Error; }
pub void Ctx.notify(Level level, str text)        // message ring (:messages) + Message event + the command line
```

`say(text)` stays and equals `notify(Info, ...)`. A toast plugin subscribes to `Message`.

### 4.7 Async, jobs, timing

Callbacks always run on the main loop with a live editor: m31 is single threaded for the editor and handlers run on
the tick, so nox's "no fast context" holds by construction (N6). 0.1.0 already has `background` and `did_job`.

```m31
pub void Ctx.schedule(FnJob job)                           // next loop turn
pub void Ctx.defer(int ms, FnJob job)                      // at the first tick at or after ms; granularity = TICK (16 to 250 ms)
pub interface FnJob { Result<bool, str> run(Ctx context); }
pub type SystemOpts { pub str cwd = ""; pub int timeout_ms = 0; pub bool is_merged = false; }
pub interface SystemFn { Result<bool, str> run(Ctx context, SystemResult result); }   // code, stdout lines, stderr lines
pub Result<bool, str> Ctx.system(List<str> argv, SystemOpts opts, SystemFn done)
```

* `Ctx.run` (blocking, capped at 1,000 ms) stays for the rare synchronous need and is deprecated for new
  plugins; `system` replaces `background` for new code. **Gap G9 (m31):** `proc` Streams do not expose the exit
  status (EXTENSIONS section 13), so `SystemResult.code` needs an m31 change; until then `code` is -1 for
  `background`-based jobs and 0.2's `system` ships only when the runtime provides it. Recorded, not worked around.
* Time: `Tick` is 250 ms idle and 16 to 50 ms while something moves; `defer` is a tick-resolution timer, which is
  enough for toasts and debounces (the 120 ms grep debounce already works this way). Per-handler time is measured
  (4.10).

### 4.8 Services between plugins

Core defines **typed slots** (the m31 reason in 4.1), a plugin implements one and others read it:

```m31
pub interface GitService {
    Option<str> branch(str directory);
    Option<GitStatus> status(str directory);                 // per file letters, for the tree and the statusline
    Option<List<Hunk>> hunks(Buf buf);
    ...
}
pub bool Registry.did_provide_git(GitService service)
pub Option<GitService> Ctx.git()
```

Slots planned: `git` (branch, status, hunks, blame), `todo` (items, for `bracketed`), `finder` (open a source by name,
for `trouble`-like plugins). A consumer declares `wants = ["git"]` and shows nothing when the service is absent.
For third parties a string protocol exists as an escape hatch: `Registry.did_provide_named(name, NamedService)` with
`Result<str, str> call(str method, str args)`. A new core slot needs an API minor, which is the point: a service
shape is a public contract.

### 4.9 Read access to LSP, diagnostics and syntax (nox `diagnostic`, `lsp`, `treesitter`)

```m31
pub type Diagnostic { pub MED_buffer.Pos start; pub MED_buffer.Pos stop; pub str message; pub int severity; pub str source; pub str code; }
pub List<Diagnostic> Buf.diagnostics()
pub DiagnosticCount Buf.diagnostic_count()         // error, warning, info, hint
pub type LspState { pub str server; pub bool is_ready; pub str status; }   // "LSP: Indexing" text
pub Option<LspState> Buf.lsp_state()
pub int Buf.syntax_at(int row, int col)            // a SYN_class value: comment, string, ... from the lexer
pub str Buf.language()
```

LSP actions stay commands (`did_run_ex("Lsp hover")`, as nox's `lsp.*` went through `exec`). There is no
tree-sitter in m31 (G3), so `syntax_at` is the "treesitter-like" read: byte classes from the `syntax` library, which
is what todo needs to find comments. Read-only first, like nox (N19).

### 4.10 Errors, stability, error isolation

* **Contract.** Every API function that can fail returns `Result<T, str>` (or `Option<T>` for absence, `bool` for
  `did_` registration). Wrong arguments, closed handles, unknown names, out-of-range rows return `Err("MED_ext:
  <function>: <reason>")` and add a problem line; **the API never traps on caller input** (clamp, check, return).
  This replaces nox's `error()`-for-contract-violations (N3) with the only mechanism m31 has.
* **Handlers** return `Result<bool, str>`: `Ok(true)` ran, `Ok(false)` ran and stop later handlers of this event,
  `Err(text)` failed. After `FAILURE_LIMIT` (3) failures in a row the plugin is switched off for the session and
  says so (0.1.0, unchanged).
* **Traps are fatal and not isolated.** This is the one place where m3 is weaker than nox (nox: "one bad callback
  is logged and isolated"). Mitigations, in order of value: (1) first-party plugins are compiled, linted,
  tested and reviewed with the editor; (2) the API validates everything it is given; (3) a **crash breaker**: the
  editor writes a small marker in the state directory at start and removes it on a normal exit; if a marker is found
  the next start runs with plugins off (`M3_PLUGINS=on` overrides) and says so on the command line; (4) ask m31
  for an `on_trap` hook (open question 11).
* **Time.** Each dispatch is timed with the monotonic clock; a handler over its budget (1 ms for `CursorMoved`,
  `TextChanged`, `ModeChanged`, `Tick`, `ViewportChanged`) three times in a row switches the plugin off, as with
  failures (EXTENSIONS open question 5, done here).
* **Versioning.** `MED_ext.API_VERSION` is separate from the editor's. While the major is 0: a plugin built for
  `0.M.p` runs on host `0.M.q` with `p <= q` (additive slices inside 0.2: patch bumps only add); a different minor
  refuses. From 1.0: major may break, minor only adds, patch changes nothing. Because plugins are compiled in, a
  signature change is a **compile error** in the plugin, not a run-time surprise; that is the main benefit of the
  design and the reason there is no run-time negotiation.
* **Deprecation.** From 1.0 a function is marked deprecated in this document and in its doc comment for one full
  minor release, then removed in the next major. **A symbol is never reused for a new signature** (N8): a changed
  shape gets a new name (`Hook` stays, `Hook2` appears if needed). 0.1.0 names that 0.2 renames (`BufOpen` and the
  other event values, `Ctx.editor`) are removed at 0.2 (pre-1.0 anti-churn: the only consumer is the sample);
  after 1.0 they would have an alias for a release. All changes are logged in a "changes" section of
  `docs/EXTENSIONS.md`, as nox logs in `NOX_API.md`.
* **Stabilisation.** Same stance as nox: stabilise before 1.0, not during. API 1.0 is tagged together with m3 1.0
  *after* the plugins of section 7 have moved (that is the dogfooding proof, open question 10).

---

## 5. Registration metadata and the build

### 5.1 What nox's manager becomes

| nox spec field | m3 | Where evaluated |
|---|---|---|
| `[1]`/`name`, `module` | `Spec.name`, the plugin's module | build time (`plugin.txt`) and start-up (`register`) |
| `dir` / `git` | none: the source is in the tree or `--plugin-dir` | build time |
| `event = ...` | `Trigger` kind `Event`, value = event string | start-up: a hook installed from data, activates the plugin on first delivery |
| `cmd = ...` | `Trigger` kind `Command`, or `CommandSpec`s in the spec | start-up: a stub `:Cmd`; first call activates, then re-dispatches to the real handler |
| `keys = ...` | `MapSpec`s in the spec | start-up: maps installed synchronously with the stub action; visible to which-key before activation |
| `ft = ...` | `Trigger` kind `Filetype` | start-up: hook on `FiletypeSet` |
| `dependencies` | `Spec.requires` (hard), `Spec.wants` (soft, order only) | build time (closure, order) and start-up (check, activate first, cycle guard as nox `load`) |
| `opts` | `Spec.options` (registered, typed) set by `:set` in `keymap.vim` | start-up, before activation of eager plugins |
| `config(opts)` | none | no code in user configuration (D2); a plugin reads its options through `Ctx.option` |
| eager unless triggered | `triggers == []` | activation at `Ready`, after the keymap file |

```m31
pub enum TriggerKind { Event; Command; Filetype; }
pub type Trigger { pub TriggerKind kind; pub str value; }

pub interface Plugin { Result<bool, str> activate(Registry api); }   // registers the real handlers once

pub type Spec {
    pub str name;                          // "git": lower case, unique, equals the plugin directory
    pub str summary;
    pub int api_major; pub int api_minor; pub int api_patch;
    pub List<str> requires = [];           // not registered unless all are built in and on
    pub List<str> wants = [];              // soft: activated first when present
    pub List<Trigger> triggers = [];       // empty = eager
    pub List<OptionSpec> options = [];
    pub List<MapSpec> maps = [];
    pub List<CommandSpec> commands = [];
    pub List<SegmentSpec> segments = [];
}
pub bool Registry.did_plugin(Spec spec, Plugin plugin);
```

Evaluation at start-up, in generated order: every `register` runs (cheap: it builds the `Spec` and calls
`did_plugin`); the registry validates `requires`, creates stubs and hooks from the data, and records problems;
the keymap file is read; at `Ready` the eager plugins activate in dependency order. A lazy plugin activates on its
first trigger: its `requires` first, then `activate`, which registers the real hooks. Laziness in m3 saves
**initialisation**, not loading: a plugin that reads a state file, builds a cache, spawns `git` or arms a timer
does it in `activate`; the code is already in the binary. That is exactly the rule of DESIGN section 12 ("nothing a
plugin owns runs at start-up except building its rows"), now enforced by structure.

Example, the whole `move` plugin shell:

```m31
// plugins/move/MEDX_move.m31
import ext.MED_ext;

pub void register(MED_ext.Registry api) {
    MED_ext.Spec spec = MED_ext.Spec(name: "move", summary: "move a line or selection with Alt-h/j/k/l", api_major: 0, api_minor: 2, api_patch: 0);
    spec.maps.push(MED_ext.map(MED_ext.MapMode.Normal, "<M-j>", MED_ext.Action.Command(":MoveDown"), "move line down"));
    // ... <M-k> <M-h> <M-l> and the Visual forms ...
    spec.commands.push(MED_ext.command("MoveDown", "move the line or selection down"));
    api.did_plugin(spec, Mover());
}
```

### 5.2 Enabling and disabling at build time

Source of truth for the build: `plugins/<name>/plugin.txt` (four keys: `name`, `summary`, `requires`, `wants`). A unit
test (`t_plugins`) checks that it equals the m31 `Spec`, so the two cannot drift. Profiles are lists in
`plugins/profiles/`:

| Profile | Contents | Use |
|---|---|---|
| `default` | every first-party plugin except the optional ones | releases (`install.sh`), what `bash scripts/build.sh` builds, CI default |
| `full` | `default` plus `colors`, `icons`, `trouble`, `indentscope` | the owner's daily driver and the all-plugins CI leg |
| `minimal` | empty | the core gate (same as `--no-plugins`) |

```
bash scripts/build.sh                            # profile default, plus extras named in ext/enabled.txt
bash scripts/build.sh --profile full
bash scripts/build.sh --no-plugins               # core only; the plugins/ tree is not even linked into the build
bash scripts/build.sh --plugins git,finder       # exactly these; their requires are added and reported
bash scripts/build.sh --without terminal,jump    # default minus these; refused if a kept plugin requires one
bash scripts/build.sh --ext MYGIT_status --ext-dir ~/src/m3-ext    # third-party modules, unchanged from 0.1.0
M3_PROFILE=full M3_WITHOUT=terminal bash scripts/build.sh          # the same through the environment
```

* `scripts/build.sh` already builds on a scratch tree of symlinks when extensions are named (it links `engine ui
  themes m3.m31 deps .m31-deps` and generates `ext/MED_ext_enabled.m31`). Two changes: link `plugins/` **only for the
  names selected** (so `--no-plugins` has no `plugins/` at all, and any import of a plugin from core is a compile
  error, which enforces rule R1), and generate the registry from the resolved, topologically ordered list
  (`requires` first, ties in profile order).
* **The checked-in `ext/MED_ext_enabled.m31` is generated from the `default` profile**, so a bare `m31c m3.m31`
  equals the release; a test checks it equals the generator's output. (Today it is empty, which would silently make
  the plain test build core-only. Decision in section 9, item 2.)
* `m3 --version` prints `m3 0.16.0 (api 0.2.0; plugins: finder git ...)`; `:Plugins` lists compiled plugins with
  state (`active`, `lazy`, `off`, `refused: requires x`) and, as today, the core features that have a switch.
* `:PluginEnable/:PluginDisable NAME` keep working at run time (keymap-file lines too): a disabled plugin's maps,
  commands, segments and hooks are inactive (the registry's `is_off`), which is what the user sees today. Build time
  removes code; run time only switches it off.
* **Release builds** contain the `default` set. A custom m3 needs the toolchain (EXTENSIONS section 1, unchanged);
  the source SDK tarball question (EXTENSIONS Q2) stays open and is recommended.
* CI legs: PR: `default` and `minimal` (two builds, about a minute each, then the gates of 7.4 and 7.5); nightly: `full`,
  and for every plugin X both `--plugins X` (closure only) and `default --without X`. That is about 20 plugins and
  40 builds nightly, which also proves that every dependency is declared.

### 5.3 Budgets

| Budget | Value | How checked |
|---|---|---|
| Registration of all `default` plugins at start-up | at most +1 ms over the 0.15.0 baseline (startup 1k-line file 0.016 s, `bench/bench.py`) | `bench.py` startup row, 20 runs |
| An event nobody listens to | one list read (`counts[index] == 0`), as 0.1.0 | `t_ext` |
| Key to first frame, single-cell action | p50 under 5 ms, p99 under 8 ms; held `j` 141 bytes per frame | `bench/uxperf.py --check` and the bytes columns compared exactly with the baseline |
| Binary size and build time | `default` within 2 percent of 0.15.0; `minimal` smaller by the m31git share (about 17 percent) | recorded per step in the CHANGELOG, as D3 did |

---

## 6. Repository layout, naming, versioning

### 6.1 Layout

```
engine/            headless core (unchanged)
ui/                front end core (shrinks as features leave)
ext/               the API: MED_ext.m31 (may split into MED_ext_*.m31), MED_ext_enabled.m31 (generated), MEDX_trim_whitespace.m31
engine/MED_hooks.m31   engine-level hook tables (slice E; no ui imports)
plugins/
  profiles/default.txt  full.txt  minimal.txt
  <name>/
    plugin.txt              name, summary, requires, wants
    MEDX_<name>.m31         register(api) and the Plugin implementation
    MEDX_<name>_*.m31       internals (several files allowed; all prefixed MEDX_<name>)
    README.md               what it does, keys, options, events used, how to turn it off
    tests/t_<name>.m31      unit tests, no terminal (printed "N failed" like the others)
    tests/<name>_pty.py     optional pty scenario
    tests/test.sh           sourced by tests/test.sh only when the plugin is in the profile
    tests/corpus/*.txt      oracle corpora the plugin owns (header `#plugins: surround repeat`)
themes/            core themes; the data plugin keeps the others in plugins/themes/
scripts/           build.sh (profiles), check_plugins.sh (R2, R3), gen_*.sh
tests/             core tests, oracles, golden screens (tests/screen_pty.py)
```

`m31c fmt --check -r .` and `m31c lint .` already run over the whole tree and so cover `plugins/`. A plugin's
oracle corpora and unit tests move with it; the corpus runner already skips corpora whose `#plugins:` header
names something not available, and the same mechanism skips plugin corpora in a build without that plugin.

### 6.2 Naming

* Directory `plugins/<name>`: lower case, one word where possible, equal to today's `MED_plugin` names so users
  keep `:PluginDisable git`: `whichkey statusline finder explorer git harpoon move jump bracketed todo terminal
  session themes surround autopairs` plus new `notify colors icons trouble indentscope`.
* Modules `MEDX_<name>` and `MEDX_<name>_<part>` (upper-case prefix, snake-case rest), user ex commands with a capital
  first letter, options `<name>_<what>`, scopes `<name>.<what>` (`todo.fixme`), event names as in 4.3.
* Hoard repo name when a plugin is mirrored: `m3-<name>`. This is the rule nox lacked (its dev directories and repos
  diverge, 1.3).
* Third-party plugins use their own module prefix (EXTENSIONS section 1) and a `plugin.txt` with the same keys.

### 6.3 Versioning

* First-party plugins carry the **editor's version**: they are built from the same tree and tested together, and
  `:Plugins` shows `0.16.0`. CHANGELOG sections gain a line per plugin changed (`plugin git: ...`).
* The API has its own version (4.10). `Spec` records the API a plugin was written for.
* Third-party plugins have their own semantic version in `plugin.txt` and declare the API they need.

### 6.4 Should each plugin become a separate hoard repo (as the nox-* are)?

**Recommendation: not now; one monorepo until API 1.0, then read-only mirrors.**

* Plugins are compiled against the exact core: a signature change is a compile error (4.10), so a plugin repo
  needs a pinned core commit and a lock file, which is what `deps.lock` does for `tui` and `syntax` already.
  nox could split because Lua plugins load against whatever runs; m3 cannot.
* The suites that matter (nvim oracle, pty scenarios, golden screens, `uxperf`) live in this repo; a split plugin
  would test against a stale copy or need the whole checkout anyway.
* nox's duplication (plugins bundled **and** standalone, two names each, a config shim to choose) is a cost the
  owner has already paid once and recorded as friction.
* After 1.0, publish mirrors with `git subtree split --prefix plugins/<name>` for people who want one plugin as
  `--plugin-dir`. Third-party plugins live in their own repositories with their own prefix.

---

## 7. Migration plan

### 7.1 Method: dogfood in place, then move

For each feature, **step A** refactors it in place so it talks to the rest of core only through the API (still in
`ui/`, behind the same interfaces, same bytes out); **step B** is then a file move into `plugins/<name>/`, a
`plugin.txt`, a `Spec` and a registry line. A is verified by the existing suites; B is almost mechanical. A step
below is "A + B" unless said otherwise. No step changes user-visible behaviour of the default build. Steps that
add features (`notify`, `colors`) are marked N and come after the API they need exists.

### 7.2 The steps

Effort: S under a day, M one to three days, L a week or more (ROADMAP legend). Risk: L, M, H for the chance of a
visible or oracle-visible change. "API" names the slice of section 4 that must land first: **A** foundation
(`Spec`, registry metadata, profiles, services slots, event rename, handles, keymaps all modes with `<Cmd>` and
`<buffer>`, options registry, commands), **B** decorations (namespaces, `Hl`, signs, `ViewportChanged`), **C**
floats, `select`, `input`, `pick_stream`, bars, notifications, `PendingKeys`, **D** docked widget and `system`
with exit codes and pty, **E** engine hooks (insert filter, operators, text-object and pending-command
registration).

| Step | Moves or adds | Needs API | Risk | Effort | Evidence it is behaviour-preserving | Depends on |
|---|---|---|---|---|---|---|
| **S0** Foundation (no feature moves) | `Spec`, `did_plugin`, registry stubs, `plugins/` and profiles, `build.sh` profiles and `--no-plugins`, `plugin.txt` and `t_plugins`, `:Plugins` from the registry, `is_ui_command` as registry data, checked-in registry from `default`, golden-screen baseline `tests/screen_pty.py` recorded **before** anything moves, `scripts/check_plugins.sh`, `Ctx.editor` deprecated | A (partly) | L | L (about a week) | Default build identical (no plugin yet); `t_ext` extended; golden baseline stored | none |
| **S1** `<Cmd>` and `<buffer>` maps as Vim features | engine `MED_map` per-buffer tables, `<Cmd>`; oracle corpora 60/61 extended | A | M (oracle) | M | New corpus cases match nvim; old corpora unchanged | S0 |
| **S2** `move` | `App.did_alt_move` (about 40 lines) and its keymap rows | none beyond S0: today's `did_map` plus `did_run_ex("m +1")`, `gv`, and `<M-j>` notation (`MED_key` has `MOD_ALT`; to verify that a map accepts it, S1 if not) | L | S | golden screens and a key-sequence pty test equal; `MED_plugin` name `move` becomes the Spec name | S0 |
| **S3** `themes` (data plugin) | 10 themes out of `MED_theme_data` into `plugins/themes`, `Registry.did_theme(name, lines)`, `gen_themes.sh` per plugin | A (`did_theme`) | L | S | `:theme` list and `m3 --dump-sample` for every theme byte-identical; `t_theme` unchanged (it reads scopes the renderer asks for) | S0 |
| **S4** `bracketed` | `App.did_bracketed`; `]b [b ]q [q` first, `]d [d` `]h [h` `]t [t` register when the service exists | A (maps, services) | L | S | pty: every pair key before and after; golden | S0 |
| **S5** `harpoon` | `App.harpoon_*`, `MED_state` per-project lists (state file API `Ctx.state_dir`), `<Space>1..9`, `<Space>h*` | A, C (`select` or `pick`) | L | S to M | pty scenario for add, pin, jump; state file format unchanged | S0, S1 |
| **S6** Decorations slice, then `todo` | namespaces, `Hl`, `ViewportChanged`, sign priorities; `todo` moves `draw_line` TODO highlight (line 4746), the TODO source and `]t` | B | M (hot path: `draw_line`) | L | `uxperf` bytes per frame identical for a TODO-heavy buffer; golden; theme scope `ui.todo` unchanged; `todohl` option kept | S0 |
| **S7** `statusline` (and bufferline) | `draw_status` extras, `draw_tabline` bufferline; segments with priorities, `set_bar` | B, C (bars) | M (truncation order must be identical) | M | golden at widths 40, 60, 80, 200; `uxperf` bytes; E/W, branch, hunk counts via services | S6 |
| **S8** `jump` | `handle_jump_key`: key capture and label overlay | B (overlay via decorations), A (`capture_keys`) | L | S to M | pty scenario `<Space>j` | S6 |
| **S9** `whichkey` | popup drawing, `PendingKeys`, fade, `MED_keymap` rows to specs; pending-key state stays core | C, A | M | M | golden of the popup for `<Space>`, `g`, `z`, `[`, `]`, `<C-w>`, `"`; timing 400 ms preserved; `t_keymap` and generated `docs/KEYMAP.md` unchanged | S0, S5 (rows moved) |
| **S10** `finder` | files, grep, recent, lines, symbols, word sources, `MED_files` walk, `MED_ignore`, `MED_grep`, `MED_frecency`, `MED_sources`; core keeps `MED_picker`, its view, `MED_fuzzy`, sources buffers/commands/options/marks/keys/quickfix/themes; `project_root` to core; `BoostFn` | C (`pick_stream`) | M to H (the most used feature, FINDER.md ranking, 7-terminal width suite) | L | `t_fuzzy t_picker t_frecency t_ignore t_grep t_sources` unchanged or moved; `finder_pty.py`, `finder_variants_pty.py`, `bench/finder_bench.m31` numbers equal; `uxperf` | S6, S9 |
| **S11** `git` | `MED_git`, `MED_gitlib`, `MED_gitcmd`, `draw_sign` git part, `run_git_*`, `run_hunk_command`, `ih ah` objects; services `git` | B (signs), A (maps incl. `o`), C (`pick_stream`), E for `ih ah` (can stay `x`/`o` maps first) | M | L | `t_git`, `t_gitlib`, `oracle_git.py`, `git_pty.py` unchanged; gutter golden; `--no-plugins` drops m31git (record size and build time) | S10 |
| **S12** `notify` (N) | message ring and `:messages` in core, `Message` event, toast plugin | C (float, `defer`), tween | L (new) | M | new tests; nothing else changes (toasts off in `default` until chosen, open question 12) | S0, C |
| **S13** `explorer` | `MED_tree`, `App.tree_*`, mouse, git letters via service | D (docked widget) | M to H (pixel parity) | L | `t_tree` moved; golden of the tree with git states; mouse pty; `follow current file` | S11 |
| **S14** `terminal` | `MED_vt`, terminal code in `App`, `:terminal`, `<Space>t` | D (pty, raw input, buffer kind) | M | L | `t_vt`, e2e terminal scenarios; no stray child after quit | S0 |
| **S15** `session` | `MED_session`, `apply_session_*`, `remember_position`; `MED_persist` and the state dir stay core | A (layout read/write), D | M | M | `t_session`; pty restore scenario; layout equalising unchanged | S0 |
| **S16** `colors` (N) | new | B (`Hl.rgb`) | L | S to M | new tests; not in `default` | S6 |
| **S17** `surround`, `autopairs` (E) | `MED_surround`, `MED_autopair`, the `sur_*` and `ap_*` fields, sentinels in `MED_ex.drain`, the 9 option-guarded call sites in `MED_vim` (lines 2979 to 7845) | E (insert filter, operator, pending command, Visual `S`) | **H** | L (each) | oracle corpora 88 to 92 (2,913 cases, with the plugins in the oracle runner's build) identical; `uxperf key` and typed-character bytes; `t_surround`; dot-repeat cases | everything else; S1 |
| **S18** `trouble`, `icons`, `indentscope` (N, optional) | new | D, B | L | S to M each | new tests | S13 or later |

Steps S2 to S5 and S3 are independent of each other once S0 is in; S6 opens the second wave.

### 7.3 Dependency graph

```
S0 foundation ----+---- S1 <Cmd>/<buffer> maps ----- S5 harpoon
                  |
                  +---- S2 move
                  +---- S3 themes (data)
                  +---- S4 bracketed
                  +---- S14 terminal (needs slice D)
                  +---- S15 session (needs slice D)
                  |
                  +---- S6 decorations + todo ---+--- S7 statusline ---- (services)
                  |                              +--- S8 jump
                  |                              +--- S16 colors (N)
                  |
                  +---- S9 whichkey (needs C) ---- S10 finder ---- S11 git ---- S13 explorer ---- S18 trouble etc.
                  |
                  +---- S12 notify (N, needs C)
                  |
                  +---- S17 surround + autopairs (needs E, S1, and everything above settled)
```

API slice order: A with S0, B with S6, C with S9 (and S5), D with S13, E with S17. Each slice is additive and
shipped before the first plugin that needs it.

### 7.4 Acceptance: the core-only build

`tests/core_only.sh` runs `bash scripts/build.sh --no-plugins -o m3-core` and then:

1. **Build gate.** Compiles with no `plugins/` reachable; the binary has no m31git symbols (record size and build
   time next to `default`).
2. **Unit gate.** Every core unit test passes (`tests/test_units.sh` minus the tests that moved to plugins).
3. **Oracle gate.** All corpora whose `#plugins:` header is absent or satisfied: the engine corpus, regex corpora,
   folds, snippets, windows. Until S17 the surround and autopairs corpora run (they are still core); afterwards they are skipped with
   the existing "plugin(s) not found" note, and the `default` build runs everything: **the whole corpus (about 40,000
   cases, 40,840 lines) stays green in the default build at every step.**
4. **Behaviour gate (pty).** A scripted session on `m3-core`: open a file, edit with an operator and a text
   object, search and `:s`, split, tab page, `:Explore`, fold, snippet expansion, `:set`, a map from a keymap file,
   undo, write, quit; LSP against `tests/fake_lsp.py` (diagnostics sign, hover, definition, completion popup,
   format on save); the picker primitive through `:Commands` and a buffers pick.
5. **Absence gate.** `:Plugins` lists none; `<Space>ff` is "not an editor command" or unbound, and nothing crashes;
   `:Git`, `:Neotree`, `:terminal` are E492.
6. **Budgets.** `uxperf --check`, startup at most the 0.15.0 baseline.

A step is done when the **default** build passes the full suite and the golden screens, **and** `minimal` passes
`core_only.sh` for the features that have left so far.

### 7.5 Verification toolkit (what "behaviour-preserving" means in practice)

| Layer | Tool | Notes |
|---|---|---|
| Engine semantics | nvim oracle corpora (about 40,000 cases in 40,840 lines, regex, fold, snippet and window oracles, fuzz seeds) | no change expected before S17; there it is the evidence |
| Units | `tests/t_*.m31` and each plugin's `tests/` | moved with the code, never weakened |
| UI behaviour | pty scenarios (`tests/e2e.py`, `finder_pty.py`, `git_pty.py`, `lsp_pty.py`, `anim_pty.py`, `width_pty.py`, `ext_pty.py`) | unchanged |
| **Screens** | new `tests/screen_pty.py`: about 25 scripted scenarios on the `pyte` emulator the width tests already use, dumping text and a style hash; **baseline recorded from 0.15.0 in S0**, compared at every step for default and, where the feature remains, minimal | DESIGN says there is no nvim oracle for pickers and buffers; this is the oracle for the UI: the old build |
| Performance | `bench/uxperf.py --check --json`, `bench/bench.py`, `bench/finder_bench.m31` | bytes columns are deterministic and must be equal; latency within the budget; startup +1 ms at most |
| Hygiene | `m31c fmt --check -r .`, `m31c lint .`, `scripts/check_plugins.sh` | in the gate |

---

## 8. What the extension API must not do

* **No runtime loading**: no `dlopen`, no loading of source or bytecode, no plugin directory scanned at start-up, no
  "install plugin" command, no network fetch inside the editor. A plugin is chosen by the build (D2). The
  `nox.plugins` git clone and update (`:NoxPluginsUpdate`) have no m3 counterpart.
* **No scripting language** in the editor (D2; ROADMAP "never in scope"): no Lua, no Vimscript beyond the ex
  subset, no `config(function)`. User configuration stays data: the keymap file, `:set`, `.m3.toml`, EditorConfig.
* **No access to internals**: no `App`, no `context.editor`, no module reached by a path that is not `ext.*` (R2,
  R3). **No frame callback** ("no draw hook, by design"): decorations are stored data written from
  `ViewportChanged`. **No direct terminal writes**: only the renderer writes.
* **No hidden global state** (m31 has none) and no blocking beyond the capped `run`; no trap on caller input; no
  API that exposes a `tui` type except through `Canvas`.
* **No second event system**: the `:autocmd` subset of ROADMAP item 24 must call the same dispatch.
* **No per-plugin binaries and no version negotiation at run time**: a mismatched plugin does not compile.

**How a Lua-like or WASM runtime could be added later without breaking this API (a note, not a plan).** The API is
deliberately data plus interfaces: arguments and results are strings, ints, bools, lists, maps and records;
callbacks are identified when registered (`Hook`, `CommandFn`, `KeyFn`, each a one-method interface); decorations,
floats and handles are ids. A scripting host is then **itself a first-party plugin** (`script`, off by default): it
implements the registry calls for a guest by marshalling, keeps a table `id -> guest function`, registers one
`Hook` per guest callback, and turns `Err` into guest errors (where nox's `error()` and `pcall` come back). Nothing in
sections 4 and 5 would change; what would be new is an interpreter, an install story and a trust model
(EXTENSIONS section 4 says there is no sandbox), which is why it is not now.

---

## 9. Open questions for the owner (answerable in one line)

1. **Monorepo or hoard repos for first-party plugins?** Recommend monorepo `plugins/` until API 1.0, then read-only mirrors named `m3-<name>` (6.4).
2. **Should the checked-in registry be the `default` profile (so `m31c m3.m31` equals the release) rather than empty?** Recommend yes, guarded by a test; `--no-plugins` for core only.
3. **Keep `:PluginEnable/:PluginDisable` as a run-time switch on top of build-time selection?** Recommend yes (users and the keymap file rely on it); it only deactivates.
4. **Is the LSP client core, as the acceptance brief says, with extraction left for later?** Recommend yes; hide it behind a facade so a later `--no-lsp` is possible.
5. **Do surround and autopairs leave the engine?** Recommend yes, as the last step (S17), and only with the oracle corpora green; until then they are core behind `:set`.
6. **Indent guides core or plugin?** Recommend core (renderer option, per cell, blank lines; nox kept them native too); an optional `indentscope` plugin adds the overlay.
7. **Rename the 0.1.0 events (`BufOpen` to `BufferOpen`, nox names) without aliases?** Recommend yes: pre-1.0, the only consumer is the sample, and the API stabilises before 1.0 (nox's stance).
8. **Byte columns (m3 engine and oracle) or nox's character columns in the API?** Recommend byte columns with conversion helpers.
9. **Explorer: widget API (identical output) or rewrite on a buffer as nox did?** Recommend the widget API (`Canvas`), because behaviour must not change; revisit if a second plugin wants it.
10. **When does the API reach 1.0?** Recommend with m3 1.0, after S0 to S15 have moved (the dogfooding proof); until then 0.2.x additive.
11. **Accept the crash breaker (marker file, plugins off after a crash) and ask m31 for an `on_trap` hook?** Recommend yes to both.
12. **Message history and toasts: history in core (`:messages`), toasts as the `notify` plugin, on by default?** Recommend history in core now; toasts in `full` first.
13. **Publish a source SDK tarball per release so a custom build needs no clone (EXTENSIONS Q2)?** Recommend yes.
14. **Do the ten non-default themes leave core as a data plugin (smaller `--no-plugins` binary)?** Recommend yes (S3); `default`, `default-light`, `term16-*` stay.
15. **Is `colors` (colour-literal preview) wanted, and in `default`?** Recommend build it (S16), keep it out of `default`.
16. **Build `trouble` as a persistent panel, or let the finder cover diagnostics?** Recommend defer until the docked widget exists (S13).
17. **First-party plugin versions equal the editor's?** Recommend yes; third-party plugins carry their own.
18. **Plugin options flat and prefixed (`harpoon_max`) as Vim does, not dotted as nox?** Recommend flat with the plugin name as prefix; `:set` and completion stay unchanged.
