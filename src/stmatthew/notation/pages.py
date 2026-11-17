"""Measure the pages of an engraved part, and select the better of two layouts.

A page turn of a part is only at a rest (see `turns.py`). The engraving
program then makes some pages with few staves, because a page must end at a
rest. The result is different if the music starts on a left page or on a
right page: a turn comes after each right page.

Each part has a cover as page 1. The build engraves each part two times: with
the music from page 2 (a left page), and with the music from page 3 (a right
page, after an empty page). This module counts the staves on each page of the
two results and gives each result a cost. The build keeps the result with the
lower cost.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

# A page with fewer staves than this has too much empty space (a part with one staff
# in a system, and a part with two staves in a system).
SPARSE = {1: 9, 2: 10}
# A page with more staves than this is too full. The guidelines of the orchestra
# librarians: not more than 12 staves on a page.
CROWDED = {1: 12, 2: 16}
# The cost of one page, and of one page with no music before the music.
PAGE_COST = 3.0
EMPTY_PAGE_COST = 1.0


def staves_on_pages(pdf: Path) -> list[int]:
    """Return the number of staves on each page of a PDF file of music.

    The function makes a small grey picture of each page and counts the rows
    that are dark for a large part of their width: these rows are staff
    lines. Five staff lines are one staff.
    """
    from PIL import Image  # at call time: only the build of the parts needs it

    counts: list[int] = []
    with tempfile.TemporaryDirectory() as directory:
        subprocess.run(
            ["pdftoppm", "-r", "50", "-gray", "-png", str(pdf), f"{directory}/page"], check=True
        )
        for path in sorted(Path(directory).glob("page-*.png")):
            image = Image.open(path).convert("L")
            width, height = image.size
            pixels = image.load()
            lines = 0
            inside = False
            for row in range(height):
                dark = sum(1 for column in range(0, width, 2) if pixels[column, row] < 170)
                is_line = dark > 0.3 * (width / 2)
                lines += is_line and not inside
                inside = is_line
            counts.append(round(lines / 5))
    return counts


def cost(pages: list[int], staves_in_system: int = 1, empty_pages: int = 0) -> float:
    """Return the cost of a layout: the staves on each page of music give the cost.

    A page with few staves costs the square of the number of staves that are
    missing. The last page can have few staves at no cost. A page that is too
    full costs two times the square of the number of staves that are too
    many. Each page costs a small amount: thus fewer pages are better.
    """
    sparse, crowded = SPARSE[staves_in_system], CROWDED[staves_in_system]
    total = PAGE_COST * len(pages) + EMPTY_PAGE_COST * empty_pages
    for index, count in enumerate(pages):
        if index < len(pages) - 1:
            total += max(0, sparse - count) ** 2
        total += 2.0 * max(0, count - crowded) ** 2
    return total


def better_start(left: list[int], right: list[int], staves_in_system: int = 1) -> int:
    """Return the page on which the music must start: 2 (a left page) or 3 (a right page).

    `left` and `right` are the staves on each page of music of the two layouts.
    """
    left_cost = cost(left, staves_in_system)
    right_cost = cost(right, staves_in_system, empty_pages=1)
    return 2 if left_cost <= right_cost else 3
