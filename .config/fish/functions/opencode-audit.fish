function opencode-audit
    if test (count $argv) -ne 1
        echo "Usage: opencode-scan <url>"
        return 1
    end
    set -l url $argv[1]

    mkdir /tmp/agents
    set -l tmpdir (mktemp -d -p /tmp/agents)
    echo "Working in $tmpdir"
    cd $tmpdir

    set -l filename (basename $url)
    switch $filename
        case '*.zip' '*.tar.gz' '*.tgz' '*.tar.bz2' '*.tbz2' '*.tar.xz' '*.txz' '*.tar'
            curl -L -o $filename $url
            switch $filename
                case '*.zip'
                    unzip -q $filename
                case '*.tar.gz' '*.tgz'
                    tar -xzf $filename
                case '*.tar.bz2' '*.tbz2'
                    tar -xjf $filename
                case '*.tar.xz' '*.txz'
                    tar -xJf $filename
                case '*.tar'
                    tar -xf $filename
            end
            set -l extracted_dir (find . -maxdepth 1 -mindepth 1 -type d | head -1)
            if test -n "$extracted_dir"
                cd $extracted_dir
            end
        case '*.git'
            git clone --depth 1 $url
            set -l repo_name (basename $url .git)
            cd $repo_name
        case '*'
            if string match -q 'git@*' $url; or string match -q 'ssh://*' $url; or string match -q '*github.com*' $url; or string match -q '*gitlab.com*' $url; or string match -q '*bitbucket.org*' $url
                git clone --depth 1 $url
                set -l repo_name (basename $url .git)
                cd $repo_name
            else
                echo "Cannot determine if URL is a git repo or archive: $url"
                return 1
            end
    end
    firejail --profile=opencode --whitelist=$repo_name /usr/bin/opencode run --standalone "Check this project for any malicious code. Report anything suspicious, or OK if everything looks good, no need for a detailed report."
end
