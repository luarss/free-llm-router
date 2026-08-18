#!/usr/bin/env bash
# Copy the canonical providers.json into each package so both ship self-contained.
# Run this after editing the root providers.json. CI can diff to enforce it.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
src="$root/providers.json"

dests=(
  "$root/python/src/tollfree/providers.json"
  "$root/js/src/providers.json"
)

for dest in "${dests[@]}"; do
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  echo "synced -> ${dest#$root/}"
done
