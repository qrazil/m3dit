# Extending m3

Status: API 0.2.0, experimental (the 0.2 plugin layer is section 0; sections 1 to 14 describe the extension form of 0.1.0, which still works, with the event names of 0.2). Decision D2 (docs/ROADMAP.md section 4): the extension language is m31 itself, used
as modules. The external-process JSON-RPC option was declined; there is no interpreter, no second language, no
`dlopen` and no C shim.

The code is `ext/MED_ext.m31` (the API and the registry), `ext/MED_ext_enabled.m31` (the list of built-in
extensions, empty by default), `ext/MEDX_trim_whitespace.m31` (a sample) and a few delimited hooks in
`ui/MED_app.m31`, `engine/MED_ex.m31`, `engine/MED_editor.m31` and `m3.m31`.

## 0. API 0.2.0: plugins (docs/CORE-AND-PLUGINS.md)

The first-party features of m3 are being moved out of the core into **plugins** that use this API (the design is in
`docs/CORE-AND-PLUGINS.md`, the owner's decisions at its top). A plugin is a module in `plugins/NAME/` compiled in
by the build; nothing is loaded at run time. What 0.2.0 adds to the extension form below:

* **A description as data.** `api.did_plugin(spec, plugin)` takes a `MED_ext.Spec` (name in lower case equal to the
  directory, summary, the API version, `requires` and `wants` (other plugins), `triggers`, `maps`, `commands`) and
  a `MED_ext.Plugin` (`activate(api)`). `register` only describes the plugin; nothing of it runs yet.
* **Activation.** After every module registered, the registry (`finish_install`) refuses a plugin whose `requires`
  is missing, installs a stub for each command in the spec and each trigger, and installs the keys. A plugin
  without triggers activates at `Ready` (after the keymap file), in dependency order; one with triggers
  (`on_event`, `on_command`, `on_filetype`) at the first trigger, the handlers it registers taking part in that
  very delivery or call. `activate` registers the real handlers (`did_hook`, `hook_with`, `did_command`, `did_map`,
  `did_group`, `did_job`). Laziness saves initialisation (state files, caches, processes), not code loading.
* **Names.** Events are nox's: `Ready Shutdown BufferOpen BufferWritePre BufferWritePost BufferClose ModeChanged
  CursorMoved TextChanged Tick` (strings `ready`, `buffer_write_pre` ... in specs). The 0.1.0 names are gone, without
  aliases (owner decision Q7). `hook_with(event, hook, HookOpts)` returns an id for `did_unhook`; `is_once` runs once.
* **Maps.** `MapSpec(mode, keys, action, desc, group, buffer, is_silent)`: `Action.Command(":Name args")` (run with `<Cmd>`),
  `Action.Call(KeyFn)` or `Action.Keys("...")` (typed keys, a `:noremap` right-hand side: use it where the ex line needs the
  Visual marks). Every mode works (`Normal Visual Insert OperatorPending Command`, from the `<Cmd>` mappings of step S1);
  `Ctx.did_map` sets buffer-local maps for the buffer a handler runs for.
* **Run time.** `:PluginDisable NAME` and `:PluginEnable NAME` switch a compiled plugin off and on (its hooks, commands
  and keys go inactive; owner decision Q3); `:Plugins` lists compiled plugins with their state (`active`, `lazy`,
  `pending`, `off`, `refused: requires x`). `m3 --version` prints `m3 0.16.0 (api 0.2.0; plugins: ...)` and
  `m3 --list-plugins` prints them, tab separated.
* **Version rule.** While the major is 0, a plugin built for `0.M.p` runs on host `0.M.q` when `p <= q`; another minor
  is refused. From 1.0 a minor only adds. Signature changes of plugin-visible functions are compile errors, not run-time
  surprises. A symbol is never reused for a new signature (0.2 removed `did_map(mode, keys, command, summary)` and
  the 0.1.0 event names in the same release: the only consumer was the sample).
* **Deprecated.** `Ctx.editor` stays public for 0.2 and is refused by `scripts/check_plugins.sh`, which also enforces
  the import rules: a plugin imports only `ext.*`, `engine.MED_buffer`, `engine.MED_key`, the m31 standard library
  without `proc`, `os` and `term`, m31git, and its own modules.

**Selecting plugins at build time** (`scripts/build.sh`, resolved by `scripts/plugins.sh`):

```
bash scripts/build.sh                            # the default profile (plugins/profiles/default.txt)
bash scripts/build.sh --profile full             # plugins/profiles/full.txt
bash scripts/build.sh --no-plugins               # core only; plugins/ is not linked into the build at all
bash scripts/build.sh --plugins git,finder       # exactly these; their requires are added and reported
bash scripts/build.sh --without terminal,jump    # the profile minus these; refused if a kept plugin requires one
bash scripts/build.sh --plugin-dir ~/src/plugins # also look in DIR/NAME/plugin.txt (fixtures, third-party)
M3_PROFILE=full M3_WITHOUT=terminal bash scripts/build.sh   # the same through the environment
```

`plugins/NAME/plugin.txt` has four keys (`name`, `summary`, `requires`, `wants`); `tests/test_plugins.sh` checks it
against the `Spec` through `m3 --list-plugins`. The checked-in `ext/MED_ext_enabled.m31` is the generated registry of
the default profile (a bare `m31c m3.m31` equals the release; a test checks it). The default profile holds `move`, the
reference plugin (`plugins/move/`: eight `Action.Keys` maps, no handler; its README is the smallest example); `--ext`
extensions still work as before and come after the plugins.

## 1. What an extension is

An extension is **an m31 module that is compiled into the m3 binary**. m31 compiles ahead of time to C (`m31c`),
so nothing is loaded at run time: changing the set of extensions means building m3 again.

**Layout and naming.** One file `ext/MEDX_<name>.m31` (or any `PREFIX_name.m31`, see below). It follows the repo
rules: module names are global to a program and take an upper-case prefix (`m31`'s naming decision), values and
functions are `snake_case` of three letters or more, and `m31c -lint` runs over the whole tree. The in-repo samples use the prefix `MEDX_`
(m3 extension); an extension kept in its own repository uses its own prefix (`MYGIT_status`), because two modules
with the same name cannot coexist. The file exports one function:

```
import ext.MED_ext;

pub void register(MED_ext.Registry api) {
    if (!api.did_declare("TrimWhitespace", "strip trailing blanks on write", MED_ext.API_MAJOR, MED_ext.API_MINOR)) {
        return;
    }
    api.did_hook(MED_ext.Event.BufferWritePre, (MED_ext.Ctx context, MED_ext.Info info) => trim_all(context));
}
```

`register` runs once, before the keymap file is read. It declares the extension (a name that starts with a
capital letter, a summary, the API version it was written for) and registers handlers. A handler is a lambda or a
function value that fits one of the one-method interfaces `Hook`, `CommandFn` and `JobFn`; a lambda may capture
the state the extension needs. m31 has no mutable module variables, so an extension keeps state in objects it
captures, or in the registry's statusline segments.

**Selecting extensions at build time.** `ext/MED_ext_enabled.m31` is the registry of built-in extensions. The
checked-in file is empty, so the default build contains no extension and its behaviour is that of m3 without this
feature. `scripts/build.sh` generates a replacement for one build:

```
M31_ROOT=... LANGC=... bash scripts/build.sh --ext MEDX_trim_whitespace
M31_ROOT=... LANGC=... bash scripts/build.sh --ext MYGIT_status,MEDX_trim_whitespace --ext-dir ~/src/m3-ext -o m3-mine
M3_EXT=MEDX_trim_whitespace bash scripts/build.sh          # the same through the environment
```

A name is a file name without `.m31`, looked up in `ext/` and then in `--ext-dir` (or `$M3_EXT_DIR`). Without
`--ext` and `$M3_EXT` the script reads the names in `ext/enabled.txt` (one per line or comma separated, `#` comments)
when that file exists. Order is the order of `register` calls and decides conflicts (section 6). The script
does not edit the checkout: it builds on a scratch tree of symlinks in which only `ext/MED_ext_enabled.m31` is
generated. With no names it runs exactly the command it always ran.

**Who needs what, stated honestly.** Building a custom m3 needs the m31 toolchain (`m31c` and the runtime SDK
given by `M31_ROOT`), a C compiler, and a checkout of this repository at the version the extension was written
against (the first build also fetches the pinned `tui` and `syntax` dependencies). The released binaries
(`install.sh`) cannot take extensions. There is no way around that while extensions are compiled in. A build with
one extension takes about as long as the normal build (about a minute here); a typical edit-build-try loop is that minute.
A source SDK tarball (the sources, `deps.lock` and a script) would let a user build without cloning; that is an
open question (section 14).

## 2. The API surface

Everything is a method of `MED_ext.Registry` (registration) or `MED_ext.Ctx` (what a handler may do). Bool-returning
methods are named `did_...` because `m31c -lint` requires it; they return false when the request was refused.

| Need | API |
|---|---|
| Identify, check version | `api.did_declare(name, summary, api_major, api_minor)`, `MED_ext.version()`, `MED_ext.is_compatible(major, minor)` |
| Ex command `:Name args` | `api.did_command(name, summary, CommandFn)`; `CommandFn.run(context, arguments, is_bang)` |
| Key mapping per mode | `api.did_map(MapSpec)` with mode `n` or `x` until `<Cmd>` maps exist (section 6) |
| Events | `api.did_hook(Event, Hook)`; events `Ready Shutdown BufferOpen BufferWritePre BufferWritePost BufferClose ModeChanged CursorMoved TextChanged Tick` |
| Read the buffer | `context.line_count() line(row) text() cursor() mode() file directory()` |
| Modify the buffer | `context.did_replace(from, stop, text)`, `did_set_line(row, text)`, `set_cursor(pos)`, `did_run_ex(line)` |
| Registers | `context.register(name)`, `context.did_set_register(name, text)` |
| Options and config, read only | `context.option(name)`, `context.is_option_on(name)` (what `:set`, `.editorconfig`, `.m3.toml` and the keymap file produced) |
| Messages | `context.say(text)` |
| Finder, popup, prompt | `context.pick(title, entries)` opens the finder list (`MED_ext.place(text, path, line, column)` builds an entry); accepting an entry opens its file at the place |
| Statusline | `context.set_segment(name, text)` (empty text removes it) |
| Subprocess, blocking | `context.run(argv, timeout_ms)` returns `Ran{code, text, errors}`; the editor freezes meanwhile; the timeout is clamped to 1000 ms |
| Subprocess, async | `context.background(job, argv)` and `api.did_job(job, JobFn)`; `JobFn.run(context, job, lines)` runs on a later tick with the standard output lines |

Mode constants are `MED_editor.NORMAL INSERT REPLACE VISUAL CMDLINE`; `Info` carries `file`, `buffer_id`,
`mode_before`, `mode_after`, `row`, `col` and `elapsed_ms` as the event allows.

**Events.** They are delivered on the editor's one thread, in registration order, after the thing they report.
`BufferOpen` fires for each command-line file after start-up and for every later buffer. `BufferWritePre` and
`BufferWritePost` wrap `:w`, `:wall`, autowrite and autosave (`Post` only after a write without an error). `BufferClose`
fires before `:bdelete`. `ModeChanged`, `CursorMoved` and `TextChanged` are checked after each key event and each
tick for the active buffer and are coalesced: one delivery per event however many keys it carried. Changes a
handler makes are not reported back to handlers (no re-entrancy). `Tick` fires about every 250 ms.

**Editing correctly.** `did_replace` is `editor.change`, the entry point every editor command uses (it keeps
marks, the change list, the `U` line and the highlighter's dirty row right). The dispatcher closes the undo
block after each handler, so everything one handler did is **one undo step**, and `.` is untouched because dot
repeat replays typed keys, not text changes. An edit is refused (the method returns false) while a command or
insert session has an open undo block, because that block is not the extension's to close. In practice: edit
in `BufferWritePre`, `BufferWritePost`, commands and ticks, not in `TextChanged` during Insert mode. `did_run_ex`
runs an ex line as if typed (`set tabstop=2`, `normal! gg`), with the same rule; it is also the way to change options.

**Not in 0.1.0** (stated so nobody looks for it): extension-defined options (needs registration in the engine's
option table), insert, operator-pending and command-line mappings (the engine has no `<Cmd>` mapping, and an
extension mapping is a `:nnoremap` to `:Command<CR>`), `BufEnter`/`BufLeave`/`FileType`/`TextYankPost` events, a
prompt widget beyond the finder, a handle on windows and tabs, and reading the keymap.

## 3. Stability policy

* The API has its own semantic version, `MED_ext.API_VERSION`, separate from the editor's (`m3 --version`).
  `MED_ext.version()` returns it; `api.did_declare` is given the version the extension was written for and
  refuses an incompatible one with a message in the message line (the extension is then not registered at all).
* While the major version is 0 (now), any minor release may change anything and the check is exact (0.1 runs
  on 0.1 only). From 1.0: a major bump may break, a minor bump only adds (an extension for 1.2 runs on 1.2
  and 1.5, not on 1.1), a patch changes no signature.
* Deprecation: from 1.0 a function is marked deprecated in this document and in its doc comment for one
  full minor release, then removed in the next major. Behaviour that is documented here (event order,
  the undo rule, the failure rule) is part of the API.
* Because extensions are compiled in, a signature change is a compile error in the extension, not a run-time
  surprise; that is the main benefit of the design and the reason there is no dynamic version negotiation.
* The recommendation is to promote the API to 1.0 together with m3 1.0 (open question 1).

## 4. Sandboxing: there is none

An extension is trusted code compiled into the editor's process. It can read and write any file the user can,
start any program, and change any editor state through the fields that are public (the API is the supported
way, not a fence: `context.editor` is the engine object). Installing an extension is the same trust decision as
installing the editor. Do not build an extension you did not read.

## 5. Errors and traps

* A handler returns `Result<bool, str>`. `Err(text)` is the recoverable failure: the editor keeps running, the
  message line shows `ext NAME: text`, the handler's other effects stay (edits already made remain, as one undo
  step), and later handlers still run. After three failures in a row the extension is switched off for the
  session (`FAILURE_LIMIT`), says so, and its commands answer that it is off; a success resets the count.
  `Ok(false)` means "handled, run no later handler of this event".
* A **trap is fatal and not recoverable**. m31 has no `recover`: an index out of range, a division by zero, a
  `trap(...)` or an unwrapped empty option ends the whole process. Observed with a deliberate out-of-range index in
  a command handler: `trap: index out of range` and the process aborts with SIGABRT; the terminal is left in raw mode on the alternate
  screen (run `reset`), and unsaved buffers are lost except what autosave, `undofile` and swap-less recovery already
  provide. So: validate before indexing, use `Option` and `Result`, and keep handlers short. The `ext_started`
  / `ext_stop` hooks cannot catch a trap either.
* Registration problems (a bad name, a taken command, an incompatible API) are not traps: they are collected and
  shown at start-up, and the offending registration is skipped.

## 6. Ordering and conflicts

* Extensions register in the order of the build list; handlers of one event run in that order, then in the
  order each extension registered them.
* A command name is first come, first kept. A second `:Name` from another extension, or one that a built-in
  command already owns (`MED_ex.is_builtin_command`, which also covers abbreviations), is refused and reported.
  An extension command must be spelled in full, starts with a capital letter and contains letters and digits.
* Key mappings: the same `(mode, keys)` from two extensions is refused for the second and reported (first
  keeps it). Extension mappings are installed as `:nnoremap` / `:xnoremap` before the user's keymap file is read,
  so a mapping in the user's file always wins, and an extension mapping wins over a built-in default. A user map
  under `<Space>` takes over from the built-in leader menu as for any user map; the extension's `summary` is shown in `:Plugins` listings, not
  in which-key (0.1.0).
* Statusline segments are drawn in the order they were first set, after the branch and diagnostics, and are
  dropped when the line is too narrow, as the built-in parts are.

## 7. Performance

Every handler runs on the thread that reads keys and draws frames; nothing can interrupt it.

* Budget: a handler for `CursorMoved`, `TextChanged`, `ModeChanged` and `Tick` should finish in well under one
  millisecond; one frame is 16 ms and a held key repeats every 30 ms or so. A `BufferWritePre` handler may take
  longer, but the user waits for it.
* The cost of having no extension is a boolean per event point (`ext.is_empty()`, `has_handler`); with one
  extension the cost of an event nobody listens to is one list read.
* Never block: `context.run` is capped at 1000 ms and still freezes the editor; use `context.background` for
  anything that talks to a process or the network and set a segment from the `JobFn`. Statusline segments are
  stored text, read by the renderer; compute them in a handler or job, never "on draw" (there is no draw hook,
  by design).
* Do not scan a whole buffer on every `TextChanged`. Look at `info.row`, or debounce with `Tick`.

## 8. Testing an extension

* **Unit tests.** `MED_ext.Registry`, `MED_ext.Ctx` and `MED_editor.Editor` need no terminal. Build a registry,
  call `register(registry)`, make a context with `MED_ext.context(registry, MED_editor.new("text"), "file")`, call
  `registry.fire(event, context, info)` or `registry.did_run_command(name, context, "args", false)` and check
  `editor.buffer.dump()`, `context.notice` and `registry.take_problems()`. `tests/t_ext.m31` is the model, and
  it also drives a whole `MED_app.App` with keys.
* **Pty test.** Build with your extension (`scripts/build.sh --ext NAME -o m3-test`) and drive it as
  `tests/ext_pty.py` does: a temp project directory (realpath'd, passed as cwd and `PWD`),
  `GIT_CEILING_DIRECTORIES`, non-blocking writes, results read from the files on disk.
* Name your test `tests/t_<name>.m31` and add it to `tests/test_units.sh` (in-repo extensions); the repo gate also
  runs `m31c -fmt --check -r .` and `m31c -lint .` over `ext/`.

## 9. Example 1: trim trailing whitespace on save (built, `ext/MEDX_trim_whitespace.m31`)

`register` declares the extension, hooks `BufferWritePre` and defines `:TrimTrailing`. Both call `trim_all`, which
checks `context.can_edit()`, walks the lines with `context.line(row)`, finds the end of the text by scanning
back over spaces and tabs, and removes the tail with `context.did_replace(Pos(row, keep), Pos(row, size), "")`.
It counts what it did and says `trimmed N line(s)`. Because the edits go through `editor.change` and the
dispatcher closes one undo block, `u` after `:w` brings back every trimmed line in one step, and a `.` typed before
the write still repeats the earlier change (`tests/ext_pty.py` checks both). The editor already trims on write
when `trimtrailing` is on (EditorConfig `trim_trailing_whitespace`); the sample shows the API, it is not needed for that.

## 10. Example 2: `:TodoList` lists the TODO lines of the buffer in the finder (prose)

(`:Todo` is a built-in command that greps the project, so the extension takes another name: a taken name is
refused.) `register` declares the extension and calls `api.did_command("TodoList", "TODO lines of this buffer", ...)`.
The handler loops `for (int row in 0 .. context.line_count())`, takes `line = context.line(row)`, looks for `TODO`
or `FIXME` with `line.index_of(...)`, and for each hit appends
`MED_ext.place(line.trim(), context.file, row, column)` to a list. It then calls `context.pick("TODO", entries)`, or
`context.say("no TODO lines")` when the list is empty. The finder does the rest: fuzzy filtering, the preview of the file at that line, and
opening the entry at its line and column when accepted. It reads only the buffer in memory, so it costs one
pass over the lines and runs when the user asks. A project-wide variant uses
`context.background("todo", ["rg", "--vimgrep", "TODO"])` and a `JobFn` that parses the `path:line:col:text` lines into entries
and calls `context.pick` when the job ends (a pick from a `JobFn` opens the finder at that moment; take care
not to steal the user's prompt, for example only pick when the mode is Normal). Bind it with
`api.did_map(MED_ext.map(MED_ext.MapMode.Normal, "<leader>xt", "TodoList", "TODO lines"))`.

## 11. Example 3: statusline git-branch segment from m31git (prose; depends on D3)

Decision D3 makes `m31git` a pinned dependency of m3 (roadmap item 12); it is not in `deps` yet, so this is the shape of
the extension, not code that builds today, and the m31git function names are those of its current modules
(`GIT_refs`) and may change with the library tag. The extension imports `m31git` for its in-process
reading of `.git/HEAD` and the ref (no `git` process). `register` declares `GitBranch`, hooks `Ready`, `BufferOpen`
and `BufferWritePost` to call `refresh(context)`, and hooks `Tick` with a counter captured in a small object so
that it refreshes only every 4th tick (one second). `refresh` finds the repository for `context.directory()`
with the library, reads the current branch, and calls `context.set_segment("branch", "git:" + branch)`
only when the text changed (setting the same text is cheap, but it also avoids needless work). Reading two
small files per second is the whole cost; a failure to find a repository sets the segment to "" so the line stays clean. If a
library call would be slow (a very large repository), move it to `context.background` with `git rev-parse` as
the interim and set the segment from the `JobFn`. The built-in statusline already prints the branch from
`.git/HEAD`; this extension is the pattern, and a place where the segment could add dirty state or ahead/behind counts the
built-in line does not show. There is no `BufEnter` event yet, so switching buffers is noticed by the next `Tick` (open question 4).

## 12. Relation to the other extension points

The keymap file (`:map`, `:source`) stays the way to bind keys without building. Roadmap item 24 (`:autocmd`
as ex lines) and item 25 (`:command`) are the no-build route for what ex lines can express; they and this API
should share the one event dispatch (`MED_ext.Event` is named after Vim's events for that reason). If an
`:autocmd` implementation lands first, the registry should call it rather than own a second table.

## 13. Verified limits of this implementation

* With no extension the editor takes the same code paths: the hooks are `if (ext.is_empty())`, an empty
  command list in the ex parser, and an unchanged write path. The default build passes the same suites as before.
* A buffer-changing handler during `BufferWritePre` on a buffer other than the active one (`:wall`) edits that buffer and
  it is then written; the active buffer's cursor is not touched.
* `Event.Shutdown` runs only on a normal exit of the loop.
* Background jobs have no exit status (the runtime's `Stream` does not expose it); a JobFn sees the lines only.

## 14. Open questions for the owner

1. **When does the API reach 1.0?** Recommendation: together with m3 1.0, so the roadmap's compatibility promise
   covers it; until then it is 0.x with the exact-match check.
2. **How should a user get a custom build without cloning?** Recommendation: publish a source SDK tarball per
   release (sources, `deps.lock`, `scripts/build.sh`), documented here; do not ship per-extension binaries.
3. **Which layer owns mappings and extension options?** The engine needs `<Cmd>` mappings and an option table that
   an extension can add to. Recommendation: add `<Cmd>` first (it is also a plain Vim feature, with an oracle);
   add extension options after 1.0 if any extension asks.
4. **More events** (`BufEnter`, `BufLeave`, `FileType`, `TextYankPost`, `DirChanged`). Recommendation: add them
   when roadmap item 24 defines them, in one dispatch.
5. **Handler time budget.** m31 cannot interrupt a handler. Recommendation: measure each handler with the monotonic
   clock and switch off an extension that exceeds a limit three times (as with failures); not done in 0.1.0.
6. **Trap containment.** Recommendation: accept fatal traps and make the editor save every modified buffer to a
   recovery file on a trap if m31 ever gives a hook; ask for that in m31 (`on_trap` or process-level handler), do not work around it.
7. **Keeping `ext/MEDX_trim_whitespace`** in the tree. Recommendation: keep it as the documented, tested sample; it is off by default.
8. **Blocking `context.run` cap** (1000 ms). Recommendation: keep it; lower to 250 ms once the async path is common.
