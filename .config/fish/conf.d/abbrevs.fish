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

abbr -a la 'ls -a'
abbr -a ll 'ls -l'

# prefer exa instead of ls if available
if type -q exa
    abbr -a ls exa
    abbr -a ee 'exa -alF'
    abbr -a ll 'exa -alF'
    abbr -a ea 'exa -a'
    abbr -a la 'exa -a'
end

# prefer eza instead of ls/exa if available
if type -q eza
    abbr -a ls eza
    abbr -a ee 'eza -alF'
    abbr -a ll 'eza -alF'
    abbr -a ea 'eza -a'
    abbr -a la 'eza -a'
end

# use running Emacs if available
if type -q emacsclient
    abbr -a e 'emacsclient -a vim'
    abbr -a vi 'emacsclient -t -a vim'
    abbr -a vim 'emacsclient -t -a vim'
end

# https://github.com/sharkdp/fd is installed as fdfind in Debian/Ubuntu
if type -q fdfind && not type -q fd
    alias fd='fdfind'
end
