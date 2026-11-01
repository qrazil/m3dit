# sourced by tests/test.sh after test_entry.sh: m3's command line. Every option
# in its long and short (--k) forms, Oro's refusals and their exit status,
# the deprecated -u, -v and -h, the generated --help, --version and --completions, and
# (through a pty, because the editor needs a terminal) that --no-mouse and
# M3_NO_MOUSE really leave the mouse alone and that -u / --keymap really read
# the keymap file. The grammar is m31's docs/cli-conventions.md.
#
# macOS-safe: bash 3.2, BSD tools, mktemp, no GNU timeout.
if [ ! -x "$WORK/m3" ]; then
    build m3 m3.m31
fi
if [ -x "$WORK/m3" ]; then
    cli_dir=$WORK/cli
    mkdir -p "$cli_dir"
    # m3_run ARGS... -> $out $err $code (standard input /dev/null: no terminal, so
    # only the paths that end before the editor starts are reachable)
    m3_run() {
        "$WORK/m3" "$@" >"$cli_dir/out" 2>"$cli_dir/err" </dev/null
        code=$?
        out=$(cat "$cli_dir/out")
        err=$(cat "$cli_dir/err")
    }
    m3_expect() {
        local label=$1 want=$2 so=${3:-} se=${4:-}
        if [ "$code" != "$want" ]; then
            bad "m3 $label" "exit $code, want $want" "stdout: $out" "stderr: $err"
        elif [ -n "$so" ] && [[ "$out" != *"$so"* ]]; then
            bad "m3 $label" "stdout lacks: $so" "stdout: $out"
        elif [ -n "$se" ] && [[ "$err" != *"$se"* ]]; then
            bad "m3 $label" "stderr lacks: $se" "stderr: $err"
        else
            note "m3 $label"
        fi
    }
    version=$(grep '^version ' deps | awk '{print $2}')

    m3_run --help;       m3_expect "--help" 0 "usage: m3 [options] [<FILE>...]"
    for want in "--k, --keymap FILE|NONE" "--theme NAME" "--colors DEPTH" "--dump-sample" "--no-mouse" "--version" "--completions SHELL" "exit status:" "[<FILE>...]"; do
        m3_run --help
        if [[ "$out" == *"$want"* ]]; then note "m3 --help lists: $want"; else bad "m3 --help lacks: $want" "${out:0:300}"; fi
    done
    m3_run --version;    m3_expect "--version" 0 "m3 $version"
    m3_run -v;           m3_expect "-v still prints the version (deprecated)" 0 "m3 $version" "warning: '-v' is deprecated, use '--version'"
    m3_run -h;           m3_expect "-h still prints the help (deprecated)" 0 "usage: m3" "warning: '-h' is deprecated, use '--help'"
    m3_run --completions bash; m3_expect "--completions bash" 0 "complete -o filenames -F _m3_complete m3"
    if printf '%s\n' "$out" | bash -n 2>"$cli_dir/syntax"; then note "m3 --completions bash is valid bash"; else bad "m3 bash completion syntax" "$(cat "$cli_dir/syntax")"; fi
    m3_run --completions fish; m3_expect "--completions fish" 0 "complete -c m3 -l keymap"
    m3_run --completions zsh;  m3_expect "--completions zsh" 0 "#compdef m3"

    m3_run --bogus;      m3_expect "unknown option" 2 "" "m3: unknown option '--bogus'"
    m3_run --no-mous;    m3_expect "typo suggests" 2 "" "did you mean '--no-mouse'?"
    m3_run -bogus;       m3_expect "-word is a command, and there are none" 2 "" "takes no commands, and got '-bogus'"
    m3_run --keymap;     m3_expect "--keymap at the end" 2 "" "'--keymap' needs a value and is the last argument"
    m3_run --keymap --no-mouse; m3_expect "--keymap does not eat an option" 2 "" "starts with a dash"
    m3_run --no-mouse=0; m3_expect "a flag takes no value" 2 "" "is a flag and takes no value"
    m3_run --;           m3_expect "a lone -- is refused" 2 "" "'--' has no meaning here"
    m3_run --clean --help; m3_expect "--clean is accepted" 0 "--clean"
    m3_run --h;          m3_expect "--h is refused" 2 "" "help has one spelling"
    m3_run --colors 8 --dump-sample; m3_expect "a bad --colors" 2 "" "'--colors' needs 16, 256 or true"
    [ "$(printf '%s\n' "$err" | wc -l | tr -d ' ')" -ge 2 ] && note "m3 usage errors carry the usage line" || bad "m3 usage error shape" "$err"
    m3_run file.txt;     m3_expect "no terminal is exit 1, not a usage error" 1 "" "needs a terminal"
    m3_run ./-odd.txt;   m3_expect "a file called -odd.txt is passed as ./-odd.txt" 1 "" "needs a terminal"
    m3_run --keymap NONE --no-mouse --theme tokyonight --dump-sample --colors 16; m3_expect "--dump-sample with every option" 0

    # -u / --keymap, --no-mouse, M3_NO_MOUSE: through a real terminal
    printf 'nnoremap Q :q<CR>\n' >"$cli_dir/keymap.vim"
    if out=$(python3 - "$WORK/m3" "$cli_dir" <<'PY' 2>&1
import os, pty, select, struct, subprocess, sys, termios, fcntl, time
binary, work = sys.argv[1], sys.argv[2]
MOUSE_ON = b"\x1b[?1000h"

def session(args, extra_env, quit_keys):
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
    env = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor", HOME=work, XDG_STATE_HOME=work, XDG_CONFIG_HOME=work)
    env.pop("M3_NO_MOUSE", None)
    env.pop("M3_KEYMAP", None)
    env.update(extra_env)
    proc = subprocess.Popen([binary] + args, stdin=slave, stdout=slave, stderr=slave,
                            env=env, start_new_session=True, close_fds=True)
    os.close(slave)
    got = b""
    def pump(seconds):
        nonlocal got
        end = time.time() + seconds
        while time.time() < end:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    got += os.read(master, 65536)
                except OSError:
                    return
    pump(1.5)
    os.write(master, quit_keys)
    deadline = time.time() + 10
    code = None
    while time.time() < deadline:
        pump(0.1)
        code = proc.poll()
        if code is not None:
            break
    if code is None:
        proc.kill()
        proc.wait()
    return got, code

def check(label, ok, detail=""):
    if not ok:
        print("FAILED: " + label + " " + detail)
        sys.exit(1)

got, code = session(["--keymap", "NONE"], {}, b":q\r")
check("default asks for mouse reports", MOUSE_ON in got and code == 0, "code=%r" % (code,))
got, code = session(["--keymap", "NONE", "--no-mouse"], {}, b":q\r")
check("--no-mouse leaves the mouse alone", MOUSE_ON not in got and code == 0, "code=%r" % (code,))
got, code = session(["--k", "NONE", "--no-mouse"], {}, b":q\r")
check("--k NONE is --keymap NONE", MOUSE_ON not in got and code == 0, "code=%r" % (code,))
got, code = session(["--keymap", "NONE"], {"M3_NO_MOUSE": "1"}, b":q\r")
check("M3_NO_MOUSE=1 leaves the mouse alone", MOUSE_ON not in got and code == 0, "code=%r" % (code,))
got, code = session(["-u", "NONE", "--no-mouse"], {}, b":q\r")
check("-u (vim's letter, deprecated) still works", MOUSE_ON not in got and code == 0, "code=%r" % (code,))
keymap = os.path.join(work, "keymap.vim")
for spelling in (["-u", keymap], ["--k", keymap], ["--keymap", keymap], ["--keymap=" + keymap]):
    got, code = session(spelling, {}, b"Q")
    check("%s maps Q to :q" % " ".join(spelling), code == 0, "code=%r" % (code,))
got, code = session(["--keymap", "NONE"], {}, b"Q")
check("without the keymap file Q does not quit", code is None, "code=%r" % (code,))
print("ok")
PY
    ); then
        note "m3 pty: -u / --keymap, --no-mouse, --mouse, M3_NO_MOUSE"
    else
        bad "m3 pty command line" "$out"
    fi
fi


# --- install.sh ----------------------------------------------------------------
install_run() {
    sh install.sh "$@" >"$WORK/out" 2>"$WORK/err" </dev/null
    code=$?
    out=$(cat "$WORK/out")
    err=$(cat "$WORK/err")
}
install_expect() {
    local label=$1 want=$2 so=${3:-} se=${4:-}
    if [ "$code" != "$want" ]; then
        bad "$label" "exit $code, want $want" "stdout: ${out:0:300}" "stderr: ${err:0:300}"
    elif [ -n "$so" ] && [[ "$out" != *"$so"* ]]; then
        bad "$label" "stdout lacks: $so" "stdout: ${out:0:300}"
    elif [ -n "$se" ] && [[ "$err" != *"$se"* ]]; then
        bad "$label" "stderr lacks: $se" "stderr: ${err:0:300}"
    else
        note "$label"
    fi
}
install_run --help; install_expect "install.sh --help" 0 "usage: sh install.sh [options] [-uninstall]"
install_run --version; install_expect "install.sh --version" 0 "installer"
install_run -h;     install_expect "install.sh: -h is refused" 2 "" "write '--help'"
install_run help;   install_expect "install.sh: help is refused" 2 "" "write '--help'"
install_run --;     install_expect "install.sh: a lone -- is refused" 2 "" "'--' has no meaning here"
install_run --prefx /x; install_expect "install.sh: typo suggests" 2 "" "did you mean '--prefix'?"
install_run -unistall;  install_expect "install.sh: a mistyped command is suggested" 2 "" "did you mean '-uninstall'?"
install_run --libc foo; install_expect "install.sh: bad --libc" 2 "" "needs gnu or musl, and got 'foo'"
install_run --prefix;   install_expect "install.sh: --prefix at the end" 2 "" "needs a value and is the last argument"
install_run extra;  install_expect "install.sh: an operand" 2 "" "unexpected argument 'extra'"
for spelling in "-uninstall --prefix $WORK/i1" "-u --prefix=$WORK/i2" "-u --p $WORK/i3"; do
    # shellcheck disable=SC2086
    install_run $spelling
    install_expect "install.sh $(printf '%s' "$spelling" | sed "s#$WORK#.#g")" 0 "removed"
done
install_run --uninstall --prefix "$WORK/i4"; install_expect "install.sh --uninstall (the old spelling) works and warns" 0 "removed" "deprecated"
