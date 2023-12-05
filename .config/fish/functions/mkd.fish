function mkd -a dir
    set -l dir $argv[1]
    if test -z $dir
        echo "Usage: mkd <dir>"
        return 1
    else if test -e $dir
        echo "$dir already exists, entering it"
        cd $dir
        return 2
    end

    mkdir -p $dir && cd $dir
end
