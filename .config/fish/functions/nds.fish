# Get a shell inside a Podman container with NodeJS
#
# Current directory will be mounted in /app
#
# Will create a nodehome volume if it doesn't exist, and map it to /home/node
# inside the Docker container. This enables persisting globally installed npm
# packages.
function nds
    if not type -q podman
        echo "Podman is required"
        return 1
    end
    if not podman volume exists nodehome
        echo "Creating volume nodehome"
        podman volume create nodehome >/dev/null
    end
    podman run \
        -it \
        --rm \
        --user=node \
        --mount type=volume,src=nodehome,target=/home/node \
        -v $PWD:/app:rw \
        --workdir /app \
        --entrypoint=/bin/bash \
        --network host \
        node:18-bullseye \
        $argv
end
