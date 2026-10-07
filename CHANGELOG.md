# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Initial `geopublish` scaffold: Nix flake devShell (Python, GDAL, PostGIS
  client tools, QGIS, docs, linters), CLI (`init-db`, `publish vector`,
  `publish raster`, `status`), pre-commit hooks, pytest suite, mkdocs site,
  CI workflow, and a QGIS `pg_service.conf` template for credential-free
  connections.
- `gp` short alias for the `geopublish` CLI.
- `geopublish docs-serve` / `gp docs-serve` command to preview the docs site
  locally without needing `nix run .#docs`.
- `SPECIFICATION.md` published as a page in the mkdocs site.
- `geopublish prepare pdf-to-geotiff` / `gp prepare pdf-to-geotiff`: clips a
  PDF plan sheet to its drawn map frame and georeferences it to a GeoTIFF,
  ready for `gp publish raster`. The frame and its real-world corner
  coordinates (UTM, zone-prefixed easting + northing, e.g. the Netze BW
  "Netzauskunft" plan format) are detected automatically from the PDF's
  vector border and printed coordinate labels -- no manual pixel-picking.
  Accepts a single PDF or a directory for batch conversion; every page of
  every PDF is converted by default, and one bad sheet doesn't abort the
  rest of the batch.
- `sql/create_collab_table.sql`: a shared `collab (id, name, geom)` table,
  EPSG:3857, for a "drop a pin with your name" workshop layer.
- `qgis/layers/collab.qlr`: a QGIS Layer Definition for the `collab` table
  (styled single-symbol point renderer, edit form with a "Your name" text
  field, `id` hidden) referencing the `workshop` PG service by name, so it
  carries no embedded credentials and is safe to share.

### Fixed

- `nix run .#docs`/`.#format`/`.#test`/`.#lint` and `bin/geopublish` resolved
  their repo root from the script's own (Nix-store, read-only) location,
  which broke `docs.sh`'s `cp` into `docs/specification.md` with "Read-only
  file system". They now resolve the repo root via `git rev-parse
  --show-toplevel` against the caller's working directory instead.
- `geopublish status` crashed with a raw `UndefinedTable` traceback when run
  against a database where `postgis_raster` (or `postgis`) hadn't been
  created yet. It now raises a clear message pointing at `geopublish
  init-db`, and the CLI entrypoint prints configuration/runtime errors as
  a one-line message instead of a full traceback.
- `geopublish init-db` ran `CREATE EXTENSION postgis` and `CREATE EXTENSION
  postgis_raster` in a single transaction, so a managed server that only
  grants the latter to superusers rolled back `postgis` too. They now
  commit independently, and an `InsufficientPrivilege` on `postgis_raster`
  raises a clear message instead of a traceback.
