# Firejail profile for asgardex
# Description: Desktop wallet and exchange client for ThorChain
# This file is overwritten after every install/update
# Persistent local customizations
include asgardex.local
# Persistent global definitions
include globals.local

noblacklist ${HOME}/.config/ASGARDEX
mkdir ${HOME}/.config/ASGARDEX
whitelist ${HOME}/.config/ASGARDEX

private-cache
private-dev
private-etc alternatives,ca-certificates,crypto-policies,dconf,fonts,ld.so.cache,ld.so.preload,machine-id,pki,resolv.conf,ssl
ignore private-tmp

# app attempts to connect to dbus but seems to work fine when blocked
ignore dbus-user none
ignore dbus-system none

# Redirect
include electron-common.profile
