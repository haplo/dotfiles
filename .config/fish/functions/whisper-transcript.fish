function whisper-transcript --description "Transcribe audio to .txt and .srt with whisper.cpp"
    if not type -q whisper-cli
        echo "whisper-cli command missing, usually found in whisper.cpp packages"
        return 1
    end
    if not type -q ffmpeg
        echo "ffmpeg command missing"
        return 1
    end

    if test (count $argv) -ne 2
        echo "Usage: whisper-transcript <language> <input-file>" >&2
        return 1
    end

    set -l lang $argv[1]
    set -l input $argv[2]

    if not test -f $input
        echo "Error: input file '$input' does not exist" >&2
        return 2
    end

    set -l base (path change-extension '' -- $input)
    set -l txt $base.txt
    set -l srt $base.srt

    for f in $txt $srt
        if test -e $f
            echo "Error: output file '$f' already exists" >&2
            return 3
        end
    end

    set -l whisper_model ~/Code/AI/whisper-models/ggml-large-v3.bin
    ffmpeg -loglevel error -i $input -ar 16000 -ac 1 -f wav - \
        | whisper-cli -m $whisper_model -f - -l $lang -otxt -osrt -of $base

    if test $pipestatus[1] -ne 0 -o $pipestatus[2] -ne 0
        echo "Error: transcription failed" >&2
        return 4
    end
end
