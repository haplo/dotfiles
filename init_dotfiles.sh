#!/usr/bin/env bash

pushd "$(dirname "${BASH_SOURCE}")" > /dev/null;

function doIt() {
    rsync --exclude ".git/" \
          --exclude "init_dotfiles.sh" \
          --exclude "README.md" \
          --exclude "LICENSE" \
          -avh --no-perms . ~;
    source ~/.bash_profile;
}

if [ "$1" == "--force" -o "$1" == "-f" ]; then
    doIt;
else
    read -p "This will overwrite existing files in your home directory. Are you sure? (y/n) " -n 1;
    echo "";
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        doIt;
    fi;
fi;
unset doIt;

popd > /dev/null;
