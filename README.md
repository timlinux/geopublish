# geopublish

A reproducible workflow for publishing vector and raster geospatial data to a
PostgreSQL/PostGIS database, and viewing the results in QGIS. Built for the
UC2026Workshop.

All tooling (Python, GDAL, PostGIS client utilities, QGIS, docs, linters) is
provisioned by a single Nix flake — no system Python, no `pip install`, no
`npm install`.

## Quickstart

```bash
# enter the fully-provisioned dev shell (or let direnv do it automatically)
nix develop

# configure your PostgreSQL/PostGIS connection
cp .env.example .env
$EDITOR .env

# create the postgis + postgis_raster extensions (once, per database)
geopublish init-db

# publish a vector file
geopublish publish vector path/to/data.gpkg --table my_layer

# publish a raster file
geopublish publish raster path/to/orthophoto.tif --table my_raster

# see what's published
geopublish status
```

## Viewing in QGIS

1. Copy `config/pg_service.conf.example` to `config/pg_service.conf` and fill
   in your connection details (this file is gitignored).
2. `export PGSERVICEFILE="$PWD/config/pg_service.conf"` before launching QGIS
   from the same shell.
3. In QGIS's **Browser** panel: PostgreSQL → New Connection → tick
   **Service** and enter `workshop`. Published tables appear immediately —
   no credentials typed into QGIS itself.

## Project layout

```
flake.nix              Nix flake: devShell + apps (geopublish, test, docs, format, lint)
bin/geopublish          CLI entrypoint
src/geopublish/         Python package (cli, config, db, vector, raster)
scripts/                Shell scripts backing the flake apps and dev-shell banner
config/                 QGIS/psql service-file template
tests/                  pytest suite
docs/                   mkdocs site (user / admin / developer guides)
1_SQL_GPKG_1 ... 5_ASSETS_1   Workshop module folders (left as-is)
```

## Development

```bash
nix run .#test     # pytest
nix run .#lint      # ruff, codespell, reuse lint
nix run .#format    # black
nix run .#docs      # mkdocs serve
```

Pre-commit hooks (black, ruff, codespell, reuse lint, gitleaks) install
automatically the first time you enter the dev shell.

## Documents

- [SPECIFICATION.md](SPECIFICATION.md) — user stories, architecture, requirements
- [PACKAGES.md](PACKAGES.md) — annotated dependency list
- [CHANGELOG.md](CHANGELOG.md) — Keep a Changelog

## License

MIT (placeholder — confirm before any external release).

---

Made with 💗 by [Kartoza](https://kartoza.com) | [Donate!](https://github.com/sponsors/kartoza) | [GitHub](https://github.com/kartoza/geopublish)
