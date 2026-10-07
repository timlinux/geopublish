# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
import pytest

from geopublish.config import load_config


def test_load_config_reads_env(monkeypatch, tmp_path):
    monkeypatch.setenv("PGHOST", "db.example.org")
    monkeypatch.setenv("PGPORT", "5432")
    monkeypatch.setenv("PGDATABASE", "workshop")
    monkeypatch.setenv("PGUSER", "workshop")
    monkeypatch.setenv("PGPASSWORD", "secret")
    monkeypatch.setenv("PGSSLMODE", "require")

    config = load_config(tmp_path / "does-not-exist.env")

    assert config.host == "db.example.org"
    assert "password=secret" in config.conninfo()
    assert "sslmode=require" in config.conninfo()


def test_load_config_missing_vars_raises(monkeypatch, tmp_path):
    for name in ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="Missing required environment variable"):
        load_config(tmp_path / "does-not-exist.env")


def test_conninfo_omits_empty_password(monkeypatch, tmp_path):
    monkeypatch.setenv("PGHOST", "localhost")
    monkeypatch.setenv("PGPORT", "5432")
    monkeypatch.setenv("PGDATABASE", "workshop")
    monkeypatch.setenv("PGUSER", "workshop")
    monkeypatch.delenv("PGPASSWORD", raising=False)

    config = load_config(tmp_path / "does-not-exist.env")

    assert "password=" not in config.conninfo()
