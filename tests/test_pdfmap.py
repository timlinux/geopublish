# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
import pytest

from geopublish.pdfmap import (
    discover_pdfs,
    frame_bbox_from_svg,
    geo_bbox_from_coordinate_words,
    pixel_srcwin,
)

# Fixtures below are trimmed from a real Netze BW "Netzauskunft" A1 plan
# sheet (page 2383.92 x 1684.08 pt): the full-page canvas border, the
# drawn content frame, and the four corner coordinate labels.
SVG_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="2383.92pt" height="1684.08pt"
     viewBox="0 0 2383.92 1684.08">
<g>
<path fill="none" stroke-width="1" stroke="rgb(0%, 0%, 0%)"
      d="M -0.00145072 0.000346254 L 2383.921251 0.000346254 L 2383.921251 1684.08 L -0.00145072 1684.08 L -0.00145072 0.000346254 "
      transform="matrix(0.999454, 0, 0, -0.999454, 0.610825, 1683.160502)"/>
<path fill="none" stroke-width="1" stroke="rgb(0%, 0%, 0%)"
      d="M 56.693567 155.905782 L 2369.745542 155.905782 L 2369.745542 1669.9082 L 56.693567 1669.9082 L 56.693567 155.905782 "
      transform="matrix(0.999454, 0, 0, -0.999454, 0.610825, 1683.160502)"/>
<path fill="rgb(100%, 100%, 100%)" stroke-width="1" stroke="rgb(0%, 0%, 0%)"
      d="M 1845.338125 14.172146 L 1845.338125 141.733982 L 2369.745542 141.733982 L 2369.745542 14.172146 L 1845.338125 14.172146 "
      transform="matrix(0.999454, 0, 0, -0.999454, 0.610825, 1683.160502)"/>
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
    <word xMin="100" yMin="100" xMax="110" yMax="110">1028/26</word>
  </page>
</doc>
</body>
</html>"""


def test_frame_bbox_from_svg_finds_inner_frame_not_full_page():
    left, top, right, bottom = frame_bbox_from_svg(SVG_FIXTURE)

    assert left == pytest.approx(57.273, abs=0.01)
    assert top == pytest.approx(14.164, abs=0.01)
    assert right == pytest.approx(2369.062, abs=0.01)
    assert bottom == pytest.approx(1527.340, abs=0.01)


def test_geo_bbox_from_coordinate_words():
    west, north, east, south = geo_bbox_from_coordinate_words(BBOX_FIXTURE, zone=32)

    assert west == pytest.approx(467488.48)
    assert east == pytest.approx(467896.48)
    assert north == pytest.approx(5307061.26)
    assert south == pytest.approx(5306794.20)


def test_geo_bbox_raises_when_labels_missing():
    with pytest.raises(RuntimeError, match="coordinate labels"):
        geo_bbox_from_coordinate_words("<doc><page><word>1028/26</word></page></doc>", zone=32)


def test_pixel_srcwin():
    assert pixel_srcwin((72, 72, 144, 216), dpi=72) == (72, 72, 72, 144)


def test_discover_pdfs_globs_directory(tmp_path):
    (tmp_path / "a.pdf").write_bytes(b"")
    (tmp_path / "b.pdf").write_bytes(b"")
    (tmp_path / "c.txt").write_bytes(b"")

    assert discover_pdfs(tmp_path) == [tmp_path / "a.pdf", tmp_path / "b.pdf"]


def test_discover_pdfs_single_file(tmp_path):
    pdf = tmp_path / "only.pdf"
    pdf.write_bytes(b"")

    assert discover_pdfs(pdf) == [pdf]
