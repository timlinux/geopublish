# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
import subprocess
from pathlib import Path

from geopublish.config import PgConfig


def publish_vector(
    config: PgConfig,
    source: Path,
    table: str,
    schema: str = "public",
    srid: int | None = None,
    overwrite: bool = True,
) -> None:
    cmd = [
        "ogr2ogr",
        "-f",
        "PostgreSQL",
        f"PG:{config.conninfo()}",
        str(source),
        "-nln",
        f"{schema}.{table}",
        "-lco",
        "GEOMETRY_NAME=geom",
        "-overwrite" if overwrite else "-append",
        "-progress",
    ]
    if srid is not None:
        cmd += ["-t_srs", f"EPSG:{srid}"]
    subprocess.run(cmd, check=True)
