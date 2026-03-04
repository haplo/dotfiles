whitelist ${HOME}/.mame

# disable network connectivity
net none

disable-mnt
private-etc empty
private-opt empty
private-srv empty
private-tmp
ignore noinput
private-dev

# private-bin mame

protocol unix,inet,inet6,netlink


apparmor
nodbus

include default.profile
