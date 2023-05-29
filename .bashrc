# ~/.bashrc: executed by bash(1) for non-login shells.
[ -n "$PS1" ] && source ~/.bash_profile

# set up direnv if available
# https://direnv.net/docs/hook.html
if $(which direnv &>/dev/null)
then
    eval "$(direnv hook bash)"
fi
