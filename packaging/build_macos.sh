#!/usr/bin/env bash
# Build the macOS .app bundle. Run from the repo root with the venv active.
set -euo pipefail

cd "$(dirname "$0")/.."
pyinstaller packaging/pdfmod.spec --noconfirm

echo
echo "Built: dist/PDF Sequence Extractor.app"
echo "Launch it directly (not via Finder) to see startup errors:"
echo '  "dist/PDF Sequence Extractor.app/Contents/MacOS/PDFSequenceExtractor"'
