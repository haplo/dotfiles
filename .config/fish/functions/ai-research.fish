function ai-research --description "Initialize or open an AI agent research project"
    # -f (force flag) must be first argument, before project_name
    set -l force_flag false
    set -l arg_idx 1
    if test "$argv[1]" = "-f"
        set force_flag true
        set arg_idx 2
    end

    if test (count $argv) -lt $arg_idx
        echo "Usage: ai-research [-f] <project-name> [opencode-args...]"
        return 1
    end

    set -l project_name $argv[$arg_idx]
    set -l opencode_args
    set -l total_args (count $argv)
    if test $total_args -gt $arg_idx
        for i in (seq (math $arg_idx + 1) $total_args)
            set -a opencode_args $argv[$i]
        end
    end
    set -l base_dir $RESEARCH_DIR
    set -l project_dir "$base_dir/$project_name"

    # Ensure base and project directories exist
    mkdir -p $project_dir
    cd $project_dir; or return 1

    # Create opencode.json if it doesn't exist
    if not test -e opencode.json
        echo '{
  "$schema": "https://opencode.ai/config.json",
  "default_agent": "researcher",
  "agent": {
    "build": {
      "disable": true
    },
    "plan": {
      "disable": true
    }
  }
}' > opencode.json
        echo "Created opencode.json"
    end

    # copy scripts to track search runs into the project for agents to execute
    if not test -d .research/bin
        mkdir -p .research/bin
    end
    # copy latest version of the scripts
    cp ~/.local/share/opencode/research-agent/bin/research-run-{init,validate}.py .research/bin/

    # Initialize git repository if not already a repo
    if not test -d .git
        git init -q
        # Set local git user and email for the researcher agent to commit
        git config --local user.name "Researcher Agent"
        git config --local user.email "researcher@agent.local"
        git add opencode.json
        git commit -m "Initial commit"
        echo "Initialized git repository"
    end

    # Create .research/runs/ directory
    if not test -d .research/runs
        mkdir -p .research/runs
        echo "Created .research/runs/"
    end

    # check if git is dirty before starting opencode
    if test "$force_flag" = "true"; or test (git status --porcelain | count) -eq 0
        # start sandboxed opencode
        # direnv exec is necessary to set environment variables via .envrc
        direnv exec . firejail --profile=opencode-research /usr/bin/opencode $opencode_args
    else
        echo "WARNING: dirty git repository, clean before starting opencode"
        echo
        git status
    end
end
