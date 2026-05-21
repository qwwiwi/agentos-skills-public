#!/usr/bin/env bash
# Usage: return-skill.sh <run-dir>
# Removes rented skill directories, keeps manifest.
set -euo pipefail

RUN_DIR="${1:?run dir required}"
RENTED="$RUN_DIR/rented-skills"

[[ -d "$RENTED" ]] || { echo "nothing to return"; exit 0; }

for d in "$RENTED"/*/; do
  [[ -d "$d" ]] && rm -rf "$d"
done

echo "rentals cleaned, manifest preserved at $RENTED/.rental-manifest.json"
