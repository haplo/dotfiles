# Completions for mise-sbx: run mise-managed tools inside mise's
# Landlock/seccomp sandbox. See ~/.config/mise/AGENTS.md.
#
# Presets and tools are read from the policy file when completing, so a new
# [presets.<name>] or [tools.<name>] section shows up without touching this
# file. The policy path follows mise-sbx's own resolution order:
# MISE_SBX_CONFIG, then MISE_CONFIG_DIR, XDG_CONFIG_HOME, ~/.config/mise.

function __fish_mise_sbx_policy
    if set -q MISE_SBX_CONFIG
        echo "$MISE_SBX_CONFIG"
    else if set -q MISE_CONFIG_DIR
        echo "$MISE_CONFIG_DIR/sandbox.toml"
    else if set -q XDG_CONFIG_HOME
        echo "$XDG_CONFIG_HOME/mise/sandbox.toml"
    else
        echo ~/.config/mise/sandbox.toml
    end
end

# Names of the [<table>.<name>] sections in the policy, one per line.
function __fish_mise_sbx_section
    set -l policy (__fish_mise_sbx_policy)
    test -f "$policy"; or return
    command grep -oE "^\[$argv[1]\.[^]]+\]" "$policy" 2>/dev/null |
        string replace -r "^\[$argv[1]\.(.*)\]" '$1' |
        command sort -u
end

function __fish_mise_sbx_presets
    printf '%s\n' home home-ro all
    __fish_mise_sbx_section presets
end

function __fish_mise_sbx_tools
    __fish_mise_sbx_section tools
end

# Tokens already typed after the command name (the partial token is excluded).
function __fish_mise_sbx_tokens
    set -l tokens (commandline -opc)
    set -e tokens[1]
    set -q tokens[1]; or return
    printf '%s\n' $tokens
end

# The option whose value is being typed, if any.
function __fish_mise_sbx_pending
    set -l tokens (__fish_mise_sbx_tokens)
    set -q tokens[1]; or return 1
    contains -- $tokens[-1] -c -a --allow --allow-ro -p --preset --env --sandbox
    and echo $tokens[-1]
end

function __fish_mise_sbx_pending_is
    set -l pending (__fish_mise_sbx_pending)
    test -n "$pending"; and contains -- $pending $argv
end

# True while mise-sbx still parses its own options, i.e. before the tool name,
# a `--` terminator or a `-c` command. Everything after those belongs to the
# child command.
function __fish_mise_sbx_still_options
    __fish_mise_sbx_pending >/dev/null; and return 1
    set -l skipping
    for token in (__fish_mise_sbx_tokens)
        if set -q skipping[1]
            set -e skipping
            continue
        end
        switch $token
            case -c
                return 1
            case --
                return 1
            case -a --allow --allow-ro -p --preset --env --sandbox
                set skipping 1
            case '-*'
            case '*'
                return 1
        end
    end
    return 0
end

# sync, dirs, policy and help only work as the very first argument.
function __fish_mise_sbx_at_start
    test (count (commandline -opc)) -eq 1
end

function __fish_mise_sbx_is_policy
    set -l tokens (commandline -opc)
    test (count $tokens) -ge 2; and test "$tokens[2]" = policy
end

function __fish_mise_sbx_policy_needs_tool
    __fish_mise_sbx_is_policy; and test (count (commandline -opc)) -le 2
end

function __fish_mise_sbx_after_double_dash
    set -l tokens (__fish_mise_sbx_tokens)
    set -q tokens[1]; and test "$tokens[-1]" = --
end

# Subcommands.
complete -c mise-sbx -n '__fish_mise_sbx_at_start' -f -a sync -d 'Regenerate the mise command wrappers'
complete -c mise-sbx -n '__fish_mise_sbx_at_start' -f -a dirs -d 'Show resolved config, data and state paths'
complete -c mise-sbx -n '__fish_mise_sbx_at_start' -f -a policy -d 'Show the effective policy for a tool'
complete -c mise-sbx -n '__fish_mise_sbx_at_start' -f -a help -d 'Show the help text'

# Options.
complete -c mise-sbx -n '__fish_mise_sbx_still_options' -s h -l help -f -d 'Show the help text'
complete -c mise-sbx -n '__fish_mise_sbx_still_options' -l net -f -d 'Allow network for this run'
complete -c mise-sbx -n '__fish_mise_sbx_still_options' -l no-net -f -d 'Deny network for this run'
complete -c mise-sbx -n '__fish_mise_sbx_still_options' -s c -x -d 'Run a shell command instead of a tool'
complete -c mise-sbx -n '__fish_mise_sbx_still_options' -s p -l preset -x -a '(__fish_mise_sbx_presets)' -d 'Add a grant preset (repeatable)'
complete -c mise-sbx -n '__fish_mise_sbx_still_options' -s a -l allow -x -a '(__fish_complete_directories)' -d 'Grant read/write access to a path (repeatable)'
complete -c mise-sbx -n '__fish_mise_sbx_still_options' -l allow-ro -x -a '(__fish_complete_directories)' -d 'Grant read-only access to a path (repeatable)'
complete -c mise-sbx -n '__fish_mise_sbx_still_options' -l env -x -a 'min all' -d 'Environment: min (default) or all'
complete -c mise-sbx -n '__fish_mise_sbx_still_options' -l sandbox -x -a 'on off' -d 'Sandbox: on (default) or off'
complete -c mise-sbx -n '__fish_mise_sbx_still_options' -l dry-run -f -d 'Print the command instead of running it'

# Value of an option that is waiting for one.
complete -c mise-sbx -n '__fish_mise_sbx_pending_is -p --preset' -x -a '(__fish_mise_sbx_presets)' -d 'Preset'
complete -c mise-sbx -n '__fish_mise_sbx_pending_is -a --allow --allow-ro' -x -a '(__fish_complete_directories)' -d 'Directory'
complete -c mise-sbx -n '__fish_mise_sbx_pending_is --env' -x -a min -d 'Minimal environment (default)'
complete -c mise-sbx -n '__fish_mise_sbx_pending_is --env' -x -a all -d 'Pass the whole environment'
complete -c mise-sbx -n '__fish_mise_sbx_pending_is --sandbox' -x -a off -d 'Disable the sandbox for this run'
complete -c mise-sbx -n '__fish_mise_sbx_pending_is --sandbox' -x -a on -d 'Keep the sandbox (default)'
complete -c mise-sbx -n '__fish_mise_sbx_pending_is -c' -x

# The tool name comes from [tools.<name>] in the policy.
complete -c mise-sbx -n '__fish_mise_sbx_still_options' -f -a '(__fish_mise_sbx_tools)' -d 'Sandboxed tool'
complete -c mise-sbx -n '__fish_mise_sbx_after_double_dash' -f -a '(__fish_mise_sbx_tools)' -d 'Sandboxed tool'

# policy <tool> [-p PRESET]
complete -c mise-sbx -n '__fish_mise_sbx_is_policy' -s h -l help -f -d 'Show the help text'
complete -c mise-sbx -n '__fish_mise_sbx_is_policy' -s p -l preset -x -a '(__fish_mise_sbx_presets)' -d 'Preset to preview'
complete -c mise-sbx -n '__fish_mise_sbx_policy_needs_tool' -f -a '(__fish_mise_sbx_tools)' -d 'Tool'

# Arguments after the tool belong to the tool, so never fall back to file
# completion for them (the exceptions above supply directories themselves).
complete -c mise-sbx -f
