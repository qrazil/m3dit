#!/usr/bin/env python3
"""A scripted language server for the completion popup tests (tests/lsp_pty.py).

Full-document sync. Completion answers depend on the text before the cursor:

  after `obj.`        member items (alpha, beta_value, gamma, Delta) with kinds and details
  the word `slow`     the answer takes 0.6 s (a client that cancels sends $/cancelRequest meanwhile)
  anything else       a list of plain items, a snippet (`for`), an item whose additionalTextEdits only
                      come with completionItem/resolve (`import_me`, adds `import me` at line 0),
                      hostile labels (control characters, wide characters, a very long label), an item
                      with its own textEdit range and one with a commit character

completionItem/resolve adds a Markdown documentation and a detail. When the word under the cursor is one
character long the answer is `isIncomplete`: the client must ask again as more is typed.

Every request and notification of interest is appended as one JSON line to $FAKE_LSP_LOG, so a test can
check what went over the wire (trigger kinds, cancels, the incremental changes of didChange).

Environment: FAKE_LSP_SYNC=1|2 (the sync kind announced), FAKE_LSP_DYNAMIC=1 (completion, formatting, didChange and
didChangeWatchedFiles are registered with client/registerCapability instead of announced; formatting is
unregistered again at the third didSave). Also: hover waits 0.4 s and first sends a workspace/applyEdit for a
document version that does not exist (the client must refuse it); formatting prepends a comment line; rename
answers with documentChanges (create, edit, rename, delete). FAKE_LSP_TOKENS=1 adds semantic tokens: `myvar` is a
keyword, `Foo` a type, `go` a function (a declaration after `def `), computed from the current text.
"""
import re
import json
import os
import sys
import time

docs = {}
versions = {}
saves = [0]
LOG = os.environ.get("FAKE_LSP_LOG")
SYNC = int(os.environ.get("FAKE_LSP_SYNC", "1"))
DYNAMIC = os.environ.get("FAKE_LSP_DYNAMIC") == "1"
TOKENS = os.environ.get("FAKE_LSP_TOKENS") == "1"


def log(kind, **fields):
    if LOG:
        with open(LOG, "a") as f:
            f.write(json.dumps(dict(kind=kind, **fields)) + "\n")


def read():
    header = sys.stdin.buffer.readline()
    if not header:
        return None
    length = int(header.split(b":")[1])
    sys.stdin.buffer.readline()
    return json.loads(sys.stdin.buffer.read(length))


def send(obj):
    data = json.dumps(obj).encode()
    sys.stdout.buffer.write(b"Content-Length: %d\r\n\r\n" % len(data) + data)
    sys.stdout.buffer.flush()


def reply(message, result):
    send({"jsonrpc": "2.0", "id": message["id"], "result": result})


def before_cursor(params):
    uri = params["textDocument"]["uri"]
    pos = params["position"]
    lines = docs.get(uri, "").split("\n")
    line = lines[pos["line"]] if pos["line"] < len(lines) else ""
    return line[:pos["character"]]


def word_of(text):
    i = len(text)
    while i > 0 and (text[i - 1].isalnum() or text[i - 1] == "_"):
        i -= 1
    return text[i:], text[:i]


def item(label, kind=6, detail=None, **extra):
    out = {"label": label, "kind": kind, "sortText": extra.pop("sort", label)}
    if detail:
        out["detail"] = detail
    out.update(extra)
    return out


def plain_items():
    items = [item("hello_world", 3, "fn() -> str"), item("hello_there", 6), item("help", 2, "fn help()"),
             item("hex_value", 6), item("print_all", 3, "fn print_all()"), item("println", 3, "fn println(x)")]
    for i in range(30):
        items.append(item("item_%02d" % i, 5 + i % 5, "field %d" % i))
    items += [
        item("for", 15, "snippet: for loop", insertText="for ${1:i} in ${2:items} {\n\t$0\n}", insertTextFormat=2),
        item("import_me", 3, "needs an import", data={"auto_import": True}),
        item("日本語の名前", 6, "wide"),
        item("evil\x1b[31mred\x07\x08", 6, "ctl\x1b]0;x\x07"),
        item("long_" + "x" * 120, 6, "very long label"),
        item("commit_me", 6, commitCharacters=["("]),
    ]
    return items


def member_items():
    return [item("alpha", 2, "fn alpha()", textEdit=None), item("beta_value", 5, "i32"), item("gamma", 6),
            item("Delta", 7, "struct Delta")]


while True:
    message = read()
    if message is None:
        break
    method = message.get("method")
    params = message.get("params", {})
    if method == "initialize":
        caps = {"textDocumentSync": {"openClose": True, "change": 1 if DYNAMIC else SYNC},
                "hoverProvider": True, "renameProvider": True}
        if not DYNAMIC:
            caps["completionProvider"] = {"triggerCharacters": ["."], "resolveProvider": True,
                                          "allCommitCharacters": [";"]}
            caps["documentFormattingProvider"] = True
        if TOKENS:
            caps["semanticTokensProvider"] = {"legend": {"tokenTypes": ["keyword", "function", "type", "variable"],
                                                         "tokenModifiers": ["declaration"]},
                                              "full": True}
        reply(message, {"capabilities": caps})
    elif method == "initialized":
        if DYNAMIC:
            send({"jsonrpc": "2.0", "id": "r1", "method": "client/registerCapability", "params": {"registrations": [
                {"id": "c1", "method": "textDocument/completion",
                 "registerOptions": {"triggerCharacters": ["."], "resolveProvider": True, "allCommitCharacters": [";"]}},
                {"id": "f1", "method": "textDocument/formatting"},
                {"id": "s1", "method": "textDocument/didChange", "registerOptions": {"syncKind": SYNC}},
                {"id": "w1", "method": "workspace/didChangeWatchedFiles",
                 "registerOptions": {"watchers": [{"globPattern": "**/*"}]}}]}})
    elif method is None and message.get("id") == "r1":
        log("registered", result=message.get("result"))
    elif method is None and message.get("id") == "ae1":
        log("applyEdit_reply", result=message.get("result"))
    elif method == "textDocument/didOpen":
        document = params["textDocument"]
        docs[document["uri"]] = document["text"]
        versions[document["uri"]] = document["version"]
        log("didOpen", version=document["version"], doc=document["text"])
    elif method == "textDocument/didChange":
        versions[params["textDocument"]["uri"]] = params["textDocument"]["version"]
        for change in params["contentChanges"]:
            uri = params["textDocument"]["uri"]
            if "range" not in change:
                docs[uri] = change["text"]
            else:
                lines = docs[uri].split("\n")
                a, b = change["range"]["start"], change["range"]["end"]
                head = lines[a["line"]][:a["character"]]
                tail = lines[b["line"]][b["character"]:]
                lines[a["line"]:b["line"] + 1] = (head + change["text"] + tail).split("\n")
                docs[uri] = "\n".join(lines)
        log("didChange", changes=params["contentChanges"], version=params["textDocument"]["version"],
            doc=docs[params["textDocument"]["uri"]])
    elif method == "textDocument/completion":
        context = params.get("context", {})
        text = before_cursor(params)
        word, rest = word_of(text)
        log("completion", trigger=context.get("triggerKind"), char=context.get("triggerCharacter"), word=word)
        if word == "slow":
            time.sleep(0.6)
        if rest.endswith("."):
            items = member_items()
        else:
            items = plain_items()
        result = {"isIncomplete": len(word) == 1, "items": items}
        reply(message, result)
    elif method == "completionItem/resolve":
        out = dict(params)
        out["documentation"] = {"kind": "markdown", "value": "Docs for **%s**\n\n```rust\nlet x = %s;\n```\nSecond paragraph of the documentation, which is long enough to wrap in the side panel." % (params["label"], params["label"])}
        out["detail"] = params.get("detail", "") or "resolved detail"
        if params.get("data", {}).get("auto_import"):
            out["additionalTextEdits"] = [{"range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 0}},
                                           "newText": "import me\n"}]
        log("resolve", label=params["label"])
        reply(message, out)
    elif method == "$/cancelRequest":
        log("cancel", id=params["id"])
    elif method == "textDocument/formatting":
        uri = params["textDocument"]["uri"]
        log("formatting")
        reply(message, [{"range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 0}}, "newText": "// formatted\n"}])
    elif method == "textDocument/didSave":
        saves[0] += 1
        log("didSave")
        if DYNAMIC and saves[0] == 3:
            send({"jsonrpc": "2.0", "id": "u1", "method": "client/unregisterCapability",
                  "params": {"unregisterations": [{"id": "f1", "method": "textDocument/formatting"}]}})
    elif method == "workspace/didChangeWatchedFiles":
        log("watched", changes=params["changes"])
    elif method == "textDocument/hover":
        uri = params["textDocument"]["uri"]
        log("hover")
        send({"jsonrpc": "2.0", "id": "ae1", "method": "workspace/applyEdit", "params": {"edit": {"documentChanges": [
            {"textDocument": {"uri": uri, "version": 999},
             "edits": [{"range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 0}},
                        "newText": "STALE"}]}]}}})
        time.sleep(0.4)
        reply(message, {"contents": "hover text"})
    elif method == "textDocument/semanticTokens/full":
        uri = params["textDocument"]["uri"]
        data, last_line, last_start = [], 0, 0
        for number, line in enumerate(docs.get(uri, "").split("\n")):
            found = []
            for match in re.finditer(r"\b(myvar|Foo|go)\b", line):
                word = match.group(1)
                units = len(line[:match.start()].encode("utf-16-le")) // 2
                kind = {"myvar": 0, "go": 1, "Foo": 2}[word]
                mods = 1 if word == "go" and line[:match.start()].endswith("def ") else 0
                found.append((units, len(word), kind, mods))
            for units, length, kind, mods in found:
                data += [number - last_line, units if number != last_line else units - last_start, length, kind, mods]
                last_line, last_start = number, units
        log("semtok", count=len(data) // 5)
        reply(message, {"data": data})
    elif method == "textDocument/rename":
        uri = params["textDocument"]["uri"]
        base = uri.rsplit("/", 1)[0]
        log("rename", name=params["newName"])
        reply(message, {"documentChanges": [
            {"kind": "create", "uri": base + "/created.txt"},
            {"textDocument": {"uri": uri, "version": versions.get(uri)},
             "edits": [{"range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
                        "newText": params["newName"]}]},
            {"kind": "rename", "oldUri": base + "/created.txt", "newUri": base + "/moved.txt"},
            {"kind": "delete", "uri": base + "/doomed.txt"}]})
    elif method == "shutdown":
        reply(message, None)
    elif method == "exit":
        break
    elif "id" in message and method is not None and method != "initialized":
        reply(message, None)
