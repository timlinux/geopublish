# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
import psycopg2

from geopublish.config import PgConfig

LIST_LAYERS_QUERY = """
    SELECT f_table_schema AS schema, f_table_name AS name, 'vector' AS kind
    FROM geometry_columns
    UNION ALL
    SELECT r_table_schema AS schema, r_table_name AS name, 'raster' AS kind
    FROM raster_columns
    ORDER BY schema, name;
"""


def connect(config: PgConfig):
    return psycopg2.connect(config.conninfo())


def ensure_postgis(config: PgConfig) -> None:
    with connect(config) as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS postgis_raster;")
        conn.commit()


def list_layers(config: PgConfig) -> list[dict]:
    with connect(config) as conn, conn.cursor() as cur:
        cur.execute(LIST_LAYERS_QUERY)
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
