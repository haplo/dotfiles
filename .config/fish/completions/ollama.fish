# MIT License
# Copyright (c) 2023 Schuldkröte
# https://github.com/Schuldkroete/ollama-fish-completion

# installed models
function __fish_ollama_models
    ollama list | awk '{if (NR>1) {print $1}}'
end

# repo models
function __fish_ollama_repo_models
    curl -s "https://ollama.ai/library" | grep --only-matching "\"/library/.*\" " | string trim | string trim -c \" | string split / -f 3
end

# ollama
complete -c ollama -f
set -l subcommands serve start create show run pull push list ls cp rm help
complete -c ollama -n "not __fish_seen_subcommand_from $subcommands" -a serve -d "Start ollama"
complete -c ollama -n "not __fish_seen_subcommand_from $subcommands" -a create -d "Create a model from a Modelfile"
complete -c ollama -n "not __fish_seen_subcommand_from $subcommands" -a show -d "Show information for a model"
complete -c ollama -n "not __fish_seen_subcommand_from $subcommands" -a run -d "Run a model"
complete -c ollama -n "not __fish_seen_subcommand_from $subcommands" -a pull -d "Pull a model from a registry"
complete -c ollama -n "not __fish_seen_subcommand_from $subcommands" -a push -d "Push a model to a registry"
complete -c ollama -n "not __fish_seen_subcommand_from $subcommands" -a list -d "List models"
complete -c ollama -n "not __fish_seen_subcommand_from $subcommands" -a cp -d "Copy a model"
complete -c ollama -n "not __fish_seen_subcommand_from $subcommands" -a rm -d "Remove a model"
complete -c ollama -n "not __fish_seen_subcommand_from $subcommands" -a help -d "Help about any command"

# create
complete -c ollama -n "__fish_seen_subcommand_from create; and not __fish_seen_subcommand_from __fish_ollama_models" -a "(__fish_ollama_models)"
complete -c ollama -n "__fish_seen_subcommand_from create" -s f -l file -F -d "Name of the Modelfile (default \"Modelfile\")"

# show
complete -c ollama -n "__fish_seen_subcommand_from show; and not __fish_seen_subcommand_from __fish_ollama_models" -a "(__fish_ollama_models)"
complete -c ollama -n "__fish_seen_subcommand_from show; and __fish_seen_subcommand_from __fish_ollama_models" -l license -d "Show license of a model"
complete -c ollama -n "__fish_seen_subcommand_from show; and __fish_seen_subcommand_from __fish_ollama_models" -l modelfile -d "Show Modelfile of a model"
complete -c ollama -n "__fish_seen_subcommand_from show; and __fish_seen_subcommand_from __fish_ollama_models" -l parameters -d "Show parameters of a model"
complete -c ollama -n "__fish_seen_subcommand_from show; and __fish_seen_subcommand_from __fish_ollama_models" -l system -d "Show system prompt of a model"
complete -c ollama -n "__fish_seen_subcommand_from show; and __fish_seen_subcommand_from __fish_ollama_models" -l template -d "Show template of a model"

# run
complete -c ollama -n "__fish_seen_subcommand_from run; and not __fish_seen_subcommand_from __fish_ollama_models" -a "(__fish_ollama_models)" -d local
complete -c ollama -n "__fish_seen_subcommand_from run; and not __fish_seen_subcommand_from __fish_ollama_repo_models" -a "(__fish_ollama_repo_models)" -d download
complete -c ollama -n "__fish_seen_subcommand_from run; and __fish_seen_subcommand_from __fish_ollama_models; or __fish_seen_subcommand_from __fish_ollama_models __fish_ollama_repo_models" -l insecure -d "Use an insecure registry"
complete -c ollama -n "__fish_seen_subcommand_from run; and __fish_seen_subcommand_from __fish_ollama_models; or __fish_seen_subcommand_from __fish_ollama_models __fish_ollama_repo_models" -l nowordwrap -d "Don't wrap words to the next line automatically"
complete -c ollama -n "__fish_seen_subcommand_from run; and __fish_seen_subcommand_from __fish_ollama_models; or __fish_seen_subcommand_from __fish_ollama_models __fish_ollama_repo_models" -l verbose -d "Show timings for response"

# pull
complete -c ollama -n "__fish_seen_subcommand_from pull; and not __fish_seen_subcommand_from __fish_ollama_repo_models" -a "(__fish_ollama_repo_models)"
complete -c ollama -n "__fish_seen_subcommand_from pull; and __fish_seen_subcommand_from __fish_ollama_repo_models" -l insecure -d "Use an insecure registry"

# push
complete -c ollama -n "__fish_seen_subcommand_from push; and not __fish_seen_subcommand_from __fish_ollama_models" -a "(__fish_ollama_models)"
complete -c ollama -n "__fish_seen_subcommand_from push; and __fish_seen_subcommand_from __fish_ollama_models" -l insecure -d "Use an insecure registry"

# cp
complete -c ollama -n "__fish_seen_subcommand_from cp; and not __fish_seen_subcommand_from __fish_ollama_models" -a "(__fish_ollama_models)"

# rm
complete -c ollama -n "__fish_seen_subcommand_from rm" -a "(__fish_ollama_models)"

# generic
complete -c ollama -s h -l help -d "show help"
complete -c ollama -n "not __fish_seen_subcommand_from $subcommands" -s v -l version -d "version for ollama"
