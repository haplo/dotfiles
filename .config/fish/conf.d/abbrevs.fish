abbr -a mv 'mv -i'

abbr -a grep 'grep --color=auto'
abbr -a fgrep 'fgrep --color=auto'
abbr -a egrep 'egrep --color=auto'

abbr -a ga 'git add'
abbr -a gb 'git branch'
abbr -a gc 'git commit'
abbr -a gca 'git commit --amend'
abbr -a gcm 'git commit -m'
abbr -a gco 'git checkout'
abbr -a gd 'git diff'
abbr -a glo 'git log'
abbr -a glp 'git log -p'
abbr -a gp 'git push'
abbr -a gpu 'git pull'
abbr -a gri 'git rebase --interactive'
abbr -a gs 'git status -sb'

abbr -a d docker
abbr -a dc 'docker compose'
abbr -a dps 'docker ps -a'
abbr -a drm 'docker rm'
abbr -a dru 'docker run --rm -it'
abbr -a p podman
abbr -a pc 'podman compose'
abbr -a pps 'podman ps -a'
abbr -a prm 'podman rm'
abbr -a pru 'podman run --rm -it'

abbr -a la 'ls -a'
abbr -a ll 'ls -l'

# prefer eza instead of ls if available
if type -q eza
    abbr -a ls eza
    abbr -a la 'eza -a'
    abbr -a ll 'eza -al'
    abbr -a lt 'eza -aT'
    abbr -a llt 'eza -alT'
end

# use running Emacs if available
if type -q emacsclient
    abbr -a e 'emacsclient -a vim'
    abbr -a vi 'emacsclient -t -a vim'
    abbr -a vim 'emacsclient -t -a vim'
end

# https://github.com/sharkdp/bat is installed as batcat in Debian/Ubuntu
if type -q batcat && not type -q bat
    alias bat='batcat'
end

# https://github.com/sharkdp/fd is installed as fdfind in Debian/Ubuntu
if type -q fdfind && not type -q fd
    alias fd='fdfind'
end

abbr -a --set-cursor logs 'journalctl -xe%'
abbr -a --set-cursor logserr 'journalctl -xep3%'
abbr -a --set-cursor logswarn 'journalctl -xep4%'

abbr -a opencode 'firejail --profile=opencode --whitelist=(pwd) /usr/bin/opencode --standalone'
abbr -a opencode-local 'OPENCODE_CONFIG=~/.config/opencode/opencode-local.json OPENCODE_DISABLE_MODELS_FETCH=1 firejail --profile=opencode-local --whitelist=(pwd) /usr/bin/opencode --standalone'
