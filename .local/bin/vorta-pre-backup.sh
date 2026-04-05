#!/bin/bash
set -euo pipefail

SNAPPER_CONFIG="home"
SNAPSHOT_LINK="$HOME/.vorta-snapshot"
STATE_FILE="/tmp/vorta-snap-num-$(id -u)"

# Clean up any stale state from a previous failed run
if [[ -f "$STATE_FILE" ]]; then
    OLD_SNAP=$(cat "$STATE_FILE")
    echo "WARNING: Cleaning up stale snapshot #${OLD_SNAP}"
    rm -f "$SNAPSHOT_LINK"
    snapper -c "$SNAPPER_CONFIG" delete "$OLD_SNAP" 2>/dev/null || true
    rm -f "$STATE_FILE"
fi

# Create a new read-only snapshot
SNAP_NUM=$(snapper -c "$SNAPPER_CONFIG" create \
    --type single \
    --read-only \
    --description "vorta-backup-$(date +%Y%m%dT%H%M%S)" \
    --cleanup-algorithm number \
    --print-number)

if [[ -z "$SNAP_NUM" ]]; then
    echo "ERROR: Failed to create snapshot" >&2
    exit 1
fi

# Determine the snapshot path
# Adjust this if your home subvolume mount point differs
SNAP_PATH="/home/.snapshots/${SNAP_NUM}/snapshot"

# Verify it exists
if [[ ! -d "$SNAP_PATH" ]]; then
    echo "ERROR: Snapshot path $SNAP_PATH does not exist" >&2
    exit 1
fi

# Create/update a stable symlink Vorta can use
ln -sfn "$SNAP_PATH" "$SNAPSHOT_LINK"

# Persist the snapshot number for the post-backup script
echo "$SNAP_NUM" > "$STATE_FILE"

echo "Created snapshot #${SNAP_NUM} → ${SNAP_PATH}"
echo "Symlinked at ${SNAPSHOT_LINK}"
