# Split a FLAC using a CUE file and tag the splitted tracks
#
function splitflac -a base
    # drop trailing dot from base if user provides it, which is common when
    # autocompleting in a shell
    set base (string replace -r '\.$' '' $argv[1])
    set cuefile $base.cue
    set flacfile $base.flac
    # cuetag command is cuetag.sh in some systems, e.g. Arch Linux
    set cuetag cuetag

    if test -z $base
        echo "Usage: splitflac <basename>"
        echo
        echo "<basename> must be the common part to the .cue and .flac files."
        echo
        echo "For example when having two files Album Name.cue Album Name.flac"
        echo "call it like this:"
        echo
        echo "  \$ splitflac \"Album Name\""
        return 0
    end
    if not test -f $cuefile
        echo "$cuefile is not a file"
        return 1
    end
    if not test -f $flacfile
        echo "$flacfile is not a file"
        return 2
    end
    if not type -q cuetag
        if type -q cuetag.sh
            set cuetag cuetag.sh
        else
            echo "cuetag command missing, usually found in cuetools package"
            return 3
        end
    end
    if not type -q flac
        echo "flac command missing, usually found in flac package"
        return 4
    end
    if not type -q shnsplit
        echo "shnsplit command missing, usually found in shntool package"
        return 5
    end

    if not shnsplit -f $cuefile -o flac $flacfile
        echo "Error splitting into multiple track files"
        return 6
    end

    if not $cuetag $cuefile split-track*
        echo "Error tagging splitted track files"
        return 7
    end
end
