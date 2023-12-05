# transform MTS files to MKV by copying video and audio
function mts2mkv -a mtsfile
    set -l mtsfile $argv[1]
    if test -z $mtsfile
        echo Usage: (status function) file.mts
        return 1
    else if not test -f $mtsfile
        echo "$mtsfile is not a file"
        return 2
    else if not string match -q -i -r '.mts$' $mtsfile
        echo "$mtsfile doesn't seem to be a .mts file"
        return 3
    else if not type -q ffmpeg
        echo "ffmpeg must be installed for the video conversion"
        return 4
    end

    set -l mkvfile (string replace -f -r '(.*).(mts|MTS)$' '$1.mkv' $mtsfile)
    or echo "Error calculating .mkv output path"

    echo "### Remuxing $mtsfile into $mkvfile ###"
    echo
    ffmpeg -i "$mtsfile" -vcodec copy -acodec copy "$mkvfile"
end
