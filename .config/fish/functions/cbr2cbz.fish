# transform a .cbr file into .cbz
function cbr2cbz -a cbrfile
    set -l cbrfile $argv[1]
    if not set -q cbrfile
        echo "Usage: cbr2cbz file.cbr"
        return 1
    else if not string match -q -r '.cbr$' $cbrfile
        echo "$cbrfile doesn't seem to be a .cbr file"
        return 2
    else if not test -f $cbrfile
        echo "$cbrfile not found"
        return 3
    else if not type -q unrar-free
        echo "unrar-free must be installed to extract the cbr file"
        return 4
    else if not type -q zip
        echo "zip must be installed to create the cbz file"
        return 5
    end

    set -l tmpdir (mktemp -d)
    if test -z $tmpdir
        echo "Couldn't create a temporary directory for extraction"
        return 6
    else
        echo "Using $tmpdir for temporary extraction"
    end

    set -l base (basename $cbrfile .cbr)

    unrar-free $cbrfile $tmpdir >/dev/null
    or echo "Error extracting $cbrfile into $tmpdir" && return 7

    echo "Creating $base.cbz"
    zip -9rq $base.cbz "$tmpdir"/*
    or echo "Error creating $base.cbz" && return 8

    echo "Created $base.cbz"
    rm -rf $tmpdir
end
