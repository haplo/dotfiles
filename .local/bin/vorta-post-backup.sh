#!/bin/bash
set -euo pipefail

SNAPPER_CONFIG="home"
SNAPSHOT_LINK="$HOME/.vorta-snapshot"
STATE_FILE="/tmp/vorta-snap-num-$(id -u)"

# Remove the symlink
rm -f "$SNAPSHOT_LINK"

# Delete the snapshot (optional — remove this block to keep them)
if [[ -f "$STATE_FILE" ]]; then
    SNAP_NUM=$(cat "$STATE_FILE")
    echo "Deleting snapshot #${SNAP_NUM}"
    snapper -c "$SNAPPER_CONFIG" delete "$SNAP_NUM"
    rm -f "$STATE_FILE"
fi

echo "Cleanup complete"
