#!/usr/bin/env bash
# Regenerate ALL user-facing artefacts in showroom/phase1/.
# Run by the user: bash showroom/phase1/build_all.sh
set -euo pipefail
cd "$(dirname "$0")"

REPO_ROOT="$(cd ../.. && pwd)"
TOOLKIT="$REPO_ROOT/.clinerules/pdf-toolkit"

# ── Unicode preprocessing helper ─────────────────────────────────────────────
# Sources the shared substitution table so xelatex never sees unmapped glyphs.
# When a new "Missing character" warning appears, add the codepoint to:
#   .clinerules/pdf-toolkit/unicode-substitutions.sed
# — do NOT add inline -e expressions here.
preprocess() {
  local src="$1"
  local tmp
  tmp="$(mktemp /tmp/phase1-build-XXXXXX.md)"
  LC_ALL=C.UTF-8 sed -f "$TOOLKIT/unicode-substitutions.sed" "$src" > "$tmp"
  echo "$tmp"
}

# ── Missing-character gate ────────────────────────────────────────────────────
# Captures pandoc/xelatex stderr+stdout. If any "Missing character" line
# appears the build fails immediately with the offending codepoint(s) shown.
# Silent missing-glyph regressions are impossible.
_pandoc_with_gate() {
  local src="$1"; shift          # preprocessed tmp file
  local out="$1"; shift          # output PDF path
  local label="$1"; shift        # human-readable name for error messages
  local log
  log="$(mktemp /tmp/pandoc-gate-XXXXXX.log)"
  pandoc "$src" "$@" -o "$out" 2>&1 | tee "$log"
  local rc=${PIPESTATUS[0]}
  if grep -q 'Missing character' "$log"; then
    echo "" >&2
    echo "FAIL: xelatex reported missing character(s) in $label" >&2
    echo "      Add the codepoint(s) below to:" >&2
    echo "      .clinerules/pdf-toolkit/unicode-substitutions.sed" >&2
    grep 'Missing character' "$log" >&2
    rm -f "$log"; exit 1
  fi
  rm -f "$log"
  return "$rc"
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
    --pdf-engine=xelatex
  rm -f "$tmp"
}

# ── 1. Render PNGs from Graphviz sources ─────────────────────────────────────
echo "Rendering showroom-phase1-architecture.png ..."
dot -Tpng showroom-phase1-architecture.dot \
    -o showroom-phase1-architecture.png
echo "OK  showroom-phase1-architecture.png"

# ── 2. Render PNGs from Mermaid sources ──────────────────────────────────────
echo "Rendering showroom-phase1-flow.png ..."
mmdc -i showroom-phase1-flow.mmd -o showroom-phase1-flow.png \
     -b white \
     --puppeteerConfigFile "$TOOLKIT/puppeteer-config.json"
echo "OK  showroom-phase1-flow.png"

# ── 3. Build PDFs ─────────────────────────────────────────────────────────────
echo "Building devops-runbook.pdf ..."
tmp_runbook="$(preprocess devops-runbook.md)"
_pandoc_with_gate "$tmp_runbook" devops-runbook.pdf "devops-runbook.md" \
  --defaults="$TOOLKIT/pandoc-defaults.yaml" \
  --lua-filter="$TOOLKIT/expand-tables.lua" \
  -H "$TOOLKIT/pandoc-header.tex" \
  -H "$(pwd)/footer.tex" \
  --pdf-engine=xelatex
rm -f "$tmp_runbook"
echo "OK  devops-runbook.pdf"

echo "Building README.pdf ..."
build_pdf README.md README.pdf
echo "OK  README.pdf"

echo "Building showroom-phase1-flow.pdf ..."
build_pdf showroom-phase1-flow.md showroom-phase1-flow.pdf
echo "OK  showroom-phase1-flow.pdf"

echo "Building aca-vs-appservice-decision.pdf ..."
build_pdf aca-vs-appservice-decision.md aca-vs-appservice-decision.pdf
echo "OK  aca-vs-appservice-decision.pdf"

echo "Building integration-options.pdf ..."
build_pdf integration-options.md integration-options.pdf
echo "OK  integration-options.pdf"
