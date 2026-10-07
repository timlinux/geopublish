#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
# Static build (not the dev server) -- used by CI to publish GitHub Pages.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
bash scripts/sync-specification-docs.sh
exec mkdocs build "$@"
