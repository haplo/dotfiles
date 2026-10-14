# set PATH so it includes user's private bin if it exists
if test -d "$HOME/.local/bin"
    fish_add_path $HOME/.local/bin
end

if test -d "$HOME/.cargo/bin"
    fish_add_path $HOME/.cargo/bin
end

if test -n "$DENO_INSTALL"
    fish_add_path $DENO_INSTALL/bin
end

# https://golang.org/doc/code.html
set -gx GOPATH "$HOME/Code/go"
if test -n "$GOPATH"/bin
    fish_add_path $GOPATH/bin
end
