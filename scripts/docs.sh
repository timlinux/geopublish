#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
# SPECIFICATION.md's image/link paths are written relative to the repo
# root (so it renders correctly on GitHub); rewrite them to be relative to
# docs/ for the copy mkdocs actually serves.
sed -e 's#docs/diagrams/#diagrams/#g' -e 's#docs/user/#user/#g' \
  SPECIFICATION.md > docs/specification.md
exec mkdocs serve "$@"
