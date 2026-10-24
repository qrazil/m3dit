# sourced by tests/test.sh: plugins (docs/CORE-AND-PLUGINS.md 5.2, 7.4).
#
#   t_plugins (test_units.sh)   the registry: Spec checks, requires/wants order, eager and lazy activation, stubs,
#                               maps as data, the run-time switch, :Plugins and :PluginDisable in the App
#   generator                   ext/MED_ext_enabled.m31 equals `scripts/plugins.sh gen` of the default profile
#   plugin.txt                  every plugin of the default and full profiles is well formed, and `m3 --list-plugins`
#                               prints what its plugin.txt says (so the files and the m31 Spec cannot drift)
#   check_plugins.sh            the import and access rules (R2, R3) for plugins/ and the fixtures
#   selection                   --without refuses a plugin another one requires; --plugins adds requires
#   fixtures                    builds with the fixture plugins (tests/fixtures/plugins) and plugins_pty.py
#   core_only.sh                the --no-plugins build passes the core gate
if [ ! -x "$WORK/m3" ]; then
    build m3 m3.m31
fi
fixtures=tests/fixtures/plugins

if out=$(bash scripts/plugins.sh gen $(bash scripts/plugins.sh resolve) 2>&1) && [ "$out" = "$(cat ext/MED_ext_enabled.m31)" ]; then
    note "ext/MED_ext_enabled.m31 is the default profile's registry"
else
    bad "ext/MED_ext_enabled.m31 differs from the generator (bash scripts/plugins.sh gen \$(bash scripts/plugins.sh resolve) > ext/MED_ext_enabled.m31)" "$(printf '%s\n' "$out" | head -5)"
fi

if out=$(bash scripts/plugins.sh check-files --profile full 2>&1 && bash scripts/plugins.sh check-files --plugin-dir "$fixtures" --plugins greeter 2>&1); then
    note "plugin.txt files are well formed"
else
    bad "plugin.txt" "$out"
fi

if out=$(bash scripts/check_plugins.sh 2>&1); then
    note "check_plugins.sh: $out"
else
    bad "check_plugins.sh" "$out"
fi

if [ -x "$WORK/m3" ]; then
    want=$(bash scripts/plugins.sh table)
    got=$("$WORK/m3" --list-plugins 2>&1)
    if [ "$got" = "$want" ]; then
        note "m3 --list-plugins equals the plugin.txt files of the default profile"
    else
        bad "m3 --list-plugins differs from plugin.txt" "want: $want" "got: $got"
    fi
fi

# selection rules (no build)
if out=$(bash scripts/plugins.sh resolve --plugin-dir "$fixtures" --plugins greeter 2>&1) && [ "$(printf '%s' "$out" | tr '\n' ' ')" = "plugins: added hello (required by greeter) hello greeter " ]; then
    note "--plugins adds what a plugin requires, in dependency order"
else
    bad "--plugins closure and order" "$out"
fi
if out=$(bash scripts/plugins.sh resolve --plugin-dir "$fixtures" --plugins greeter,hello --without hello 2>&1); then
    bad "--without a plugin that another requires is refused" "$out"
else
    case "$out" in *"requires hello"*) note "--without refuses a plugin that a kept one requires" ;; *) bad "--without refusal text" "$out" ;; esac
fi
if out=$(bash scripts/plugins.sh resolve --plugin-dir "$fixtures" --plugins nosuch 2>&1); then
    bad "an unknown plugin is refused" "$out"
else
    note "an unknown plugin is refused"
fi
if out=$(bash scripts/plugins.sh resolve --no-plugins --plugins x 2>&1); then
    bad "--no-plugins with --plugins is refused" "$out"
else
    note "--no-plugins and --plugins exclude each other"
fi

# the core-only build
if [ -f tests/core_only.sh ]; then
    if out=$(bash tests/core_only.sh "$WORK" 2>&1); then
        note "core_only.sh: $(printf '%s\n' "$out" | tail -1)"
    else
        bad "core_only.sh" "$(printf '%s\n' "$out" | tail -15)"
    fi
fi

# builds with the fixture plugins
if LANGC="$LANGC" bash scripts/build.sh --plugin-dir "$fixtures" --plugins hello -o "$WORK/m3_hello" >"$WORK/m3_hello.log" 2>&1 \
    && LANGC="$LANGC" bash scripts/build.sh --plugin-dir "$fixtures" --plugins greeter -o "$WORK/m3_greeter" >"$WORK/m3_greeter.log" 2>&1; then
    if out=$("$WORK/m3_greeter" --version 2>&1) && [ "$out" = "m3 $(grep '^version ' deps | awk '{print $2}') (api 0.2.0; plugins: hello greeter)" ]; then
        note "m3 --version names the api and the plugins: $out"
    else
        bad "m3 --version with plugins" "$out"
    fi
    want=$(bash scripts/plugins.sh table --plugin-dir "$fixtures" --plugins greeter)
    got=$("$WORK/m3_greeter" --list-plugins 2>&1)
    if [ "$got" = "$want" ]; then
        note "fixture m3 --list-plugins equals the fixture plugin.txt files"
    else
        bad "fixture --list-plugins" "want: $want" "got: $got"
    fi
    if out=$(python3 tests/plugins_pty.py "$WORK/m3_hello" "$WORK/m3_greeter" "$WORK/m3" 2>&1); then
        note "plugins_pty: $(printf '%s\n' "$out" | tail -1)"
    else
        bad "plugins_pty" "$(printf '%s\n' "$out" | tail -25)"
    fi
else
    bad "build with the fixture plugins" "$(grep -v '^warning' "$WORK/m3_hello.log" "$WORK/m3_greeter.log" 2>/dev/null | tail -8)"
fi
