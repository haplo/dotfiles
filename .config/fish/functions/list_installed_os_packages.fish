# function that outputs to stdout a list of all installed OS packages
function list_installed_os_packages
    if type -q apt
        # Debian/Ubuntu
        apt list --installed
    else if type -q pacman
        # Arch Linux
        pacman -Q
    else
        # Unknown
        echo "Unknown OS, don't know how to list installed packages."
    end
end
