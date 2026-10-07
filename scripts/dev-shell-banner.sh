#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGO="$REPO_ROOT/assets/kartoza-logo.png"

if command -v chafa >/dev/null 2>&1 && [ -f "$LOGO" ]; then
  chafa --size=40x20 "$LOGO"
else
  cat <<'EOF'
  _  __           _
 | |/ /__ _ _ _ __| |_ ___ ______ _
 | ' </ _` | '_|  _/ _ (_-<_-< _` |
 |_|\_\__,_|_|  \__\___/__/__/\__,_|
EOF
fi

cat <<'EOF'

  geopublish dev shell — publish vector/raster data to PostGIS, view in QGIS

  Commands:
    geopublish --help          Show CLI usage
    geopublish init-db         Create postgis/postgis_raster extensions
    geopublish publish vector  Load a vector file into PostGIS (ogr2ogr)
    geopublish publish raster  Load a raster file into PostGIS (raster2pgsql)
    geopublish status          Test the DB connection, list published layers

    nix run .#test             Run the test suite
    nix run .#docs             Serve docs locally (mkdocs serve)
    nix run .#format           Format code (black)
    nix run .#lint             Lint code (ruff, codespell, reuse)

  Made with 💗 by Kartoza | https://kartoza.com
EOF
