#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
DIAGRAMS_DIR="$REPO_ROOT/docs/diagrams"

for svg in "$DIAGRAMS_DIR"/*.svg; do
  png="${svg%.svg}.png"
  echo "rendering $(basename "$svg") -> $(basename "$png")"
  inkscape --export-type=png --export-dpi=150 --export-filename="$png" "$svg"
done
