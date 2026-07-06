#!/usr/bin/env bash
# Regenerate ALL user-facing artefacts in docs/.
# Run by the user: bash docs/build_all.sh
set -euo pipefail
cd "$(dirname "$0")"

REPO_ROOT="$(cd .. && pwd)"

# ── Preprocessing helper ──────────────────────────────────────────────────────
preprocess() {
  local src="$1"
  local tmp
  tmp="$(mktemp /tmp/build-all-XXXXXX.md)"
  LC_ALL=C.UTF-8 sed \
    -e 's/✓/Yes/g' -e 's/✔/Yes/g' \
    -e 's/✗/No/g'  -e 's/✘/No/g' \
    -e 's/○/Partial/g' -e 's/●/Full/g' \
    -e 's/☑/Yes/g' -e 's/☒/No/g' \
    -e 's/→/->/g'  -e 's/↔/<->/g' -e 's/←/<-/g' \
    -e 's/≥/>=/g'  -e 's/≤/<=/g'  -e 's/≈/~/g' \
    -e 's/×/x/g'   -e 's/÷/\//g' \
    -e 's/—/ - /g' -e 's/–/-/g'  -e 's/…/.../g' \
    -e 's/·/*/g' \
    "$src" > "$tmp"
  echo "$tmp"
}

build_pdf() {
  local src="$1"
  local out="$2"
  local tmp
  tmp="$(preprocess "$src")"
  pandoc "$tmp" \
    --defaults="$REPO_ROOT/.clinerules/pdf-toolkit/pandoc-defaults.yaml" \
    --lua-filter="$REPO_ROOT/.clinerules/pdf-toolkit/expand-tables.lua" \
    -H "$REPO_ROOT/.clinerules/pdf-toolkit/pandoc-header.tex" \
    --pdf-engine=xelatex \
    --pdf-engine-opt="-interaction=nonstopmode" \
    --pdf-engine-opt="-halt-on-error" \
    --resource-path="$REPO_ROOT/docs:$REPO_ROOT" \
    -o "$out" 2>&1
  rm -f "$tmp"
}

# ── 1. Render PNGs from Graphviz sources ─────────────────────────────────────
echo "Rendering decision-tree.png ..."
dot -Tpng -Gdpi=300 decision-tree.dot -o decision-tree.png
echo "OK  decision-tree.png regenerated."

echo "Rendering ara-a-showroom-marketplace.png ..."
dot -Tpng ara-a-showroom-marketplace.dot -o ara-a-showroom-marketplace.png
echo "OK  ara-a-showroom-marketplace.png regenerated."

# ── 2. Build PDFs ─────────────────────────────────────────────────────────────
echo "Building docs/agent-assetization-research.pdf ..."
build_pdf agent-assetization-research.md agent-assetization-research.pdf
echo "OK  docs/agent-assetization-research.pdf"

echo "Building docs/ara-a-showroom-marketplace.pdf ..."
build_pdf ara-a-showroom-marketplace.md ara-a-showroom-marketplace.pdf
echo "OK  docs/ara-a-showroom-marketplace.pdf"
