# Developer guide

## Layout

- `src/geopublish/cli.py` — Click CLI surface.
- `src/geopublish/config.py` — environment-variable loading (`PgConfig`).
- `src/geopublish/db.py` — psycopg2 helpers (`ensure_postgis`, `list_layers`).
- `src/geopublish/vector.py` — `ogr2ogr` wrapper.
- `src/geopublish/raster.py` — `raster2pgsql | psql` wrapper.
- `src/geopublish/pdfmap.py` — PDF plan sheet → GeoTIFF: frame detection
  (`frame_bbox_from_svg`), corner-coordinate detection
  (`geo_bbox_from_coordinate_words`), and the `pdftocairo`/`gdal_translate`
  pipeline (`pdf_to_geotiff`, `batch_convert`).
- `sql/create_collab_table.sql`, `qgis/layers/collab.qlr` — one-off shared
  "drop a pin" table + its QGIS Layer Definition; not wired into the CLI
  since it's a single named table, not a generalized feature.

## Adding a new publish format

Vector and raster publishing are deliberately thin wrappers around the
standard GDAL/PostGIS CLI tools rather than reimplementations — prefer
extending `vector.py`/`raster.py` with new `ogr2ogr`/`raster2pgsql` flags
over adding a new code path.

## Running checks locally

```bash
nix run .#test     # pytest (no live DB required)
nix run .#lint      # ruff, codespell, reuse lint
nix run .#format    # black
```

All of the above are also wired into `.pre-commit-config.yaml` and CI
(`.github/workflows/ci.yml`).
