#!/bin/bash

export SSH_AUTH_SOCK="$XDG_RUNTIME_DIR/ssh-agent.socket"
export SSH_ASKPASS="/usr/bin/ksshaskpass"

[ -z "$SSH\_AGENT\_PID" ] || eval "$(ssh-agent -s -a $SSH_AUTH_SOCK)"
