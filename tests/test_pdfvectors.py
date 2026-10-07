# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
from unittest.mock import MagicMock

import pytest

from geopublish.pdfvectors import (
    ExtractedFeature,
    _classify_and_project,
    _extract_label_lines,
    _iter_drawn_paths,
    _nearest_label,
    extract_vector_features,
    load_features,
    page_to_geo,
)
from geopublish.config import PgConfig
import xml.etree.ElementTree as ET

# Frame + corner labels trimmed from the same real plan sheet used in
# test_pdfmap.py, plus three synthetic drawn shapes (a filled polygon, an
# unfilled line, a tiny point marker) and two text labels, to exercise
# classification + label-matching end to end.
SVG_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="2383.92pt" height="1684.08pt"
     viewBox="0 0 2383.92 1684.08">
<defs>
<path fill="rgb(0%, 0%, 0%)" d="M 0 0 L 1 0 L 1 1 L 0 1 L 0 0 "/>
</defs>
<g>
<path fill="none" stroke-width="1" stroke="rgb(0%, 0%, 0%)"
      d="M -0.00145072 0.000346254 L 2383.921251 0.000346254 L 2383.921251 1684.08 L -0.00145072 1684.08 L -0.00145072 0.000346254 "
      transform="matrix(0.999454, 0, 0, -0.999454, 0.610825, 1683.160502)"/>
<path fill="none" stroke-width="1" stroke="rgb(0%, 0%, 0%)"
      d="M 56.693567 155.905782 L 2369.745542 155.905782 L 2369.745542 1669.9082 L 56.693567 1669.9082 L 56.693567 155.905782 "
      transform="matrix(0.999454, 0, 0, -0.999454, 0.610825, 1683.160502)"/>
<path fill="rgb(70%, 70%, 70%)" stroke="rgb(0%, 0%, 0%)"
      d="M 100 100 L 200 100 L 200 150 L 100 150 L 100 100 "/>
<path fill="none" stroke="rgb(0%, 0%, 0%)"
      d="M 300 300 L 400 320 L 450 290 "/>
<path fill="rgb(0%, 0%, 0%)"
      d="M 500 500 L 505 500 L 505 505 L 500 505 L 500 500 "/>
</g>
</svg>"""

BBOX_FIXTURE = """<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
<doc>
  <page width="2383.920000" height="1684.080000">
    <word xMin="61.7" yMin="1475.0" xMax="70.7" yMax="1517.5">5306794,20</word>
    <word xMin="2360.6" yMin="23.7" xMax="2369.6" yMax="66.2">5307061,26</word>
    <word xMin="2320.2" yMin="15.9" xMax="2367.1" yMax="24.9">32467896,48</word>
    <word xMin="65.2" yMin="1519.7" xMax="112.2" yMax="1528.7">32467488,48</word>
    <word xMin="140" yMin="118" xMax="168" yMax="128">Building</word>
    <word xMin="170" yMin="118" xMax="180" yMax="128">12</word>
    <word xMin="360" yMin="295" xMax="390" yMax="305">Fence</word>
  </page>
</doc>
</body>
</html>"""

PT_BBOX = (57.273437, 14.163868, 2369.062486, 1527.339845)
GEO_BBOX = (467488.48, 5307061.26, 467896.48, 5306794.20)


def _config() -> PgConfig:
    return PgConfig(
        host="h", port="5432", dbname="d", user="u", password="", sslmode="prefer"
    )


def test_page_to_geo_corners_round_trip():
    west, north, east, south = GEO_BBOX
    assert page_to_geo(PT_BBOX, GEO_BBOX, PT_BBOX[0], PT_BBOX[1]) == pytest.approx(
        (west, north), abs=1e-3
    )
    assert page_to_geo(PT_BBOX, GEO_BBOX, PT_BBOX[2], PT_BBOX[3]) == pytest.approx(
        (east, south), abs=1e-3
    )


def test_iter_drawn_paths_skips_defs():
    root = ET.fromstring(SVG_FIXTURE)
    fills = [p.get("fill") for p in _iter_drawn_paths(root)]
    # the decoy glyph in <defs> (black fill, 1x1) must not appear
    assert "rgb(0%, 0%, 0%)" in fills  # the point marker legitimately has it
    assert fills.count("rgb(0%, 0%, 0%)") == 1  # only the point marker, not the glyph


def test_classify_polygon():
    root = ET.fromstring(SVG_FIXTURE)
    polygon_elem = next(
        p for p in _iter_drawn_paths(root) if p.get("fill") == "rgb(70%, 70%, 70%)"
    )
    kind, coords, anchor = _classify_and_project(
        polygon_elem, PT_BBOX, GEO_BBOX, 2383.92, 1684.08
    )
    assert kind == "polygon"
    assert coords[0] == coords[-1]
    assert len(coords) == 5


def test_classify_line():
    root = ET.fromstring(SVG_FIXTURE)
    line_elem = next(
        p for p in _iter_drawn_paths(root) if p.get("fill") == "none" and "300 300" in p.get("d")
    )
    kind, coords, anchor = _classify_and_project(
        line_elem, PT_BBOX, GEO_BBOX, 2383.92, 1684.08
    )
    assert kind == "line"
    assert len(coords) == 3


def test_classify_point():
    root = ET.fromstring(SVG_FIXTURE)
    point_elem = next(p for p in _iter_drawn_paths(root) if "500 500" in p.get("d"))
    kind, coords, anchor = _classify_and_project(
        point_elem, PT_BBOX, GEO_BBOX, 2383.92, 1684.08
    )
    assert kind == "point"
    assert len(coords) == 1


def test_classify_skips_frame_and_page_canvas():
    root = ET.fromstring(SVG_FIXTURE)
    results = [
        _classify_and_project(p, PT_BBOX, GEO_BBOX, 2383.92, 1684.08)
        for p in _iter_drawn_paths(root)
        if p.get("fill") == "none"
    ]
    # of the two fill="none" rects (page canvas, frame) plus the real line,
    # only the line should classify as real content
    assert results.count(None) == 2
    assert sum(1 for r in results if r is not None) == 1


def test_extract_label_lines_merges_adjacent_words():
    lines = _extract_label_lines(BBOX_FIXTURE)
    texts = [text for text, _, _ in lines]
    assert "Building 12" in texts
    assert "Fence" in texts


def test_nearest_label_respects_radius():
    labels = [("Fence", 375.0, 300.0)]
    assert _nearest_label((375.0, 305.0), labels, max_distance=80.0) == "Fence"
    assert _nearest_label((1000.0, 1000.0), labels, max_distance=80.0) is None


def test_extract_vector_features_end_to_end(monkeypatch):
    def fake_run(cmd):
        if "-svg" in cmd:
            return SVG_FIXTURE
        if "-bbox" in cmd:
            return BBOX_FIXTURE
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr("geopublish.pdfvectors._run", fake_run)

    features = extract_vector_features(pdf="dummy.pdf", page=1, zone=32)
    kinds = {f.kind for f in features}
    assert kinds == {"point", "line", "polygon"}

    polygon = next(f for f in features if f.kind == "polygon")
    assert polygon.label == "Building 12"

    line = next(f for f in features if f.kind == "line")
    assert line.label == "Fence"

    point = next(f for f in features if f.kind == "point")
    assert point.label is None


def test_load_features_creates_tables_and_inserts(monkeypatch):
    cursor = MagicMock()
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cursor

    monkeypatch.setattr("geopublish.pdfvectors.connect", lambda config: conn)

    features = [
        ExtractedFeature("point", [(1.0, 2.0)], "marker"),
        ExtractedFeature("line", [(0.0, 0.0), (1.0, 1.0)], "boundary"),
        ExtractedFeature("polygon", [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 0.0)], "building"),
        ExtractedFeature("line", [(0.0, 0.0)], "degenerate"),  # < 2 points, skipped
    ]

    loaded = load_features(_config(), features, source_pdf="x.pdf", source_page=1)

    assert loaded == {"point": 1, "line": 1, "polygon": 1}
    insert_calls = [c for c in cursor.execute.call_args_list if "INSERT INTO" in c.args[0]]
    assert len(insert_calls) == 3
