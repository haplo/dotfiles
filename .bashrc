# Omarchy environment (OMARCHY_PATH + PATH), needed even for non-interactive shells
[[ -r /usr/share/Omarchy/default/bash/env-bootstrap ]] && source /usr/share/omarchy/default/bash/env-bootstrap

# If not running interactively, don't do anything else (leave this above the rc source)
[[ $- != *i* ]] && return

# set up mise if available
# https://mise.jdx.dev/
if command -v mise &> /dev/null; then
  eval "$(mise activate bash)"
fi

# set up direnv if available
# https://direnv.net/docs/hook.html
if command -v direnv &> /dev/null; then
    eval "$(direnv hook bash)"
fi

# use gpg-agent as ssh-agent
unset SSH_AGENT_PID
if [ "${gnupg_SSH_AUTH_SOCK_by:-0}" -ne $$ ]; then
  export SSH_AUTH_SOCK="$(gpgconf --list-dirs agent-ssh-socket)"
fi
export GPG_TTY=$(tty)

# All the default Omarchy aliases and functions
# (don't mess with these directly, just overwrite them here!)
source "$OMARCHY_PATH/default/bash/rc"

# my config overrides
# * ~/.config/bash/extra can be used for local settings not to commit
for file in ~/.config/bash/{path,exports,init,aliases,functions,prompt,extra}; do
    [ -r "$file" ] && [ -f "$file" ] && source "$file";
done;
unset file;
