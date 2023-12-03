# https://github.com/PatrickF1/fzf.fish#configuration
set fzf_diff_highlighter diff-so-fancy
set fzf_fd_opts --hidden --exclude=.git
if type -q eza
    set fzf_preview_dir_cmd eza --all --color=always
else if type -q exa
    set fzf_preview_dir_cmd exa --all --color=always
end
