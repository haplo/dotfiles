set -U fish_greeting
set -U fish_features ampersand-nobg-in-token,qmark-noglob,regex-easyesc,stderr-nocaret

# source /etc/profile in login shells
if status is-login && test -e /etc/profile
    fenv source /etc/profile
end

# enable direnv if available
if type -q direnv
    direnv hook fish | source
end
