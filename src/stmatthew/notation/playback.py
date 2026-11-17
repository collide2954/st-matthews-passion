"""Select the dynamic mark and the articulation that the playback program gets for each note.

Muse Sounds do not play all marks at balanced levels. The command
`stmatthew calibrate` measured each instrument: the level of each dynamic
mark for a long note, a staccato note, a note with an accent, a note with a
marcato mark, and a pizzicato note (the table `audio/muse_levels.csv`). The
measurement showed these faults:

- The steps between the marks are not regular. Many instruments have a step
  of 9 to 17 dB between two adjacent marks (bass clarinet: mf to f), and
  almost no step between other marks (oboe: mp to fff).
- Some marks are softer than the mark below them (clarinet: mp is 10 dB
  softer than p).
- A staccato note at a soft dynamic mark is almost silent on some
  instruments (flute, trumpet, trombones, tuba, bass clarinet).
- A marcato mark on a brass instrument makes a note much louder and much
  harder than its dynamic mark (trumpet: 12 dB at mp). The owner of the
  project heard this as a "splat" of the brass.

This module gives the mark and the articulation for the audio file, with
these rules:

1. Of the eight marks of an instrument, the module uses the largest set
   whose measured levels go up from mark to mark.
2. The level of the mark f of the instrument is the anchor. Each written
   mark has a target level in relation to the anchor (the table `LADDER_DB`):
   about 5 to 6 dB for each mark below f, and less above f.
3. A note gets the mark whose measured level is nearest to the target. If
   two marks are almost equally near, the written mark is selected, or the
   louder mark.
4. A brass instrument plays no mark louder than ff.
5. A note with an articulation has a target in relation to the level that
   a note with no articulation gets: staccato and pizzicato 3 dB below,
   accent 3 dB above, marcato 5 dB above. For an accent and a marcato mark,
   the softest mark that is near the target is selected: its sound is less
   hard.
6. If no mark agrees, the note gets a different articulation, or none.

The printed score and the parts do not change.
"""

from __future__ import annotations

import csv
from functools import cache
from itertools import combinations
from pathlib import Path

TABLE = Path(__file__).resolve().parents[1] / "audio" / "muse_levels.csv"

MARKS = ["ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"]
SOFTER = ["ppppp", "pppp"]  # softer than the measured marks
LOUDER = ["ffff", "fffff"]  # louder than the measured marks
WAYS = ("long", "staccato", "accent", "marcato", "pizzicato")

# The target level of each written mark, in dB from the level of the mark f.
LADDER_DB = {
    "ppp": -30.0, "pp": -24.5, "p": -19.0, "mp": -13.0, "mf": -6.5, "f": 0.0, "ff": 3.0,
    "fff": 5.0,
}  # fmt: skip
OFFSET_DB = {"staccato": -3.0, "pizzicato": -3.0, "accent": 3.0, "marcato": 5.0}
SUBSTITUTES = {"marcato": ("accent", "long"), "accent": ("long",), "staccato": ("long",)}
TOLERANCE_DB = 4.0  # the largest distance from the target level for the written articulation
NEAR_DB = 1.5  # accent and marcato: of the marks this near to the best, the softest is selected
TIE_DB = 1.0  # a note with no articulation: of two marks this near, the louder is selected
HARD_WAYS = ("accent", "marcato")
LOUDEST_BRASS = "ff"
ANCHOR = MARKS.index("f")

Levels = dict[str, list[float]]  # way to play -> the level in dB of each mark in MARKS


@cache
def load(path: Path = TABLE) -> dict[str, Levels]:
    """Read the table of the measured levels: part name -> way to play -> levels.

    If the table is not there, the result is empty: the audio file then has
    the marks of the score.
    """
    if not path.exists():
        return {}
    table: dict[str, Levels] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            table.setdefault(row["part"], {})[row["way"]] = [float(row[mark]) for mark in MARKS]
    return table


def usable(levels: list[float]) -> list[int]:
    """Return the numbers of the marks whose levels go up from mark to mark (rule 1).

    The result is the largest such set. Of two sets of the same size, the
    set that has the mark f is selected.
    """
    for size in range(len(levels), 0, -1):
        found = [
            list(chosen)
            for chosen in combinations(range(len(levels)), size)
            if all(levels[a] < levels[b] for a, b in zip(chosen, chosen[1:], strict=False))
        ]
        if found:
            return min(found, key=lambda chosen: (ANCHOR not in chosen, chosen))
    return []


def _anchor(levels: list[float], kept: list[int]) -> float:
    """Return the level of the mark f, or a level between its adjacent marks in the set."""
    if ANCHOR in kept:
        return levels[ANCHOR]
    below = [index for index in kept if index < ANCHOR]
    above = [index for index in kept if index > ANCHOR]
    near = [levels[side[position]] for side, position in ((below, -1), (above, 0)) if side]
    return sum(near) / len(near)


def base_mark(levels: Levels, written: str, brass: bool = False) -> str:
    """Return the mark that a note with no articulation gets (rules 1 to 4)."""
    extra = 0
    if written in SOFTER:
        extra = len(SOFTER) - SOFTER.index(written)  # the number of marks below ppp
        written = MARKS[0]
    elif written in LOUDER:
        written = MARKS[-1]
    if written not in MARKS:
        return written
    long = levels["long"]
    kept = usable(long)
    if brass:
        written = MARKS[min(MARKS.index(written), MARKS.index(LOUDEST_BRASS))]
        kept = [index for index in kept if index <= MARKS.index(LOUDEST_BRASS)] or kept
    target = _anchor(long, usable(long)) + LADDER_DB[written]
    smallest = min(abs(long[number] - target) for number in kept)
    near = [number for number in kept if abs(long[number] - target) <= smallest + TIE_DB]
    index = MARKS.index(written) if MARKS.index(written) in near else max(near)
    # A written mark below ppp stays softer than ppp by the same number of marks.
    index -= extra
    return MARKS[index] if index >= 0 else SOFTER[len(SOFTER) + index]


def played(
    levels: Levels | None, written: str, way: str = "long", brass: bool = False
) -> tuple[str, str]:
    """Return the dynamic mark and the way to play that the audio file gets for a note.

    `levels` are the measured levels of the instrument (None = not
    measured). `written` is the dynamic mark in effect in the score. `way`
    is the articulation of the note: "long" (none), "staccato", "accent",
    "marcato", or "pizzicato".
    """
    if not levels or "long" not in levels:
        return written, way
    base = base_mark(levels, written, brass)
    if way == "long" or way not in levels or base not in MARKS:
        return base, way
    # The target is in relation to the level that the note gets with no articulation.
    reached = levels["long"][MARKS.index(base)]
    target = reached + OFFSET_DB[way]
    count = MARKS.index(LOUDEST_BRASS) + 1 if brass else len(MARKS)

    def best(other: str) -> tuple[float, str]:
        errors = [abs(level - target) for level in levels[other][:count]]
        smallest = min(errors)
        if other in HARD_WAYS:
            index = next(i for i, error in enumerate(errors) if error <= smallest + NEAR_DB)
        else:
            index = max(i for i, error in enumerate(errors) if error == smallest)
        return errors[index], MARKS[index]

    error, mark = best(way)
    if error <= TOLERANCE_DB:
        return mark, way
    choices = [(error, mark, way)]
    for other in SUBSTITUTES.get(way, ()):
        if other == "long":
            choices.append((abs(OFFSET_DB[way]), base, "long"))
        elif other in levels:
            choices.append((*best(other), other))
    _, mark, other = min(choices, key=lambda choice: choice[0])
    return mark, other
