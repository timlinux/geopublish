# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
from unittest.mock import MagicMock

import psycopg2.errors
import pytest

from geopublish.config import PgConfig
from geopublish.db import ensure_postgis, list_layers


def _config() -> PgConfig:
    return PgConfig(
        host="h", port="5432", dbname="d", user="u", password="", sslmode="prefer"
    )


def test_list_layers_missing_extension_raises_friendly_error(monkeypatch):
    cursor = MagicMock()
    cursor.execute.side_effect = psycopg2.errors.UndefinedTable(
        'relation "raster_columns" does not exist'
    )

    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cursor

    monkeypatch.setattr("geopublish.db.connect", lambda config: conn)

    with pytest.raises(RuntimeError, match="init-db"):
        list_layers(_config())


def test_ensure_postgis_commits_postgis_before_raster_fails(monkeypatch):
    cursor = MagicMock()
    cursor.execute.side_effect = [
        None,  # CREATE EXTENSION postgis
        psycopg2.errors.InsufficientPrivilege("permission denied"),
    ]

    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cursor

    monkeypatch.setattr("geopublish.db.connect", lambda config: conn)

    with pytest.raises(RuntimeError, match="superuser"):
        ensure_postgis(_config())

    # postgis's own transaction was committed before postgis_raster ran.
    assert conn.commit.call_count == 1
