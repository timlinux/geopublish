# User guide

## Setup

1. `nix develop` (or let direnv activate it automatically).
2. `cp .env.example .env` and fill in your PostgreSQL/PostGIS connection
   details.
3. `geopublish init-db` once, to create the `postgis` and `postgis_raster`
   extensions.

## Publishing data

```bash
geopublish publish vector path/to/data.gpkg --table my_layer
geopublish publish raster path/to/orthophoto.tif --table my_raster
geopublish status
```

Run `geopublish publish vector --help` or `geopublish publish raster --help`
for the full option list (`--append`, `--srid`, `--tile-size`, `--schema`).

## Viewing in QGIS

See the [README](https://github.com/kartoza/geopublish#viewing-in-qgis) for
the `pg_service.conf` + QGIS Browser-panel steps.
