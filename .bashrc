# ~/.bashrc: executed by bash(1) for non-login shells.
[ -n "$PS1" ] && source ~/.bash_profile

# set up direnv if available
# https://direnv.net/docs/hook.html
if $(which direnv &>/dev/null)
then
    eval "$(direnv hook bash)"
fi

# gpg-agent as ssh-agent
unset SSH_AGENT_PID
if [ "${gnupg_SSH_AUTH_SOCK_by:-0}" -ne $$ ]; then
  export SSH_AUTH_SOCK="$(gpgconf --list-dirs agent-ssh-socket)"
fi
export GPG_TTY=$(tty)
