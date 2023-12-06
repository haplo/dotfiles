set -U fish_greeting
set -U fish_features ampersand-nobg-in-token,qmark-noglob,regex-easyesc,stderr-nocaret

# enable direnv if available
if type -q direnv
    direnv hook fish | source
end

# source /etc/profile with bash
if status is-login
    exec bash -c "test -e /etc/profile && source /etc/profile;\
    exec fish"
end
