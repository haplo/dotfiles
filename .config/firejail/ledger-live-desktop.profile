# Firejail profile for Ledger Live
# This file is overwritten after every install/update
# Persistent local customizations
include ledger-live-desktop.local
# Persistent global definitions
include globals.local

noblacklist ${HOME}/.config/Ledger Live

mkdir ${HOME}/.config/Ledger Live
whitelist ${HOME}/.config/Ledger Live
whitelist ${DOWNLOADS}
whitelist /opt/ledger-live
include whitelist-common.inc
include whitelist-usr-share-common.inc
include whitelist-runuser-common.inc
include whitelist-var-common.inc

apparmor
caps.drop all
ipc-namespace
machine-id
netfilter
nodvd
nogroups
nonewprivs
noroot
notv
nosound
novideo
protocol unix,inet,inet6,netlink
seccomp !chroot
tracelog

disable-mnt
private-cache
# enabling private-dev blocks USB hardware wallets
# private-dev
private-etc alternatives,ca-certificates,crypto-policies,host.conf,nsswitch.conf,pki,resolv.conf,rpc,selinux,ssl
private-lib
private-tmp

# app attempts to connect to dbus but seems to work fine when blocked
dbus-user none
dbus-system none