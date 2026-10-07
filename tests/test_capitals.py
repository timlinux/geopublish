# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
from unittest.mock import MagicMock

import pytest

from geopublish.capitals import load_capitals, parse_temperature, refresh_weather
from geopublish.config import PgConfig

# A real response captured from https://api.open-meteo.com/v1/forecast
# (no API key) for London, trimmed to the fields parse_temperature reads.
OPEN_METEO_RESPONSE = {
    "latitude": 51.51147,
    "longitude": -0.13078308,
    "current_weather_units": {"temperature": "°C"},
    "current_weather": {
        "time": "2026-10-07T10:15",
        "temperature": 13.9,
        "windspeed": 7.6,
        "winddirection": 3,
        "is_day": 1,
        "weathercode": 61,
    },
}


def _config() -> PgConfig:
    return PgConfig(
        host="h", port="5432", dbname="d", user="u", password="", sslmode="prefer"
    )


def test_parse_temperature():
    assert parse_temperature(OPEN_METEO_RESPONSE) == 13.9


def test_load_capitals_names_the_primary_key_id(monkeypatch):
    # Regression test: ogr2ogr's PostgreSQL driver defaults its
    # auto-generated primary key to "ogc_fid", not "id" -- without
    # `-lco FID=id`, refresh_weather()'s `SELECT id, ...` fails with
    # psycopg2.errors.UndefinedColumn.
    calls = []
    monkeypatch.setattr(
        "geopublish.capitals.subprocess.run",
        lambda cmd, **kwargs: calls.append(cmd),
    )

    conn = MagicMock()
    conn.__enter__.return_value = conn
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    monkeypatch.setattr("geopublish.capitals.connect", lambda config: conn)

    load_capitals(_config())

    (ogr2ogr_cmd,) = calls
    lco_values = [
        ogr2ogr_cmd[i + 1] for i, arg in enumerate(ogr2ogr_cmd) if arg == "-lco"
    ]
    assert "FID=id" in lco_values


def test_refresh_weather_skips_failures_and_counts_both(monkeypatch):
    cursor = MagicMock()
    cursor.fetchall.return_value = [(1, 51.5, -0.1), (2, 48.8, 2.3), (3, 35.6, 139.7)]

    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cursor

    monkeypatch.setattr("geopublish.capitals.connect", lambda config: conn)

    def fake_fetch(lat, lon):
        if lat == 48.8:
            raise RuntimeError("network blip")
        return 20.0

    monkeypatch.setattr("geopublish.capitals.fetch_temperature", fake_fetch)

    updated, failed = refresh_weather(_config())

    assert (updated, failed) == (2, 1)
    update_calls = [c for c in cursor.execute.call_args_list if "UPDATE" in c.args[0]]
    assert len(update_calls) == 2  # one UPDATE per successful fetch, none for the failure
