alias mv='mv -i'

alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

alias ga='git add'
alias gp='git push'
alias gl='git log'
alias glp='git log -p'
alias gs='git status -sb'
alias gd='git diff'
alias gc='git commit'
alias gca='git commit --amend'
alias gcm='git commit -m'
alias gcma='git commit -ma'
alias gb='git branch'
alias gco='git checkout'
alias gra='git remote add'
alias gri='git rebase --interactive'
alias grr='git remote rm'
alias gpu='git pull'
alias gcl='git clone'

alias la='ls -a'
alias ll='ls -l'

# use exa instead of ls if available
if type -q exa
    alias e='exa'
    alias ls='exa'
    alias ee='exa -alF'
    alias ll='exa -alF'
    alias ea='exa -a'
    alias la='exa -a'
end

# use eza instead of ls if available
if type -q eza
    alias e='eza'
    alias ls='eza'
    alias ee='eza -alF'
    alias ll='eza -alF'
    alias ea='eza -a'
    alias la='eza -a'
end


# use running Emacs if available
if type -q emacsclient
    alias e='emacsclient -a vim'
    alias vi='emacsclient -t -a vim'
    alias vim='emacsclient -t -a vim'
end

# https://github.com/sharkdp/fd is installed as fdfind in Debian/Ubuntu
if type -q fdfind
    alias fd='fdfind'
end
