complete -c ai-research -f -a "(__fish_complete_ai_research_projects)"

function __fish_complete_ai_research_projects
    set -l base_dir $AI_RESEARCH_DIR
    test -d $base_dir; or return
    for entry in $base_dir/*/
        basename $entry
    end
end
