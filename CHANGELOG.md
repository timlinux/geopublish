# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Initial `geopublish` scaffold: Nix flake devShell (Python, GDAL, PostGIS
  client tools, QGIS, docs, linters), CLI (`init-db`, `publish vector`,
  `publish raster`, `status`), pre-commit hooks, pytest suite, mkdocs site,
  CI workflow, and a QGIS `pg_service.conf` template for credential-free
  connections.
