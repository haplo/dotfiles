# Firejail profile for tagutil
# Description: CLI music files tags editor
# This file is overwritten after every install/update
# Persistent local customizations
include tagutil.local
# Persistent global definitions
include globals.local

noblacklist ${MUSIC}

include disable-common.inc
include disable-devel.inc
include disable-exec.inc
include disable-interpreters.inc
include disable-programs.inc
include disable-shell.inc
include disable-write-mnt.inc
include disable-xdg.inc

apparmor
caps.drop all
ipc-namespace
machine-id
net none
netfilter
no3d
nodvd
nogroups
noinput
nonewprivs
noroot
nosound
notv
nou2f
novideo
protocol unix,inet,inet6
seccomp
# tracelog

# disable-mnt
# private-bin
private-dev
private-etc alternatives
private-opt none
private-tmp

dbus-user none
dbus-system none

restrict-namespaces
