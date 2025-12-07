#!/usr/bin/env fish

# Pull yadm changes with signature verification
# Need to force a merge (--no-rebase --ff-only) otherwise --verify-signatures won't work
# 2>&1 captures both standard output and errors
# string collect preserves newlines for the notification body
set -l output (yadm pull --autostash --no-rebase --ff-only --verify-signatures 2>&1 | string collect)
set -l result $status

if test $result -eq 0
    # Success: Check if there were actual changes
    if string match -q "Already up to date.*" -- $output
        echo "Dotfiles already up to date"
    else
        # Success with changes
        echo "Dotfiles update SUCCESS: $output"
        notify-send \
            --urgency=normal \
            --icon=software-update-available \
            "Dotfiles updated" "$output"
    end
else
    # Failure: GPG error, merge conflict, or network issue
    echo "Dotfiles update FAILED: $output" >&2
    notify-send \
        --urgency=critical \
        --icon=dialog-error \
        "Dotfiles update FAILED" "$output"
end
