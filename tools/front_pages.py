"""Engrave only the pages before the music of the score: a fast check of their layout.

Use: uv run python tools/front_pages.py OUTPUT_DIRECTORY
"""

import subprocess
import sys
from pathlib import Path

from stmatthew.notation import lilypond
from stmatthew.work import build

output = Path(sys.argv[1])
output.mkdir(parents=True, exist_ok=True)
work = build()
text = "\n\n".join(
    [
        f'\\version "{lilypond.LILYPOND_VERSION}"',
        lilypond.style(lilypond.SCORE_REHEARSAL_POINTS),
        f"#(set-global-staff-size {lilypond.SCORE_PAGE.staff_size:g})",
        lilypond.SCORE_PAPER.strip(),
        lilypond.front_part(work, lilypond.SCORE_PAGE, "Full score in C"),
    ]
)
source = output / "front.ly"
source.write_text(text + "\n", encoding="utf-8")
result = subprocess.run(
    ["lilypond", "-dno-point-and-click", "--loglevel=WARNING", "-o", str(output / "front"),
     str(source)],
    capture_output=True, text=True, check=False,
)  # fmt: skip
print(result.returncode, result.stderr[-3000:])
