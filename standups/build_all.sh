#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

REPO_ROOT="$(cd .. && pwd)"
TOOLKIT="$REPO_ROOT/.clinerules/pdf-toolkit"

preprocess() {
  local src="$1"
  local tmp
  tmp="$(mktemp /tmp/build-XXXXXX.md)"
  LC_ALL=C.UTF-8 sed \
    -e 's/☐/[ ]/g' -e 's/☑/[x]/g' -e 's/☒/[x]/g' \
    -e 's/⚠/WARNING:/g' -e 's/✓/Yes/g' -e 's/✗/No/g' \
    -e 's/→/->/g' -e 's/—/ - /g' -e 's/–/-/g' -e 's/…/.../g' \
    "$src" > "$tmp"
  echo "$tmp"
}

build_pdf() {
  local src="$1" out="$2" tmp
  tmp="$(preprocess "$src")"
  pandoc "$tmp" \
    --defaults="$TOOLKIT/pandoc-defaults.yaml" \
    --lua-filter="$TOOLKIT/expand-tables.lua" \
    -H "$TOOLKIT/pandoc-header.tex" \
    --pdf-engine=xelatex \
    -o "$out"
  rm -f "$tmp"
}

for md_file in *.md; do
  [ -f "$md_file" ] || continue
  pdf_file="${md_file%.md}.pdf"
  build_pdf "$md_file" "$pdf_file"
  echo "OK  $pdf_file"
done
