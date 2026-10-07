# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
import json
import subprocess
import urllib.request

from geopublish.config import PgConfig
from geopublish.db import connect

# Natural Earth's populated places dataset is public domain, hosted on a
# free CDN with no signup and no API key. /vsizip/vsicurl/ lets GDAL read
# the zipped shapefile straight over HTTP, with no separate download step.
NATURAL_EARTH_CAPITALS_URL = (
    "/vsizip/vsicurl/https://naciscdn.org/naturalearth/10m/cultural/"
    "ne_10m_populated_places_simple.zip"
)

# adm0cap = 1 flags the ~200 national ("admin-0") capitals in the dataset.
LOAD_SQL = (
    "SELECT name, adm0name AS country, iso_a2 "
    "FROM ne_10m_populated_places_simple WHERE adm0cap = 1"
)

# Open-Meteo is free for non-commercial and commercial use, with no API
# key and no signup (https://open-meteo.com) -- just a plain HTTPS GET.
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def load_capitals(config: PgConfig, table: str = "capitals", schema: str = "public") -> None:
    """Load the world's national capitals (Natural Earth) into PostGIS.
    Overwrites the table -- this is the reference dataset load, not the
    repeatable step; run it once, then use refresh_weather() going
    forward."""
    subprocess.run(
        [
            "ogr2ogr",
            "-f",
            "PostgreSQL",
            f"PG:{config.conninfo()}",
            NATURAL_EARTH_CAPITALS_URL,
            "-dialect",
            "OGRSQL",
            "-sql",
            LOAD_SQL,
            "-nln",
            f"{schema}.{table}",
            "-lco",
            "GEOMETRY_NAME=geom",
            # ogr2ogr's PostgreSQL driver names its auto-generated primary
            # key "ogc_fid" by default, not "id" -- refresh_weather() (and
            # the GRANT/UML docs) assume "id", so force it here.
            "-lco",
            "FID=id",
            "-overwrite",
        ],
        check=True,
    )

    with connect(config) as conn, conn.cursor() as cur:
        cur.execute(
            f"ALTER TABLE {schema}.{table} "
            "ADD COLUMN IF NOT EXISTS temperature double precision"
        )
        cur.execute(
            f"ALTER TABLE {schema}.{table} "
            "ADD COLUMN IF NOT EXISTS temperature_updated_at timestamptz"
        )
        conn.commit()


def fetch_temperature(lat: float, lon: float) -> float:
    url = f"{OPEN_METEO_URL}?latitude={lat}&longitude={lon}&current_weather=true"
    with urllib.request.urlopen(url, timeout=10) as response:
        payload = json.load(response)
    return parse_temperature(payload)


def parse_temperature(payload: dict) -> float:
    return float(payload["current_weather"]["temperature"])


def refresh_weather(
    config: PgConfig, table: str = "capitals", schema: str = "public"
) -> tuple[int, int]:
    """Fetch current temperature for every row and update it in place.
    Returns (updated, failed); one city's fetch failing doesn't stop the
    rest."""
    with connect(config) as conn, conn.cursor() as cur:
        cur.execute(f"SELECT id, ST_Y(geom), ST_X(geom) FROM {schema}.{table}")
        rows = cur.fetchall()

    updated = 0
    failed = 0
    with connect(config) as conn, conn.cursor() as cur:
        for city_id, lat, lon in rows:
            try:
                temperature = fetch_temperature(lat, lon)
            except Exception:
                failed += 1
                continue
            cur.execute(
                f"UPDATE {schema}.{table} "
                "SET temperature = %s, temperature_updated_at = now() "
                "WHERE id = %s",
                (temperature, city_id),
            )
            updated += 1
        conn.commit()
    return updated, failed
