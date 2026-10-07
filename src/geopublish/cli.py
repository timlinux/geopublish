# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
import subprocess
from pathlib import Path

import click

from geopublish.capitals import load_capitals, refresh_weather
from geopublish.config import load_config
from geopublish.db import ensure_postgis, list_layers
from geopublish.pdfmap import batch_convert, discover_pdfs, page_count
from geopublish.pdfvectors import extract_vector_features, load_features
from geopublish.raster import publish_raster
from geopublish.vector import publish_vector

REPO_ROOT = Path(__file__).resolve().parents[2]


@click.group()
def cli() -> None:
    """geopublish: publish vector and raster data to PostGIS, for viewing in QGIS."""


@cli.command("init-db")
def init_db() -> None:
    """Create the postgis and postgis_raster extensions if missing."""
    config = load_config()
    ensure_postgis(config)
    click.echo(f"postgis + postgis_raster ready on {config.dbname}@{config.host}")


@cli.group()
def publish() -> None:
    """Publish a file into PostGIS."""


@publish.command("vector")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option("--table", required=True, help="Destination table name.")
@click.option("--schema", default="public", show_default=True)
@click.option("--srid", type=int, default=None, help="Reproject to this EPSG code.")
@click.option("--append", "append_", is_flag=True, help="Append instead of overwrite.")
def publish_vector_cmd(source, table, schema, srid, append_) -> None:
    """Load a vector file (shapefile, GeoPackage, GeoJSON, ...) via ogr2ogr."""
    config = load_config()
    publish_vector(
        config, source, table, schema=schema, srid=srid, overwrite=not append_
    )
    click.echo(f"published vector {source} -> {schema}.{table}")


@publish.command("raster")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option("--table", required=True, help="Destination table name.")
@click.option("--schema", default="public", show_default=True)
@click.option("--srid", type=int, default=None, help="Raster's EPSG code.")
@click.option("--tile-size", default="256x256", show_default=True)
@click.option("--append", "append_", is_flag=True, help="Append instead of overwrite.")
def publish_raster_cmd(source, table, schema, srid, tile_size, append_) -> None:
    """Load a raster file (GeoTIFF, COG, ...) via raster2pgsql."""
    config = load_config()
    publish_raster(
        config,
        source,
        table,
        schema=schema,
        srid=srid,
        tile_size=tile_size,
        overwrite=not append_,
    )
    click.echo(f"published raster {source} -> {schema}.{table}")


@publish.command("pdf-vectors")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--page",
    "pages",
    type=int,
    multiple=True,
    help="Restrict to this page number (repeatable). Default: every page.",
)
@click.option(
    "--utm-zone",
    type=int,
    default=32,
    show_default=True,
    help="UTM zone used to decode zone-prefixed easting labels.",
)
@click.option("--srid", type=int, default=25832, show_default=True)
def publish_pdf_vectors_cmd(source, pages, utm_zone, srid) -> None:
    """Extract point/line/polygon geometry from PDF plan sheet(s) and load
    it into shared points/lines/polygons tables.

    SOURCE is a single PDF or a directory of PDFs (batch mode). Geometry
    is classified by how it's drawn -- a filled shape is a polygon, an
    unfilled stroked path is a line, a very small shape (e.g. a vertex
    marker) is a point -- and projected to real-world coordinates using
    the same frame/corner-coordinate detection as 'prepare pdf-to-geotiff'.
    The nearest printed text label is attached as a best-effort
    annotation. One bad page doesn't abort the rest of a batch.
    """
    total = {"point": 0, "line": 0, "polygon": 0}
    failed = 0
    config = load_config()
    for pdf in discover_pdfs(source):
        page_numbers = list(pages) or list(range(1, page_count(pdf) + 1))
        for page in page_numbers:
            try:
                features = extract_vector_features(pdf, page=page, zone=utm_zone)
                loaded = load_features(
                    config, features, source_pdf=pdf.name, source_page=page, srid=srid
                )
            except Exception as exc:
                click.echo(f"FAILED {pdf.name} page {page}: {exc}", err=True)
                failed += 1
                continue
            for kind, count in loaded.items():
                total[kind] += count
            click.echo(
                f"{pdf.name} page {page}: "
                f"{loaded['point']} points, {loaded['line']} lines, {loaded['polygon']} polygons"
            )
    click.echo(
        f"loaded {total['point']} points, {total['line']} lines, "
        f"{total['polygon']} polygons ({failed} page(s) failed)"
    )
    if failed and not any(total.values()):
        raise SystemExit(1)


@cli.command()
def status() -> None:
    """Test the DB connection and list published vector/raster layers."""
    config = load_config()
    layers = list_layers(config)
    click.echo(f"connected to {config.dbname}@{config.host}:{config.port}")
    if not layers:
        click.echo("no vector or raster layers published yet")
        return
    for layer in layers:
        click.echo(f"  {layer['kind']:6s} {layer['schema']}.{layer['name']}")


@cli.group()
def prepare() -> None:
    """Prepare non-PostGIS source data for publishing."""


@prepare.command("pdf-to-geotiff")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", required=True, type=click.Path(path_type=Path))
@click.option(
    "--page",
    "pages",
    type=int,
    multiple=True,
    help="Restrict to this page number (repeatable). Default: every page.",
)
@click.option("--dpi", type=int, default=300, show_default=True)
@click.option("--srs", default="EPSG:25832", show_default=True)
@click.option(
    "--utm-zone",
    type=int,
    default=32,
    show_default=True,
    help="UTM zone used to decode zone-prefixed easting labels.",
)
def pdf_to_geotiff_cmd(source, output_dir, pages, dpi, srs, utm_zone) -> None:
    """Clip and georeference PDF plan sheet(s) into GeoTIFFs.

    SOURCE is a single PDF or a directory of PDFs (batch mode). The map
    frame and its real-world corner coordinates are detected automatically
    from the PDF's drawn border and printed coordinate labels -- no manual
    pixel-picking needed. Every page of every PDF is converted unless
    --page is given.
    """
    results = batch_convert(
        source,
        output_dir=output_dir,
        dpi=dpi,
        srs=srs,
        zone=utm_zone,
        pages=list(pages) or None,
    )
    ok = [r for r in results if r.error is None]
    failed = [r for r in results if r.error is not None]
    for r in ok:
        click.echo(f"wrote {r.output}")
    for r in failed:
        click.echo(f"FAILED {r.pdf.name} page {r.page}: {r.error}", err=True)
    click.echo(f"{len(ok)} succeeded, {len(failed)} failed")
    if failed and not ok:
        raise SystemExit(1)


@cli.group()
def capitals() -> None:
    """World capital cities layer with live temperature."""


@capitals.command("load")
@click.option("--table", default="capitals", show_default=True)
@click.option("--schema", default="public", show_default=True)
def capitals_load_cmd(table, schema) -> None:
    """Load the world's national capitals (Natural Earth, public domain,
    no API key) into PostGIS. Overwrites the table -- run this once, then
    use 'capitals refresh-weather' going forward."""
    config = load_config()
    load_capitals(config, table=table, schema=schema)
    click.echo(f"loaded capitals -> {schema}.{table}")


@capitals.command("refresh-weather")
@click.option("--table", default="capitals", show_default=True)
@click.option("--schema", default="public", show_default=True)
def capitals_refresh_weather_cmd(table, schema) -> None:
    """Fetch each capital's current temperature from Open-Meteo (free, no
    API key) and update the table in place."""
    config = load_config()
    updated, failed = refresh_weather(config, table=table, schema=schema)
    click.echo(f"updated {updated} cities, {failed} failed")


@cli.command("docs-serve")
def docs_serve() -> None:
    """Serve the mkdocs site locally for live preview."""
    subprocess.run([str(REPO_ROOT / "scripts" / "docs.sh")], check=True)


@cli.command("test")
def test_cmd() -> None:
    """Run the pytest suite. Same entrypoint as 'nix run .#test'."""
    subprocess.run([str(REPO_ROOT / "scripts" / "test.sh")], check=True)


@cli.command("format")
def format_cmd() -> None:
    """Format code with black. Same entrypoint as 'nix run .#format'."""
    subprocess.run([str(REPO_ROOT / "scripts" / "format.sh")], check=True)


@cli.command("lint")
def lint_cmd() -> None:
    """Lint with ruff, codespell, reuse. Same entrypoint as 'nix run .#lint'."""
    subprocess.run([str(REPO_ROOT / "scripts" / "lint.sh")], check=True)


@cli.command("diagrams")
def diagrams_cmd() -> None:
    """Render docs/diagrams/*.svg to PNG via Inkscape. Same entrypoint as
    'nix run .#diagrams'."""
    subprocess.run([str(REPO_ROOT / "scripts" / "render-diagrams.sh")], check=True)


def main() -> None:
    try:
        cli()
    except RuntimeError as exc:
        raise SystemExit(f"Error: {exc}")


if __name__ == "__main__":
    main()
