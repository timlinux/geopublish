#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
# Thin wrapper so `nix run .#prepare-pdf-to-geotiff` is the same
# entrypoint as `gp prepare pdf-to-geotiff`.
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"
exec "$REPO_ROOT/bin/geopublish" prepare pdf-to-geotiff "$@"
