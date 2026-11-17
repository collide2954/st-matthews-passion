"""Print the level of each stem of an excerpt render, in windows of some seconds.

Use: uv run python tools/stem_levels.py FIRST LAST [SECONDS]

The levels are in dB, in the level domain of the mix. The piano stem has the
gain of its role (the soloist of the interlude is louder). The command needs
the stems of `stmatthew audio --engine musescore --bars FIRST-LAST`.
"""

import sys
from pathlib import Path

import numpy as np

from stmatthew.audio import dsp, musescore
from stmatthew.work import build

first, last = int(sys.argv[1]), int(sys.argv[2])
window = int(sys.argv[3]) if len(sys.argv) > 3 else 6
work = build()
structure = work.structure
begin = structure.seconds(structure.bar(first).start)
marks = {
    label: round(structure.seconds(structure.bar(bar).start) - begin, 1)
    for bar, label in structure.marks.items()
}
print("marks (seconds):", {label: value for label, value in marks.items() if 0 <= value <= 3600})
rows = {}
for stem in [*musescore.STEMS, musescore.PIANO_STEM]:
    path = Path(f"build/musescore/{stem}-{first}-{last}/score.wav")
    if not path.exists():
        continue
    audio = musescore._load(path)
    if stem == musescore.PIANO_STEM:
        role = musescore.piano_role(work, begin, len(audio))
        audio *= (10.0 ** (musescore.PIANO_MUSE_SOLO_DB * role / 20.0))[:, None]
    rows[stem] = audio.mean(axis=1)
step = window * dsp.RATE
length = max(len(values) for values in rows.values())
print("second " + " ".join(f"{name[:7]:>8s}" for name in rows))
for start in range(0, length - step, step):
    levels = []
    for values in rows.values():
        part = values[start : start + step]
        level = 20 * np.log10(np.sqrt(np.mean(part**2)) + 1e-9) if len(part) else -180.0
        levels.append(f"{level:8.1f}")
    print(f"{start // dsp.RATE:5d}  " + " ".join(levels))
