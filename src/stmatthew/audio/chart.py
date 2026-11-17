"""Draw the loudness of the master against the time, as an SVG picture.

The picture shows the form of the work: the five parts, the two climaxes,
and the still centre. The documents of the project show this picture.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..notation.work import Work
from . import loudness, reference

WIDTH, HEIGHT = 960, 300
LEFT, RIGHT, TOP, BOTTOM = 52, 16, 34, 40
LOWEST, HIGHEST = -50.0, -8.0  # range of the loudness axis in LUFS
LINE = "#3b6fb6"
GRID = "#8a8f98"


def loudness_chart(work: Work, audio_file: Path, output: Path) -> Path:
    """Write the picture of the short-term loudness of the master."""
    audio = reference.load_stereo(audio_file)
    values = loudness.short_term(loudness.block_power(audio), step_blocks=20)
    seconds = 1.5 + 2.0 * np.arange(len(values))
    total = len(audio) / 48000.0
    plot_width, plot_height = WIDTH - LEFT - RIGHT, HEIGHT - TOP - BOTTOM

    def x_of(time: float) -> float:
        return LEFT + plot_width * time / total

    def y_of(level: float) -> float:
        share = (min(max(level, LOWEST), HIGHEST) - LOWEST) / (HIGHEST - LOWEST)
        return TOP + plot_height * (1.0 - share)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'font-family="sans-serif" font-size="12">',
        "<title>Loudness of the master against the time</title>",
    ]
    # The loudness axis.
    for level in range(-50, -5, 10):
        y = y_of(level)
        parts.append(
            f'<line x1="{LEFT}" y1="{y:.1f}" x2="{WIDTH - RIGHT}" y2="{y:.1f}" '
            f'stroke="{GRID}" stroke-width="0.5" stroke-dasharray="2 4"/>'
        )
        parts.append(
            f'<text x="{LEFT - 6}" y="{y + 4:.1f}" text-anchor="end" fill="{GRID}">{level}</text>'
        )
    parts.append(
        f'<text x="14" y="{TOP + plot_height / 2:.1f}" fill="{GRID}" text-anchor="middle" '
        f'transform="rotate(-90 14 {TOP + plot_height / 2:.1f})">LUFS</text>'
    )
    # The time axis: one label each 5 minutes.
    for minute in range(0, int(total // 60) + 1, 5):
        x = x_of(60.0 * minute)
        parts.append(
            f'<text x="{x:.1f}" y="{HEIGHT - BOTTOM + 16}" text-anchor="middle" '
            f'fill="{GRID}">{minute}:00</text>'
        )
    # The five parts: a line and a number at the start of each part.
    structure = work.structure
    starts = [bar for bar in _part_starts(work)]
    for number, bar in enumerate(starts, start=1):
        x = x_of(structure.seconds(structure.bar(bar).start))
        parts.append(
            f'<line x1="{x:.1f}" y1="{TOP - 6}" x2="{x:.1f}" y2="{HEIGHT - BOTTOM}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        parts.append(f'<text x="{x + 5:.1f}" y="{TOP - 12}" fill="{GRID}">Part {number}</text>')
    points = " ".join(f"{x_of(t):.1f},{y_of(v):.1f}" for t, v in zip(seconds, values, strict=True))
    parts.append(
        f'<polyline points="{points}" fill="none" stroke="{LINE}" stroke-width="1.6" '
        f'stroke-linejoin="round"/>'
    )
    parts.append("</svg>")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return output


def _part_starts(work: Work) -> list[int]:
    """Return the first bar of each of the five parts."""
    marks = {label: bar for bar, label in work.structure.marks.items()}
    return [1, marks["D"], marks["S"], marks["AA"], marks["GG"]]
