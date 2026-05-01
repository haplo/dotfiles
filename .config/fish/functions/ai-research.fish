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

    # copy scripts for searches
    if not test -d .research/bin
        mkdir -p .research/bin
    end
    if not test -e .research/bin/research-run-init.py
        cp ~/.local/share/opencode/research-agent/bin/research-run-init.py .research/bin/
    end
    if not test -e .research/bin/research-run-validate.py
        cp ~/.local/share/opencode/research-agent/bin/research-run-validate.py .research/bin/
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

    if test -z (git status --porcelain 2>/dev/null)
        # start sandboxed opencode
        firejail --profile=opencode-research /usr/bin/opencode
    else
        echo "WARNING: dirty git repository, clean before starting opencode"
    end
end
