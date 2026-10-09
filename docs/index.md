---
hide:
  - navigation
  - toc
---
<!-- SPDX-FileCopyrightText: 2026 Kartoza -->
<!-- SPDX-License-Identifier: MIT -->

<div class="kz-hero" markdown>

<span class="kz-eyebrow">KARTOZA · GEOPUBLISH</span>

# Publish vector and raster geodata to PostGIS, view it in QGIS

One command loads a shapefile, GeoPackage, GeoJSON, or GeoTIFF into
PostgreSQL/PostGIS &mdash; and QGIS opens straight onto the result, with no
credentials typed by hand.

<div class="kz-cta" markdown>
[:material-rocket-launch: Get Started](user/index.md){ .kz-cta__primary }
[:material-file-document-outline: Specification](specification.md){ .kz-cta__secondary }
[:simple-github: GitHub](https://github.com/timlinux/geopublish){ .kz-cta__secondary }
</div>

</div>

## What it is

`geopublish` is a reproducible, Nix-provisioned workflow for publishing
vector and raster geospatial files to an existing PostgreSQL/PostGIS
database. Run `gp publish vector` or `gp publish raster` to load a file,
`gp status` to confirm what's there, and open QGIS to see the published
layers immediately &mdash; connection details come from a project
`.env`, never from credentials pasted into QGIS itself.

Source data doesn't have to start out as GIS-ready: `gp prepare
pdf-to-geotiff` georeferences PDF plan sheets with printed corner
coordinates directly, with no manual pixel-picking.

## Explore the docs

<div class="grid cards" markdown>

-   :material-compass-outline:{ .lg .middle } __User guide__

    ---

    Setup, `gp publish`, `gp status`, and georeferencing PDF plan sheets
    from the command line.

    [:octicons-arrow-right-24: Get started](user/index.md)

-   :material-database-cog-outline:{ .lg .middle } __Administrator guide__

    ---

    Database prerequisites, required privileges, and connection
    configuration via `.env`.

    [:octicons-arrow-right-24: Set up the database](admin/index.md)

-   :material-code-braces:{ .lg .middle } __Developer guide__

    ---

    CLI layout, the `psycopg2`/`ogr2ogr`/`raster2pgsql` wrappers, and the
    PDF-to-GeoTIFF pipeline internals.

    [:octicons-arrow-right-24: Extend the CLI](developer/index.md)

-   :material-file-document-outline:{ .lg .middle } __Specification__

    ---

    User stories, business rules, architecture, and everything needed to
    rebuild this application from scratch.

    [:octicons-arrow-right-24: Read the spec](specification.md)

-   :material-history:{ .lg .middle } __Session transcript__

    ---

    Every prompt given while building `geopublish`, annotated with the
    requirement it introduced and a diagram per milestone.

    [:octicons-arrow-right-24: Read the transcript](transcript.md)

</div>

<div class="kz-footer-credits" markdown>
Made with 💗 by [Kartoza](https://kartoza.com) &middot;
[Donate!](https://github.com/sponsors/kartoza) &middot;
[GitHub](https://github.com/timlinux/geopublish)
</div>
