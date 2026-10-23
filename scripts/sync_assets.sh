#!/usr/bin/env bash
# Copy the model and data assets the app needs from another deployment.
#
# The assets are not tracked by git, so they are copied from the test deployment
# to the production one. Only the paths used by src/constants.py are copied, and
# nothing is copied unless all of them exist.
#
# Usage, from the root of the destination deployment (with its venv activated):
#   scripts/sync_assets.sh <root of the source deployment>
set -euo pipefail

src_root="${1:?Usage: $0 <root of the source deployment>}"

mapfile -t paths < <(python -c "
from src.constants import AVERAGES, CLASSIFIER, OPERATIONS, REGRESSOR
print(*[AVERAGES, CLASSIFIER, OPERATIONS, REGRESSOR], sep='\n')
")

for path in "${paths[@]}"; do
    if [ ! -e "$src_root/$path" ]; then
        echo "Missing asset in the source deployment: $path" >&2
        exit 1
    fi
done

for path in "${paths[@]}"; do
    mkdir -p "$(dirname "$path")"
    # Copy beside the destination, then swap, so a failed copy keeps the old asset
    # and files that no longer exist in the source do not stay behind
    rm -rf "$path.new"
    cp -a "$src_root/$path" "$path.new"
    rm -rf "$path"
    mv "$path.new" "$path"
    echo "Synced $path"
done
