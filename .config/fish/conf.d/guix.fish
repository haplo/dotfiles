# Load Guix if installed in the system

if test -f "$HOME/.config/guix/current/etc/profile"
    GUIX_PROFILE="$HOME/.config/guix/current" fenv source "$GUIX_PROFILE/etc/profile"
end

if test -f "$HOME/.guix-profile/etc/profile"
    GUIX_PROFILE="$HOME/.guix-profile/" fenv source "$GUIX_PROFILE/etc/profile"
    set -gx SSL_CERT_DIR "$GUIX_PROFILE/etc/ssl/certs"
    set -gx SSL_CERT_FILE "$SSL_CERT_DIR/ca-certificates.crt"
    set -gx GIT_SSL_CAINFO "$SSL_CERT_FILE"
    set -gx CURL_CA_BUNDLE "$SSL_CERT_FILE"
end
