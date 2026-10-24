# sourced by tests/test.sh: the real binary (m3.m31, the entry file no unit
# program compiles), its --version and --help, and a pty smoke test: start it,
# type `:q`, expect a clean exit.
if build m3 m3.m31; then
    version=$(grep '^version ' deps | awk '{print $2}')
    built_in=$(bash scripts/plugins.sh resolve 2>/dev/null | tr '\n' ' ' | sed 's/ $//')
    [ -n "$built_in" ] || built_in=none
    if out=$("$WORK/m3" --version 2>&1) && [ "$out" = "m3 $version (api 0.2.0; plugins: $built_in)" ]; then
        note "m3 --version: $out"
    else
        bad "m3 --version (want 'm3 $version (api 0.2.0; plugins: $built_in)')" "$out"
    fi
    if out=$("$WORK/m3" --help 2>&1) && printf '%s' "$out" | grep -q '^usage: m3'; then
        note "m3 --help"
    else
        bad "m3 --help" "$out"
    fi
    # --dump-sample needs no terminal: a theme drawn as ANSI text at the depth asked for
    if out=$("$WORK/m3" --theme tokyonight --colors true --dump-sample 2>&1 </dev/null) \
        && case "$out" in *'== theme tokyonight =='*'38;2;'*) true ;; *) false ;; esac; then
        note "m3 --dump-sample (truecolor)"
    else
        bad "m3 --dump-sample (truecolor)" "$(printf '%s' "$out" | head -5)"
    fi
    if out=$("$WORK/m3" --theme default --colors 16 --dump-sample 2>&1 </dev/null) && case "$out" in *'38;2;'*|*'38;5;'*) false ;; *) true ;; esac; then
        note "m3 --dump-sample (16 colours has no 24-bit or 256-colour escape)"
    else
        bad "m3 --dump-sample (16 colours)" "$(printf '%s' "$out" | head -5)"
    fi
    if out=$("$WORK/m3" --theme nonesuch --dump-sample 2>&1 </dev/null) && case "$out" in *'cannot load: unknown theme'*) true ;; *) false ;; esac; then
        note "m3 --dump-sample (unknown theme says so)"
    else
        bad "m3 --dump-sample (unknown theme)" "$(printf '%s' "$out" | head -5)"
    fi
    if out=$(python3 - "$WORK/m3" <<'PY' 2>&1
import os, pty, select, struct, subprocess, sys, termios, fcntl, time
binary = sys.argv[1]
master, slave = pty.openpty()
fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
env = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor")
proc = subprocess.Popen([binary, "-u", "NONE"], stdin=slave, stdout=slave, stderr=slave,
                        env=env, start_new_session=True, close_fds=True)
os.close(slave)
def pump(seconds):
    end = time.time() + seconds
    got = b""
    while time.time() < end:
        ready, _, _ = select.select([master], [], [], 0.1)
        if ready:
            try:
                got += os.read(master, 65536)
            except OSError:
                break
    return got
first = pump(1.5)
if not first:
    print("no output from the editor")
    proc.kill()
    sys.exit(1)
os.write(master, b":q\r")
deadline = time.time() + 10
code = None
while time.time() < deadline:
    pump(0.1)
    code = proc.poll()
    if code is not None:
        break
if code is None:
    proc.kill()
    print("did not exit after :q")
    sys.exit(1)
if code != 0:
    print("exit status %d" % code)
    sys.exit(1)
print("started, drew %d bytes, :q exited 0" % len(first))
PY
    ); then
        note "m3 pty smoke: $out"
    else
        bad "m3 pty smoke" "$out"
    fi
    if out=$(python3 tests/e2e.py "$WORK/m3" 2>&1); then
        note "m3 pty e2e: $(printf '%s\n' "$out" | tail -1)"
    else
        bad "m3 pty e2e" "$(printf '%s\n' "$out" | tail -15)"
    fi
fi
