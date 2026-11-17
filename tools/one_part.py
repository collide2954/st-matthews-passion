"""Engrave one part: a fast check of its layout.

Use: uv run python tools/one_part.py PART OUTPUT_DIRECTORY [MUSIC_PAGE]

PART is for example vn1 or pno. MUSIC_PAGE is the page on which the music
starts: 2 (the usual value: a cover, then the music), 3, or 1 (no cover).
"""

import subprocess
import sys
import time
from pathlib import Path

from stmatthew.notation import lilypond
from stmatthew.work import build

part, output = sys.argv[1], Path(sys.argv[2])
output.mkdir(parents=True, exist_ok=True)
source = output / f"part-{part}.ly"
music_page = int(sys.argv[3]) if len(sys.argv) > 3 else 2
source.write_text(lilypond.part_file(build(), part, music_page=music_page), encoding="utf-8")
start = time.time()
result = subprocess.run(
    ["lilypond", "-dno-point-and-click", "--loglevel=WARNING", "-o",
     str(output / f"part-{part}"), str(source)],
    capture_output=True, text=True, check=False,
)  # fmt: skip
print(f"LilyPond: {time.time() - start:.0f} s, exit {result.returncode}")
print(result.stderr[-2500:])
