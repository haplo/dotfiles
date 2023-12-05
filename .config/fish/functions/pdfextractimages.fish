# extract images from a PDF file
function pdfextractimages -a pdffile -a output
    set pdffile $argv[1]
    set output $argv[2]
    # default to current directory
    test -z $output; and set output .

    if test -z $pdffile
        echo Usage: (status function) file.pdf
        return 1
    else if not test -f $pdffile
        echo "$pdffile is not a file"
        return 2
    else if not string match -q -i -e '*.pdf' $pdffile
        echo "$pdffile doesn't seem to be a PDF file"
        return 3
    else if not type -q pdfimages
        echo "pdfimages command must be installed, usually present in a poppler package"
        return 4
    end

    # extract JPEG and PNG images
    pdfimages -j -png $pdffile $output/

    # remove bad prefix (-) from images
    pushd $output
    for i in -*
        set new (string replace -f -r -- '^-' '' "$i")
        and mv ./$i $new
    end
    popd
end
