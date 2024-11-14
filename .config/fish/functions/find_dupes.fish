function find_dupes -a path
    set path $argv[1]

    if test -z $path
        echo Usage: (status function)
        return 1
    else if not test -d $path
        echo "$path should be a directory"
        return 2
    end

    # https://unix.stackexchange.com/questions/277697/whats-the-quickest-way-to-find-duplicated-files
    # maybe not the quickest, but simple and with no dependencies
    find $path ! -empty -type f -print0 | xargs -0 md5sum | sort | uniq -w32 -dD
end
