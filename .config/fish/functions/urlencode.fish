function urlencode
    python -c "import sys; from urllib.parse import quote; print(quote(sys.argv[1]));"
end
