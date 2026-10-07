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

  Every gp command has a matching `nix run .#<name>` and vice versa
  (gp is a short alias for geopublish):

    gp --help                     Show full CLI usage
    gp init-db                    Create postgis/postgis_raster extensions
    gp publish vector             Load a vector file into PostGIS (ogr2ogr)
    gp publish raster             Load a raster file into PostGIS (raster2pgsql)
    gp publish pdf-vectors        Extract PDF plan vectors into points/lines/polygons
    gp status                     Test the DB connection, list published layers
    gp prepare pdf-to-geotiff     Clip + georeference PDF plan sheet(s)
    gp capitals load              Load world capitals (Natural Earth)
    gp capitals refresh-weather   Fetch current temperature (Open-Meteo)
    gp docs-serve   = nix run .#docs-serve      Serve the docs site locally
    gp test         = nix run .#test            Run the test suite
    gp format       = nix run .#format          Format code (black)
    gp lint         = nix run .#lint             Lint (ruff, codespell, reuse)
    gp diagrams     = nix run .#diagrams         Render docs/diagrams/*.svg -> png
    gp docs-build   = nix run .#docs-build       Static mkdocs build (CI/Pages)
    gp docs-pdf     = nix run .#docs-pdf         Render transcript.md -> transcript.pdf

  e.g. `nix run .#publish-vector -- file.gpkg --table foo` == `gp publish vector file.gpkg --table foo`

  Made with 💗 by Kartoza | https://kartoza.com
EOF
