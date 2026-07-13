#!/usr/bin/env bash
# vision/build_all.sh
# Regenerates all artefacts in this directory.
# Run manually: bash vision/build_all.sh
# NEVER run automatically by Cline.
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

# ── PDF build helper ──────────────────────────────────────────────────────────
build_pdf() {
  local src="$1"
  local out="$2"
  local tmp
  tmp="$(preprocess "$src")"
  _pandoc_with_gate "$tmp" "$out" "$src" \
    --defaults="$TOOLKIT/pandoc-defaults.yaml" \
    --lua-filter="$TOOLKIT/expand-tables.lua" \
    -H "$TOOLKIT/pandoc-header.tex" \
    --pdf-engine=xelatex
  rm -f "$tmp"
}

# ── 1. Render PNGs from Graphviz sources ─────────────────────────────────────
for dot_file in *.dot; do
  [ -f "$dot_file" ] || continue
  png_file="${dot_file%.dot}.png"
  dot -Tpng "$dot_file" -o "$png_file"
  echo "OK  $png_file"
done

# ── 2. Render PNGs from Mermaid sources ──────────────────────────────────────
for mmd_file in *.mmd; do
  [ -f "$mmd_file" ] || continue
  png_file="${mmd_file%.mmd}.png"
  mmdc -i "$mmd_file" -o "$png_file" -b transparent \
    --puppeteerConfigFile "$TOOLKIT/puppeteer-config.json"
  echo "OK  $png_file"
done

# ── 3. Build PDFs from Markdown sources ──────────────────────────────────────
for md_file in *.md; do
  [ -f "$md_file" ] || continue
  pdf_file="${md_file%.md}.pdf"
  build_pdf "$md_file" "$pdf_file"
  echo "OK  $pdf_file"
done
