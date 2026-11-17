"""Engrave the conductor score of the first bars of the work: a fast check of the layout.

Use: uv run python tools/short_score.py BARS OUTPUT_DIRECTORY [transposed]

The tool keeps the sections that start before the bar number BARS. It prints
the time that LilyPond needs.
"""

import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

from stmatthew.notation import lilypond
from stmatthew.work import build

limit = int(sys.argv[1])
output = Path(sys.argv[2])
output.mkdir(parents=True, exist_ok=True)
work = build()
last = 0
for player, chunks in work.chunks.items():
    kept = [(first, chunk) for first, chunk in chunks if first < limit]
    work.chunks[player] = kept
structure = work.structure
ends = [bar.number for bar in structure.bars]
first_dropped = min(
    (first for chunks in [build().chunks["vn1"]] for first, _ in chunks if first >= limit),
    default=len(ends) + 1,
)
bars = [bar for bar in structure.bars if bar.number < first_dropped]
end = bars[-1].end
work.structure = replace(
    structure,
    bars=bars,
    tempo_points=[point for point in structure.tempo_points if point.position < end],
    marks={bar: label for bar, label in structure.marks.items() if bar < first_dropped},
    double_bars={bar for bar in structure.double_bars if bar < first_dropped},
    breaks=set(),
)
print(f"{len(bars)} bars")
text = lilypond.score_file(work, transposed="transposed" in sys.argv)
source = output / "short.ly"
source.write_text(text, encoding="utf-8")
start = time.time()
result = subprocess.run(
    ["lilypond", "-dno-point-and-click", "--loglevel=WARNING", "-o", str(output / "short"),
     str(source)],
    capture_output=True, text=True, check=False,
)  # fmt: skip
print(f"LilyPond: {time.time() - start:.0f} s, exit {result.returncode}")
print(result.stderr[-2500:])
