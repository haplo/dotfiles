#!/usr/bin/env fish

# Update files in .config/fish/vendor/ to their latest upstream versions

function download_and_update
    set name $argv[1]
    set url $argv[2]
    echo "Updating $name from $url"
    set paths_to_copy $argv[3..]
    set tmp_dir (mktemp --directory)
    or echo "Error creating temporary directory" && return 1
    and echo "Extracting files to $tmp_dir"
    curl -L $url | tar xzf - --strip-components=1 -C $tmp_dir
    for path in $paths_to_copy
        cp $tmp_dir/$path/* .config/fish/vendor/$name/$path/
    end
    rm -rf $tmp_dir
    echo
end

function update_fzf_fish
    set FILES_TO_COPY completions/ conf.d/ functions/
    download_and_update fzf-fish https://github.com/PatrickF1/fzf.fish/archive/refs/heads/main.tar.gz $FILES_TO_COPY
end

function update_pure
    set FILES_TO_COPY conf.d/ functions/
    download_and_update pure https://github.com/pure-fish/pure/archive/refs/heads/master.tar.gz $FILES_TO_COPY
end

update_fzf_fish
update_pure
