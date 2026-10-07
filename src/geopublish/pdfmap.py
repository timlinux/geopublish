# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

PtBBox = tuple[float, float, float, float]  # left, top, right, bottom (points, top-down)
GeoBBox = tuple[float, float, float, float]  # west, north, east, south

_COORD_WORD = re.compile(r"^(\d{7,8}),(\d{2})$")
_MATRIX = re.compile(
    r"matrix\(\s*([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)[,\s]+"
    r"([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)\s*\)"
)
_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def _local_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def pixel_srcwin(pt_bbox: PtBBox, dpi: int) -> tuple[int, int, int, int]:
    """Convert a PDF-point frame bbox (left, top, right, bottom; top-down) to
    a pixel (xoff, yoff, xsize, ysize) window at the given rasterization
    DPI."""
    left, top, right, bottom = pt_bbox
    return (
        round(left / 72 * dpi),
        round(top / 72 * dpi),
        round((right - left) / 72 * dpi),
        round((bottom - top) / 72 * dpi),
    )


def parse_coordinate_words(xhtml_bbox: str, zone: int) -> tuple[list[float], list[float]]:
    """Parse 'pdftotext -bbox' XHTML for German-formatted UTM corner
    coordinate labels, e.g. "32467896,48" (zone-prefixed easting) or
    "5307061,26" (northing). Returns (eastings, northings)."""
    root = ET.fromstring(xhtml_bbox)
    zone_prefix = str(zone)
    eastings: list[float] = []
    northings: list[float] = []
    for word in root.iter():
        if _local_tag(word.tag) != "word":
            continue
        match = _COORD_WORD.match((word.text or "").strip())
        if not match:
            continue
        integer_part, frac_part = match.groups()
        if len(integer_part) == 8 and integer_part.startswith(zone_prefix):
            eastings.append(float(f"{integer_part[2:]}.{frac_part}"))
        elif len(integer_part) == 7:
            northings.append(float(f"{integer_part}.{frac_part}"))
    return eastings, northings


def geo_bbox_from_coordinate_words(xhtml_bbox: str, zone: int) -> GeoBBox:
    eastings, northings = parse_coordinate_words(xhtml_bbox, zone=zone)
    if len(eastings) < 2 or len(northings) < 2:
        raise RuntimeError(
            "could not find at least 2 easting and 2 northing corner "
            "coordinate labels printed on this PDF page"
        )
    return min(eastings), max(northings), max(eastings), min(northings)


def _rect_from_path(d: str) -> tuple[float, float, float, float] | None:
    """If d is a 5-point closed axis-aligned rectangle, return its local
    (xmin, ymin, xmax, ymax); else None."""
    nums = [float(n) for n in _NUM.findall(d)]
    if len(nums) != 10:
        return None
    points = list(zip(nums[0::2], nums[1::2]))
    if points[0] != points[4]:
        return None
    corners = points[:4]
    if len({round(p[0], 3) for p in corners}) != 2:
        return None
    if len({round(p[1], 3) for p in corners}) != 2:
        return None
    xs = [p[0] for p in corners]
    ys = [p[1] for p in corners]
    return min(xs), min(ys), max(xs), max(ys)


def _apply_matrix(matrix: tuple[float, ...], x: float, y: float) -> tuple[float, float]:
    a, b, c, d, e, f = matrix
    return a * x + c * y + e, b * x + d * y + f


def frame_bbox_from_svg(svg_text: str) -> PtBBox:
    """Find the drawn content frame in an SVG exported by `pdftocairo -svg`:
    the largest fill="none"-stroked axis-aligned rectangle that isn't the
    full page canvas. Returns (left, top, right, bottom) in page points,
    top-down -- the same convention as `pdftotext -bbox`."""
    root = ET.fromstring(svg_text)
    page_width = float(root.get("width", "0pt").rstrip("pt"))
    page_height = float(root.get("height", "0pt").rstrip("pt"))

    candidates = []
    for elem in root.iter():
        if _local_tag(elem.tag) != "path" or elem.get("fill") != "none":
            continue
        d = elem.get("d")
        if not d:
            continue
        rect = _rect_from_path(d)
        if rect is None:
            continue
        tmatch = _MATRIX.search(elem.get("transform", ""))
        matrix = tuple(float(g) for g in tmatch.groups()) if tmatch else (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        x0, y0, x1, y1 = rect
        corners = [_apply_matrix(matrix, x, y) for x, y in ((x0, y0), (x1, y1))]
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        candidates.append((min(xs), min(ys), max(xs), max(ys)))

    if not candidates:
        raise RuntimeError("no frame rectangle found on this rendered PDF page")

    tolerance = 2.0

    def is_full_page(box: PtBBox) -> bool:
        left, top, right, bottom = box
        return (
            abs(left) < tolerance
            and abs(top) < tolerance
            and abs(right - page_width) < tolerance
            and abs(bottom - page_height) < tolerance
        )

    def area(box: PtBBox) -> float:
        left, top, right, bottom = box
        return (right - left) * (bottom - top)

    inner = [box for box in candidates if not is_full_page(box)]
    if not inner:
        raise RuntimeError("only found the full-page border; no inner content frame")
    return max(inner, key=area)


def _run(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def extract_frame_and_geo_bbox(pdf: Path, page: int, zone: int) -> tuple[PtBBox, GeoBBox]:
    svg = _run(["pdftocairo", "-svg", "-f", str(page), "-l", str(page), str(pdf), "-"])
    bbox_xhtml = _run(["pdftotext", "-bbox", "-f", str(page), "-l", str(page), str(pdf), "-"])
    return frame_bbox_from_svg(svg), geo_bbox_from_coordinate_words(bbox_xhtml, zone=zone)


def pdf_to_geotiff(
    source: Path,
    page: int,
    dpi: int,
    srs: str,
    output: Path,
    zone: int = 32,
    pt_bbox: PtBBox | None = None,
    geo_bbox: GeoBBox | None = None,
) -> None:
    """Rasterize one PDF page, clip it to its drawn frame, and georeference
    the clip. The frame and its real-world corner coordinates are detected
    automatically unless pt_bbox/geo_bbox are given explicitly."""
    if pt_bbox is None or geo_bbox is None:
        auto_pt_bbox, auto_geo_bbox = extract_frame_and_geo_bbox(source, page, zone=zone)
        pt_bbox = pt_bbox or auto_pt_bbox
        geo_bbox = geo_bbox or auto_geo_bbox

    xoff, yoff, xsize, ysize = pixel_srcwin(pt_bbox, dpi)
    west, north, east, south = geo_bbox

    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "page"
        subprocess.run(
            [
                "pdftocairo",
                "-tiff",
                "-r",
                str(dpi),
                "-f",
                str(page),
                "-l",
                str(page),
                str(source),
                str(prefix),
            ],
            check=True,
        )
        (rasterized,) = Path(tmp).glob("page*.tif")
        subprocess.run(
            [
                "gdal_translate",
                "-srcwin",
                str(xoff),
                str(yoff),
                str(xsize),
                str(ysize),
                "-a_ullr",
                str(west),
                str(north),
                str(east),
                str(south),
                "-a_srs",
                srs,
                "-co",
                "COMPRESS=LZW",
                str(rasterized),
                str(output),
            ],
            check=True,
        )


def discover_pdfs(source: Path) -> list[Path]:
    return sorted(source.glob("*.pdf")) if source.is_dir() else [source]


def page_count(pdf: Path) -> int:
    for line in _run(["pdfinfo", str(pdf)]).splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise RuntimeError(f"couldn't determine page count for {pdf}")


@dataclass
class ConversionResult:
    pdf: Path
    page: int
    output: Path | None
    error: str | None


def batch_convert(
    source: Path,
    output_dir: Path,
    dpi: int,
    srs: str,
    zone: int = 32,
    pages: list[int] | None = None,
) -> list[ConversionResult]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for pdf in discover_pdfs(source):
        page_numbers = pages or list(range(1, page_count(pdf) + 1))
        for page in page_numbers:
            output = output_dir / f"{pdf.stem}_p{page}.tif"
            try:
                pdf_to_geotiff(pdf, page=page, dpi=dpi, srs=srs, output=output, zone=zone)
                results.append(ConversionResult(pdf, page, output, None))
            except Exception as exc:  # a batch run must survive one bad sheet
                results.append(ConversionResult(pdf, page, None, str(exc)))
    return results
