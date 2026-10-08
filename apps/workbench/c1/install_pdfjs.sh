#!/usr/bin/env bash
# Install a pinned local PDF.js distribution. Requires registry access at build time.
set -euo pipefail
cd "$(dirname "$0")"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
(cd "$WORK" && npm pack pdfjs-dist@4.10.38 --silent >/dev/null)
mkdir -p web/vendor/pdfjs
TAR="$(find "$WORK" -name 'pdfjs-dist-*.tgz' -print -quit)"
tar xzf "$TAR" -C "$WORK"
cp "$WORK/package/build/pdf.min.mjs" web/vendor/pdfjs/pdf.min.mjs
cp "$WORK/package/build/pdf.worker.min.mjs" web/vendor/pdfjs/pdf.worker.min.mjs
cp "$WORK/package/LICENSE" web/vendor/pdfjs/LICENSE
printf 'PDF.js v4.10.38 installed locally.\n'