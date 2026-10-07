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
| `inkscape` | nixpkgs | Renders hand-authored SVG diagrams (`docs/diagrams/*.svg`) to PNG via `nix run .#diagrams` / `scripts/render-diagrams.sh`. Diagrams are plain SVG, not Mermaid, so they render identically wherever the PNG is embedded (GitHub, mkdocs, a PDF export). |

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

## External data sources

Not nixpkgs packages, but worth recording why each was picked: both are
free, require no API key and no signup, so there's no account-setup
hassle for workshop participants.

| Source | License | Used by | Purpose |
|---|---|---|---|
| [Natural Earth](https://www.naturalearthdata.com) `ne_10m_populated_places_simple` | Public domain | `geopublish capitals load` | World capital cities (`adm0cap = 1`), fetched directly over HTTP via GDAL's `/vsizip/vsicurl/` — no separate download step, no dependency beyond `gdal` itself. |
| [Open-Meteo](https://open-meteo.com) `/v1/forecast` | Free for commercial and non-commercial use (attribution appreciated: "Weather data by Open-Meteo.com") | `geopublish capitals refresh-weather` | Current temperature by latitude/longitude. Plain HTTPS GET via Python's stdlib `urllib` — no extra package needed. |
