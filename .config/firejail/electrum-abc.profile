# Firejail profile for electrum-abc
# Description: Lightweight eCash wallet
# This file is overwritten after every install/update
# Persistent local customizations
include electrum-abc.local
# Persistent global definitions
include globals.local

noblacklist ${HOME}/.electrum-abc

# Allow python (blacklisted by disable-interpreters.inc)
include allow-python3.inc

# Add to electrum-abc.local if installed from AppImage
#ignore include disable-shell.inc

include disable-common.inc
include disable-devel.inc
include disable-exec.inc
include disable-interpreters.inc
include disable-programs.inc
include disable-shell.inc
include disable-xdg.inc

mkdir ${HOME}/.electrum-abc
whitelist ${HOME}/.electrum-abc
include whitelist-common.inc
include whitelist-var-common.inc

caps.drop all
#ipc-namespace
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
# Add to electrum-abc.local if installed from AppImage
#private-bin electrum-abc,dirname,python*,readlink,sh
private-bin electrum-abc,python*
private-cache
?HAS_APPIMAGE: ignore private-dev
private-dev
private-etc alternatives,ca-certificates,crypto-policies,dconf,fonts,ld.so.cache,ld.so.preload,machine-id,pki,resolv.conf,ssl
private-opt electrum-abc
private-tmp

restrict-namespaces
