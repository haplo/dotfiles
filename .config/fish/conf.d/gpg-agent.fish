# gpg-agent as ssh-agent
if status --is-interactive
    set -e SSH_AGENT_PID

    if not set -q gnupg_SSH_AUTH_SOCK_by
        set -gx SSH_AUTH_SOCK (gpgconf --list-dirs agent-ssh-socket)
    else if test "$gnupg_SSH_AUTH_SOCK_by" != "$fish_pid"
        set -gx SSH_AUTH_SOCK (gpgconf --list-dirs agent-ssh-socket)
    end

    set -gx GPG_TTY (tty)
end
