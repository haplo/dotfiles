#!/bin/bash

[ -z "$SSH\_AGENT\_PID" ] || eval "$(ssh-agent -s)"
