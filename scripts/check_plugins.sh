#!/usr/bin/env bash
# The import and access rules of first-party plugins (docs/CORE-AND-PLUGINS.md 2.4, rules R2 and R3).
#
#   bash scripts/check_plugins.sh [DIR...]    default: plugins/ and tests/fixtures/plugins
#
# DIR holds plugin directories (DIR/NAME/MEDX_NAME*.m31). R2: a plugin imports only `ext.*`, the value types
# `engine.MED_buffer` and `engine.MED_key`, the m31 standard library except `proc`, `os` and `term`, the
# m31git library, and its own modules (`plugins.NAME.*`; the module itself is found by its directory). R3: no
# `context.editor` (or any `.editor` access) and no `MED_app` / `App`: a plugin never reaches the editor's
# internals. Files under NAME/tests/ are not plugin code and are not checked. bash 3.2 and BSD tools only.
set -euo pipefail
cd "$(dirname "$0")/.."

dirs=("$@")
if [ ${#dirs[@]} -eq 0 ]; then
    dirs=(plugins tests/fixtures/plugins)
fi

bad=0
complain() { echo "check_plugins: $1" >&2; bad=$((bad + 1)); }

for root in "${dirs[@]}"; do
    [ -d "$root" ] || continue
    for plugin in "$root"/*/; do
        [ -f "${plugin}plugin.txt" ] || continue
        name=$(basename "$plugin")
        for file in "$plugin"*.m31; do
            [ -f "$file" ] || continue
            # R2: imports
            while IFS= read -r line; do
                module=${line#import }
                module=${module%;*}
                module=$(printf '%s' "$module" | tr -d '[:space:]')
                case "$module" in
                    ext.*|engine.MED_buffer|engine.MED_key) ;;
                    plugins."$name".*) ;;
                    m31git|m31git.*) ;;
                    proc|proc.*|os|os.*|term|term.*) complain "$file: imports $module (the process, environment and terminal modules are core's)" ;;
                    engine.*|ui.*|tui.*|syntax.*|tests.*) complain "$file: imports $module (a plugin imports only ext.*, engine.MED_buffer and engine.MED_key)" ;;
                    plugins.*) complain "$file: imports $module (a plugin never imports another plugin; use a service slot)" ;;
                    *) ;;
                esac
            done < <(grep -E '^import[[:space:]]' "$file" || true)
            # R3: the editor's internals
            if grep -nE '(^|[^A-Za-z0-9_])(context|ctx)\.editor([^A-Za-z0-9_]|$)|\.editor\.|MED_app|MED_editor' "$file" | grep -v '^[0-9]*:[[:space:]]*//' >/dev/null; then
                complain "$file: reaches the editor's internals ($(grep -nE '\.editor|MED_app|MED_editor' "$file" | grep -v '^[0-9]*:[[:space:]]*//' | head -1))"
            fi
        done
    done
done

if [ "$bad" -ne 0 ]; then
    echo "check_plugins: $bad problem(s)" >&2
    exit 1
fi
echo "check_plugins: ok"
