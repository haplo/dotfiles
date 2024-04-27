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

private-bin asgardex
private-cache
?HAS_APPIMAGE: ignore private-dev
private-dev
private-etc alternatives,ca-certificates,crypto-policies,dconf,fonts,ld.so.cache,ld.so.preload,machine-id,pki,resolv.conf,ssl
private-opt asgardex
private-tmp

# Redirect
include electron.profile
