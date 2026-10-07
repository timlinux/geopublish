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
- `sql/create_collab_table.sql`, `sql/drop_collab_notify.sql`,
  `sql/create_collab_buffer_view.sql`, `sql/drop_collab_buffer_view.sql`,
  `qgis/layers/collab.qlr`, `qgis/layers/collab_buffer_100km.qlr` —
  one-off shared "drop a pin" table, its dissolved-buffer view, their
  reversible `pg_notify` wiring, and their QGIS Layer Definitions; not
  wired into the CLI since they're specific named tables, not a generalized
  feature.
- `src/geopublish/capitals.py` — world capitals: `load_capitals` (GDAL
  `/vsizip/vsicurl/` straight from Natural Earth's CDN, no download
  step), `refresh_weather`/`fetch_temperature` (Open-Meteo, stdlib
  `urllib`, no extra dependency).
- `src/geopublish/pdfvectors.py` — PDF plan sheet → vector features:
  classification by drawing style (`_classify_and_project`), text-line
  reconstruction and nearest-label matching (`_extract_label_lines`,
  `_nearest_label`), and the shared `points`/`lines`/`polygons` table
  loader (`load_features`). Reuses `pdfmap.py`'s frame/corner-coordinate
  detection rather than duplicating it — same PDF, same two detection
  problems, solved once.

## `pg_notify` convention

QGIS's PostgreSQL provider hardcodes `LISTEN qgis` (verified against the
provider source, not configurable), so every table in this project that
wants a QGIS layer to auto-refresh on change uses channel `qgis` and a
table-specific payload (e.g. `'collab'`), matched by the layer's
`setRefreshOnNotifyMessage()`. See `sql_1/0001_poi_notify.up.sql` for the
original worked example (the `poi` table) and
`sql/create_collab_table.sql` for `collab`'s. Keep the trigger
statement-level (`FOR EACH STATEMENT`, not `FOR EACH ROW`) so a bulk
write fires one notification, and include `TRUNCATE` in the trigger
events. Ship a `drop_*_notify.sql` alongside any new one, reverting just
the trigger/function (not the table).

## Adding a new publish format

Vector and raster publishing are deliberately thin wrappers around the
standard GDAL/PostGIS CLI tools rather than reimplementations — prefer
extending `vector.py`/`raster.py` with new `ogr2ogr`/`raster2pgsql` flags
over adding a new code path.

## Diagrams

Diagrams are hand-authored SVG under `docs/diagrams/*.svg`, rendered to
PNG with Inkscape (provisioned by the flake, not whatever happens to be on
your system) — not Mermaid. After editing an SVG:

```bash
nix run .#diagrams   # or: scripts/render-diagrams.sh
```

then commit both the `.svg` source and the regenerated `.png`.

## Session transcript

`docs/transcript.md` is a record of every prompt that built this
project, each annotated with the requirement/fix it introduced, plus
`docs/diagrams/requirements-timeline.svg` tracing the distinct ones as
one diagram. `gp docs-pdf` / `nix run .#docs-pdf` renders the transcript
page to `transcript.pdf` (pandoc -> HTML -> weasyprint; gitignored, not
committed). Append to the transcript as new substantive prompts come in
-- it's a log, not something to rewrite.

## Docs theme

`mkdocs.yml` plus `docs/stylesheets/kartoza-tokens.css`,
`docs/stylesheets/extra.css`, and `docs/assets/brand/*` are the **Kartoza
Brand Pack v0.1**, vendored byte-for-byte from
[kartoza/InfrastructureMapper](https://github.com/kartoza/InfrastructureMapper)
so this project's docs look the same as other Kartoza projects'. Don't
hand-edit the vendored files — if the brand pack changes upstream, pull a
fresh copy of all four and diff before replacing. `mkdocs.yml`'s own
`nav`/`site_name`/`site_description` stay project-specific.

## Running checks locally

```bash
nix run .#test       # == gp test        pytest (no live DB required)
nix run .#lint        # == gp lint        ruff, codespell, reuse lint
nix run .#format      # == gp format      black
nix run .#diagrams    # == gp diagrams    re-render docs/diagrams/*.svg -> *.png
nix run .#docs-build  # == gp docs-build  static mkdocs build (CI/Pages)
nix run .#docs-pdf    # == gp docs-pdf    render transcript.md -> transcript.pdf
```

All of the above are also wired into `.pre-commit-config.yaml` and CI
(`.github/workflows/ci.yml`).

## `gp` / `nix run` symmetry

Every `gp` command has a matching `nix run .#<name>` and vice versa:
`gp init-db` / `nix run .#init-db`, `gp publish vector` /
`nix run .#publish-vector`, and so on (see `scripts/apps/*.sh` for the
thin wrappers backing the data/workflow ones -- each just forwards to
`bin/geopublish <subcommand> "$@"`; the dev-tool ones -- test/format/
lint/diagrams/docs-serve -- point straight at the same scripts `gp`
itself calls). When adding a new `gp` subcommand, add its mirror in the
same commit: a new `scripts/apps/<name>.sh` wrapper plus the matching
entry in `flake.nix`'s `apps`.
