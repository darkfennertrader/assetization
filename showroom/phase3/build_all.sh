#!/usr/bin/env bash
# Regenerate all artefacts in showroom/phase3/.
# Run by the user: bash showroom/phase3/build_all.sh
set -euo pipefail
cd "$(dirname "$0")"

# ── 1. Render PNGs from Graphviz sources ─────────────────────────────────────
for dot_file in *.dot; do
  [ -f "$dot_file" ] || continue
  png_file="${dot_file%.dot}.png"
  dot -Tpng "$dot_file" -o "$png_file"
  echo "OK  $png_file"
done
