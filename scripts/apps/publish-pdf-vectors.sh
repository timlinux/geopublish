#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
# Thin wrapper so `nix run .#publish-pdf-vectors` is the same entrypoint
# as `gp publish pdf-vectors`.
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"
exec "$REPO_ROOT/bin/geopublish" publish pdf-vectors "$@"
