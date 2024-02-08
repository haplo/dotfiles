# source /etc/profile in login shells
if status is-login && test -e /etc/profile
    fenv source /etc/profile
end

# enable direnv if available
if type -q direnv
    direnv hook fish | source
end

# keybindings
bind \cg _fzf_grep_directory
bind \eo fish_onlykey_agent_prepend
