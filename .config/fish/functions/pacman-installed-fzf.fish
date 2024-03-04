# Interactive browsing of installed pacman packages using fzf
# https://wiki.archlinux.org/title/Pacman/Tips_and_tricks#Browsing_packages
function pacman-installed-fzf
    pacman -Qq | fzf --preview 'pacman -Qil {}' --layout=reverse --bind 'enter:execute(pacman -Qil {} | less)'
end
