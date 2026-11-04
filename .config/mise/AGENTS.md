# Sandboxing mise tools (mise-sbx)

Every mise-managed command is launched through a sandbox by default: reads and
writes are limited to the current project plus that tool's own state, the
environment is filtered, and network access is off unless the tool's policy
allows it. Enforcement is Landlock (filesystem) and seccomp (network) via
`mise exec --deny-* / --allow-*`.

Read this before changing anything here.

## Files

| Path | Role |
| --- | --- |
| `~/.config/mise/sandbox.toml` | **The policy.** Per-tool network, path and env rules, plus named `-p` presets (`[presets.<name>]`). |
| `~/.local/bin/mise-sbx` | Dispatcher: reads policy, builds flags, execs `mise x`. Also `sync`, `dirs`, `policy`, `-c`, `-p`, `--dry-run`. |
| `~/.config/fish/completions/mise-sbx.fish` | Fish completion. Presets and tools are read from the policy at completion time; the flags, value options and subcommands are hard-coded, so keep it in step with the dispatcher. |
| `~/.config/mise/conf.d/90-sandbox-wrappers.toml` | **Generated.** `[wrappers.<bin>] command = "/home/fidel/.local/bin/mise-sbx"`. Never edit by hand; run `mise-sbx sync`. |
| `~/.config/mise/config.toml` | `[hooks] postinstall = "$HOME/.local/bin/mise-sbx sync"` keeps wrappers current. Note the shell-expanded `$HOME`: a bare `mise-sbx` breaks when `~/.local/bin` is not on PATH (CI, cron, minimal systems). |
| `~/.local/bin/<agent>` | Launcher scripts (`claude`, `codex`, `gemini`, `gh`, `muse`, ...). **Owned by Omarchy** — see below. |
| `~/.local/state/mise-sbx.log` | One audit line per launch: time, tool, cwd, flags, args, path notes. |

## Requirements

- **mise >= 2026.10.0.** `mise-sbx` runs `mise --version` and exits with an
  error below that, because earlier releases reject `--deny-read`/`--deny-net`.
  Override for testing only: `MISE_SBX_SKIP_VERSION_CHECK=1`.
- **Python 3.13.** The dispatcher uses `tomllib` and 3.13-only typing syntax.
- **bash**, for the child `PATH` sanitizer (`bash_executable()` searches `PATH`,
  then `/bin/bash`, then `/usr/bin/bash`).
- **Linux** with Landlock >= 5.13; `--deny-net` needs x86_64 or arm64. In
  containers without Landlock mise fails closed rather than running unsandboxed.

## Directories

Everything is resolved at runtime; `mise-sbx dirs` prints the result.

| Path | Resolution order |
| --- | --- |
| config dir | `MISE_CONFIG_DIR`, `$XDG_CONFIG_HOME/mise`, `~/.config/mise` |
| policy | `MISE_SBX_CONFIG`, `<config dir>/sandbox.toml` |
| wrappers | `<config dir>/conf.d/90-sandbox-wrappers.toml` |
| data / shims | `MISE_DATA_DIR`, `$XDG_DATA_HOME/mise`, `~/.local/share/mise`; shims are `MISE_SBX_SHIMS_DIR` or `<data>/shims` |
| state / log | `MISE_STATE_DIR`, `$XDG_STATE_HOME`, `~/.local/state`; log is `MISE_SBX_LOG_PATH` or `<state>/mise-sbx.log` |
| cache | `$XDG_CACHE_HOME/mise-sbx`, `~/.cache/mise-sbx` |

`MISE_*_DIR` values already point at mise-specific directories, so no `mise`
suffix is appended to them.

## How a launch works

```
claude
  -> ~/.local/share/mise/command-wrappers/bin/claude   (mise wrapper)
  -> mise-sbx claude                                   (unsandboxed)
       resolves the real binary with `mise which`
       builds --deny-read/--deny-write/--deny-env, --allow-*, --deny-net
  -> mise x <flags> -- bash -c <sanitize PATH> -- <real binary> <args>
  -> tool runs under Landlock + seccomp
```

The PATH sanitizer removes `command-wrappers/bin` and `shims` from the child
`PATH`. mise re-adds them, and without this a tool that shells out to another
mise command (`gemini`'s shell shim calling `node`) would re-enter mise inside
the sandbox, where mise cannot read its own config.

## Critical constraint: do not set global `sandbox.*` settings

Do **not** add this to `~/.config/mise/config.toml`:

```toml
[settings]
sandbox.deny_read = true   # breaks mise-sbx
```

mise runs the wrapper's `command` (`mise-sbx`) **inside** the sandbox, so a
global `deny_read` prevents executing `~/.local/bin/mise-sbx` and stops the
dispatcher from reading mise's config. Enforcement therefore lives in the
dispatcher's flags, which are applied to the tool only. `deny_net` cannot be
global either, because mise cannot re-grant network to agents afterwards.

## Add a new tool

1. Install it: `mise use -g <tool>` (or the tool's `~/.local/bin` launcher).
   The `postinstall` hook runs `mise-sbx sync`; otherwise run `mise-sbx sync`.
2. Decide its policy. Tools with no `[tools.<name>]` entry get `[default]`:
   read/write the project only, no network. Add an entry when the tool needs
   network, extra paths, or env vars. Coding agents also need the skill roots
   from *Agent skill directories* below.
3. Verify: `mise-sbx policy <tool>`, run the tool, then read the audit log.

For an internal helper that only its already-sandboxed parent invokes, add it
to `[sync] exclude` instead of giving it a policy.

## Omarchy owns the `~/.local/bin` launchers

`/usr/bin/omarchy-mise-install` (package `omarchy`) writes
`~/.local/bin/<command>` from this template:

```bash
#!/bin/bash
export MISE_MINIMUM_RELEASE_AGE=0
mise use -g --quiet <package> || exit 1
exec mise x <package> -- <bin> "$@"
```

It is called by `/usr/share/omarchy/install/user/mise.sh` (provisioning) and by
migrations such as `1784909971.sh`, `1785617047.sh`, `1785846769.sh` and
`1788577553.sh` (upgrades). Those runs `rm -f` the file and rewrite it, so any
hand edit to a launcher is lost.

**Do not delete or hand-edit those files.** Instead, `mise-sbx sync`
reconciles them: for every executable in `~/.local/bin` that contains all three
markers (`MISE_MINIMUM_RELEASE_AGE=0`, `mise use -g --quiet `, `exec mise x `),
it rewrites only the `exec mise x …` line to `exec mise-sbx "<name>" "$@"`,
keeping Omarchy's install line and backend spec. The write is atomic, so a
launcher that is mid-execution keeps its inode. Anything without the markers is
never touched.

`[sync] reconcile` in `sandbox.toml` controls this: `"repoint"` (default),
`"warn"` (list unsandboxed launchers), or `"off"`.

Healing happens on the next `mise install`/`mise use` (the `postinstall` hook
runs sync), when a launcher runs its own `mise use -g`, or when you run
`mise-sbx sync` by hand. After `omarchy update`, run `mise-sbx sync`.

Residual window: if Omarchy regenerates a launcher and you invoke it **by
absolute path** before any sync runs, that one invocation executes the old
`exec mise x` line unsandboxed. Normal `claude`/`gh` invocations never hit it,
because `command-wrappers/bin` (PATH entry #1) shadows `~/.local/bin` (#9).

## PATH precedence

`mise activate` puts, in order: `command-wrappers/bin`, each tool's install dirs,
the shims dir, then your `~/.local/bin`. So mise's wrappers win over the Omarchy
launchers in an activated shell, and the launchers only matter for absolute-path
invocation or non-activated contexts.

## Tweak a policy

```toml
[default]
allow_read  = ["."]        # relative to the launch directory; "~" is expanded
allow_write = ["."]        # write implies read
net         = false        # false | true | "opt-in"
allow_env   = []

[tools.claude]
net         = true                    # overrides [default]
allow_write = ["~/.claude", "~/.cache/claude"]
allow_read  = ["~/.claude.json", "~/.gitconfig", "~/.config/git"]
allow_env   = ["ANTHROPIC_*", "CLAUDE_*"]   # fnmatch patterns, merged with [default]
```

Rules:

- `[tools.<name>]` merges over `[default]`: `allow_read`, `allow_write` and
  `allow_env` are appended, `net` is replaced.
- `net = "opt-in"` allows network only when `MISE_SANDBOX_NET=1` is set.
- Paths that do not exist are dropped (Landlock can only bind existing paths).
  A missing write path whose last segment has no dot is created first; a path
  that looks like a file (last segment contains a dot) is skipped. Watch the
  `notes=` field in the log if a tool cannot see something.
- Path lists are **alphabetical, case-insensitive**: `$XDG_RUNTIME_DIR` sorts
  before `/usr/…` before `~/…`. The one exception is `[deny] paths`, which is
  grouped by category with each group alphabetical. Keep it that way when you
  add a path — a sorted list is reviewable at a glance and makes a stray entry
  obvious.
- Paths expand `~`, `$VAR` and `${VAR}`; `$XDG_RUNTIME_DIR` falls back to
  `/run/user/<uid>` when unset, so a policy also resolves from cron or a systemd
  unit. Unknown variables stay literal, so the path fails the existence check
  and is dropped with a note instead of becoming a grant.
- Landlock grants a directory and everything under it. Never allow `~` or `/`
  in a policy — that is what `-p home` / `-p all` are for.
- Network is all-or-nothing. mise cannot filter by host; use `--no-net` or a
  separate firewall if a tool must only reach specific hosts.

## Presets (`-p`)

`-p/--preset NAME` adds a named bundle of paths and env patterns on top of the
tool policy. It is repeatable. It replaces the old `--fs` flag (removed:
`--fs=…` is now an unknown option) and `MISE_SANDBOX_FS` (detected, warned
about on stderr for one line, then ignored).

With no `-p`, a run grants read/write on the current directory only — what the
old `project` value meant, and already expressed by `[default] allow_write`.

Built in: `home` (read/write `$HOME`), `home-ro` (read `$HOME`), `all`
(read/write `/`, ignores the deny list with a warning). Everything else comes
from `sandbox.toml`:

```toml
[presets.gui]
include     = ["home"]                # optional; resolved transitively
allow_write = ["~/.config/gtk-3.0"]   # same syntax as [tools.<name>]
allow_read  = ["/usr/share/themes"]
allow_env   = ["GTK_*"]               # fnmatch, merged with the tool policy
```

```bash
mise-sbx -p omarchy claude            # one preset
mise-sbx -p home -p omarchy claude    # additive union
MISE_SANDBOX_PRESET=home:omarchy claude
mise-sbx policy claude -p omarchy     # preview the resulting flags
```

Rules:

- Presets are **additive** to `[default]` + `[tools.<name>]`; they never replace
  them. Repeating a name is a no-op, and a write root wins over a read root for
  the same path.
- `[deny]` still subtracts from every preset path, exactly like a policy root.
- A `[presets.<name>]` that reuses a built-in name (`home`, `home-ro`, `all`) is
  a hard config error, as is an `include` cycle or an unknown `include` target.
- Presets never change network access: `--net`/`--no-net` (or the tool's `net`
  setting) stay in charge.
- Without `-p home` or `-p all`, launching from `$HOME` is refused, because
  `[default] allow_write = ["."]` would otherwise grant the whole home
  directory. `-a ~` also overrides the refusal, and `-p home-ro` is *not* enough
  — that case used to leave `$HOME` writable.
- The audit log records the names: `notes=[presets=home+omarchy; …]`.

Two Omarchy presets ship, both covering the same user surface:

- **`omarchy`** — read-only, for debugging. Read on
  `~/.config/{hypr,omarchy,alacritty,foot,kitty,ghostty,btop,lazygit}`,
  `~/.config/starship.toml`, `~/.local/state/omarchy`, `~/.cache/omarchy`,
  `/usr/share/omarchy`, `/var/lib/pacman`, `~/.local/share/icons` and
  `$XDG_RUNTIME_DIR`. No write access anywhere, so a tool can inspect the
  desktop but cannot change it.
- **`omarchy-rw`** — `include = ["omarchy"]` plus write on the same user config
  and state paths and on `$XDG_RUNTIME_DIR`. This is the one for `omarchy theme
  set`, region capture, `reminder clear` and brightness.

Env for both: `HYPRLAND_*`, `WAYLAND_DISPLAY`, `XDG_RUNTIME_DIR`,
`XDG_CURRENT_DESKTOP`, `XDG_SESSION_*`, `DBUS_SESSION_BUS_ADDRESS`,
`OMARCHY_*`. The env patterns are what make `hyprctl` (and anything talking to
quickshell over dbus) work — the unix sockets themselves are not path-mediated.

`$XDG_RUNTIME_DIR` is granted read-only in `omarchy` and read/write in
`omarchy-rw`, and that distinction is real: omarchy keeps
`omarchy-theme-set.lock`, `omarchy-brightness-display.lock`,
`omarchy-reminders/` and the capture markers directly in that directory. With
the read-only preset those commands still run (no `set -e`; the failed `exec
9>lock` + `flock` just print "Permission denied"/"Bad file descriptor"), but
the capture-region picker and `reminder clear` need the files, so they fail.
Landlock needs `MAKE_REG` on the parent directory, which is why the runtime dir
cannot be sub-granted or denied piecemeal.

```bash
mise-sbx -p omarchy    -c 'omarchy theme current'      # inspect
mise-sbx -p omarchy    -c 'hyprctl -j activeworkspace'
mise-sbx -p omarchy-rw -c 'omarchy theme set Tokyo\ Night'
```

Not covered on purpose: `sudo`/`pkexec` flows (`omarchy pkg add`, `omarchy
update`, `omarchy setup …`) and anything needing network (`omarchy theme
install <url>` still needs `--net`). Neither preset carries write access to
`~/Pictures`, so screenshot output still needs `-a ~/Pictures`.

## Agent skill directories

Agents discover skills in `~/.agents/skills` and `~/.claude/skills`. Both sit
outside every `$HOME` grant (`[deny]` keeps `$HOME` itself ungranted), so each
agent section must list them in `allow_read`:

```toml
[tools.opencode]
allow_read = ["~/.gitconfig", "~/.config/git", "~/.agents/skills", "~/.claude/skills"]
```

The failure is **silent**: the agent starts normally, just without those skills.
The two paths are read-only markdown and helper `.md` files; granting them does
not expose `~/.agents` or `~/.claude` themselves.

## Deny list

`[deny] paths` in `sandbox.toml` is subtracted from every grant, including
`-p home`, `-p home-ro`, preset roots and policy `allow_read`/`allow_write`
roots. Landlock has no negative rules, so the dispatcher stops granting the
parent and grants its non-denied children instead.

```toml
[deny]
paths = ["~/.ssh", "~/.mozilla"]

[tools.claude]
deny = ["~/work/clients"]   # extra denies for one tool
```

Rules:

- A deny wins over an implicit `-p home`, a preset root, or a policy grant.
- `-a PATH` overrides a deny at or above `PATH`; a deny *below* `PATH` still
  applies. So `-a ~/.ssh` works, `-a ~` does not disable the list.
- The current directory being inside a deny aborts the launch:
  `refusing to launch in …; pass -a <dir> to override`.
- `-p all` warns and **ignores** the deny list (it grants `/`).
- Denies inside mise's implicit paths (`/usr`, `/etc`, `/tmp`, `/proc`, the mise
  data dir, …) cannot be enforced; `sync`/`policy` note that and skip them.
- `$HOME` itself is no longer granted when denies are active, so `ls ~` fails
  with `EACCES`. Specific paths under home still work.
- Symlinks resolving into a denied directory are not granted. Hardlinks to a
  denied file cannot be blocked (Landlock limitation).
- Landlock blocks access, it does not hide names. Unix sockets are not
  path-mediated: a deny does not stop `SSH_AUTH_SOCK`, but `--deny-env` strips
  it unless you allow it.
- Denies apply to wrapped launches and `mise-sbx -c`; raw `mise run` tasks that
  bypass the dispatcher are unaffected.

## Escape hatches

Flags go before the tool name; env vars work everywhere.

| Need | Flag | Env |
| --- | --- | --- |
| Network for one run | `mise-sbx --net node server.js` | `MISE_SANDBOX_NET=1` |
| Read/write `$HOME` | `mise-sbx -p home claude` | `MISE_SANDBOX_PRESET=home` |
| Read `$HOME` only | `mise-sbx -p home-ro claude` | `MISE_SANDBOX_PRESET=home-ro` |
| Everything | `mise-sbx -p all npm install` | `MISE_SANDBOX_PRESET=all` |
| Omarchy debugging (read-only) | `mise-sbx -p omarchy claude` | `MISE_SANDBOX_PRESET=omarchy` |
| Omarchy changes (read/write) | `mise-sbx -p omarchy-rw claude` | `MISE_SANDBOX_PRESET=omarchy-rw` |
| Two presets at once | `mise-sbx -p home -p omarchy claude` | `MISE_SANDBOX_PRESET=home:omarchy` |
| See which presets exist | `mise-sbx policy <tool>` (`presets:` line) | |
| Grant one directory | `mise-sbx -a ~/datasets claude` | `MISE_SANDBOX_ALLOW=~/datasets` |
| Grant it read-only | `mise-sbx --allow-ro /srv/ref claude` | `MISE_SANDBOX_ALLOW_RO=/srv/ref` |
| Full environment | `mise-sbx --env=all gh auth status` | `MISE_SANDBOX_ENV=all` |
| No sandbox at all | `mise-sbx --sandbox=off claude /login` | `MISE_SANDBOX=off` |
| Inspect without running | `mise-sbx --dry-run claude --version` | |
| Ad-hoc command | `mise-sbx --net -c 'curl -s https://example.com'` | |

`--sandbox=off` sets `MISE_SANDBOX_DENY_*=false` for that run; it keeps mise's
tool environment, unlike calling the raw install binary directly.

## Sandboxing `mise run` tasks

A task that calls a mise-managed tool by name (`node`, `npm`) is sandboxed,
because the tool goes through its wrapper. System binaries a task calls
(`ls`, `curl`) are **not** sandboxed. To sandbox a task, use task properties:

```toml
[tasks.build]
run = "npm run build"
deny_net = true
allow_write = ["./dist"]
```

## Debugging

```bash
mise-sbx dirs                          # resolved config/data/state paths
mise-sbx policy claude                 # effective policy + configured presets
mise-sbx policy claude -p omarchy      # same, with a preset applied (expanded flags)
mise-sbx --dry-run claude --version    # exact command, no side effects
tail -n 20 ~/.local/state/mise-sbx.log # what actually ran, and why
MISE_SANDBOX_LOG=0 mise-sbx ...        # skip the audit log
```

Sanity checks inside a project directory:

```bash
node -e "require('fs').readFileSync(process.env.HOME+'/.ssh/known_hosts')"   # EACCES expected
node -e "fetch('https://example.com').then(()=>console.log('ok'))"           # blocked expected
npm ping --registry=https://registry.npmjs.org                               # allowed expected
```

## Known bypasses and limits

- **Stale PATH.** Wrappers win only where mise's `command-wrappers/bin` is ahead
  of the install dirs, which `mise activate` and shims both do. A long-running
  process that captured `PATH` before the wrappers existed (editors, agent
  harnesses, tmux servers) still resolves raw install binaries and bypasses the
  sandbox. Restart it, or run `mise-sbx` explicitly.
- **Absolute paths.** `~/.local/share/mise/installs/<tool>/<version>/<bin>` runs
  unsandboxed. The `~/.local/bin/<agent>` launchers are sandboxed.
- **No namespaces.** Landlock + seccomp only: same-user processes are visible,
  Unix sockets (dbus, gpg-agent, keyring) are reachable when env and paths allow
  them. This stops prompt-injected agents and accidents, not a determined
  attacker. Use `syd`/`bubblewrap` if you need PID and network namespaces.
- **Per-host network** is not possible with mise; `--allow-net` is unsupported.
- **OAuth/browser flows** need `--sandbox=off` (or `--net -p home`) once.
- **Keyring/dbus** env vars are filtered; `gh` and similar may need
  `--env=all`.
- **Performance.** Every wrapped call pays a `mise x` startup plus a `bash -c`.
  Run hot loops inside one `mise-sbx` invocation.

## Verification after a change

```bash
mise-sbx sync
mise-sbx policy <tool>
fish -lc 'command -v <tool>'   # must print .../mise/command-wrappers/bin/<tool>
```

When you add, rename or remove a flag, value option, `-c` or a subcommand in
`mise-sbx`, update `~/.config/fish/completions/mise-sbx.fish` as well (presets
and tools are read from the policy automatically). Both files are plain text;
check the completion with `fish -n` and `fish -c 'complete -C"mise-sbx -"'`.

Reconciliation check (writes a launcher, then restores it):

```bash
omarchy-mise-install npm:@kitlangton/ghui ghui   # simulate an Omarchy rewrite
grep -n 'exec' ~/.local/bin/ghui                # old: exec mise x ...
mise-sbx sync                                   # repoints it
grep -n 'mise use -g\|exec' ~/.local/bin/ghui   # spec intact, exec mise-sbx
```

## Rollback

```bash
rm ~/.config/mise/conf.d/90-sandbox-wrappers.toml
rm ~/.local/bin/mise-sbx ~/.config/mise/sandbox.toml
# drop [hooks] postinstall from ~/.config/mise/config.toml
mise reshim
```

Then restore the Omarchy launchers' last line to
`exec mise x "<package>" -- "<bin>" "$@"` (or just run `omarchy-mise-install`
for each, which rewrites the template).
