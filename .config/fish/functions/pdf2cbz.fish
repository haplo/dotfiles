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

    if set -l tmpdir (mktemp -d)
        echo "Using $tmpdir for temporary extraction"
    else
        echo "Couldn't create a temporary directory for extraction"
        return 6
    end

    # extract images from PDF
    if not pdfextractimages $pdffile $tmpdir
        echo "Error extracting images from $pdffile"
        return 7
    end

    # create CBZ comic file and delete the extracted images
    set images $tmpdir/*.{jpg,JPG,jpeg,JPEG,png,PNG}
    if test (count $images) -eq 0
        echo "No images extracted from $pdffile, stopping"
        return 8
    end

    echo "Creating $cbzfile"
    if not zip -9 --move --junk-paths --quiet $cbzfile $images
        echo "Error creating $cbzfile"
        return 9
    end

    echo "Created $cbzfile"
    rm -rf $tmpdir
end
