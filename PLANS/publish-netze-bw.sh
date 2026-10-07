#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
GEOTIFF_DIR="$REPO_ROOT/PLANS/geotiff"

gp publish raster "$GEOTIFF_DIR/20231030_0047_V01_Auskunft_05_A1_Q_p1.tif" --table netze_bw_strom_p1
gp publish raster "$GEOTIFF_DIR/20231030_0047_V01_Auskunft_05_A1_Q_p2.tif" --table netze_bw_fttx_p1

gp status
