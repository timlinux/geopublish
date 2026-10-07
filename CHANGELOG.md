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
  carries no embedded credentials and is safe to share. Grants `SELECT,
  INSERT, UPDATE, DELETE` on the table (and `USAGE, SELECT` on its `id`
  sequence) to `PUBLIC`, so any connected role can edit pins, not just the
  table's owner.
- `collab` now fires `pg_notify('qgis', 'collab')` on every CRUD event via
  a statement-level `AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE`
  trigger, matching the pattern in `sql_1/0001_poi_notify.up.sql`: channel
  `qgis` because QGIS's PostgreSQL provider hardcodes `LISTEN qgis`, and
  payload `'collab'` for `setRefreshOnNotifyMessage()` to match on.
  `qgis/layers/collab.qlr` now sets `refreshOnNotifyEnabled`/
  `refreshOnNotifyMessage` so a loaded layer auto-refreshes without extra
  setup. `sql/drop_collab_notify.sql` reverts just the trigger/function.
- `sql/create_collab_buffer_view.sql`: a live `collab_buffer_100km` view
  (not materialized) dissolving a geodesically-correct 100km buffer
  around every `collab` pin. Extends `notify_collab_change()` with a
  second payload (`'collab_buffer'`, same `qgis` channel) since a view
  has no change events of its own to trigger on; `qgis/layers/
  collab_buffer_100km.qlr` shares the styled, notify-wired layer.
  `sql/drop_collab_buffer_view.sql` reverts just this addition.
- `geopublish capitals load` / `gp capitals load`: loads the world's
  ~200 national capitals from Natural Earth (public domain, no API key,
  fetched directly via GDAL's `/vsizip/vsicurl/`, no download step) into
  a `capitals` table.
- `geopublish capitals refresh-weather` / `gp capitals refresh-weather`:
  fetches each capital's current temperature from Open-Meteo (free, no
  API key) and updates `temperature`/`temperature_updated_at` in place.
  One city's fetch failing doesn't stop the rest; the command reports
  how many succeeded and how many failed.
- `geopublish publish pdf-vectors` / `gp publish pdf-vectors`: extracts
  point/line/polygon geometry directly from a PDF's drawing commands
  (classified by fill: filled -> polygon, unfilled-stroked -> line, very
  small -> point) and loads it into shared `points`/`lines`/`polygons`
  tables, as a lighter-to-query alternative to `prepare pdf-to-geotiff`'s
  raster. Reuses the same frame/corner-coordinate detection, so
  `--utm-zone`/`--srid` match `pdf-to-geotiff`'s `--utm-zone`/`--srs`.
  The nearest printed text label (words merged into lines by proximity,
  matched within a kind-specific radius) is attached as `label`; no
  close-enough text leaves it `NULL` rather than guessing. Rows
  accumulate across every PDF/page processed, tagged with
  `source_pdf`/`source_page`; one bad page is reported and skipped.
  Adds `docs/diagrams/pdf-vector-tables.svg`, a side-by-side UML diagram
  of the three (identical shape, differing only in `geom`'s type).
- `docs/transcript.md`: every prompt from this project's build session,
  each annotated with the requirement/fix it introduced, plus
  `docs/diagrams/requirements-timeline.svg` tracing the distinct ones as
  one UML-stereotyped timeline (feature vs. fix). `geopublish docs-pdf`
  / `gp docs-pdf` renders the transcript to `transcript.pdf` (pandoc ->
  HTML -> weasyprint; gitignored, not committed). `geopublish docs-build`
  / `gp docs-build` produces the static mkdocs site, for CI/Pages.
- Docs site now uses the Kartoza Brand Pack v0.1 theme (logo, favicon,
  Nunito/JetBrains Mono fonts, light/dark palette, flat admonitions and
  tables), vendored from `kartoza/InfrastructureMapper` so every Kartoza
  project's docs look the same: `docs/stylesheets/kartoza-tokens.css`,
  `docs/stylesheets/extra.css`, `docs/assets/brand/*`, and the matching
  `mkdocs.yml` theme/markdown_extensions config.
- Diagrams are now hand-authored SVG (`docs/diagrams/*.svg`) rendered to
  PNG via Inkscape (`nix run .#diagrams` / `scripts/render-diagrams.sh`),
  not Mermaid -- `architecture.svg` replaces the old Mermaid flowchart in
  `SPECIFICATION.md`, and `collab-table.svg` is a UML class diagram for
  the `collab` table, alongside a plain Markdown attributes table.

### Changed

- Every `gp` command now has a matching `nix run .#<name>` and vice
  versa. Added `gp test`/`gp format`/`gp lint`/`gp diagrams` (same
  scripts the existing `nix run .#test`/`.#format`/`.#lint`/`.#diagrams`
  already called), and added `nix run .#init-db`,
  `.#publish-vector`/`.#publish-raster`/`.#publish-pdf-vectors`,
  `.#status`, `.#prepare-pdf-to-geotiff`, `.#capitals-load`/
  `.#capitals-refresh-weather`, and `.#docs-serve` (replacing the
  inconsistently-named `.#docs`), via thin wrappers in `scripts/apps/`
  that forward to `bin/geopublish <subcommand> "$@"`.

### Fixed

- `geopublish publish pdf-vectors` reported `0 points, 0 lines, 0
  polygons` with no explanation on a page whose map content turns out to
  be an embedded raster image rather than vector paths (confirmed on the
  `PLANS/` Netze BW sample: 72 of its 81 `<path>` elements are text-glyph
  outlines, the other 9 are the frame/title-block/page-canvas, and the
  actual cadastral drawing is 8 embedded `2891x1893` PNGs). It now raises
  a clear error pointing at `prepare pdf-to-geotiff` instead.
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
