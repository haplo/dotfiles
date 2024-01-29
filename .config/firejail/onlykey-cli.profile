# Firejail profile for onlykey
# Description: A command line interface to the OnlyKey

quiet

include disable-common.inc
include disable-devel.inc
include disable-programs.inc
include disable-shell.inc
include disable-write-mnt.inc
include disable-xdg.inc

apparmor
caps.drop all
hostname onlykey
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
novideo
protocol unix,inet,inet6,netlink
seccomp
tracelog

disable-mnt
# private
private-bin onlykey-cli,python,python3
private-cache
# private-dev
private-opt none
private-tmp

dbus-user none
dbus-system none

restrict-namespaces
