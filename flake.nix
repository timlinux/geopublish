# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
{
  description = "geopublish: workflow for publishing vector and raster data to PostGIS, for viewing in QGIS";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        pythonEnv = pkgs.python3.withPackages (
          ps: with ps; [
            gdal
            psycopg2
            python-dotenv
            click
            pytest
            mkdocs
            mkdocs-material
          ]
        );

        postgis = pkgs.postgresql_16.pkgs.postgis;

        devTools = [
          pythonEnv
          pkgs.gdal
          pkgs.postgresql_16
          postgis
          pkgs.qgis
          pkgs.chafa
          pkgs.pre-commit
          pkgs.black
          pkgs.ruff
          pkgs.codespell
          pkgs.reuse
          pkgs.gitleaks
        ];

        mkApp = scriptPath: {
          type = "app";
          program = toString scriptPath;
        };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = devTools;

          shellHook = ''
            repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
            export PYTHONPATH="$repo_root/src:$PYTHONPATH"
            export PATH="$repo_root/bin:$PATH"
            if [ -f "$repo_root/.pre-commit-config.yaml" ] && [ -d "$repo_root/.git" ]; then
              pre-commit install --install-hooks >/dev/null 2>&1 || true
            fi
            bash "$repo_root/scripts/dev-shell-banner.sh" || true
            unset repo_root
          '';
        };

        apps = {
          default = mkApp "${self}/bin/geopublish";
          geopublish = mkApp "${self}/bin/geopublish";
          gp = mkApp "${self}/bin/gp";
          test = mkApp "${self}/scripts/test.sh";
          docs = mkApp "${self}/scripts/docs.sh";
          format = mkApp "${self}/scripts/format.sh";
          lint = mkApp "${self}/scripts/lint.sh";
        };
      }
    );
}
