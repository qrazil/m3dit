# sourced by tests/test.sh: differential tests against `nvim --headless`
# (skipped with a note when nvim is not installed).

oracle_run() {   # NAME SOURCE ARGS... : build SOURCE, run python oracle with --runner
    local name=$1 src=$2
    shift 2
    build "$name" "$src" || return
    local out
    if out=$("$@" --runner "$WORK/$name" 2>&1); then
        note "$name: $(printf '%s\n' "$out" | tail -1)"
    else
        bad "$name" "$(printf '%s\n' "$out" | tail -25)"
    fi
}

if ! command -v nvim >/dev/null 2>&1; then
    echo "skip engine and regex oracles: nvim not found"
else
    oracle_run t_oracle_run tests/t_oracle_run.m31 python3 tests/oracles/oracle_nvim.py --corpus
    oracle_run t_regex_run tests/t_regex_run.m31 python3 tests/oracles/oracle_regex.py --corpus
    for seed in 1 2 3; do
        oracle_run t_regex_run tests/t_regex_run.m31 python3 tests/oracles/oracle_regex.py --fuzz --seed "$seed" --cases 2000
    done
    # snippets: expansion, tabstops, mirrors and Select mode against nvim's vim.snippet
    oracle_run t_snippet_run tests/t_snippet_run.m31 python3 tests/oracles/oracle_snippet.py
    # window layouts: :split, CTRL-W commands, :resize, tab pages, terminal size
    oracle_run t_split_run tests/t_split_run.m31 python3 tests/oracles/oracle_windows.py
    oracle_run t_split_run tests/t_split_run.m31 python3 tests/oracles/oracle_windows.py --fuzz 150 --seed 1
fi
