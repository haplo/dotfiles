#!/usr/bin/env bash

pushd "$(dirname "${BASH_SOURCE}")" > /dev/null;

function doIt() {
    echo -e "\n********************************\nCopying files to $HOME\n********************************\n"
    rsync --exclude ".git/" \
          --exclude ".dir-locals.el" \
          --exclude "init_dotfiles.sh" \
          --exclude "update_vendor.sh" \
          --exclude "README.md" \
          --exclude "LICENSE" \
          -avh --no-perms . $HOME;
    # set up fish vendored plugins
    echo -e "\n********************************\nSetting up fish vendored plugins\n********************************\n"
    rsync -av --remove-source-files $HOME/.config/fish/vendor/*/* $HOME/.config/fish/
    rm -rf $HOME/.config/fish/vendor/
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

# create persistent Docker volume for NodeJS containers (see .aliases)
if command -v docker &> /dev/null; then
    if ! docker volume inspect nodehome &> /dev/null; then
        echo "Creating Docker volume nodehome"
        docker volume create nodehome > /dev/null
    fi
fi

popd > /dev/null;
