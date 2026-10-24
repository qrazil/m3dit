# Request to m31: an `on_trap` hook

Status: written up for the m31 maintainers, 2026-10-23 (m3 owner decision Q11 in docs/CORE-AND-PLUGINS.md). Nothing in
m3 depends on it; it would make a safety net cheaper.

## The problem

In m31 a trap (an out-of-range index, an arithmetic fault, an assertion, a failed `unwrap`) ends the process; there is
no `recover` and no unwinding (docs/EXTENSIONS.md section 5). m3 compiles first-party plugins and third-party
extensions into one binary, so a trap in a plugin handler takes the editor with it, with the user's unsaved buffers.
Nox, the owner's earlier editor, isolated a bad plugin callback (Lua `pcall`); m3 cannot.

## What m3 does today instead

Every API function returns `Result` and never traps on caller input; first-party plugins are linted, tested and reviewed
with the editor; and a **crash breaker** is planned (docs/CORE-AND-PLUGINS.md 4.10): m3 writes a marker file in its state
directory at start and removes it on a normal exit; a marker found at the next start means the last run did not end
normally, so plugins start off (`M3_PLUGINS=on` overrides) and the command line says so. That protects the next start, not
the buffers of the run that trapped.

## The request

A way to run code when the process is about to end because of a trap, before it ends:

```
// registered once, e.g. at the top of the program
os.on_trap((str reason, str where) => { ... });     // or: pub void on_trap(TrapFn handler)
```

* The handler runs on the trapping thread, with the heap as it is; it may do plain file writes and `exit`, and nothing
  that allocates is guaranteed. A second trap inside the handler ends the process at once.
* `reason` is the trap's message ("index 7 out of range for a list of 3"), `where` the function or `file:line` when known.
* Not `recover`: the handler cannot resume the program. A later, separate question is whether a trap inside a
  *spawned task* could end only that task (m3 has none that run plugin code).

## What m3 would use it for

1. Write the crash marker with the reason and the plugin that was running (m3 keeps "the plugin whose handler is
   running" in `Ctx.owner`), so the next start can say "plugin X trapped: index 7 out of range" and switch only that
   plugin off, not all of them.
2. Write each modified buffer to a recovery file (`.name.m3-crash`) so that a trap loses no text. The editor's undo tree
   is already text, so this is a loop over open buffers that does plain writes.
3. Restore the terminal (leave the alternate screen, show the cursor, reset the modes) before the process ends, so that
   a trap does not leave the user's shell unusable.

## Cost and alternatives

The hook is a function pointer read by the runtime's trap path (rt.c); nothing on the normal path changes. An alternative
without language support is a signal handler for SIGABRT/SIGSEGV written in C in the runtime; m3 cannot ship C (decision
D2: m31 only), which is why the request is for the runtime.
