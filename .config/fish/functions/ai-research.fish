function ai-research --description "Initialize or open an AI agent research project"
    if test (count $argv) -lt 1
        echo "Usage: ai-research <project-name>"
        return 1
    end

    set -l project_name $argv[1]
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

    # start sandboxed opencode
    firejail --profile=opencode-research /usr/bin/opencode
end
