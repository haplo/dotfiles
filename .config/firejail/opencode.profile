# Firejail profile for opencode
# Description: DESCRIPTION OF THE PROGRAM
# This file is overwritten after every install/update
quiet
# Persistent local customizations
include opencode.local
# Persistent global definitions
include globals.local

# allow executables in HOME, see disable-exec.inc
ignore noexec ${HOME}

# blacklisted by disable-programs.inc
noblacklist ${HOME}/.cache/opencode
noblacklist ${HOME}/.config/opencode
noblacklist ${HOME}/.local/share/opencode

# Allows files commonly used by IDEs
#include allow-common-devel.inc

# Disable Wayland
blacklist ${RUNUSER}/wayland-*
# Disable RUNUSER (cli only; supersedes Disable Wayland)
blacklist ${RUNUSER}
# Remove the next blacklist if your system has no /usr/libexec dir,
# otherwise try to add it.
blacklist /usr/libexec

# disable-*.inc includes
# remove disable-write-mnt.inc if you set disable-mnt
#include disable-common.inc
#include disable-exec.inc
include disable-proc.inc
#include disable-programs.inc
#include disable-shell.inc
include disable-write-mnt.inc
include disable-x11.inc
include disable-xdg.inc

mkdir ${HOME}/.cache/opencode
whitelist ${HOME}/.cache/opencode
mkdir ${HOME}/.config/opencode
whitelist ${HOME}/.config/opencode
mkdir ${HOME}/.local/share/opencode
whitelist ${HOME}/.local/share/opencode
#include whitelist-common.inc
#include whitelist-run-common.inc
#include whitelist-runuser-common.inc
#include whitelist-usr-share-common.inc
#include whitelist-var-common.inc

# Commands that reduce access to resources.
#apparmor
caps.drop all
##caps.keep CAPS
##hostname NAME
# CLI only
ipc-namespace
# breaks audio and sometimes dbus related functions
machine-id
no3d
nodvd
nogroups
noinput
nonewprivs
noprinters
noroot
nosound
notv
nou2f
novideo
protocol unix,inet,inet6
seccomp
#tracelog

disable-mnt
private-cache
private-dev
private-etc alternatives,ca-certificates,crypto-policies,dconf,fonts,ld.so.cache,ld.so.preload,machine-id,pki,resolv.conf,ssl
private-tmp

dbus-user none
dbus-system none

# Note: read-only entries should usually go in disable-common.inc (especially
# entries for configuration files that allow arbitrary command execution).
##deterministic-shutdown
##env VAR=VALUE
##join-or-start NAME
#memory-deny-write-execute
##noexec PATH
##read-only ${HOME}
##read-write ${HOME}
#restrict-namespaces
