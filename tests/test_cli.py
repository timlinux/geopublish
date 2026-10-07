# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
from click.testing import CliRunner

from geopublish.cli import cli


def test_cli_help():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "publish vector and raster data" in result.output


def test_publish_vector_help():
    result = CliRunner().invoke(cli, ["publish", "vector", "--help"])
    assert result.exit_code == 0
    assert "--table" in result.output


def test_publish_raster_help():
    result = CliRunner().invoke(cli, ["publish", "raster", "--help"])
    assert result.exit_code == 0
    assert "--tile-size" in result.output


def test_docs_serve_help():
    result = CliRunner().invoke(cli, ["docs-serve", "--help"])
    assert result.exit_code == 0
    assert "mkdocs" in result.output


def test_docs_build_and_docs_pdf_help():
    for args in (["docs-build", "--help"], ["docs-pdf", "--help"]):
        result = CliRunner().invoke(cli, args)
        assert result.exit_code == 0, args


def test_prepare_pdf_to_geotiff_help():
    result = CliRunner().invoke(cli, ["prepare", "pdf-to-geotiff", "--help"])
    assert result.exit_code == 0
    assert "--utm-zone" in result.output


def test_capitals_load_help():
    result = CliRunner().invoke(cli, ["capitals", "load", "--help"])
    assert result.exit_code == 0
    assert "--table" in result.output


def test_capitals_refresh_weather_help():
    result = CliRunner().invoke(cli, ["capitals", "refresh-weather", "--help"])
    assert result.exit_code == 0
    assert "Open-Meteo" in result.output


def test_publish_pdf_vectors_help():
    result = CliRunner().invoke(cli, ["publish", "pdf-vectors", "--help"])
    assert result.exit_code == 0
    assert "--utm-zone" in result.output


def test_test_format_lint_diagrams_help():
    for name in ("test", "format", "lint", "diagrams"):
        result = CliRunner().invoke(cli, [name, "--help"])
        assert result.exit_code == 0, name


def test_status_without_config_fails_cleanly():
    result = CliRunner().invoke(cli, ["status"], env={"PGHOST": ""})
    assert result.exit_code != 0
