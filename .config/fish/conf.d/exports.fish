# set PATH so it includes user's private bin if it exists
if test -d "$HOME/bin"
    fish_add_path $HOME/bin
end
if test -d "$HOME/.local/bin"
    fish_add_path $HOME/.local/bin
end

if test -d "$HOME/.cargo/bin"
    fish_add_path $HOME/.cargo/bin
end

if test -n "$GOPATH"
    fish_add_path $GOPATH/bin
end

if test -n "$DENO_INSTALL"
    fish_add_path $DENO_INSTALL/bin
end

if type -q most
    set -gx PAGER most
    set -gx MANPAGER most
else if type -q less
    set -gx PAGER less
    # don’t clear the screen after quitting a manual page
    set -gx MANPAGER 'less -X'
    # colored man pages
    set -gx LESS_TERMCAP_mb \e'[1;32m'
    set -gx LESS_TERMCAP_md \e'[1;32m'
    set -gx LESS_TERMCAP_me \e'[0m'
    set -gx LESS_TERMCAP_se \e'[0m'
    set -gx LESS_TERMCAP_so \e'[01;33m'
    set -gx LESS_TERMCAP_ue \e'[0m'
    set -gx LESS_TERMCAP_us \e'[1;4;31m'
end

set -gx LANG 'en_US.UTF-8'
set -gx LC_ALL 'en_US.UTF-8'

if type -q emacsclient
    set -gx EDITOR 'emacsclient --tty'
    set -gx VISUAL 'emacsclient --reuse-frame'
    set -gx ALTERNATE_EDITOR ""
end
set -gx SUDO_EDITOR rvim

# OnlyKey for GPG https://docs.crp.to/onlykey-agent.html
set -gx GNUPGHOME "$HOME/.gnupg/onlykey"

# make Python use UTF-8 encoding for output to stdin, stdout, and stderr
set -gx PYTHONIOENCODING UTF-8
# use ipdb for Python debugging by default
set -gx PYTHONBREAKPOINT 'ipdb.set_trace'

# https://golang.org/doc/code.html
set -gx GOPATH "$HOME/Code/go"

# https://wiki.debian.org/KVM
set -gx LIBVIRT_DEFAULT_URI 'qemu:///system'
set -gx VAGRANT_DEFAULT_PROVIDER libvirt
