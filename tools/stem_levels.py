"""Print the level of each group of the mix, in windows of some seconds.

Use: uv run python tools/stem_levels.py [FIRST LAST [SECONDS]]

FIRST and LAST are bar numbers (default: the full work). The levels are in
dB, in the level domain of the mix. The groups are the stems of MuseScore
and the group of the sampler (the organ, and a voice of the sampler). The
command renders the groups that are not in the directory `build/musescore`.
"""

import sys
from pathlib import Path

import numpy as np

from stmatthew.audio import dsp, musescore
from stmatthew.work import build

bars = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else None
window = int(sys.argv[3]) if len(sys.argv) > 3 else 6
work = build()
structure = work.structure
begin = structure.seconds(structure.bar(bars[0]).start) if bars else 0.0
marks = {
    label: round(structure.seconds(structure.bar(bar).start) - begin, 1)
    for bar, label in structure.marks.items()
}
print("marks (seconds):", {label: value for label, value in marks.items() if 0 <= value <= 3600})
parts = musescore.render_parts(work, Path("build/musescore"), bars)
rows = {name: audio.mean(axis=1) for name, audio in parts.items()}


def level(values: np.ndarray) -> float:
    return 20 * np.log10(np.sqrt(np.mean(values**2)) + 1e-9) if len(values) else -180.0


step = window * dsp.RATE
length = max(len(values) for values in rows.values())
print("second " + " ".join(f"{name[:9]:>9s}" for name in rows))
for start in range(0, length - step, step):
    levels = [f"{level(values[start : start + step]):9.1f}" for values in rows.values()]
    print(f"{start // dsp.RATE:5d}  " + " ".join(levels))
print("  all  " + " ".join(f"{level(values):9.1f}" for values in rows.values()))
