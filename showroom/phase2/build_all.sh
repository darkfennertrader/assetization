#!/usr/bin/env bash
# Regenerate ALL user-facing artefacts in showroom/.
# Run by the user: bash showroom/build_all.sh
set -euo pipefail
cd "$(dirname "$0")"

REPO_ROOT="$(cd .. && pwd)"

# ── Preprocessing helper ──────────────────────────────────────────────────────
preprocess() {
  local src="$1"
  local tmp
  tmp="$(mktemp /tmp/showroom-build-XXXXXX.md)"
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
    -o "$out" 2>&1
  rm -f "$tmp"
}

# ── 1. Render PNGs from Graphviz sources ─────────────────────────────────────
echo "Rendering showroom-qr-flow.png ..."
dot -Tpng showroom-qr-flow.dot -o showroom-qr-flow.png
echo "OK  showroom-qr-flow.png regenerated."

echo "Rendering showroom-azure-architecture.png ..."
dot -Tpng showroom-azure-architecture.dot -o showroom-azure-architecture.png
echo "OK  showroom-azure-architecture.png regenerated."

# ── 2. Build PDFs ─────────────────────────────────────────────────────────────
echo "Building showroom-qr-flow.pdf ..."
build_pdf showroom-qr-flow.md showroom-qr-flow.pdf
echo "OK  showroom-qr-flow.pdf"

echo "Building showroom-azure-architecture.pdf ..."
build_pdf showroom-azure-architecture.md showroom-azure-architecture.pdf
echo "OK  showroom-azure-architecture.pdf"
