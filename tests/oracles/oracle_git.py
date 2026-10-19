#!/usr/bin/env python3
"""Differential oracle for the in-process git: m3 over the m31git library against real `git`.

    python3 tests/oracles/oracle_git.py --runner BIN [-v] [--no-timing]

BIN is tests/t_gitlib_run.m31 built. Every check builds repositories with `git` itself and compares what
the library-backed code answers with what `git` answers:

  * the gutter's base (index, else HEAD), untracked files, a linked worktree, a SHA-256 repository, an
    index the library cannot read (version 4: the editor must fall back to `git`, same answer);
  * blame (`git blame --porcelain`), file history (`git log -- FILE`), line-range history (`git log -L`),
    `show`, and `diff` (working tree, `--cached`, `HEAD`) texts;
  * hunk commands on twin repositories: the same operation done by m3 (`:Hunk stage|reset|undo`, `dih`,
    `dah`) in one copy and by git (`git add -p`, `git restore -p`, `git reset -p` with zero context, answering for that one hunk) in the other; afterwards the index (`ls-files -s`), `status`, the work tree files, the
    refs and `diff --cached` must be equal and `fsck` clean.

macOS-safe: temp roots are resolved with realpath and handed to children as cwd and PWD, git is fenced off
with GIT_CEILING_DIRECTORIES and told to read no user or system configuration, no GNU-only tools, git 2.49
and 2.55 both work (nothing here depends on output that changed between them).
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time

VERBOSE = False
FAILURES = []
CHECKS = 0


def check(label, ok, detail=""):
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILURES.append(label)
        print("FAIL %s %s" % (label, detail))
    elif VERBOSE:
        print("ok   %s" % label)


class Env:
    def __init__(self, root):
        self.root = root
        self.tick = 1700000000

    def env(self, cwd):
        self.tick += 60
        stamp = "%d +0000" % self.tick
        return dict(os.environ, PWD=cwd, HOME=self.root, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                    GIT_CEILING_DIRECTORIES=os.path.dirname(self.root), GIT_AUTHOR_NAME="A U Thor",
                    GIT_AUTHOR_EMAIL="author@example.com", GIT_COMMITTER_NAME="C O Mitter",
                    GIT_COMMITTER_EMAIL="committer@example.com", GIT_AUTHOR_DATE=stamp,
                    GIT_COMMITTER_DATE=stamp, LC_ALL="C.UTF-8", GIT_PAGER="cat", GIT_TERMINAL_PROMPT="0")


ENV = None


def git(repo, *args, stdin=None, check_ok=True):
    proc = subprocess.run(["git"] + list(args), cwd=repo, env=ENV.env(repo), input=stdin,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check_ok and proc.returncode != 0:
        raise RuntimeError("git %s failed in %s: %s" % (" ".join(args), repo, proc.stderr.decode(errors="replace")))
    return proc.stdout.decode("utf-8", errors="replace") if proc.returncode == 0 else ""


def run(binary, repo, *args, timeout=120):
    proc = subprocess.run([binary] + list(args), cwd=repo, env=ENV.env(repo), stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=timeout)
    out = {}
    for line in proc.stdout.decode("utf-8", errors="replace").split("\n"):
        if "\t" in line or line in ("NONE",):
            tag, _, rest = line.partition("\t")
            out.setdefault(tag, []).append(rest)
    out["_code"] = proc.returncode
    out["_err"] = proc.stderr.decode("utf-8", errors="replace")
    return out


def write(repo, name, text):
    path = os.path.join(repo, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(text.encode())


def lines_of(text):
    parts = text.split("\n")
    if parts and parts[-1] == "":
        parts.pop()
    return parts


def new_repo(extra=()):
    path = os.path.join(ENV.root, "repo%d" % len(os.listdir(ENV.root)))
    os.makedirs(path)
    git(path, "init", "-q", "-b", "main", *extra)
    return path


def numbered(count, prefix="line"):
    return "".join("%s %d\n" % (prefix, n) for n in range(1, count + 1))


def history_repo(extra=()):
    """f.txt edited over several commits, a side branch merged, a second file, one in a directory."""
    repo = new_repo(extra)
    write(repo, "f.txt", numbered(30))
    write(repo, "other.txt", "o1\no2\n")
    write(repo, "sub/g.txt", "g1\ng2\ng3\n")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "first")
    text = lines_of(numbered(30))
    text[4] = "five changed"
    text.insert(10, "inserted after ten")
    write(repo, "f.txt", "\n".join(text) + "\n")
    git(repo, "commit", "-q", "-am", "second: change five, insert")
    write(repo, "other.txt", "o1\no2\no3\n")
    git(repo, "commit", "-q", "-am", "third: other only")
    git(repo, "checkout", "-q", "-b", "side")
    text = lines_of(open(os.path.join(repo, "f.txt")).read())
    text[20] = "side twenty-one"
    write(repo, "f.txt", "\n".join(text) + "\n")
    git(repo, "commit", "-q", "-am", "side: change 21")
    git(repo, "checkout", "-q", "main")
    text = lines_of(open(os.path.join(repo, "f.txt")).read())
    del text[1:3]
    text.append("tail line")
    write(repo, "f.txt", "\n".join(text) + "\n")
    git(repo, "commit", "-q", "-am", "main: drop 2 and 3, add a tail")
    git(repo, "merge", "-q", "--no-edit", "side")
    text = lines_of(open(os.path.join(repo, "f.txt")).read())
    text[5] = "six rewritten"
    write(repo, "f.txt", "\n".join(text) + "\n")
    git(repo, "commit", "-q", "-am", "last: rewrite six")
    return repo


# ------------------------------------------------------------------ reads

def blame_oracle(repo, name):
    out = git(repo, "blame", "--porcelain", "--", name)
    ids = []
    for line in out.split("\n"):
        parts = line.split(" ")
        if len(parts[0]) in (40, 64) and all(c in "0123456789abcdef" for c in parts[0]) and len(parts) >= 3:
            ids.append(parts[0])
    return ids


def diff_text(output):
    return [line for line in output.split("\n")][:-1] if output.endswith("\n") else output.split("\n")


def reads(binary, repo, tag):
    # the base: index, else HEAD
    ref = lines_of(git(repo, "show", ":./f.txt"))
    got = run(binary, repo, "libbase", "f.txt")
    check(tag + " base from the index", got.get("LINE", []) == ref, "%r" % got.get("_err"))
    check(tag + " base with the fallback", run(binary, repo, "base", "f.txt").get("LINE", []) == ref)
    write(repo, "untracked.txt", "x\n")
    check(tag + " untracked file", "UNTRACKED" in run(binary, repo, "libbase", "untracked.txt"))
    check(tag + " untracked file, editor path", "NONE" in run(binary, repo, "base", "untracked.txt"))
    check(tag + " file in a directory", run(binary, repo, "libbase", "sub/g.txt").get("LINE") == ["g1", "g2", "g3"])
    # blame
    want = blame_oracle(repo, "f.txt")
    got = run(binary, repo, "blame", "f.txt").get("COMMIT", [])
    check(tag + " blame, every line", got == want, "got %d lines, git %d; first difference %r" % (
        len(got), len(want), next(((i, a, b) for i, (a, b) in enumerate(zip(got, want)) if a != b), None)))
    check(tag + " blame in a directory", run(binary, repo, "blame", "sub/g.txt").get("COMMIT", []) == blame_oracle(repo, "sub/g.txt"))
    # history
    want = git(repo, "log", "--format=%H", "--", "f.txt").split()
    check(tag + " file history", run(binary, repo, "log", "f.txt").get("COMMIT", []) == want)
    want = git(repo, "log", "--format=%H", "--", "other.txt").split()
    check(tag + " other file history", run(binary, repo, "log", "other.txt").get("COMMIT", []) == want)
    for first, last in ((1, 3), (5, 7), (6, 6), (10, 14), (18, 24), (28, 31), (1, 36)):
        proc = subprocess.run(["git", "log", "--first-parent", "-L", "%d,%d:f.txt" % (first, last), "-s", "--format=%H"], cwd=repo,
                              env=ENV.env(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            continue
        want = [line for line in proc.stdout.decode().split() if len(line) in (40, 64)]
        got = run(binary, repo, "log", "f.txt", str(first), str(last)).get("COMMIT", [])
        check(tag + " log -L %d,%d" % (first, last), got == want, "got %r want %r" % (got, want))
    # show and diff
    head = git(repo, "rev-parse", "HEAD").strip()
    for rev in ("HEAD", "HEAD~1", "HEAD~2", "HEAD~4"):
        parents = git(repo, "rev-list", "--parents", "-n", "1", rev).split()
        if len(parents) > 2:
            continue   # a merge: git shows a combined diff, the library the first-parent diff
        want = lines_of(git(repo, "show", "--format=", "--patch", rev))
        got = run(binary, repo, "show", rev).get("LINE", [])
        cut = next((i for i, line in enumerate(got) if line.startswith("diff --git")), len(got))
        check(tag + " show " + rev, got[cut:] == want, "first difference %r" % str(
            next(((i, a, b) for i, (a, b) in enumerate(zip(got[cut:], want)) if a != b), (len(got) - cut, len(want)))))
    got = run(binary, repo, "show", "HEAD").get("LINE", [])
    check(tag + " show header", got[0] == "commit " + head and got[1].startswith("Merge:") or got[1].startswith("Author:"))
    # a working tree with every kind of change
    text = lines_of(open(os.path.join(repo, "f.txt")).read())
    text[2] = "worktree change"
    write(repo, "f.txt", "\n".join(text) + "\n")
    git(repo, "add", "f.txt")
    text[9] = "second, unstaged"
    text.append("appended unstaged")
    write(repo, "f.txt", "\n".join(text) + "\n")
    write(repo, "staged_new.txt", "n1\nn2\n")
    git(repo, "add", "staged_new.txt")
    os.remove(os.path.join(repo, "other.txt"))
    write(repo, "sub/g.txt", "g1\nG2\ng3\n")
    for what, args in (("working", ["diff"]), ("index", ["diff", "--cached"]), ("head", ["diff", "HEAD"])):
        want = lines_of(git(repo, *args))
        got = run(binary, repo, "diff", what).get("LINE", [])
        check(tag + " diff " + what, got == want, "first difference %r" % str(
            next(((i, a, b) for i, (a, b) in enumerate(zip(got, want)) if a != b), (len(got), len(want)))))
    git(repo, "checkout", "-q", "--", ".")
    git(repo, "reset", "-q", "--hard")
    os.remove(os.path.join(repo, "untracked.txt"))


# ------------------------------------------------------------------ hunks

def u0_hunks(repo, name, cached=False):
    """(header text, new start, new count, old start, old count, body) for every hunk of git's -U0 diff."""
    args = ["diff", "-U0", "--no-color"] + (["--cached"] if cached else []) + ["--", name]
    out = git(repo, *args)
    if not out:
        return None
    lines = out.split("\n")
    at = next(i for i, line in enumerate(lines) if line.startswith("@@"))
    header = "\n".join(lines[:at]) + "\n"
    hunks = []
    current = None
    for line in lines[at:]:
        if line.startswith("@@"):
            if current:
                hunks.append(current)
            spec = line.split(" ")
            old = spec[1][1:].split(",")
            new = spec[2][1:].split(",")
            current = {"head": line, "old": (int(old[0]), int(old[1]) if len(old) > 1 else 1),
                       "new": (int(new[0]), int(new[1]) if len(new) > 1 else 1), "body": []}
        elif current is not None and (line == "" and False):
            pass
        elif current is not None:
            current["body"].append(line)
    if current:
        hunks.append(current)
    for hunk in hunks:
        while hunk["body"] and hunk["body"][-1] == "":
            hunk["body"].pop()
    return header, hunks


def hunk_patch(header, hunk):
    return (header + hunk["head"] + "\n" + "\n".join(hunk["body"]) + "\n").encode()


def interactive(repo, args, number):
    """`git add|restore|reset -p`, splitting every hunk as far as git can (`s`), taking sub-hunk `number`
    (0-based, the same hunks `diff -U0` shows) and no other. Prompts are read until `]? ` and answered one at
    a time, so nothing depends on how many prompts a git version prints."""
    import select
    proc = subprocess.Popen(["git"] + list(args), cwd=repo, env=ENV.env(repo), stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    seen = b""
    decided = 0
    finished = False
    deadline = time.time() + 60
    try:
        while time.time() < deadline:
            ready, _, _ = select.select([proc.stdout], [], [], 0.2)
            if ready:
                chunk = os.read(proc.stdout.fileno(), 65536)
                if not chunk:
                    break
                seen += chunk
            if seen.endswith(b"]? "):
                prompt = seen[seen.rfind(b"\n") + 1:].decode(errors="replace")
                seen = b""
                options = prompt[prompt.rfind("[") + 1:prompt.rfind("]")].split(",")
                if "s" in options:
                    answer = "s"
                elif finished:
                    answer = "q"
                elif decided == number:
                    answer = "y"
                    decided += 1
                    finished = True
                else:
                    answer = "n"
                    decided += 1
                proc.stdin.write((answer + "\n").encode())
                proc.stdin.flush()
            elif proc.poll() is not None and not ready:
                break
        proc.stdin.close()
    except (BrokenPipeError, OSError):
        pass
    proc.wait(timeout=30)


def snapshot(repo):
    files = {}
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for filename in filenames:
            full = os.path.join(dirpath, filename)
            with open(full, "rb") as handle:
                files[os.path.relpath(full, repo)] = handle.read()
    return {"index": git(repo, "ls-files", "-s"), "status": git(repo, "status", "--porcelain"),
            "refs": git(repo, "for-each-ref") + git(repo, "rev-parse", "HEAD"), "files": files,
            "cached": git(repo, "diff", "--cached"), "diff": git(repo, "diff")}


def same(label, left, right):
    for key in ("index", "status", "refs", "files", "cached", "diff"):
        check("%s: %s" % (label, key), left[key] == right[key],
              "\n--- m3 ---\n%s\n--- git ---\n%s" % (left[key], right[key]) if key != "files" else "")


def clone(repo):
    target = os.path.join(ENV.root, "twin%d" % len(os.listdir(ENV.root)))
    shutil.copytree(repo, target, symlinks=True)
    return target


def fsck_ok(label, repo):
    proc = subprocess.run(["git", "fsck", "--strict", "--no-dangling"], cwd=repo, env=ENV.env(repo),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    check(label + " fsck", proc.returncode == 0, proc.stderr.decode()[:300])


def row_for(hunk):
    """The 1-based line to put the cursor on for a hunk of `diff -U0` (the new side)."""
    start, count = hunk["new"]
    if count == 0:
        return max(start, 1)
    return start


def hunk_twin(binary, base_repo, label, name, edit, cached_edit=None, extra_ops=("stage", "reset")):
    """Build `base_repo` + edit as a work tree, then do every hunk with m3 in one copy and git in another."""
    probe = clone(base_repo)
    if cached_edit:
        cached_edit(probe)
        git(probe, "add", "-A")
    edit(probe)
    found = u0_hunks(probe, name)
    shutil.rmtree(probe)
    if found is None:
        check(label + " has hunks", False)
        return
    header, hunks = found
    for number in range(len(hunks)):
        for op in extra_ops:
            mine = clone(base_repo)
            theirs = clone(base_repo)
            for repo in (mine, theirs):
                if cached_edit:
                    cached_edit(repo)
                    git(repo, "add", "-A")
                edit(repo)
            _, hunks_here = u0_hunks(mine, name)
            row = row_for(hunks_here[number])
            full = os.path.join(mine, name)
            if op == "stage":
                got = run(binary, mine, "app", full, ":%d\r:Hunk stage\r" % row)
                interactive(theirs, ["add", "-p", "--", name], number)
            else:
                got = run(binary, mine, "app", full, ":%d\r:Hunk reset\r:w\r" % row)
                interactive(theirs, ["restore", "-p", "--", name], number)
            check("%s %s hunk %d notice" % (label, op, number + 1), got["_code"] == 0, got["_err"])
            same("%s %s hunk %d" % (label, op, number + 1), snapshot(mine), snapshot(theirs))
            if op == "stage":
                fsck_ok("%s %s hunk %d" % (label, op, number + 1), mine)
            shutil.rmtree(mine)
            shutil.rmtree(theirs)


def undo_twin(binary, base_repo, label, name, staged_edit):
    probe = clone(base_repo)
    staged_edit(probe)
    git(probe, "add", name)
    found = u0_hunks(probe, name, cached=True)
    shutil.rmtree(probe)
    header, hunks = found
    for number in range(len(hunks)):
        mine = clone(base_repo)
        theirs = clone(base_repo)
        for repo in (mine, theirs):
            staged_edit(repo)
            git(repo, "add", name)
        _, hunks_here = u0_hunks(mine, name, cached=True)
        row = row_for(hunks_here[number])
        got = run(binary, mine, "app", os.path.join(mine, name), ":%d\r:Hunk undo\r" % row)
        interactive(theirs, ["reset", "-p", "--", name], number)
        check("%s undo hunk %d ran" % (label, number + 1), got["_code"] == 0, got["_err"])
        same("%s undo hunk %d" % (label, number + 1), snapshot(mine), snapshot(theirs))
        fsck_ok("%s undo hunk %d" % (label, number + 1), mine)
        shutil.rmtree(mine)
        shutil.rmtree(theirs)


def text_objects(binary, base_repo, name, edit):
    probe = clone(base_repo)
    edit(probe)
    header, hunks = u0_hunks(probe, name)
    before = lines_of(open(os.path.join(probe, name)).read())
    shutil.rmtree(probe)
    for number, hunk in enumerate(hunks):
        start, count = hunk["new"]
        if count == 0:
            continue
        for obj in ("ih", "ah"):
            mine = clone(base_repo)
            edit(mine)
            got = run(binary, mine, "app", os.path.join(mine, name), ":%d\rd%s:w\r" % (start, obj))
            after = lines_of(open(os.path.join(mine, name)).read())
            stop = start - 1 + count
            if obj == "ah":
                while stop < len(before) and before[stop].strip() == "":
                    stop += 1
            want = before[:start - 1] + before[stop:]
            check("text object d%s on hunk %d" % (obj, number + 1), after == want and got["_code"] == 0,
                  "got %r want %r" % (after[:12], want[:12]))
            shutil.rmtree(mine)
    # `ih` away from any hunk, and the object on a removal-only hunk, do nothing
    mine = clone(base_repo)
    edit(mine)
    run(binary, mine, "app", os.path.join(mine, name), ":1\rdih:w\r")
    check("dih outside a hunk changes nothing", lines_of(open(os.path.join(mine, name)).read()) == before or
          any(h["new"][0] == 1 and h["new"][1] > 0 for h in hunks))
    shutil.rmtree(mine)


def hunks_section(binary):
    repo = new_repo()
    write(repo, "f.txt", numbered(40))
    write(repo, "keep.txt", "k\n")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "base")

    def lines(repo_path):
        return lines_of(open(os.path.join(repo_path, "f.txt")).read())

    def save(repo_path, rows):
        write(repo_path, "f.txt", "\n".join(rows) + "\n")

    def mixed(repo_path):
        rows = lines(repo_path)
        rows[2] = "three changed"
        del rows[9:12]
        rows.insert(19, "after twenty")
        rows.insert(19, "")
        rows[30] = "thirty-one changed"
        rows.append("tail one")
        save(repo_path, rows)

    def first_and_last(repo_path):
        rows = lines(repo_path)
        rows[0] = "FIRST"
        del rows[-1]
        save(repo_path, rows)

    def remove_top(repo_path):
        rows = lines(repo_path)
        del rows[0:2]
        save(repo_path, rows)

    def append_only(repo_path):
        save(repo_path, lines(repo_path) + ["a", "b"])

    def blank_after(repo_path):
        rows = lines(repo_path)
        rows[4:5] = ["changed five", "", "", "x"]
        save(repo_path, rows)

    hunk_twin(binary, repo, "mixed", "f.txt", mixed)
    hunk_twin(binary, repo, "first-and-last", "f.txt", first_and_last)
    hunk_twin(binary, repo, "remove-top", "f.txt", remove_top)
    hunk_twin(binary, repo, "append", "f.txt", append_only)
    # already partly staged: the unstaged hunks are taken against the index
    hunk_twin(binary, repo, "over a staged change", "f.txt", mixed, cached_edit=first_and_last, extra_ops=("stage",))
    undo_twin(binary, repo, "mixed", "f.txt", mixed)
    undo_twin(binary, repo, "first-and-last", "f.txt", first_and_last)
    text_objects(binary, repo, "f.txt", mixed)
    text_objects(binary, repo, "f.txt", blank_after)
    # a file with no newline at the end
    bare = new_repo()
    write(bare, "n.txt", "one\ntwo\nthree")
    git(bare, "add", ".")
    git(bare, "commit", "-q", "-m", "bare")

    def bare_edit(repo_path):
        write(repo_path, "n.txt", "ONE\ntwo\nthree")

    hunk_twin(binary, bare, "no newline at the end, edit the top", "n.txt", bare_edit, extra_ops=("stage",))


def sha256_section(binary):
    try:
        repo = history_repo(("--object-format=sha256",))
    except RuntimeError as problem:
        print("skip sha256: %s" % str(problem)[:100])
        return
    reads(binary, repo, "sha256")
    solo = new_repo(("--object-format=sha256",))
    write(solo, "f.txt", numbered(12))
    git(solo, "add", ".")
    git(solo, "commit", "-q", "-m", "base")

    def edit(repo_path):
        rows = lines_of(open(os.path.join(repo_path, "f.txt")).read())
        rows[3] = "changed"
        write(repo_path, "f.txt", "\n".join(rows) + "\n")

    hunk_twin(binary, solo, "sha256", "f.txt", edit, extra_ops=("stage",))


def worktree_section(binary, repo):
    linked = os.path.join(ENV.root, "linked")
    git(repo, "worktree", "add", "-q", linked, "-b", "wt")
    ref = lines_of(git(linked, "show", ":./f.txt"))
    check("linked worktree base", run(binary, linked, "libbase", "f.txt").get("LINE", []) == ref)
    check("linked worktree blame", run(binary, linked, "blame", "f.txt").get("COMMIT", []) == blame_oracle(linked, "f.txt"))
    rows = lines_of(open(os.path.join(linked, "f.txt")).read())
    rows[7] = "edited in the linked worktree"
    write(linked, "f.txt", "\n".join(rows) + "\n")
    got = run(binary, linked, "app", os.path.join(linked, "f.txt"), ":8\r:Hunk stage\r")
    check("linked worktree stage ran", got["_code"] == 0, got["_err"])
    check("linked worktree staged", "edited in the linked worktree" in git(linked, "show", ":f.txt"))
    check("main worktree index untouched", "edited in the linked" not in git(repo, "show", ":f.txt"))
    fsck_ok("linked worktree", linked)


def fallback_section(binary, repo):
    """An index the library does not read (version 4): the gutter still gets its base through `git`."""
    git(repo, "update-index", "--index-version", "4")
    ref = lines_of(git(repo, "show", ":./f.txt"))
    check("index v4: the library declines", "FAILED" in run(binary, repo, "libbase", "f.txt"))
    check("index v4: the editor falls back to git", run(binary, repo, "base", "f.txt").get("LINE", []) == ref)
    git(repo, "update-index", "--index-version", "2")


def timing_section(binary):
    repo = new_repo()
    write(repo, "big.txt", numbered(100000))
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "big")
    began = time.time()
    got = run(binary, repo, "libbase", "big.txt")
    library = time.time() - began
    began = time.time()
    git(repo, "show", ":./big.txt")
    plain = time.time() - began
    check("100k lines: read through the library", len(got.get("LINE", [])) == 100000, got["_err"])
    check("100k lines: the library is not absurdly slow (%.2fs, git show %.2fs)" % (library, plain), library < 30)
    print("timing: 100000-line base %.3fs in process (with start-up), `git show` %.3fs" % (library, plain))
    rows = numbered(100000).split("\n")
    rows[50000] = "edited"
    write(repo, "big.txt", "\n".join(rows))
    began = time.time()
    got = run(binary, repo, "app", os.path.join(repo, "big.txt"), ":50001\r:Hunk stage\r", timeout=300)
    staged = time.time() - began
    check("100k lines: stage one hunk", got["_code"] == 0 and "edited" in git(repo, "show", ":big.txt"), got["_err"])
    print("timing: open 100000 lines, stage one hunk %.3fs" % staged)


# ------------------------------------------------------------------ app commands

def app_section(binary, repo):
    path = os.path.join(repo, "f.txt")
    got = run(binary, repo, "app", path, ":Git log %\r")
    entries = got.get("ENTRY", [])
    want = git(repo, "log", "--format=%H", "--", "f.txt").split()
    check(":Git log % lists the file history", [e.split("\t")[1] for e in entries] == want, "%r" % entries[:3])
    check(":Git log % is a list titled with the file", got.get("PICKER") == ["Git log f.txt"])
    got = run(binary, repo, "app", path, ":Git log -L 5,7\r")
    proc = git(repo, "log", "--first-parent", "-L", "5,7:f.txt", "-s", "--format=%H").split()
    check(":Git log -L 5,7", [e.split("\t")[1] for e in got.get("ENTRY", [])] == proc)
    got = run(binary, repo, "app", path, ":Git log\r")
    check(":Git log lists the project", [e.split("\t")[1] for e in got.get("ENTRY", [])] == git(repo, "log", "--format=%H").split())
    got = run(binary, repo, "app", path, ":Git show HEAD~1\r")
    body = got.get("BUF", [])
    want = lines_of(git(repo, "show", "--format=", "--patch", "HEAD~1"))
    cut = next((i for i, line in enumerate(body) if line.startswith("diff --git")), len(body))
    check(":Git show opens the patch in a scratch buffer", body[cut:cut + len(want)] == want)
    rows = lines_of(open(path).read())
    rows[11] = "dirty line"
    write(repo, "f.txt", "\n".join(rows) + "\n")
    got = run(binary, repo, "app", path, ":Git diff\r")
    check(":Git diff shows the working tree", [l for l in got.get("BUF", []) if l.startswith("+dirty")] == ["+dirty line"])
    got = run(binary, repo, "app", path, ":Git diff index\r")
    check(":Git diff index with nothing staged says so", any("no changes" in n for n in got.get("NOTICE", [])))
    got = run(binary, repo, "app", path, ":Git blame\r")
    entries = got.get("ENTRY", [])
    ids = blame_oracle(repo, "f.txt")
    mine = [e.split("\t")[1] for e in entries]
    check(":Git blame has a row per buffer line", len(entries) == len(rows))
    check(":Git blame: unchanged lines carry git's commit, the dirty one none",
          mine[:11] == ids[:11] and mine[11] == "" and mine[12:] == ids[12:], "%r vs %r" % (mine[:14], ids[:14]))
    check(":Git blame is a list", got.get("PICKER") == ["Git blame f.txt"])
    got = run(binary, repo, "app", path, ":Git bogus\r")
    check(":Git with an unknown word says so", any("unknown command" in n for n in got.get("NOTICE", [])))
    git(repo, "checkout", "-q", "--", "f.txt")
    got = run(binary, repo, "app", path, ":13\r gB")
    sha = blame_oracle(repo, "f.txt")[12]
    check("<Space>gB names the commit of the line", any(n.startswith(sha[:8]) or n.startswith("^" + sha[:7]) for n in got.get("NOTICE", [])), "%r" % got.get("NOTICE"))
    got = run(binary, repo, "app", path, ":Hunk bogus\r")
    check(":Hunk with an unknown word says so", any(n.startswith("Hunk:") for n in got.get("NOTICE", [])))


def main():
    global ENV, VERBOSE
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", required=True)
    parser.add_argument("-v", action="store_true")
    parser.add_argument("--no-timing", action="store_true")
    options = parser.parse_args()
    VERBOSE = options.v
    binary = os.path.realpath(options.runner)
    root = os.path.realpath(tempfile.mkdtemp(prefix="m3git"))
    ENV = Env(root)
    try:
        repo = history_repo()
        reads(binary, repo, "history")
        app_section(binary, repo)
        worktree_section(binary, repo)
        fallback_section(binary, repo)
        hunks_section(binary)
        sha256_section(binary)
        if not options.no_timing:
            timing_section(binary)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("oracle_git: %d checks, %d failed" % (CHECKS, len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
