# Firejail profile for onlykey-agent
# Description: SSH agent for the OnlyKey

quiet

# Persistent local customisations
include onlykey-agent.local

# Persistent global definitions
include globals.local

# Allow ssh (blacklisted by disable-common.inc)
# include allow-ssh.inc

blacklist /tmp/.X11-unix
blacklist ${RUNUSER}/wayland-*

include disable-common.inc
include disable-programs.inc
