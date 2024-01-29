# Firejail profile for OnlyKey
# Description: The official app for OnlyKey
#
# OnlyKey package install is in /opt, so run it with:
# /usr/bin/firejail --profile OnlyKey /opt/OnlyKey/nw
#
# You can also edit OnlyKey.desktop:
#
# [Desktop Entry]
# Exec=/usr/bin/firejail --profile OnlyKey /opt/OnlyKey/nw
# [...]

quiet

# Persistent local customisations
include OnlyKey.local

# Persistent global definitions
include globals.local

include disable-common.inc
include disable-devel.inc
include disable-exec.inc
include disable-interpreters.inc
include disable-programs.inc
#include disable-shell.inc
include disable-write-mnt.inc
include disable-xdg.inc

whitelist /opt/OnlyKey

mkdir ${HOME}/.config/OnlyKey
whitelist ${HOME}/.config/OnlyKey
mkdir ${HOME}/.cache/OnlyKey
whitelist ${HOME}/.cache/OnlyKey

# Add to OnlyKey.local with the directory you want for OnlyKey backups
# mkdir ${HOME}/backups/onlykey
# whitelist ${HOME}/backups/onlykey

# include whitelist-common.inc
include whitelist-runuser-common.inc
include whitelist-usr-share-common.inc
include whitelist-var-common.inc

caps.drop all
hostname onlykey
ipc-namespace
machine-id

# blocks App update check, add ignore net none to OnlyKey.local to enable
net none

netfilter
nodvd
nogroups
noinput
nonewprivs
nosound
notv

# noroot

# unix protocol needed for X11 connection (even if using XWayland)
# netlink protocol needed for USB device interaction
protocol unix,netlink

seccomp
tracelog

disable-mnt
private
private-cache
# see /usr/share/doc/firejail/profile.template for more common private-etc paths.
private-lib
private-opt OnlyKey
private-tmp
