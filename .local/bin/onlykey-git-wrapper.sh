#!/bin/sh
# This is a git SSH wrapper (GIT_SSH_COMMAND / core.sshCommand) that picks an
# onlykey-agent identity based on the SSH destination and then exec's ssh with
# the agent socket in scope.
#
# It avoids the need to manually call onlykey-agent <identity> -- git push
# it's handled transparently.
#
# Identity selection:
#   1) If $ONLYKEY_IDENTITY is set in the environment, use it verbatim.
#   2) Otherwise, look up the destination host in the identity_for() map.
#   3) Fall back to the host string itself (e.g. github.com) as identity
#
# If needing different identities for the same host:
#   1) Use SSH host aliases in ~/.ssh/config:
#     Host gh-personal
#         HostName github.com
#         User git
#     Host gh-work
#         HostName github.com
#         User git
#   2) change host in git remote set-url git@gh-work:acme/widgets.git
#   3) Add entry to identity_for below.
#

set -eu

# --- user-editable identity map ------------------------------------------
# Keys are SSH hosts (i.e. real DNS names OR ~/.ssh/config Host aliases).
# Values are the identity string passed to onlykey-agent.
identity_for() {
    case "$1" in
        aur.archlinux.org) echo "haplo@archlinux.org" ;;
        git.fidelramos.net)  echo "fidelramos.net" ;;
        # default: use host as onlykey-agent identity
        *)              echo "$1" ;;
    esac
}

# ssh -G is a config dump; no connection, no agent needed.
case " $* " in
    *" -G "*) exec ssh "$@" ;;
esac

dest=
skip_next=0
for arg do
    if [ "$skip_next" = 1 ]; then
        skip_next=0
        continue
    fi
    case "$arg" in
        --)                 break ;;                  # remote cmd follows
        -[bBcDEeFIiJLlmOopQRSWw])
                            skip_next=1 ;;            # value is next arg
        -*)                 ;;                        # bundled or flag
        *)                  dest="$arg"; break ;;
    esac
done

if [ -z "${dest:-}" ]; then
    echo "onlykey-ssh: could not determine SSH destination from: $*" >&2
    exec ssh "$@"
fi

# Normalise destination -> bare host.
case "$dest" in
    ssh://*)
        d=${dest#ssh://}; d=${d%%/*}
        host=${d#*@}; host=${host%:*} ;;
    *@*)  host=${dest#*@} ;;
    *)    host=$dest ;;
esac

identity=${ONLYKEY_IDENTITY:-$(identity_for "$host")}

# HACK: onlykey-agent prints a challenge code prompt to stdout, but
# we need a clean stdout for git communication. The solution is to create
# a named pipe to redirect
fifo=$(mktemp -u "${TMPDIR:-/tmp}/onlykey-ssh.$$.XXXXXX")
mkfifo -m 600 "$fifo"
trap 'rm -f "$fifo"' EXIT INT TERM HUP

# Hold the FIFO open RDWR on fd 9 so opens don't block and we control EOF.
exec 9<>"$fifo"

# Bridge: FIFO -> wrapper's original stdout. Must close fd 9 in this child,
# otherwise cat inherits a writer end of its own input and never sees EOF.
cat <"$fifo" 9<&- &
bridge_pid=$!

# Agent's stdout -> stderr (so the challenge prompt is visible).
# Inner `sh -c` redirects ssh's stdout to the FIFO before exec'ing ssh.
# 9<&- ensures Python and its subprocesses don't hold an extra writer.
onlykey-agent "$identity" -- \
    sh -c 'exec ssh "$@" >"$0"' "$fifo" "$@" 9<&- >&2
status=$?

# Close our write side. Now no writers remain -> cat sees EOF and exits.
exec 9>&-

wait "$bridge_pid" 2>/dev/null || true
exit "$status"
