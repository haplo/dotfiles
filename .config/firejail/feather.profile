# Firejail profile for feather
# Description: A free, open-source Monero light wallet
# This file is overwritten after every install/update
# Persistent local customizations
include feather.local
# Persistent global definitions
include globals.local

noblacklist ${HOME}/.config/feather

include disable-common.inc
include disable-devel.inc
include disable-exec.inc
include disable-interpreters.inc
include disable-programs.inc
include disable-shell.inc
include disable-xdg.inc

mkdir ${HOME}/.config/feather
whitelist ${HOME}/.config/feather

# add mkdir and whitelist for where your Monero wallets are to feather.local
# mkdir ${HOME}/.monero
# whitelist ${HOME}/.monero

include whitelist-common.inc
include whitelist-var-common.inc

caps.drop all
ipc-namespace
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

disable-mnt
private-bin feather
private-cache
?HAS_APPIMAGE: ignore private-dev
private-dev
private-etc alternatives,ca-certificates,crypto-policies,dconf,fonts,ld.so.cache,ld.so.preload,machine-id,pki,resolv.conf,ssl
private-tmp

# dbus-user none
# dbus-system none

restrict-namespaces
