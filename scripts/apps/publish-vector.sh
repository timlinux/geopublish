#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
# Thin wrapper so `nix run .#publish-vector` is the same entrypoint as
# `gp publish vector`.
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"
exec "$REPO_ROOT/bin/geopublish" publish vector "$@"
