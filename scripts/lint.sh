#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ruff check src tests
codespell src tests docs README.md SPECIFICATION.md PACKAGES.md CHANGELOG.md
reuse lint
