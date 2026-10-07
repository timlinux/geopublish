# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
import subprocess
from pathlib import Path

from geopublish.config import PgConfig


def publish_raster(
    config: PgConfig,
    source: Path,
    table: str,
    schema: str = "public",
    srid: int | None = None,
    tile_size: str = "256x256",
    overwrite: bool = True,
) -> None:
    raster2pgsql_cmd = ["raster2pgsql", "-I", "-C", "-M", "-d" if overwrite else "-a"]
    if srid is not None:
        raster2pgsql_cmd += ["-s", str(srid)]
    raster2pgsql_cmd += ["-t", tile_size, str(source), f"{schema}.{table}"]

    raster_proc = subprocess.Popen(raster2pgsql_cmd, stdout=subprocess.PIPE)
    try:
        subprocess.run(["psql", config.conninfo()], stdin=raster_proc.stdout, check=True)
    finally:
        assert raster_proc.stdout is not None
        raster_proc.stdout.close()
        raster_proc.wait()

    if raster_proc.returncode != 0:
        raise subprocess.CalledProcessError(raster_proc.returncode, raster2pgsql_cmd)
