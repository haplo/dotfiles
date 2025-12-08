#!/usr/bin/env fish

function get_hostname
    if type -q hostname
        hostname
    else if type -q hostnamectl
        hostnamectl --static
    else if test -f /etc/hostname
        read -l host_from_file < /etc/hostname
        echo $host_from_file | string trim
    else
        echo "Error: cannot reliably get hostname" >&2
        exit 2
    end
end

set current_hostname (get_hostname)
set current_date (date +%Y-%m-%d)
set backup_dir "$HOME/Backups/$current_hostname/packages"
set temp_file (mktemp)

function save_if_changed -a input_file -a suffix
    set -l target_file "$backup_dir/$current_date$suffix.txt"

    # regex matches YYYY-MM-DD followed optionally by suffix, ending in .txt
    set -l pattern
    if test -z "$suffix"
        set pattern '^\d{4}-\d{2}-\d{2}\.txt$'
    else
        set pattern "^\d{4}-\d{2}-\d{2}$suffix\.txt\$"
    end

    # find the most recent backup file that matches the specific pattern
    set -l latest_backup_name (ls -1 $backup_dir 2>/dev/null | string match -r $pattern | sort | tail -n 1)

    if test -n "$latest_backup_name"
        set -l latest_backup_path "$backup_dir/$latest_backup_name"

        if cmp -s $input_file $latest_backup_path
            echo "No changes in package list compared to $latest_backup_path. Skipping."
            rm $input_file
            return
        end
    end

    # if we reach here, either no backup exists or content is different
    mv $input_file $target_file
    echo "Installed packages backup saved: $target_file"
    notify-send \
        --urgency=normal \
        --wait \
        --icon=backup \
        "New backup of installed OS packages: $target_file"
end

mkdir -p $backup_dir

if type -q apt
    # https://www.debian.org/doc/manuals/debian-reference/ch10.en.html#_backup_and_recovery_policy
    dpkg --get-selections > $temp_file
    save_if_changed $temp_file ""
else if type -q pacman
    # https://wiki.archlinux.org/title/Migrate_installation_to_new_hardware#List_of_installed_packages
    pacman -Qqen > $temp_file
    save_if_changed $temp_file ""
    pacman -Qqem > $temp_file
    save_if_changed $temp_file "_aur"
else
    echo "Error: Neither apt nor pacman found." >&2
    rm $temp_file
    exit 1
end
