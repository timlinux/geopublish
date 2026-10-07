#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
# SPECIFICATION.md's image/link paths are written relative to the repo
# root (so it renders correctly on GitHub); rewrite them to be relative
# to docs/ for the copy mkdocs actually serves/builds. Shared by
# docs.sh (serve) and docs-build.sh (build), so there's one place that
# knows the rewrite rules.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
sed -e 's#docs/diagrams/#diagrams/#g' -e 's#docs/user/#user/#g' \
  "$REPO_ROOT/SPECIFICATION.md" > "$REPO_ROOT/docs/specification.md"
