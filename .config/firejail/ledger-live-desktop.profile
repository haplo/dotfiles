# Firejail profile for Ledger Live
# This file is overwritten after every install/update
# Persistent local customizations
include ledger-live.local
# Persistent global definitions
include globals.local

noblacklist ${HOME}/.config/Ledger Live

mkdir ${HOME}/.config/Ledger Live
whitelist ${HOME}/.config/Ledger Live
whitelist ${DOWNLOADS}
include whitelist-common.inc
include whitelist-usr-share-common.inc
include whitelist-runuser-common.inc
include whitelist-var-common.inc

apparmor
caps.drop all
ipc-namespace
machine-id
netfilter
nodbus
nodvd
nogroups
nonewprivs
noroot
notv
nou2f
nosound
novideo
protocol unix,inet,inet6,netlink
seccomp !chroot
shell none
tracelog # - breaks on Arch?

disable-mnt
#private-bin bash,sh
private-cache
private-dev
private-etc alternatives,fonts
#private-etc alternatives,asound.conf,ca-certificates,crypto-policies,fonts,nsswitch.conf,pki,pulse,selinux,ssl,X11,xdg
private-lib
private-opt ledger-live
private-tmp

# Redirect
include electron.profile
