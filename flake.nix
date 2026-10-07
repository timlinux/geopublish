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
          pkgs.poppler_utils
          pkgs.postgresql_16
          postgis
          pkgs.qgis
          pkgs.inkscape
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

          # Mirrors gp's dev-tool subcommands (same scripts gp itself calls).
          test = mkApp "${self}/scripts/test.sh";
          format = mkApp "${self}/scripts/format.sh";
          lint = mkApp "${self}/scripts/lint.sh";
          diagrams = mkApp "${self}/scripts/render-diagrams.sh";

          # Mirrors every gp data/workflow subcommand 1:1 (see
          # scripts/apps/*.sh) -- "one implementation, two entry points".
          docs-serve = mkApp "${self}/scripts/docs.sh";
          init-db = mkApp "${self}/scripts/apps/init-db.sh";
          publish-vector = mkApp "${self}/scripts/apps/publish-vector.sh";
          publish-raster = mkApp "${self}/scripts/apps/publish-raster.sh";
          publish-pdf-vectors = mkApp "${self}/scripts/apps/publish-pdf-vectors.sh";
          status = mkApp "${self}/scripts/apps/status.sh";
          prepare-pdf-to-geotiff = mkApp "${self}/scripts/apps/prepare-pdf-to-geotiff.sh";
          capitals-load = mkApp "${self}/scripts/apps/capitals-load.sh";
          capitals-refresh-weather = mkApp "${self}/scripts/apps/capitals-refresh-weather.sh";
        };
      }
    );
}
