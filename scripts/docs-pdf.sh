#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
# Renders docs/transcript.md to transcript.pdf (repo root) via pandoc +
# weasyprint. The intermediate HTML is written inside docs/ so its
# relative image paths (diagrams/*.png) resolve without rewriting.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

TMP_HTML="docs/.transcript-tmp.html"
trap 'rm -f "$TMP_HTML"' EXIT

pandoc docs/transcript.md -o "$TMP_HTML" --standalone \
  --metadata title="geopublish session transcript"
weasyprint "$TMP_HTML" transcript.pdf
echo "wrote transcript.pdf"
