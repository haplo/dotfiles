function urldecode
    python -c "import sys; from urllib.parse import unquote; print(unquote(sys.argv[1]));"
end
