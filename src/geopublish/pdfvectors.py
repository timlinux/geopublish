# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from geopublish.config import PgConfig
from geopublish.db import connect
from geopublish.pdfmap import (
    GeoBBox,
    PtBBox,
    _apply_matrix,
    _local_tag,
    _MATRIX,
    _NUM,
    _run,
    discover_pdfs,
    frame_bbox_from_svg,
    geo_bbox_from_coordinate_words,
    page_count,
)

# A path whose (page-point) bounding-box diagonal is smaller than this is
# treated as a point symbol (e.g. a small vertex-marker circle) rather
# than a line or polygon -- it's drawn as a tiny shape, not meant to be
# read as one.
POINT_DIAGONAL_THRESHOLD_PT = 10.0

# How far (in page points) a printed text label may be from a feature's
# bbox centre and still count as its annotation. Points get a tight
# radius so a nearby parcel number doesn't get misattributed to every
# vertex marker along a boundary; lines/polygons get a looser one since
# their labels are usually placed somewhere inside/near the shape, not
# pinned to an exact point.
POINT_LABEL_RADIUS_PT = 12.0
LINE_LABEL_RADIUS_PT = 80.0
POLYGON_LABEL_RADIUS_PT = 80.0


def page_to_geo(pt_bbox: PtBBox, geo_bbox: GeoBBox, x: float, y: float) -> tuple[float, float]:
    """Map a page-point (top-down) coordinate to real-world (easting,
    northing) using the same linear frame<->geo mapping as
    pdfmap.pdf_to_geotiff's -a_ullr."""
    left, top, right, bottom = pt_bbox
    west, north, east, south = geo_bbox
    easting = west + (x - left) / (right - left) * (east - west)
    northing = north + (y - top) / (bottom - top) * (south - north)
    return easting, northing


def _path_points(d: str) -> list[tuple[float, float]]:
    nums = [float(n) for n in _NUM.findall(d)]
    return list(zip(nums[0::2], nums[1::2]))


def _iter_drawn_paths(elem):
    """Yield <path> elements that are actually drawn content, skipping
    <defs> (font glyph outlines live there, referenced via <use> -- they
    are not map geometry)."""
    for child in elem:
        tag = _local_tag(child.tag)
        if tag == "defs":
            continue
        if tag == "path":
            yield child
        yield from _iter_drawn_paths(child)


def _bbox_close(a: tuple[float, float, float, float], b: tuple[float, float, float, float], tol: float = 2.0) -> bool:
    return all(abs(x - y) < tol for x, y in zip(a, b))


def _extract_label_lines(xhtml_bbox: str) -> list[tuple[str, float, float]]:
    """Merge pdftotext -bbox's individual <word> elements into text
    lines (poppler doesn't group them itself): words on the same
    baseline with a small horizontal gap are joined in reading order.
    Returns (text, centre_x, centre_y) in page points."""
    root = ET.fromstring(xhtml_bbox)
    words = []
    for word in root.iter():
        if _local_tag(word.tag) != "word":
            continue
        text = (word.text or "").strip()
        if not text:
            continue
        words.append(
            [
                text,
                float(word.get("xMin")),
                float(word.get("yMin")),
                float(word.get("xMax")),
                float(word.get("yMax")),
            ]
        )
    words.sort(key=lambda w: (w[2], w[1]))

    lines: list[list] = []
    for text, xmin, ymin, xmax, ymax in words:
        for line in lines:
            _, lxmin, lymin, lxmax, lymax = line
            vertical_overlap = not (ymax < lymin - 1 or ymin > lymax + 1)
            horizontal_gap = xmin - lxmax
            if vertical_overlap and -2 <= horizontal_gap <= 20:
                line[0].append(text)
                line[1] = min(lxmin, xmin)
                line[2] = min(lymin, ymin)
                line[3] = max(lxmax, xmax)
                line[4] = max(lymax, ymax)
                break
        else:
            lines.append([[text], xmin, ymin, xmax, ymax])

    return [
        (" ".join(parts), (xmin + xmax) / 2, (ymin + ymax) / 2)
        for parts, xmin, ymin, xmax, ymax in lines
    ]


def _nearest_label(
    anchor: tuple[float, float], labels: list[tuple[str, float, float]], max_distance: float
) -> str | None:
    ax, ay = anchor
    best_text = None
    best_dist = max_distance
    for text, lx, ly in labels:
        dist = math.hypot(lx - ax, ly - ay)
        if dist < best_dist:
            best_dist = dist
            best_text = text
    return best_text


def _classify_and_project(
    elem, pt_bbox: PtBBox, geo_bbox: GeoBBox, page_width: float, page_height: float
):
    """Classify one drawn <path> as a point/line/polygon and project its
    vertices to real-world coordinates. Returns (kind, geo_coords,
    anchor_page_point) or None if the path isn't real map content (the
    frame border, the page canvas, or a title-block background cell)."""
    fill = elem.get("fill")
    if fill == "rgb(100%, 100%, 100%)":
        return None
    d = elem.get("d")
    if not d:
        return None
    local_points = _path_points(d)
    if len(local_points) < 2:
        return None

    tmatch = _MATRIX.search(elem.get("transform", ""))
    matrix = tuple(float(g) for g in tmatch.groups()) if tmatch else (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    page_points = [_apply_matrix(matrix, x, y) for x, y in local_points]

    xs = [p[0] for p in page_points]
    ys = [p[1] for p in page_points]
    bbox = (min(xs), min(ys), max(xs), max(ys))

    if _bbox_close(bbox, pt_bbox) or _bbox_close(bbox, (0.0, 0.0, page_width, page_height)):
        return None  # the drawn frame border, or the full-page canvas

    anchor = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]

    if math.hypot(width, height) < POINT_DIAGONAL_THRESHOLD_PT:
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        return "point", [page_to_geo(pt_bbox, geo_bbox, cx, cy)], anchor

    geo_coords = [page_to_geo(pt_bbox, geo_bbox, x, y) for x, y in page_points]
    if fill and fill != "none":
        if geo_coords[0] != geo_coords[-1]:
            geo_coords.append(geo_coords[0])
        return "polygon", geo_coords, anchor
    return "line", geo_coords, anchor


@dataclass
class ExtractedFeature:
    kind: str  # "point" | "line" | "polygon"
    coords: list[tuple[float, float]]
    label: str | None


def extract_vector_features(pdf: Path, page: int, zone: int = 32) -> list[ExtractedFeature]:
    """Extract point/line/polygon geometry from one PDF page's vector
    content, in real-world coordinates, with the nearest printed text
    label attached as a best-effort annotation."""
    svg = _run(["pdftocairo", "-svg", "-f", str(page), "-l", str(page), str(pdf), "-"])
    bbox_xhtml = _run(["pdftotext", "-bbox", "-f", str(page), "-l", str(page), str(pdf), "-"])

    pt_bbox = frame_bbox_from_svg(svg)
    geo_bbox = geo_bbox_from_coordinate_words(bbox_xhtml, zone=zone)
    labels = _extract_label_lines(bbox_xhtml)

    root = ET.fromstring(svg)
    page_width = float(root.get("width", "0pt").rstrip("pt"))
    page_height = float(root.get("height", "0pt").rstrip("pt"))

    label_radius = {
        "point": POINT_LABEL_RADIUS_PT,
        "line": LINE_LABEL_RADIUS_PT,
        "polygon": POLYGON_LABEL_RADIUS_PT,
    }

    features = []
    for elem in _iter_drawn_paths(root):
        result = _classify_and_project(elem, pt_bbox, geo_bbox, page_width, page_height)
        if result is None:
            continue
        kind, geo_coords, anchor = result
        label = _nearest_label(anchor, labels, label_radius[kind])
        features.append(ExtractedFeature(kind, geo_coords, label))

    if not features and "<image" in svg:
        raise RuntimeError(
            "no vector paths found, and this page embeds raster image(s) -- "
            "its map content is almost certainly a rasterized basemap baked "
            "into the PDF, not real vector geometry. Use 'prepare "
            "pdf-to-geotiff' + 'publish raster' for this page instead."
        )
    return features


TABLE_DDL = {
    "point": """
        CREATE TABLE IF NOT EXISTS points (
            id SERIAL PRIMARY KEY,
            source_pdf TEXT NOT NULL,
            source_page INTEGER NOT NULL,
            label TEXT,
            geom geometry(Point, {srid}) NOT NULL
        )
    """,
    "line": """
        CREATE TABLE IF NOT EXISTS lines (
            id SERIAL PRIMARY KEY,
            source_pdf TEXT NOT NULL,
            source_page INTEGER NOT NULL,
            label TEXT,
            geom geometry(LineString, {srid}) NOT NULL
        )
    """,
    "polygon": """
        CREATE TABLE IF NOT EXISTS polygons (
            id SERIAL PRIMARY KEY,
            source_pdf TEXT NOT NULL,
            source_page INTEGER NOT NULL,
            label TEXT,
            geom geometry(Polygon, {srid}) NOT NULL
        )
    """,
}

TABLE_NAMES = {"point": "points", "line": "lines", "polygon": "polygons"}


def _to_wkt(kind: str, coords: list[tuple[float, float]]) -> str:
    if kind == "point":
        x, y = coords[0]
        return f"POINT({x} {y})"
    pairs = ", ".join(f"{x} {y}" for x, y in coords)
    if kind == "line":
        return f"LINESTRING({pairs})"
    return f"POLYGON(({pairs}))"


def load_features(
    config: PgConfig,
    features: list[ExtractedFeature],
    source_pdf: str,
    source_page: int,
    srid: int = 25832,
) -> dict[str, int]:
    with connect(config) as conn, conn.cursor() as cur:
        for ddl in TABLE_DDL.values():
            cur.execute(ddl.format(srid=srid))
        conn.commit()

    loaded = {"point": 0, "line": 0, "polygon": 0}
    with connect(config) as conn, conn.cursor() as cur:
        for feature in features:
            if feature.kind == "line" and len(feature.coords) < 2:
                continue
            if feature.kind == "polygon" and len(feature.coords) < 4:
                continue
            table = TABLE_NAMES[feature.kind]
            wkt = _to_wkt(feature.kind, feature.coords)
            cur.execute(
                f"INSERT INTO {table} (source_pdf, source_page, label, geom) "
                f"VALUES (%s, %s, %s, ST_SetSRID(ST_GeomFromText(%s), %s))",
                (source_pdf, source_page, feature.label, wkt, srid),
            )
            loaded[feature.kind] += 1
        conn.commit()
    return loaded
