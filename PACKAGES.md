# Packages

Annotated list of every package the flake provisions, and why.

## Runtime / CLI

| Package | Source | Purpose |
|---|---|---|
| `python3` + `gdal`, `psycopg2`, `python-dotenv`, `click` | nixpkgs `python3.withPackages` | Runs the `geopublish` CLI: argument parsing (click), `.env` loading (python-dotenv), DB queries (psycopg2), GDAL Python bindings available if a command needs them directly. |
| `gdal` (CLI) | nixpkgs | Provides `ogr2ogr`, `gdal_translate`, etc. used by `geopublish publish vector` and `geopublish prepare pdf-to-geotiff`. |
| `poppler_utils` | nixpkgs | Provides `pdftocairo`, `pdftotext`, `pdfinfo` used by `geopublish prepare pdf-to-geotiff` to rasterize PDF plan sheets and read their vector frame/coordinate labels. |
| `postgresql_16` | nixpkgs | Provides `psql`, used both directly and as the receiving end of `raster2pgsql \| psql`. |
| `postgresql_16.pkgs.postgis` | nixpkgs | Provides `raster2pgsql`, `shp2pgsql`, `pgsql2shp` used by `geopublish publish raster`. |
| `qgis` | nixpkgs | Desktop viewer for the published PostGIS layers. |
| `chafa` | nixpkgs | Renders the Kartoza logo banner on `nix develop`. |

## Docs

| Package | Source | Purpose |
|---|---|---|
| `mkdocs`, `mkdocs-material` | nixpkgs (python3Packages, same env as above) | Builds/serves `docs/`. |

## Quality / CI

| Package | Source | Purpose |
|---|---|---|
| `pre-commit` | nixpkgs | Runs the hooks in `.pre-commit-config.yaml`. |
| `black` | nixpkgs | Python formatting. |
| `ruff` | nixpkgs | Python linting. |
| `codespell` | nixpkgs | Spell checking docs and source. |
| `reuse` | nixpkgs | REUSE/SPDX license-header compliance. |
| `gitleaks` | nixpkgs | Secret scanning before commit. |
| `pytest` | nixpkgs (python3Packages, same env as above) | Runs `tests/`. |

No package in this project is sourced from PyPI or npm — everything above
comes from nixpkgs. If a future dependency isn't available there, it should
be added as a new Nix derivation before falling back to `pip`.
