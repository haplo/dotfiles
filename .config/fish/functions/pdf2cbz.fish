# Transform a PDF into a CBZ comic file
function pdf2cbz -a pdffile
    set pdffile $argv[1]
    set cbzfile (string replace -f -r '.pdf$' .cbz $pdffile)
    or echo "$pdffile doesn't seem to be a .pdf file" && return 1

    if test -z $pdffile
        echo Usage: (status function) file.pdf
        return 2
    else if not test -f $pdffile
        echo "$pdffile is not a file"
        return 3
    else if test -e $cbzfile
        echo "$cbzfile already exists"
        return 4
    else if not type -q pdfimages
        echo "pdfimages command must be installed, usually present in a poppler package"
        return 5
    end

    set tmpdir (mktemp -d)
    and echo "Using $tmpdir for temporary extraction"
    or echo "Couldn't create a temporary directory for extraction" && return 6

    # extract images from PDF
    pdfextractimages $pdffile $tmpdir

    # create CBZ comic file and delete the extracted images
    set images $tmpdir/*.{jpg,JPG,jpeg,JPEG,png,PNG}
    if test (count $images) -eq 0
        echo "No images extracted from $pdffile, stopping"
        return 7
    end

    echo "Creating $cbzfile"
    zip -9 --move --junk-paths --quiet $cbzfile $images
    or echo "Error creating $cbzfile" && return 7

    echo "Created $cbzfile"
    rm -rf $tmpdir

    # remove original PDF file, prompting user first
    rm -i $pdffile
end
