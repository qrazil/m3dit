# sourced by tests/test.sh: the in-process git (m31git) against real `git`.
#
#   t_gitlib                unit checks of the pure parts (listed in test_units.sh)
#   oracles/oracle_git.py   the library-backed reads (gutter base, blame, log, log -L, show, diff), the hunk
#                           commands on twin repositories (m3 in one copy, `git add|restore|reset -p` in the
#                           other, then index, work tree, refs and status compared, fsck clean), a linked
#                           worktree, a SHA-256 repository, a version 4 index (the fallback to `git`), and the
#                           100,000-line timing check
if ! command -v git >/dev/null 2>&1 || ! command -v python3 >/dev/null 2>&1; then
    echo "skip git oracle: git or python3 not found"
elif build t_gitlib_run tests/t_gitlib_run.m31; then
    if out=$(python3 tests/oracles/oracle_git.py --runner "$WORK/t_gitlib_run" 2>&1); then
        note "oracle_git: $(printf '%s\n' "$out" | tail -1)"
        printf '%s\n' "$out" | grep '^timing:' | sed 's/^/     /'
    else
        bad "oracle_git" "$(printf '%s\n' "$out" | tail -25)"
    fi
fi
# the same commands in the real binary, in a pty (needs pyte; skips cleanly without it)
if [ ! -x "$WORK/m3" ]; then
    build m3 m3.m31
fi
if [ -x "$WORK/m3" ] && command -v git >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
    if out=$(python3 tests/git_pty.py "$WORK/m3" 2>&1); then
        note "git_pty: $(printf '%s\n' "$out" | tail -1)"
    else
        bad "git_pty" "$(printf '%s\n' "$out" | tail -25)"
    fi
fi
