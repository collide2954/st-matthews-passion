"""The structure of the work that all players share: bars, metres, tempo, and marks."""

from __future__ import annotations

import bisect
import math
from dataclasses import dataclass, field
from fractions import Fraction


@dataclass
class Bar:
    """One bar. `start` and `length` are in quarter notes."""

    number: int
    start: Fraction
    numerator: int
    denominator: int
    grouping: tuple[int, ...] = ()  # beat groups of an uneven metre, for example (2, 2, 3)

    @property
    def length(self) -> Fraction:
        return Fraction(4 * self.numerator, self.denominator)

    @property
    def end(self) -> Fraction:
        return self.start + self.length


@dataclass
class TempoPoint:
    """A point of the tempo plan.

    `bpm` is the number of quarter notes in a minute at this point.
    If `glide` is true, the tempo changes in a straight line from this point to
    the subsequent point. If not, the tempo stays the same to the subsequent point.
    """

    position: Fraction
    bpm: float
    glide: bool = False
    text: str = ""  # the mark in the score; empty = no mark
    unit: str = ""  # note value of the metronome mark, for example "4" or "4."; empty = no number
    italic: bool = False
    hold: bool = False  # the point is the hold of a fermata: it is not a tempo of the music


def _segment_seconds(start_bpm: float, end_bpm: float, span: float, quarters: float) -> float:
    """Return the seconds for `quarters` quarter notes from the start of a tempo segment.

    The tempo goes in a straight line from `start_bpm` to `end_bpm` in `span` quarter notes.
    """
    if quarters <= 0.0:
        return 0.0
    if end_bpm == start_bpm or span <= 0.0:
        return 60.0 * quarters / start_bpm
    now_bpm = start_bpm + (end_bpm - start_bpm) * quarters / span
    return 60.0 * span / (end_bpm - start_bpm) * math.log(now_bpm / start_bpm)


@dataclass
class Structure:
    """Bars, tempo plan, rehearsal marks, and double bar lines."""

    bars: list[Bar] = field(default_factory=list)
    tempo_points: list[TempoPoint] = field(default_factory=list)
    marks: dict[int, str] = field(default_factory=dict)  # bar number -> rehearsal mark
    double_bars: set[int] = field(default_factory=set)  # double bar line at the END of these bars
    breaks: set[int] = field(default_factory=set)  # line break at the END of these bars
    final_bar: bool = True
    _table: tuple | None = field(default=None, repr=False, compare=False)
    _table_key: tuple = field(default=(), repr=False, compare=False)

    # ------------------------------------------------------------ bars

    def add_bars(
        self, count: int, numerator: int, denominator: int, grouping: tuple[int, ...] = ()
    ) -> int:
        """Add bars at the end. Return the number of the first new bar."""
        first = len(self.bars) + 1
        for _ in range(count):
            start = self.bars[-1].end if self.bars else Fraction(0)
            self.bars.append(Bar(len(self.bars) + 1, start, numerator, denominator, grouping))
        return first

    def bar(self, number: int) -> Bar:
        return self.bars[number - 1]

    @property
    def length(self) -> Fraction:
        return self.bars[-1].end if self.bars else Fraction(0)

    def position(self, bar: int, beat: float | Fraction = 1) -> Fraction:
        """Return the position of a beat of a bar. Beat 1 is the start of the bar.

        The unit of the beat is the denominator of the time signature.
        """
        target = self.bar(bar)
        offset = (Fraction(beat) - 1) * Fraction(4, target.denominator)
        return target.start + offset

    def bar_at(self, position: Fraction) -> Bar:
        """Return the bar that contains a position."""
        low, high = 0, len(self.bars) - 1
        while low < high:
            middle = (low + high + 1) // 2
            if self.bars[middle].start <= position:
                low = middle
            else:
                high = middle - 1
        return self.bars[low]

    # ------------------------------------------------------------ tempo

    def tempo(
        self,
        bar: int,
        beat: float | Fraction,
        bpm: float,
        text: str = "",
        *,
        unit: str = "4",
        show_number: bool = True,
    ) -> None:
        """Set a new tempo at a point. `bpm` is for the note value `unit`."""
        quarter_bpm = bpm * float(_unit_quarters(unit))
        self._add(
            TempoPoint(
                self.position(bar, beat), quarter_bpm, False, text, unit if show_number else ""
            )
        )

    def change(self, bar: int, beat: float | Fraction, text: str) -> None:
        """Start a gradual tempo change (for example "rit." or "accel.").

        The tempo goes in a straight line to the tempo of the subsequent point.
        """
        position = self.position(bar, beat)
        self._add(TempoPoint(position, self.bpm_at(position), True, text, "", True))

    def arrive(self, bar: int, beat: float | Fraction, bpm: float, *, unit: str = "4") -> None:
        """End a gradual change at a tempo with no mark in the score."""
        quarter_bpm = bpm * float(_unit_quarters(unit))
        self._add(TempoPoint(self.position(bar, beat), quarter_bpm))

    def ritardando(
        self,
        bar: int,
        beat: float | Fraction,
        slow: float,
        text: str = "poco rit.",
        resume: str = "a tempo",
    ) -> None:
        """Go slower from a beat of a bar to the end of that bar. Then the tempo comes back.

        `slow` is the tempo at the end of the bar (quarter notes in a minute).
        If `resume` is empty, the tempo does not come back: the subsequent
        tempo mark of the work gives the new tempo.
        """
        position = self.position(bar, beat)
        before = self.bpm_at(position)
        self._add(TempoPoint(position, before, True, text, "", True))
        end = self.bar(bar).end
        self._add(TempoPoint(end - Fraction(1, 8), slow))
        if resume:
            self._add(TempoPoint(end, before, False, resume, "", True))

    def fermata(self, bar: int, seconds: float) -> None:
        """Hold the end of a bar: its last quarter note gets `seconds` more time.

        The score shows a fermata as a sign on the notes. This function puts
        the time of the fermata into the tempo plan. Thus the audio and the
        video have the same time.
        """
        target = self.bar(bar)
        position = target.end - 1
        earlier = [point for point in self.tempo_points if point.position < position]
        if earlier and earlier[-1].glide:
            # A gradual change of tempo is in effect: it stops one quarter note before
            # the hold. If not, the hold becomes the end of the gradual change.
            pin = max(position - 1, (earlier[-1].position + position) / 2)
            self._add(TempoPoint(pin, self.bpm_at(pin)))
        before = self.bpm_at(position)
        self._add(TempoPoint(position, 60.0 / (seconds + 60.0 / before), hold=True))
        last = bar == len(self.bars)
        if not last and all(point.position != target.end for point in self.tempo_points):
            self._add(TempoPoint(target.end, before))

    def _add(self, point: TempoPoint) -> None:
        self.tempo_points = [p for p in self.tempo_points if p.position != point.position]
        self.tempo_points.append(point)
        self.tempo_points.sort(key=lambda p: p.position)

    def bpm_at(self, position: Fraction) -> float:
        """Return the tempo (quarter notes in a minute) at a position."""
        points = self.tempo_points
        if not points:
            return 60.0
        earlier = [p for p in points if p.position <= position]
        if not earlier:
            return points[0].bpm
        current = earlier[-1]
        later = [p for p in points if p.position > position]
        if current.glide and later:
            target = later[0]
            share = float(position - current.position) / float(target.position - current.position)
            return current.bpm + (target.bpm - current.bpm) * share
        return current.bpm

    def _time_table(self) -> tuple[list[float], list[tuple[float, float, float, float]]]:
        """Return the tempo plan as a table, for fast calculations.

        The first list has the start of each segment (quarter notes). Each
        row of the second list has: the seconds at the start of the
        segment, the tempo at its start, the tempo at its end, and its
        length (quarter notes; 0 = the segment has no end).
        """
        key = tuple((p.position, p.bpm, p.glide) for p in self.tempo_points)
        if self._table_key == key and self._table is not None:
            return self._table
        points = self.tempo_points or [TempoPoint(Fraction(0), 60.0)]
        if points[0].position > 0:
            points = [TempoPoint(Fraction(0), points[0].bpm), *points]
        starts: list[float] = []
        rows: list[tuple[float, float, float, float]] = []
        total = 0.0
        for index, point in enumerate(points):
            following = points[index + 1] if index + 1 < len(points) else None
            span = float(following.position - point.position) if following else 0.0
            end_bpm = following.bpm if (point.glide and following) else point.bpm
            starts.append(float(point.position))
            rows.append((total, point.bpm, end_bpm, span))
            total += _segment_seconds(point.bpm, end_bpm, span, span)
        self._table, self._table_key = (starts, rows), key
        return self._table

    def seconds(self, position: Fraction | float) -> float:
        """Return the time in seconds from the start of the work to a position."""
        starts, rows = self._time_table()
        quarters = float(position)
        index = max(0, bisect.bisect_right(starts, quarters) - 1)
        start_seconds, start_bpm, end_bpm, span = rows[index]
        return start_seconds + _segment_seconds(start_bpm, end_bpm, span, quarters - starts[index])

    @property
    def duration_seconds(self) -> float:
        return self.seconds(self.length)

    # ------------------------------------------------------------ marks

    def mark(self, bar: int, label: str) -> None:
        """Put a rehearsal mark at the start of a bar."""
        self.marks[bar] = label

    def double_bar(self, bar: int) -> None:
        """Put a double bar line at the end of a bar."""
        self.double_bars.add(bar)


def _unit_quarters(unit: str) -> Fraction:
    base = Fraction(4, int(unit.rstrip(".")))
    dots = unit.count(".")
    return base * (2 - Fraction(1, 2**dots))


def skip_text(quarters: Fraction) -> str:
    """Return a LilyPond spacer rest of a given length in quarter notes."""
    whole = quarters / 4
    if whole.denominator == 1:
        return f"s1*{whole.numerator}"
    return f"s1*{whole.numerator}/{whole.denominator}"


# A gradual change of tempo (for example "poco rit.") can take its own width. Thus it
# does not collide with the mark after it. "{context}" is the context of the mark.
CHANGE_WIDTH = "\\once \\override {context}MetronomeMark.extra-spacing-width = #'(-0.3 . 0.8) "


def global_to_lilypond(
    structure: Structure,
    *,
    change_context: str | None = None,
    marks: str = "all",
    turns: frozenset[int] = frozenset(),
) -> str:
    """Write the structure as a LilyPond voice of spacer rests with all marks.

    One spacer rest goes from each mark to the subsequent mark. Thus the parts
    can show many empty bars as one rest with a number.

    If `change_context` is given, each gradual change of tempo takes its own
    width (see `CHANGE_WIDTH`). The value is the context of the tempo marks
    with a dot ("Score." in a part), or an empty text for a line of marks.

    `marks` selects the rehearsal marks and the tempo marks:

    - "all": all marks (a part).
    - "none": no marks. A staff of a score uses this: the lines of marks have them.
    - "line": a line of marks of a score. A rehearsal mark and a tempo mark at
      the same bar line are one mark: the letter in its box, then the tempo.
      Thus the two marks are side by side, and the line is not high.

    `turns` are the bars before which a page turn is possible (a part).
    """
    events: dict[Fraction, list[str]] = {}
    with_tempo: dict[Fraction, str] = {}  # a rehearsal mark that goes into a tempo mark
    if marks == "line":
        texts = {point.position for point in structure.tempo_points if point.text or point.unit}
        for number, label in structure.marks.items():
            if structure.bar(number).start in texts:
                with_tempo[structure.bar(number).start] = label

    def add(position: Fraction, text: str) -> None:
        events.setdefault(position, []).append(text)

    previous: Bar | None = None
    for bar in structure.bars:
        if bar.number - 1 in structure.double_bars:
            add(bar.start, '\\bar "||"')
        if bar.number - 1 in structure.breaks:
            add(bar.start, "\\break")
        if bar.number in turns:
            add(bar.start, "\\allowPageTurn")
        changed = previous is None or (
            (bar.numerator, bar.denominator, bar.grouping)
            != (previous.numerator, previous.denominator, previous.grouping)
        )
        if changed:
            if bar.grouping:
                groups = ",".join(str(g) for g in bar.grouping)
                add(bar.start, f"\\time {groups} {bar.numerator}/{bar.denominator}")
            else:
                add(bar.start, f"\\time {bar.numerator}/{bar.denominator}")
        if bar.number in structure.marks and bar.start not in with_tempo and marks != "none":
            add(bar.start, f'\\mark \\markup \\rehearsal "{structure.marks[bar.number]}"')
        previous = bar
    for point in structure.tempo_points:
        if (point.text or point.unit) and marks != "none":
            width = ""
            if change_context is not None and point.italic and not point.unit:
                width = CHANGE_WIDTH.format(context=change_context)
            add(point.position, width + _tempo_text(point, with_tempo.pop(point.position, "")))
    add(structure.length, '\\bar "|."' if structure.final_bar else "")

    lines: list[str] = []
    positions = sorted(events)
    for index, position in enumerate(positions):
        commands = " ".join(text for text in events[position] if text)
        if index + 1 < len(positions):
            bar = structure.bar_at(position)
            skip = skip_text(positions[index + 1] - position)
            lines.append(f"{commands} {skip} % bar {bar.number}".strip())
        elif commands:
            lines.append(commands)
    return "\n".join(lines)


def _tempo_text(point: TempoPoint, mark: str = "") -> str:
    """Return the LilyPond text of a tempo mark. `mark` is a rehearsal mark at the same place."""
    words = f'\\tempochange "{point.text}"' if point.italic else f'"{point.text}"'
    if mark:
        box = f'\\rehearsal "{mark}"'
        words = f"\\markup {{ {box} \\hspace #1.2 {words} }}" if point.text else f"\\markup {box}"
    elif point.italic:
        words = f"\\markup {words}"
    if point.unit:
        quarters = _unit_quarters(point.unit)
        number = round(point.bpm / float(quarters))
        if point.text or mark:
            return f"\\tempo {words} {point.unit} = {number}"
        return f"\\tempo {point.unit} = {number}"
    return f"\\tempo {words}"
