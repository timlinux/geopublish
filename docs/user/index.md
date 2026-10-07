# User guide

## Setup

1. `nix develop` (or let direnv activate it automatically).
2. `cp .env.example .env` and fill in your PostgreSQL/PostGIS connection
   details.
3. `gp init-db` once, to create the `postgis` and `postgis_raster`
   extensions.

## Publishing data

```bash
gp publish vector path/to/data.gpkg --table my_layer
gp publish raster path/to/orthophoto.tif --table my_raster
gp status
```

Run `gp publish vector --help` or `gp publish raster --help` for the full
option list (`--append`, `--srid`, `--tile-size`, `--schema`).

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

## Collaboration layer

A shared "drop a pin with your name" layer, EPSG:3857:

```bash
psql -f sql/create_collab_table.sql
```

Creates `collab (id, name, geom)`. Share `qgis/layers/collab.qlr` with
participants — it's a QGIS Layer Definition file: a double-click (or
drag-and-drop into QGIS) adds the layer already styled (red circle marker)
and with its edit form configured (a single "Your name" text field; `id` is
hidden/read-only). It points at the `workshop` PG service by name, so it
carries no embedded credentials — anyone with the same
`config/pg_service.conf` set up can load it straight away.

## Viewing in QGIS

1. Copy `config/pg_service.conf.example` to `config/pg_service.conf` and
   fill in your connection details (this file is gitignored).
2. `export PGSERVICEFILE="$PWD/config/pg_service.conf"` before launching
   QGIS from the same shell.
3. In QGIS's **Browser** panel: PostgreSQL → New Connection → tick
   **Service** and enter `workshop`. Published tables appear immediately —
   no credentials typed into QGIS itself. Drag a layer onto the canvas to
   add it.

Alternative for a specific raster: **Layer → Add Layer → Add PostGIS
Raster Layer...**, pick the `workshop` connection, schema `public`, then
the table.
