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
