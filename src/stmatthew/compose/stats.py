"""Measure the work, to compare it with the targets of the form plan.

The measurement of the loudness is the same as in the style study: for each
moment, the code finds the dynamic level in effect. In an orchestra, this
is the loudest level of the players that sound at that moment.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..notation.work import Work
from ..perform.events import DYNAMIC_LEVEL, perform

STEP = 0.5  # the grid of the measurement, in quarter notes


@dataclass
class Stats:
    """Numbers that describe the work."""

    bars: int
    minutes: float
    notes: int
    tempo_marks: int
    slowest_quarter: float
    fastest_quarter: float
    share_silent: float
    share_p_or_softer: float
    share_mp_or_mf: float
    share_f_or_louder: float
    share_fff: float

    @property
    def bars_for_each_tempo_mark(self) -> float:
        return self.bars / max(self.tempo_marks, 1)

    def rows(self) -> list[tuple[str, str]]:
        """Return the numbers as rows of a table."""
        return [
            ("Bars", f"{self.bars}"),
            ("Length in minutes", f"{self.minutes:.1f}"),
            ("Notes", f"{self.notes}"),
            ("Tempo marks", f"{self.tempo_marks}"),
            ("Bars for each tempo mark", f"{self.bars_for_each_tempo_mark:.1f}"),
            ("Slowest tempo (quarter notes in a minute)", f"{self.slowest_quarter:.0f}"),
            ("Fastest tempo (quarter notes in a minute)", f"{self.fastest_quarter:.0f}"),
            ("Share of the time: p or softer", f"{self.share_p_or_softer:.2f}"),
            ("Share of the time: mp or mf", f"{self.share_mp_or_mf:.2f}"),
            ("Share of the time: f or louder", f"{self.share_f_or_louder:.2f}"),
            ("Share of the time: fff", f"{self.share_fff:.3f}"),
            ("Share of the time: silence", f"{self.share_silent:.3f}"),
        ]


def measure(work: Work) -> Stats:
    """Measure the work."""
    structure = work.structure
    length = float(structure.length)
    count = int(np.ceil(length / STEP))
    level = np.zeros(count)
    notes = 0
    for player in work.orchestra.players:
        for note in perform(work, player.id):
            if note.grace:
                continue
            notes += 1
            first = int(float(note.start) / STEP)
            last = max(first + 1, int(np.ceil(float(note.start + note.duration) / STEP)))
            loudness = note.level  # the dynamic mark in effect at the start of the note
            level[first:last] = np.maximum(level[first:last], loudness)
    edges = np.array([structure.seconds(min(i * STEP, length)) for i in range(count + 1)])
    seconds = np.diff(edges)
    total = float(seconds.sum())

    def share(mask: np.ndarray) -> float:
        return float(seconds[mask].sum() / total)

    soft_limit = 0.5 * (DYNAMIC_LEVEL["p"] + DYNAMIC_LEVEL["mp"])
    loud_limit = 0.5 * (DYNAMIC_LEVEL["mf"] + DYNAMIC_LEVEL["f"])
    loudest_limit = 0.5 * (DYNAMIC_LEVEL["ff"] + DYNAMIC_LEVEL["fff"])
    sounding = level > 0
    tempos = [point.bpm for point in structure.tempo_points if not point.hold]
    return Stats(
        bars=len(structure.bars),
        minutes=total / 60.0,
        notes=notes,
        tempo_marks=sum(1 for point in structure.tempo_points if point.text),
        slowest_quarter=min(tempos),
        fastest_quarter=max(tempos),
        share_silent=share(~sounding),
        share_p_or_softer=share(sounding & (level <= soft_limit)),
        share_mp_or_mf=share((level > soft_limit) & (level <= loud_limit)),
        share_f_or_louder=share(level > loud_limit),
        share_fff=share(level > loudest_limit),
    )


PASSAGE_GRID = 0.1  # the grid of the loudness plan, in seconds
PASSAGE_SECONDS = 6.0  # a passage is not shorter than this


def loudness_plan(work: Work) -> np.ndarray:
    """Return the dynamic mark in effect for each 0.1 s of the work.

    The value is the number of the mark in `DYNAMIC_LEVEL` (0 = the softest
    mark). It is the loudest mark of the notes that sound at that moment.
    A moment with no notes has the value of the moment before it.
    """
    structure = work.structure
    count = int(np.ceil(structure.duration_seconds / PASSAGE_GRID)) + 1
    level = np.zeros(count)
    for player in work.orchestra.players:
        for note in perform(work, player.id):
            if note.grace:
                continue
            first = int(structure.seconds(note.start) / PASSAGE_GRID)
            end = structure.seconds(note.start + note.duration)
            last = max(first + 1, int(np.ceil(end / PASSAGE_GRID)))
            level[first:last] = np.maximum(level[first:last], note.level)
    marks = np.array(sorted(DYNAMIC_LEVEL.values()))
    limits = 0.5 * (marks[:-1] + marks[1:])
    plan = np.searchsorted(limits, level)
    # Fill the moments with no notes.
    sounding = np.flatnonzero(level > 0)
    if len(sounding) == 0:
        return np.zeros(count, dtype=int)
    places = np.clip(np.searchsorted(sounding, np.arange(count), side="right") - 1, 0, None)
    return plan[sounding[places]]


def passages(work: Work, smallest: float = PASSAGE_SECONDS) -> list[float]:
    """Return the start times of the passages of the work, in seconds.

    A passage is a part of the music that has one dynamic mark in effect
    for `smallest` seconds or more. A short change of the mark (for example
    one loud call in a soft passage) does not start a new passage.

    The master uses the passages for its gain riding: each passage gets one
    level change.
    """
    plan = loudness_plan(work)
    width = int(smallest / PASSAGE_GRID) | 1
    # The mark of each moment: the mark that is in effect for the most time around it.
    padded = np.pad(plan, width // 2, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, width)
    classes = int(plan.max()) + 1
    counts = np.stack([(windows == value).sum(axis=1) for value in range(classes)])
    smooth = counts.argmax(axis=0)
    changes = np.flatnonzero(np.diff(smooth)) + 1
    edges = [0, *changes.tolist(), len(smooth)]
    # Each run is [first moment, moment after the last, mark].
    runs = [
        [first, after, int(smooth[first])] for first, after in zip(edges, edges[1:], strict=False)
    ]
    # A run that is too short becomes a part of the adjacent run that has the nearer
    # mark. Then two adjacent runs with the same mark are one run.
    shortest = smallest / PASSAGE_GRID
    while len(runs) > 1:
        lengths = [after - first for first, after, _mark in runs]
        index = int(np.argmin(lengths))
        if lengths[index] >= shortest:
            break
        mark = runs[index][2]
        before = abs(runs[index - 1][2] - mark) if index > 0 else None
        after = abs(runs[index + 1][2] - mark) if index + 1 < len(runs) else None
        if after is None or (before is not None and before <= after):
            runs[index - 1][1] = runs[index][1]
        else:
            runs[index + 1][0] = runs[index][0]
        del runs[index]
        merged = [runs[0]]
        for run in runs[1:]:
            if run[2] == merged[-1][2]:
                merged[-1][1] = run[1]
            else:
                merged.append(run)
        runs = merged
    # Put each change between two passages at the moment where the louder music
    # starts or stops. Thus loud notes are not in the softer passage.
    half = width // 2
    for index in range(1, len(runs)):
        left, right = runs[index - 1], runs[index]
        low = max(left[0] + 1, right[0] - half)
        high = min(right[1] - 1, right[0] + half)
        louder = np.flatnonzero(plan[low:high] > min(left[2], right[2]))
        if len(louder):
            place = low + int(louder[0]) if right[2] > left[2] else low + int(louder[-1]) + 1
            left[1] = right[0] = place
    kept = [first for first, _after, _mark in runs]
    return [value * PASSAGE_GRID for value in kept]
