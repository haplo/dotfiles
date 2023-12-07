#!/usr/bin/env fish

function make_it_so
    copy_files
    setup_fish_vendor
    set_fish_universal_vars
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
end

if test -n "$argv[1]"; and test "$argv[1]" = -f
    make_it_so
else
    read -f -P "This will overwrite existing files in your home directory. Are you sure? (y/n) " -n 1 reply
    if string match -i $reply y
        make_it_so
    end
end
