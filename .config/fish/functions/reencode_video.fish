# This function is designed to reencode videos shot by my digital camera and
# phones into smaller versions, while keeping metadata (EXIF tags and the like)
function reencode_video -a vid
    set vid $argv[1]
    set newvid (path change-extension .x265.mp4 $vid)

    if test -z $vid
        echo Usage: (status function) video.mp4
        return 1
    else if not test -f $vid
        echo "$vid not found"
        return 2
    else if test -e $newvid
        echo "$newvid already exists"
        return 3
    else if not type -q ffmpeg
        echo "ffmpeg must be installed to encode the video"
        return 4
    else if not type -q exiftool
        echo "exiftool must be installed to copy the video metadata"
        return 5
    end

    if not ffmpeg -i $vid -c:v libx265 -crf 24 -c:a libopus -b:a 112k -preset slow $newvid
        echo "Error encoding $vid into $newvid"
        return 6
    end

    echo "Copying metadata from $vid to $newvid"
    if not exiftool -tagsFromFile $vid -All:All -overwrite_original $newvid
        echo "Error copying metadata from $vid to $newvid"
        return 7
    end

    echo "Created $newvid"
end
