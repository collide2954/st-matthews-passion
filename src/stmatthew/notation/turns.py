"""Page turns in the parts.

A player needs time to turn a page. The guidelines of the orchestra
librarians ask for a page turn at a rest. This module finds the bar lines at
which a page turn is possible: the engraving program puts a page turn only at
these bar lines.

The rule uses the time in seconds, not the number of bars: one bar of a slow
tempo is sufficient, and three bars of a fast tempo are not.

A player with two staves (piano, harp, celesta) can turn a page with one hand
while the other hand plays.

Two string players read one part: one of them turns the page, and the other
continues to play. Thus a string part can also have a page turn at a short
rest, and at a bar line through which the section holds a note.
"""

from __future__ import annotations

import bisect
from fractions import Fraction
from typing import TYPE_CHECKING

from . import combine

if TYPE_CHECKING:
    from .work import Work

# The smallest rest for a page turn, in seconds.
TURN_SECONDS = 4.0
# One hand of a keyboard player must be free for this time before or after the bar line.
HAND_SECONDS = 2.0
# The smallest rest for a page turn in a string part, in seconds.
STRING_TURN_SECONDS = 2.0
# A string section holds a note through a bar line: the note before the bar line or the
# note after it must have this length in seconds, for a page turn at that bar line.
HELD_SECONDS = 2.0


def _gaps(spans: list[tuple[Fraction, Fraction]], end: Fraction) -> list[tuple[Fraction, Fraction]]:
    """Return the silences between the notes, from the start of the work to its end."""
    gaps: list[tuple[Fraction, Fraction]] = []
    free = Fraction(0)
    for start, stop in sorted(spans):
        if start > free:
            gaps.append((free, start))
        free = max(free, stop)
    if end > free:
        gaps.append((free, end))
    return gaps


def split_bars(work: Work) -> set[int]:
    """Return the bars at which a long rest of a part stops and starts again.

    These are the bars with a rehearsal mark, a tempo mark, a new metre, or a
    double bar line before them.
    """
    structure = work.structure
    bars = set(structure.marks) | {bar + 1 for bar in structure.double_bars}
    previous = None
    for bar in structure.bars:
        metre = (bar.numerator, bar.denominator, bar.grouping)
        if previous is not None and metre != previous:
            bars.add(bar.number)
        previous = metre
    for point in structure.tempo_points:
        if point.text or point.unit:
            bar = structure.bar_at(min(point.position, structure.length - Fraction(1, 64)))
            bars.add(bar.number)
            if point.position > bar.start:
                bars.add(bar.number + 1)
    return bars


def turn_bars(work: Work, part_id: str, cue_starts: frozenset[Fraction] = frozenset()) -> set[int]:
    """Return the bars before which a page turn is possible in a part.

    `cue_starts` are the positions at which a cue of the part starts: a long
    rest stops there, thus a page turn can be there.
    """
    structure = work.structure
    seconds = structure.seconds
    staves: list[list[tuple[Fraction, Fraction]]] = []
    held: set[Fraction] = set()  # the bar lines through which a string section holds a note
    smallest = TURN_SECONDS
    for player in work.orchestra.players:
        if player.id.split(".")[0] == part_id:
            elements = work.music_of(player.id).children
            notes, _end = combine.sounding(elements, Fraction(0))
            staves.append([(start, stop) for start, stop, _pitch in notes])
            if player.family == "strings":
                smallest = STRING_TURN_SECONDS
                held.update(_held_lines(work, elements, notes))
    lines = [bar.start for bar in structure.bars]
    numbers = {bar.start: bar.number for bar in structure.bars}
    splits = split_bars(work) | {numbers[start] for start in cue_starts if start in numbers}

    def bars_in(free: Fraction, start: Fraction) -> list[int]:
        """Return the bars whose bar line is in the silence."""
        low, high = bisect.bisect_left(lines, free), bisect.bisect_right(lines, start)
        return list(range(low + 1, high + 1))

    turns: set[int] = set()
    silent: set[int] = set()  # the bars whose bar line is in a rest of all staves
    for free, start in _gaps([span for staff in staves for span in staff], structure.length):
        inside = bars_in(free, start)
        silent.update(number for number in inside if free < lines[number - 1] < start)
        # No page turn is necessary after the last note of the part.
        if inside and start < structure.length and seconds(start) - seconds(free) >= smallest:
            # A rest of many bars shows as one rest: a page turn is possible only where
            # that rest starts, where it stops, and where it is divided.
            turns.update({inside[0], inside[-1]})
            turns.update(number for number in inside if number in splits)
    if len(staves) > 1:
        for staff in staves:
            for free, start in _gaps(staff, structure.length):
                if seconds(start) - seconds(free) < TURN_SECONDS:
                    continue
                for number in bars_in(free, min(start, lines[-1])):
                    before = seconds(lines[number - 1]) - seconds(free)
                    after = seconds(start) - seconds(lines[number - 1])
                    if max(before, after) >= HAND_SECONDS and number not in silent:
                        turns.add(number)
    turns.update(numbers[line] for line in held)
    return turns - {1}


def _held_lines(
    work: Work, elements: list, notes: list[tuple[Fraction, Fraction, float]]
) -> set[Fraction]:
    """Return the bar lines through which a tie goes, where one of the two notes is long."""
    seconds = work.structure.seconds
    lines = {bar.start for bar in work.structure.bars}
    ends = {stop: start for start, stop, _pitch in notes}
    starts = {start: stop for start, stop, _pitch in notes}
    found: set[Fraction] = set()
    for point in combine.tie_points(elements, Fraction(0))[0]:
        if point not in lines or point not in ends or point not in starts:
            continue
        before = seconds(point) - seconds(ends[point])
        after = seconds(starts[point]) - seconds(point)
        if max(before, after) >= HELD_SECONDS:
            found.add(point)
    return found
