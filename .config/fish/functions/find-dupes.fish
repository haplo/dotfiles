function find-dupes
    argparse d/delete -- $argv
    or return

    set -l dir $argv[1]

    if test -z "$dir"
        echo "Usage: find-dupes [-d|--delete] <path>"
        return 1
    else if not test -d "$dir"
        echo "$dir should be a directory"
        return 2
    end

    set -l lines (find "$dir" ! -empty -type f -print0 | xargs -0 -n 125 md5sum | sort | uniq -w32 -dD)

    if test (count $lines) -eq 0
        echo "No duplicates found."
        return 0
    end

    if not set -q _flag_delete
        printf '%s\n' $lines
        return 0
    end

    # Interactive deletion mode: walk the sorted output and group by hash
    set -l current_hash ""
    set -l group

    for line in $lines
        set -l hash (string sub -l 32 -- "$line")
        set -l file (string replace -r '^[a-f0-9]{32}\s+' '' -- "$line")

        if test "$hash" != "$current_hash" -a "$current_hash" != ""
            __find_dupes_prompt $group
            set group
        end

        set current_hash "$hash"
        set -a group "$file"
    end

    # Process the last group
    if test (count $group) -gt 0
        __find_dupes_prompt $group
    end
end


function __find_dupes_prompt
    set -l files $argv
    set -l n (count $files)

    echo
    echo "Duplicate group ($n files):"
    for i in (seq $n)
        echo "  $i) $files[$i]"
    end
    echo "  a) Keep all"

    while true
        read -P "Keep which file? [1-$n/a]: " choice

        switch "$choice"
            case a
                echo "  Keeping all."
                return
            case '*'
                if string match -qr '^\d+$' -- "$choice"
                    and test "$choice" -ge 1
                    and test "$choice" -le $n
                    for i in (seq $n)
                        if test "$i" -ne "$choice"
                            rm -- "$files[$i]"
                            echo "  Deleted: $files[$i]"
                        end
                    end
                    echo "  Kept: $files[$choice]"
                    return
                end
        end

        echo "  Invalid choice, try again."
    end
end
