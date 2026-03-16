#!/usr/bin/env fish

# Update files in .config/fish/vendor/ to their latest upstream versions

function __download_and_update_vendor
    set name $argv[1]
    set url $argv[2]

    echo "Updating $name from $url"
    set paths_to_copy $argv[3..]
    set tmp_dir (mktemp --directory)
    or echo "Error creating temporary directory" && return 1
    and echo "Extracting files to $tmp_dir"

    curl -L $url | tar xzf - --strip-components=1 -C $tmp_dir

    for path in $paths_to_copy
        rm -r $HOME/.config/fish/vendor/$name/$path/
        cp -r $tmp_dir/$path $HOME/.config/fish/vendor/$name/
    end
    rm -rf $tmp_dir
    echo
end

function __update_fzf_fish
    set DIRS_TO_COPY completions conf.d functions
    __download_and_update_vendor fzf-fish https://github.com/PatrickF1/fzf.fish/archive/refs/heads/main.tar.gz $DIRS_TO_COPY
end

function __update_pure
    set DIRS_TO_COPY conf.d functions
    __download_and_update_vendor pure https://github.com/pure-fish/pure/archive/refs/heads/master.tar.gz $DIRS_TO_COPY
end

function update-fish-vendored-plugins
    __update_fzf_fish
    __update_pure
    # force yadm add because ~/.config/fish/vendor/ is in .gitignore
    yadm add -f $HOME/.config/fish/vendor/
end
