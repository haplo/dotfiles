# Firejail profile for jellyfin-media-player
# Description: Official Jellyfin desktop client
# This file is overwritten after every install/update
# Persistent local customizations
include jellyfinmediaplayer.local
# Persistent global definitions
include globals.local

noblacklist ${HOME}/.local/share/jellyfinmediaplayer

include disable-common.inc
include disable-devel.inc
include disable-exec.inc
include disable-programs.inc

include whitelist-common.inc
include whitelist-player-common.inc
include whitelist-run-common.inc
include whitelist-runuser-common.inc
include whitelist-var-common.inc

apparmor
caps.drop all
netfilter
nogroups
noinput
nonewprivs
noroot
nou2f
protocol unix,inet,inet6,netlink
seccomp

private-bin jellyfinmediaplayer
private-dev
private-tmp

# dbus-user filter
# dbus-user.own org.mpris.MediaPlayer2.vlc
# dbus-user.talk org.freedesktop.Notifications
# dbus-user.talk org.freedesktop.ScreenSaver
# ?ALLOW_TRAY: dbus-user.talk org.kde.StatusNotifierWatcher
# dbus-user.talk org.mpris.MediaPlayer2.Player
# dbus-system none

restrict-namespaces
