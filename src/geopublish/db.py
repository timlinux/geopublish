# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
import psycopg2
import psycopg2.errors

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
        conn.commit()

    with connect(config) as conn, conn.cursor() as cur:
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis_raster;")
        except psycopg2.errors.InsufficientPrivilege as exc:
            raise RuntimeError(
                "postgis was created, but creating postgis_raster on "
                f"{config.dbname}@{config.host} needs superuser privileges "
                f"that {config.user!r} doesn't have. Ask your DB "
                "administrator or hosting provider to run 'CREATE EXTENSION "
                "IF NOT EXISTS postgis_raster;' for you."
            ) from exc
        conn.commit()


def list_layers(config: PgConfig) -> list[dict]:
    with connect(config) as conn, conn.cursor() as cur:
        try:
            cur.execute(LIST_LAYERS_QUERY)
        except psycopg2.errors.UndefinedTable as exc:
            raise RuntimeError(
                "postgis/postgis_raster extensions aren't set up on "
                f"{config.dbname}@{config.host} yet. Run 'geopublish init-db' first."
            ) from exc
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
