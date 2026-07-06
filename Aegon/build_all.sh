#!/usr/bin/env bash
# Regenerate ALL user-facing artefacts in Aegon/.
# Run by the user: bash Aegon/build_all.sh
set -euo pipefail
cd "$(dirname "$0")"

REPO_ROOT="$(cd .. && pwd)"

# ── Preprocessing helper ──────────────────────────────────────────────────────
preprocess() {
  local src="$1"
  local tmp
  tmp="$(mktemp /tmp/aegon-build-XXXXXX.md)"
  LC_ALL=C.UTF-8 sed \
    -e 's/→/->/g' \
    -e 's/—/ - /g' \
    -e 's/–/-/g' \
    -e 's/…/.../g' \
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
    --resource-path=".:$REPO_ROOT" \
    -o "$out" 2>&1
  rm -f "$tmp"
}

# ── 1. Render PNGs from Graphviz sources ─────────────────────────────────────
echo "Rendering architecture-azure-highlevel.png ..."
dot -Tpng -Gdpi=150 architecture-azure-highlevel.dot \
    -o architecture-azure-highlevel.png
echo "OK  architecture-azure-highlevel.png regenerated."

echo "Rendering architecture-azure.png ..."
dot -Tpng -Gdpi=150 architecture-azure.dot \
    -o architecture-azure.png
echo "OK  architecture-azure.png regenerated."

echo "Rendering tenancy-supply-chain.png ..."
dot -Tpng tenancy-supply-chain.dot \
    -o tenancy-supply-chain.png
echo "OK  tenancy-supply-chain.png regenerated."

# ── 2. Build PDFs ─────────────────────────────────────────────────────────────
echo "Building architecture-highlevel-explained.pdf ..."
build_pdf architecture-highlevel-explained.md architecture-highlevel-explained.pdf
echo "OK  Aegon/architecture-highlevel-explained.pdf"

echo "Building poc-mvp-estimates.pdf ..."
build_pdf poc-mvp-estimates.md poc-mvp-estimates.pdf
echo "OK  Aegon/poc-mvp-estimates.pdf"

echo "Building lh-estimates-summary.pdf ..."
build_pdf lh-estimates-summary.md lh-estimates-summary.pdf
echo "OK  Aegon/lh-estimates-summary.pdf"
