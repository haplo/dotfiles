# Interactive browsing of all packages known to pacman using fzf
# https://wiki.archlinux.org/title/Pacman/Tips_and_tricks#Browsing_packages
function pacman-all-fzf
    pacman -Slq | fzf --preview 'pacman -Si {}' --layout=reverse
end
