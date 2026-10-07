# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
import subprocess
from pathlib import Path

import click

from geopublish.config import load_config
from geopublish.db import ensure_postgis, list_layers
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


@cli.command("docs-serve")
def docs_serve() -> None:
    """Serve the mkdocs site locally for live preview."""
    subprocess.run([str(REPO_ROOT / "scripts" / "docs.sh")], check=True)


def main() -> None:
    try:
        cli()
    except RuntimeError as exc:
        raise SystemExit(f"Error: {exc}")


if __name__ == "__main__":
    main()
