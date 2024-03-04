# Interactive browsing of all packages known to paru using fzf
# https://wiki.archlinux.org/title/Pacman/Tips_and_tricks#Browsing_packages
function paru-all-fzf
    paru -Slq | fzf --preview 'paru -Si {}' --layout=reverse
end
