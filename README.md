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
gp init-db

# publish a vector file
gp publish vector path/to/data.gpkg --table my_layer

# publish a raster file
gp publish raster path/to/orthophoto.tif --table my_raster

# see what's published
gp status

# browse the docs locally
gp docs-serve
```

`gp` is a short alias for `geopublish` — both run the same CLI.

## Georeferencing PDF plan sheets

Some source data arrives as PDF plan sheets with printed corner coordinate
labels (e.g. Netze BW "Netzauskunft" exports) rather than as GIS files.
`gp prepare pdf-to-geotiff` clips each page to its drawn map frame and
georeferences it, with no manual pixel-picking: the frame and its
real-world corner coordinates are read directly from the PDF's vector
border and printed coordinate labels.

```bash
# single PDF, every page -> one GeoTIFF per page
gp prepare pdf-to-geotiff PLANS/some-plan.pdf --output-dir PLANS/geotiff

# a whole folder of PDFs (batch mode)
gp prepare pdf-to-geotiff PLANS --output-dir PLANS/geotiff

# then publish
gp publish raster PLANS/geotiff/some-plan_p1.tif --table some_plan_p1
```

Assumes UTM coordinates with a zone-prefixed easting label (e.g.
`32467896,48` = zone 32, easting 467896.48) and a plain northing label
(e.g. `5307061,26`); override `--utm-zone`/`--srs` if your plans use a
different zone. If a sheet is missing at least two easting and two
northing labels, that page is reported as failed and the rest of the
batch still runs.

A raster is slow to query compared to real vector features — to extract
the PDF's actual points/lines/polygons instead:

```bash
gp publish pdf-vectors PLANS/some-plan.pdf   # or a folder, for batch mode
```

See the [user guide](docs/user/index.md#extracting-pdf-plan-sheets-as-vectors)
for how classification and label-matching work.

## Collaboration layer

A shared "drop a pin with your name" layer, EPSG:3857:

```bash
command psql -f sql/create_collab_table.sql
```

Creates `collab (id, name, geom)`. Share `qgis/layers/collab.qlr` with
participants — it's a QGIS Layer Definition file: a double-click (or
drag-and-drop into QGIS) adds the layer already styled (red circle marker)
and with its edit form configured (a single "Your name" text field; `id` is
hidden/read-only). It points at the `workshop` PG service by name, so it
carries no embedded credentials — anyone with the same
`config/pg_service.conf` set up can load it straight away.

## World capitals + live temperature

Free, no API key needed for either data source:

```bash
gp capitals load             # once: ~200 national capitals (Natural Earth)
gp capitals refresh-weather  # repeatable: current temperature (Open-Meteo)
```

See the [user guide](docs/user/index.md#world-capitals--live-temperature)
for details.

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
flake.nix              Nix flake: devShell + apps (geopublish, gp, test, docs, format, lint)
bin/geopublish          CLI entrypoint
bin/gp                  Short alias for bin/geopublish
src/geopublish/         Python package (cli, config, db, vector, raster, pdfmap, pdfvectors, capitals)
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

- [SPECIFICATION.md](SPECIFICATION.md) — user stories, architecture, requirements (also published in the docs site, see `gp docs-serve`)
- [PACKAGES.md](PACKAGES.md) — annotated dependency list
- [CHANGELOG.md](CHANGELOG.md) — Keep a Changelog

## License

MIT (placeholder — confirm before any external release).

---

Made with 💗 by [Kartoza](https://kartoza.com) | [Donate!](https://github.com/sponsors/kartoza) | [GitHub](https://github.com/kartoza/geopublish)
