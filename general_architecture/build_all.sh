#!/usr/bin/env bash
# Regenerate ALL user-facing artefacts in general_architecture/.
# Run by the user: bash general_architecture/build_all.sh
set -euo pipefail
cd "$(dirname "$0")"

REPO_ROOT="$(cd .. && pwd)"

# ── Preprocessing helper ──────────────────────────────────────────────────────
preprocess() {
  local src="$1"
  local tmp
  tmp="$(mktemp /tmp/genarch-build-XXXXXX.md)"
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
echo "Rendering general-architecture-highlevel.png ..."
dot -Tpng general-architecture-highlevel.dot \
    -o general-architecture-highlevel.png
echo "OK  general-architecture-highlevel.png regenerated."

echo "Rendering general-architecture-overview.png ..."
dot -Tpng general-architecture-overview.dot \
    -o general-architecture-overview.png
echo "OK  general-architecture-overview.png regenerated."

echo "Rendering tenancy-supply-chain-general.png ..."
dot -Tpng tenancy-supply-chain-general.dot \
    -o tenancy-supply-chain-general.png
echo "OK  tenancy-supply-chain-general.png regenerated."

echo "Rendering tenancy-supply-chain-overview.png ..."
dot -Tpng tenancy-supply-chain-overview.dot \
    -o tenancy-supply-chain-overview.png
echo "OK  tenancy-supply-chain-overview.png regenerated."

# ── 2. Build PDFs ─────────────────────────────────────────────────────────────
echo "Building general-architecture-highlevel-explained.pdf ..."
build_pdf general-architecture-highlevel-explained.md general-architecture-highlevel-explained.pdf
echo "OK  general-architecture-highlevel-explained.pdf"

echo "Building kickoff-speech.pdf ..."
build_pdf kickoff-speech.md kickoff-speech.pdf
echo "OK  kickoff-speech.pdf"

echo "Building tenancy-supply-chain-general.pdf ..."
build_pdf tenancy-supply-chain-general.md tenancy-supply-chain-general.pdf
echo "OK  tenancy-supply-chain-general.pdf"
