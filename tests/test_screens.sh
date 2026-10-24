# sourced by tests/test.sh: the golden screens.
#
#   screen_pty.py   49 scripted scenarios on the real binary in a pty, fed to the pyte emulator; text, cell styles,
#                   cursor and byte counts are compared with tests/golden/screens.json, which was recorded from
#                   m3 0.15.0 before the core/plugins reorganisation (docs/CORE-AND-PLUGINS.md 7.5). The default build
#                   must reproduce it exactly. Re-record only for a change that is meant to alter the screens:
#                   python3 tests/screen_pty.py ./m3 --record
if [ ! -x "$WORK/m3" ]; then
    build m3 m3.m31
fi
if [ -x "$WORK/m3" ]; then
    if out=$(python3 tests/screen_pty.py "$WORK/m3" --raw --scratch "$WORK/screens" 2>&1); then
        note "screen_pty: $(printf '%s\n' "$out" | tail -1)"
    else
        bad "screen_pty" "$(printf '%s\n' "$out" | tail -25)"
    fi
fi
