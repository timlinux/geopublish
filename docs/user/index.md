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
command psql -f sql/create_collab_table.sql
```

(If `psql` is aliased to `pgcli` in your shell, plain `psql -f ...` will
fail with a `pgcli` usage error — `command psql` bypasses that; see the
[administrator guide](../admin/index.md#if-psql--f--fails-with-a-pgcli-error)
if it still doesn't work.)

Creates `collab (id, name, geom)`, with `SELECT, INSERT, UPDATE, DELETE`
granted to `PUBLIC` so every participant's connection can add, move, and
delete pins — not just whoever ran the script. Share
`qgis/layers/collab.qlr` with participants — it's a QGIS Layer Definition
file: a double-click (or drag-and-drop into QGIS) adds the layer already
styled (red circle marker) and with its edit form configured (a single
"Your name" text field; `id` is hidden/read-only). It points at the
`workshop` PG service by name, so it carries no embedded credentials —
anyone with the same
`config/pg_service.conf` set up can load it straight away.

### Live updates

`create_collab_table.sql` also wires a statement-level trigger that fires
`pg_notify('qgis', 'collab')` on every insert/update/delete/truncate.
QGIS's PostgreSQL provider only ever issues `LISTEN qgis` — that channel
is hardcoded in QGIS itself, not configurable — so every notify-enabled
layer in this project uses channel `qgis` and tells `collab.qlr` apart
from others by payload (`'collab'`). The shared `.qlr` already sets
`refreshOnNotifyEnabled`/`refreshOnNotifyMessage` for this, so once
loaded, everyone's map should refresh within a second or two of anyone
else adding a pin — no manual re-run needed. If a loaded layer doesn't
auto-refresh (e.g. an older QGIS that ignores those two attributes), set
it by hand in the QGIS Python console with that layer selected:

```python
lyr = iface.activeLayer()
lyr.setRefreshOnNotifyEnabled(True)
lyr.setRefreshOnNotifyMessage('collab')
```

To remove just the notify wiring later (keeping the table and its data):

```bash
command psql -f sql/drop_collab_notify.sql
```

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
