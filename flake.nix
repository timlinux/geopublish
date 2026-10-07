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
            export PYTHONPATH="${self}/src:$PYTHONPATH"
            export PATH="${self}/bin:$PATH"
            if [ -f "${self}/.pre-commit-config.yaml" ] && [ -d .git ]; then
              pre-commit install --install-hooks >/dev/null 2>&1 || true
            fi
            bash "${self}/scripts/dev-shell-banner.sh" || true
          '';
        };

        apps = {
          default = mkApp "${self}/bin/geopublish";
          geopublish = mkApp "${self}/bin/geopublish";
          test = mkApp "${self}/scripts/test.sh";
          docs = mkApp "${self}/scripts/docs.sh";
          format = mkApp "${self}/scripts/format.sh";
          lint = mkApp "${self}/scripts/lint.sh";
        };
      }
    );
}
