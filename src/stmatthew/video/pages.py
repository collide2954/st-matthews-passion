"""Make the score pages for the video, and find where each moment is on each page.

Each section of the work becomes a small LilyPond file. Each system of music is
one page (one screen of the video). LilyPond writes the pages two times: as PDF
for the image, and as SVG with tags. The tags give the position of each note
column, each bar line, and each staff.
"""

from __future__ import annotations

import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

import numpy as np

from ..notation import lilypond
from ..notation.work import Work

GROUP_RE = re.compile(
    r'<g class="(nh|rest|bar|staff)"([^>]*)>(.*?)\n</g>\n(?=<g class=|<g transform|</svg>)', re.S
)
TRANSLATE_RE = re.compile(r"translate\(([-\d.]+), ([-\d.]+)\)")
LINE_RE = re.compile(r'x1="([-\d.]+)"[^>]*x2="([-\d.]+)"')
VIEWBOX_RE = re.compile(r'viewBox="([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)"')


@dataclass
class Page:
    """One screen of the video: one system of the score."""

    image: Path
    start: float  # quarter notes from the start of the work
    end: float
    times: np.ndarray  # quarter notes, increasing
    xs: np.ndarray  # horizontal position of each time, in pixels
    staves: dict[str, tuple[float, float]] = field(default_factory=dict)  # player -> top, bottom
    left: float = 0.0
    right: float = 0.0
    top: float = 0.0
    bottom: float = 0.0


def staff_size(staves: int, mobile: bool = False) -> float:
    """Return the staff size (points) for a section with a number of staves.

    The size is as large as possible. The tallest system must fit on the
    screen. The screen of a telephone is tall: the staves can be larger.
    """
    if mobile:
        # A measurement of the pages gave the height of a system: about 3.6 pixels for
        # each staff and each point of the staff size. The score area is 1500 pixels.
        return float(np.clip(400.0 / (staves + 0.5), 6.5, 30.0))
    return float(np.clip(215.0 / (staves + 1.5), 5.5, 15.0))


def _compile(path: Path, dpi: float) -> None:
    # Remove the pages of an earlier build: the new build can have fewer pages.
    for suffix in ("png", "svg"):
        for old in _numbered(path.parent, path.stem, suffix):
            old.unlink()
    for backend in ([], ["-dbackend=svg"]):
        result = subprocess.run(
            ["lilypond", *backend, "-dno-point-and-click", "--loglevel=ERROR", path.name],
            cwd=path.parent,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"LilyPond failed for {path}:\n{result.stderr[-1500:]}")
    subprocess.run(
        ["pdftoppm", "-r", f"{dpi:.3f}", "-png", f"{path.stem}.pdf", path.stem],
        cwd=path.parent,
        check=True,
    )


def _numbered(directory: Path, stem: str, suffix: str) -> list[Path]:
    """Return the files `stem-N.suffix` in number sequence (or `stem.suffix`)."""
    single = directory / f"{stem}.{suffix}"
    found = sorted(
        directory.glob(f"{stem}-*.{suffix}"),
        key=lambda path: int(path.stem.rsplit("-", 1)[1]),
    )
    return found or ([single] if single.exists() else [])


def _parse(svg: Path, image: Path, section_start: Fraction, width_px: int) -> Page | None:
    text = svg.read_text(encoding="utf-8")
    view = VIEWBOX_RE.search(text)
    assert view is not None
    scale = width_px / float(view.group(3))
    columns: dict[float, float] = {}
    bars: dict[float, float] = {}
    staves: dict[str, tuple[float, float]] = {}
    left, right = np.inf, -np.inf
    for kind, attributes, body in GROUP_RE.findall(text):
        positions = [(float(x), float(y)) for x, y in TRANSLATE_RE.findall(body)]
        if not positions:
            continue
        if kind == "staff":
            name = re.search(r'data-staff="([^"]+)"', attributes)
            ys = [y for _, y in positions]
            lines = LINE_RE.findall(body)
            x0 = positions[0][0]
            if name and lines:
                top, bottom = min(ys) * scale, max(ys) * scale
                player = name.group(1).split(".")[0]
                if player in staves:
                    top = min(top, staves[player][0])
                    bottom = max(bottom, staves[player][1])
                staves[player] = (top, bottom)
                left = min(left, (x0 + float(lines[0][0])) * scale)
                right = max(right, (x0 + float(lines[0][1])) * scale)
            continue
        when = re.search(r'data-when="([-\d.]+)"', attributes)
        if not when:
            continue
        moment = float(section_start) + 4.0 * float(when.group(1))
        x = min(x for x, _ in positions) * scale
        target = bars if kind == "bar" else columns
        target[moment] = min(x, target.get(moment, np.inf))
    if not staves or not (columns or bars):
        return None
    # A note column gives the position of its moment. A bar line gives the
    # position only if no note starts at that moment.
    points = dict(bars)
    points.update(columns)
    times = np.array(sorted(points))
    xs = np.array([points[t] for t in times])
    xs = np.maximum.accumulate(xs)
    return Page(
        image=image,
        start=float(times[0]),
        end=float(times[-1]),
        times=times,
        xs=xs,
        staves=staves,
        left=float(left),
        right=float(right),
        top=min(top for top, _ in staves.values()),
        bottom=max(bottom for _, bottom in staves.values()),
    )


def build_pages(
    work: Work, directory: Path, width_px: int = 1920, *, mobile: bool = False
) -> list[Page]:
    """Write, compile, and read the score pages of the full work.

    If `mobile` is true, the pages are for the video for a telephone.
    """
    directory.mkdir(parents=True, exist_ok=True)
    page_mm = lilypond.MOBILE_PAGE_MM if mobile else lilypond.VIDEO_PAGE_MM
    dpi = width_px / (page_mm[0] / 25.4)
    files: list[tuple[Path, Fraction]] = []
    changed: list[Path] = []
    for index in range(lilypond.chunk_count(work)):
        first, _last = lilypond.chunk_bars(work, index)
        staves = len(lilypond.active_players(work, index))
        path = directory / f"section-{index + 1:03d}.ly"
        text = lilypond.video_file(work, index, staff_size(staves, mobile), mobile=mobile)
        # A file that did not change keeps its pages from the last build.
        same = path.exists() and path.read_text(encoding="utf-8") == text
        if not (same and _numbered(directory, path.stem, "png")):
            path.write_text(text, encoding="utf-8")
            changed.append(path)
        files.append((path, work.structure.bar(first).start))
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        list(pool.map(lambda path: _compile(path, dpi), changed))

    pages: list[Page] = []
    for path, start in files:
        vectors = _numbered(directory, path.stem, "svg")
        images = _numbered(directory, path.stem, "png")
        for svg, image in zip(vectors, images, strict=True):
            page = _parse(svg, image, start, width_px)
            if page:
                pages.append(page)
    # Each page ends where the subsequent page starts.
    for page, following in zip(pages, pages[1:], strict=False):
        page.end = max(page.end, following.start)
    pages[-1].end = max(pages[-1].end, float(work.structure.length))
    return pages
