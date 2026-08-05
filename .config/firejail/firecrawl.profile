# Firejail profile for firecrawl-cli
# Description: Command-line interface for Firecrawl

quiet

include disable-common.inc
include disable-devel.inc
include disable-programs.inc
include disable-shell.inc
include disable-write-mnt.inc
include disable-xdg.inc

mkdir ${HOME}/.config/firecrawl-cli
noblacklist ${HOME}/.config/firecrawl-cli
whitelist ${HOME}/.config/firecrawl-cli

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
private-cache
private-dev
private-etc @default,@tls-ca
private-opt none
private-tmp

dbus-user none
dbus-system none

restrict-namespaces
