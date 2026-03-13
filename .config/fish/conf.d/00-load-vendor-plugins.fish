set -l vendor_dir $__fish_config_dir/vendor

for plugin in $vendor_dir/*/
    if test -d "$plugin/functions"
        set -p fish_function_path "$plugin/functions"
    end

    if test -d "$plugin/completions"
        set -p fish_complete_path "$plugin/completions"
    end

    for f in $plugin/conf.d/*.fish
        source "$f"
    end
end
