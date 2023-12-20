# transform a .cbr file into .cbz
function cbr2cbz -a cbrfile
    set cbrfile $argv[1]
    set cbzfile (path change-extension .cbz $cbrfile)

    if test -z $cbrfile
        echo Usage: (status function) file.cbr
        return 1
    else if test (string lower (path extension $cbrfile)) != '.cbr'
        echo "$cbrfile doesn't seem to be a .cbr file"
        return 2
    else if not test -f $cbrfile
        echo "$cbrfile not found"
        return 3
    else if test -e $cbzfile
        echo "$cbzfile already exists"
        return 4
    else if not type -q unrar-free
        echo "unrar-free must be installed to extract the cbr file"
        return 5
    else if not type -q zip
        echo "zip must be installed to create the cbz file"
        return 6
    end

    if set -l tmpdir (mktemp -d)
        echo "Using $tmpdir for temporary extraction"
    else
        echo "Couldn't create a temporary directory for extraction"
        return 10
    end

    if not unrar-free $cbrfile $tmpdir >/dev/null
        echo "Error extracting $cbrfile into $tmpdir"
        rmdir $tmpdir
        return 11
    end

    echo "Creating $cbzfile"
    if not zip -9 --recurse-paths --quiet $cbzfile "$tmpdir"/*
        echo "Error creating $cbzfile"
        return 12
    end

    echo "Created $cbzfile"
    rm -rf $tmpdir
end
