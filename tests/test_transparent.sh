# sourced by tests/test.sh: transparency (docs/TRANSPARENCY.md).
#
#   t_theme (in test_units.sh)   the style resolver, the theme key, the option, `:set transparent`, the dumps
#   golden dumps                 `--dump-sample` of every built-in theme at 16, 256 and 24 bits writes the bytes
#                                0.15.0 wrote (tests/golden/dump_sample_0.15.0.txt, sha256): the default mode did
#                                not change
#   transparent_pty.py           the pty property: with `:set transparent`, in every theme, no surface paints a
#                                background but the interactive highlights (pyte, every frame), and under
#                                `nobg-NAME` themes the byte stream has no background colour at all; the default
#                                mode is what it was after set / unset; skips cleanly when pyte is missing
if [ ! -x "$WORK/m3" ]; then
    build m3 m3.m31
fi
if [ -x "$WORK/m3" ]; then
    if command -v sha256sum >/dev/null 2>&1; then
        sha256_of() { sha256sum | cut -d' ' -f1; }
    else
        sha256_of() { shasum -a 256 | cut -d' ' -f1; }
    fi
    golden_bad=""
    golden_count=0
    while read -r gtheme gdepth ghash; do
        [ -n "$gtheme" ] || continue
        got=$(HOME="$WORK" XDG_CONFIG_HOME="$WORK/none" M3_TRANSPARENT= "$WORK/m3" --theme "$gtheme" --colors "$gdepth" --dump-sample 2>/dev/null | sha256_of)
        golden_count=$((golden_count + 1))
        [ "$got" = "$ghash" ] || golden_bad="$golden_bad $gtheme/$gdepth"
    done < tests/golden/dump_sample_0.15.0.txt
    if [ -z "$golden_bad" ]; then
        note "default mode unchanged: $golden_count dumps equal 0.15.0's"
    else
        bad "default-mode dump differs from 0.15.0" "$golden_bad"
    fi
    if out=$(python3 tests/transparent_pty.py "$WORK/m3" 2>&1); then
        note "transparent_pty: $(printf '%s\n' "$out" | tail -1)"
    else
        bad "transparent_pty" "$(printf '%s\n' "$out" | tail -25)"
    fi
fi
