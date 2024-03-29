# ~/.bash_profile: executed by bash(1) for login shells.

# load the shell dotfiles, and then some:
# * ~/.path can be used to extend `$PATH`.
# * ~/.extra can be used for other local settings you don’t want to commit
for file in ~/.{path,bash_prompt,exports,aliases,functions}; do
    [ -r "$file" ] && [ -f "$file" ] && source "$file";
done;
unset file;

# autocorrect typos in path names when using `cd`
shopt -s cdspell;

# append to the history file, don't overwrite it
shopt -s histappend

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# enable some Bash 4 features when possible:
# * `autocd`, e.g. `**/qux` will enter `./foo/bar/baz/qux`
# * recursive globbing, e.g. `echo **/*.txt`
for option in autocd globstar; do
    shopt -s "$option" 2> /dev/null;
done;

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# Alias definitions.
# You may want to put all your additions into a separate file like
# ~/.bash_aliases, instead of adding them here directly.
# See /usr/share/doc/bash-doc/examples in the bash-doc package.

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if [ -f /etc/bash_completion ] && ! shopt -oq posix; then
    . /etc/bash_completion
fi

# use fzf if available
if [ -f /usr/share/doc/fzf/examples/key-bindings.bash ]; then
    source /usr/share/doc/fzf/examples/key-bindings.bash
fi
if [ -f /usr/share/doc/fzf/examples/completion.bash ]; then
    source /usr/share/doc/fzf/examples/completion.bash
fi

# use up and down keys to search in history
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'

# Use Guix if available
export GUIX_PROFILE="/home/fidel/.config/guix/current"
if [ -f "$GUIX_PROFILE/etc/profile" ]; then
    source "$GUIX_PROFILE/etc/profile"
fi
# https://guix.gnu.org/en/manual/devel/en/html_node/Getting-Started.html
export GUIX_PROFILE="/home/fidel/.guix-profile"
if [ -f "$GUIX_PROFILE/etc/profile" ]; then
    source "$GUIX_PROFILE/etc/profile"
    export SSL_CERT_DIR="$GUIX_PROFILE/etc/ssl/certs"
    export SSL_CERT_FILE="$SSL_CERT_DIR/ca-certificates.crt"
    export GIT_SSL_CAINFO="$SSL_CERT_FILE"
    export CURL_CA_BUNDLE="$SSL_CERT_FILE"
fi

# load .extra right at the end if present, this file is not in version control
# and is meant for this system specific changes
[ -r .extra ] && [ -f .extra ] && source .extra;
