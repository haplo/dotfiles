function find_dupes
    set -l dir $argv[1]

    if test -z "$dir"
        echo Usage: (status function)
        return 1
    else if not test -d "$dir"
        echo "$dir should be a directory"
        return 2
    end

    # https://unix.stackexchange.com/questions/277697/whats-the-quickest-way-to-find-duplicated-files
    # maybe not the quickest, but simple and with no dependencies
    # xargs needs to batch the arguments to avoid argc getting over the 128 limit
    find "$dir" ! -empty -type f -print0 | xargs -0 -n 125 md5sum | sort | uniq -w32 -dD
end
