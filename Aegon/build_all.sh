#!/usr/bin/env bash
# Regenerate ALL user-facing artefacts in Aegon/.
# Run by the user: bash Aegon/build_all.sh
set -euo pipefail
cd "$(dirname "$0")"

REPO_ROOT="$(cd .. && pwd)"
TOOLKIT="$REPO_ROOT/.clinerules/pdf-toolkit"

# ── Unicode preprocessing helper ─────────────────────────────────────────────
preprocess() {
  local src="$1" tmp
  tmp="$(mktemp /tmp/build-XXXXXX.md)"
  LC_ALL=C.UTF-8 sed -f "$TOOLKIT/unicode-substitutions.sed" "$src" > "$tmp"
  echo "$tmp"
}

# ── Missing-character gate ────────────────────────────────────────────────────
_pandoc_with_gate() {
  local src="$1"; shift; local out="$1"; shift; local label="$1"; shift
  local log; log="$(mktemp /tmp/pandoc-gate-XXXXXX.log)"
  pandoc "$src" "$@" -o "$out" 2>&1 | tee "$log"
  local rc=${PIPESTATUS[0]}
  if grep -q 'Missing character' "$log"; then
    echo "FAIL: missing character(s) in $label — add to unicode-substitutions.sed" >&2
    grep 'Missing character' "$log" >&2
    rm -f "$log"; exit 1
  fi
  rm -f "$log"; return "$rc"
}

build_pdf() {
  local src="$1"
  local out="$2"
  local tmp
  tmp="$(preprocess "$src")"
  _pandoc_with_gate "$tmp" "$out" "$src" \
    --defaults="$TOOLKIT/pandoc-defaults.yaml" \
    --lua-filter="$TOOLKIT/expand-tables.lua" \
    -H "$TOOLKIT/pandoc-header.tex" \
    --pdf-engine=xelatex \
    --pdf-engine-opt="-interaction=nonstopmode" \
    --pdf-engine-opt="-halt-on-error" \
    --resource-path=".:$REPO_ROOT"
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

echo "Building use-cases-summary.pdf ..."
build_pdf use-cases-summary.md use-cases-summary.pdf
echo "OK  Aegon/use-cases-summary.pdf"
