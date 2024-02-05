#!/usr/bin/env fish

function make_it_so
    copy_files
    setup_fish_vendor
    set_fish_universal_vars
    setup_emacs
end

function copy_files
    set message "Copying files to $HOME"
    set length (string length $message)
    echo (string repeat --no-newline -n $length "*")
    echo $message
    echo (string repeat --no-newline -n $length "*")
    rsync \
        --exclude ".git/" \
        --exclude ".dir-locals.el" \
        --exclude "init_dotfiles.sh" \
        --exclude "init_dotfiles.fish" \
        --exclude "update_vendor.fish" \
        --exclude "README.md" \
        --exclude LICENSE \
        -avh . $HOME
    # fix permissions of files in .ssh, ssh will complain if they are world-readable
    find $HOME/.ssh/ -type d -print0 | xargs -0 chmod 700
    find $HOME/.ssh/ -type f -print0 | xargs -0 chmod 600
    find $HOME/.ssh/*.pub -type f -print0 | xargs -0 chmod 644
end

function setup_fish_vendor
    echo
    echo "********************************"
    echo "Setting up fish vendored plugins"
    echo "********************************"
    rsync -av --remove-source-files $HOME/.config/fish/vendor/*/* $HOME/.config/fish/
    rm -rf $HOME/.config/fish/vendor/
end

function set_fish_universal_vars
    echo
    echo "********************************"
    echo "Setting fish universal variables"
    echo "********************************"

    echo "Unsetting fish_greeting"
    set -U fish_greeting

    set enabled_features ampersand-nobg-in-token,qmark-noglob,regex-easyesc,stderr-nocaret
    echo "Enabling fish_features:" $enabled_features
    set -U fish_features $enabled_features

    echo "Enabling pure prompt show root prefix"
    set -U pure_show_prefix_root_prompt true

    echo "Enabling pure prompt show error code in prompt"
    set -U pure_separate_prompt_on_error true
end

function setup_emacs
    echo
    echo "******************************"
    echo "Setting up emacs configuration"
    echo "******************************"
    if type -q emacs
        echo Emacs installation found at (which emacs), version (emacs --version)[1]
        if test -e $HOME/.emacs.d
            echo "Emacs config already found at $HOME/.emacs.d, skipping further configuration"
        else
            set repo https://github.com/haplo/dotemacs
            set target $HOME/.emacs.d
            echo "Downloading Emacs config from $repo to $target"
            git clone $repo $target
        end
    else
        echo "No Emacs installation detected, skipping Emacs configuration"
    end
end

if test -n "$argv[1]"; and test "$argv[1]" = -f
    make_it_so
else
    read -f -P "This will overwrite existing files in your home directory. Are you sure? (y/n) " -n 1 reply
    if string match -i $reply y
        make_it_so
    end
end
