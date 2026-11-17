"""Read the music as a listener hears it: the notes that sound together at each moment.

The assistant that writes this work cannot hear it. This module gives some
of the facts that an ear gives:

- the chord at each beat, with its bass note and the intervals above the bass;
- the notes that clash (a semitone, a major seventh, or a minor ninth apart);
- the pairs of voices that move in parallel fifths or octaves;
- the phrases of the voice: their length in seconds (the breath), their
  range, and the share of steps and of leaps.

The command `stmatthew ears --bars FIRST-LAST` prints the report.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from fractions import Fraction

from ..notation import music
from ..notation.work import Work
from ..perform.events import PerfNote, perform

NOTE_NAMES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B")

# Chords from a root: the semitones above the root, and the symbol after the root name.
CHORDS: tuple[tuple[tuple[int, ...], str], ...] = (
    ((0, 4, 7), ""),
    ((0, 3, 7), "m"),
    ((0, 3, 6), "dim"),
    ((0, 4, 8), "aug"),
    ((0, 4, 7, 10), "7"),
    ((0, 3, 7, 10), "m7"),
    ((0, 4, 7, 11), "maj7"),
    ((0, 3, 6, 10), "m7b5"),
    ((0, 3, 6, 9), "dim7"),
    ((0, 3, 7, 11), "m(maj7)"),
    ((0, 4, 10), "7(no 5)"),
    ((0, 3, 10), "m7(no 5)"),
    ((0, 4, 11), "maj7(no 5)"),
    ((0, 7, 10), "7(no 3)"),
    ((0, 5, 7), "sus4"),
    ((0, 2, 7), "sus2"),
    ((0, 4, 7, 9), "6"),
    ((0, 3, 7, 9), "m6"),
    ((0, 4, 7, 10, 13), "7b9"),
    ((0, 4, 7, 10, 14), "9"),
    ((0, 4), "(3)"),
    ((0, 3), "m(3)"),
    ((0, 7), "(5)"),
)


def note_name(midi: float) -> str:
    """Return the name of a note with its octave number (C4 is the middle C)."""
    number = round(midi)
    return f"{NOTE_NAMES[number % 12]}{number // 12 - 1}"


def chord_symbol(pitches: Iterable[float]) -> str:
    """Return a chord symbol for the notes, or the names of the pitch classes.

    The symbol has the root, the type, and the bass note if the bass is not
    the root, for example "Am/C". A set of notes that is not a chord of the
    table gets its pitch classes in braces.
    """
    ordered = sorted(round(pitch) for pitch in pitches)
    if not ordered:
        return "-"
    classes = sorted({pitch % 12 for pitch in ordered})
    bass = ordered[0] % 12
    if len(classes) == 1:
        return NOTE_NAMES[bass]
    found = []
    for root in classes:
        shape = tuple(sorted((pc - root) % 12 for pc in classes))
        for number, (intervals, symbol) in enumerate(CHORDS):
            if tuple(sorted(interval % 12 for interval in intervals)) == shape:
                # Of two names (C6 and Am7), the name with the bass as its root is first.
                found.append((root != bass, number, root, symbol))
    if not found:
        return "{" + " ".join(NOTE_NAMES[pc] for pc in classes) + "}"
    _, _, root, symbol = min(found)
    name = NOTE_NAMES[root] + symbol
    return name if root == bass else f"{name}/{NOTE_NAMES[bass]}"


@dataclass(frozen=True)
class Moment:
    """The notes that sound at one moment."""

    bar: int
    beat: Fraction  # 1 = the start of the bar, in quarter notes
    notes: tuple[tuple[int, str], ...]  # MIDI number and player, from the lowest note

    @property
    def pitches(self) -> tuple[int, ...]:
        return tuple(pitch for pitch, _player in self.notes)

    @property
    def classes(self) -> frozenset[int]:
        return frozenset(pitch % 12 for pitch in self.pitches)

    @property
    def symbol(self) -> str:
        return chord_symbol(self.pitches)

    @property
    def figures(self) -> str:
        """Return the intervals above the bass as a figured bass has them (2 to 8)."""
        if not self.notes:
            return ""
        bass = self.pitches[0]
        steps = {_generic_interval(bass, pitch) for pitch in self.pitches[1:]}
        return " ".join(str(step) for step in sorted(steps, reverse=True))

    @property
    def clashes(self) -> tuple[tuple[int, int], ...]:
        """Return the pairs of notes a semitone, a major seventh, or a minor ninth apart."""
        unique = sorted(set(self.pitches))
        return tuple(
            (low, high)
            for index, low in enumerate(unique)
            for high in unique[index + 1 :]
            if (high - low) % 12 in (1, 11)
        )

    @property
    def cluster(self) -> bool:
        """Return true if three or more pitch classes are adjacent (semitones or whole tones)."""
        classes = self.classes
        return any(
            {(pc + first) % 12, (pc + first + second) % 12} <= classes
            for pc in classes
            for first in (1, 2)
            for second in (1, 2)
        )


def _generic_interval(low: int, high: int) -> int:
    """Return the interval number (2 to 8) from the semitones between two notes."""
    semitones = (high - low) % 12
    if semitones == 0:
        return 8 if high != low else 1
    return (0, 2, 2, 3, 3, 4, 5, 5, 6, 6, 7, 7)[semitones] if semitones != 6 else 4


def notes_of(
    work: Work, first_bar: int, last_bar: int, players: Sequence[str] | None = None
) -> list[PerfNote]:
    """Return the notes that sound in the bars (no grace notes), for some players or for all."""
    structure = work.structure
    begin, end = structure.bar(first_bar).start, structure.bar(last_bar).end
    names = players if players is not None else [p.id for p in work.orchestra.players]
    found = []
    for name in names:
        for note in perform(work, name):
            if not note.grace and note.start < end and note.start + note.duration > begin:
                found.append(note)
    return found


def moments(
    work: Work,
    first_bar: int,
    last_bar: int,
    step: Fraction = Fraction(1),
    players: Sequence[str] | None = None,
) -> list[Moment]:
    """Return the notes that sound at each step (in quarter notes) of the bars."""
    structure = work.structure
    notes = notes_of(work, first_bar, last_bar, players)
    result = []
    for bar in structure.bars[first_bar - 1 : last_bar]:
        position = bar.start
        while position < bar.end:
            sounding = sorted(
                {
                    (round(note.midi), note.player)
                    for note in notes
                    if note.start <= position < note.start + note.duration
                }
            )
            result.append(Moment(bar.number, position - bar.start + 1, tuple(sounding)))
            position += step
    return result


def summary(found: Sequence[Moment]) -> dict[str, float]:
    """Return the shares of the moments: silence, triads, clashes, and clusters."""
    count = max(len(found), 1)
    sounding = [moment for moment in found if moment.notes]
    triads = sum(
        1
        for moment in sounding
        if len(moment.classes) == 3
        and tuple(sorted((pc - min(moment.classes)) % 12 for pc in moment.classes))
        in ((0, 3, 7), (0, 4, 7), (0, 3, 8), (0, 4, 9), (0, 5, 8), (0, 5, 9))
    )
    return {
        "silence": (len(found) - len(sounding)) / count,
        "major and minor triads": triads / count,
        "with a semitone clash": sum(1 for m in sounding if m.clashes) / count,
        "with a cluster": sum(1 for m in sounding if m.cluster) / count,
        "pitch classes (mean)": sum(len(m.classes) for m in sounding) / max(len(sounding), 1),
    }


def report(found: Sequence[Moment]) -> list[str]:
    """Return one line of text for each moment."""
    lines = []
    for moment in found:
        names = " ".join(note_name(pitch) for pitch in sorted(set(moment.pitches)))
        marks = ""
        if moment.clashes:
            pairs = ", ".join(f"{note_name(a)}/{note_name(b)}" for a, b in moment.clashes)
            marks = f"  clash: {pairs}"
        if moment.cluster:
            marks += "  cluster"
        lines.append(
            f"{moment.bar:4d}.{float(moment.beat):<5g} {moment.symbol:14s} {moment.figures:10s} "
            f"{names}{marks}"
        )
    return lines


@dataclass(frozen=True)
class Parallel:
    """Two voices that move in parallel fifths or octaves."""

    bar: int
    beat: Fraction
    kind: str  # "fifths" or "octaves"
    low: str
    high: str

    def __str__(self) -> str:
        place = f"bar {self.bar}, beat {float(self.beat):g}"
        return f"{place}: parallel {self.kind}, {self.low} and {self.high}"


def _line(notes: Sequence[PerfNote], player: str, top: bool) -> list[PerfNote]:
    """Return one line of a player: the highest (or the lowest) note at each start."""
    by_start: dict[Fraction, PerfNote] = {}
    for note in notes:
        if note.player != player:
            continue
        known = by_start.get(note.start)
        if known is None or (note.midi > known.midi) == top:
            by_start[note.start] = note
    return [by_start[start] for start in sorted(by_start)]


def parallels(
    work: Work, first_bar: int, last_bar: int, players: Sequence[str] | None = None
) -> list[Parallel]:
    """Return the parallel fifths and octaves between each pair of players.

    The line of a player is its highest note at each moment (for the left
    hand of a keyboard instrument: its lowest note). Two lines are parallel
    if the two move at the same moment, in the same direction, from a fifth
    to a fifth or from an octave to an octave. Two players who have the same
    line for some time (most of their notes near a place are in unison or in
    octaves) are a doubling there: these octaves are not in the result.
    """
    structure = work.structure
    if players is not None:
        names = list(players)
    else:
        # The chords of a keyboard instrument and of the theorbo are a realization of the
        # harmony: they double the lines of the other players, and they are not lines.
        names = [p.id for p in work.orchestra.players if p.family not in ("keyboards", "plucked")]
    notes = notes_of(work, first_bar, last_bar, names)
    lines = {name: _line(notes, name, top=not name.endswith(".lh")) for name in names}
    found = []
    for index, low_name in enumerate(names):
        for high_name in names[index + 1 :]:
            first, second = lines[low_name], lines[high_name]
            starts = {note.start: note for note in second}
            pairs = []  # the moments at which the two lines start a note together
            for note in first:
                other = starts.get(note.start)
                if other is not None:
                    pairs.append((note, other))
            octaves = [round(abs(b.midi - a.midi)) % 12 == 0 for a, b in pairs]
            for index, ((a1, b1), (a2, b2)) in enumerate(zip(pairs[:-1], pairs[1:], strict=True)):
                # A doubling: most of the notes near this place are in unison or in octaves.
                near = octaves[max(0, index - DOUBLING_SPAN + 1) : index + DOUBLING_SPAN + 1]
                doubling = len(near) >= 4 and sum(near) >= DOUBLING_SHARE * len(near)
                # The two notes must follow the notes before them with no other note between.
                if a1.start + a1.duration != a2.start or b1.start + b1.duration != b2.start:
                    continue
                before = round(abs(b1.midi - a1.midi)) % 12
                after = round(abs(b2.midi - a2.midi)) % 12
                moved = (a2.midi - a1.midi) * (b2.midi - b1.midi) > 0
                # Two players on the same note (a unison) are always a doubling.
                unison = round(a1.midi) == round(b1.midi) and round(a2.midi) == round(b2.midi)
                if (
                    moved
                    and before == after
                    and before in (0, 7)
                    and not unison
                    and not (doubling and before == 0)
                ):
                    bar = structure.bar_at(a2.start)
                    kind = "octaves" if before == 0 else "fifths"
                    place = a2.start - bar.start + 1
                    found.append(Parallel(bar.number, place, kind, low_name, high_name))
    return found


# Two lines are a doubling at a place if this share of their common notes near the place
# (`DOUBLING_SPAN` notes before it and after it) is in unison or in octaves.
DOUBLING_SHARE = 0.7
DOUBLING_SPAN = 4


@dataclass(frozen=True)
class Phrase:
    """One phrase of the voice: the notes between two breaths."""

    bar: int
    seconds: float
    notes: int
    lowest: int
    highest: int


BREATH = Fraction(1, 4)  # a rest of this length (quarter notes) or more is a breath


def phrases(work: Work, player: str = "alto") -> list[Phrase]:
    """Return the phrases of a voice.

    A rest of a sixteenth note or more is a breath. A note with a fermata is
    the end of a phrase: the singer breathes after it. A breath mark
    (`\\breathe`) is a breath also.
    """
    structure = work.structure
    notes = [note for note in perform(work, player) if not note.grace]
    marks: list[Fraction] = []
    _breath_marks(work.music_of(player).children, Fraction(0), Fraction(1), marks)
    result: list[Phrase] = []
    group: list[PerfNote] = []

    def close() -> None:
        if group:
            begin = structure.seconds(group[0].start)
            end = structure.seconds(group[-1].start + group[-1].duration)
            pitches = [round(note.midi) for note in group]
            result.append(
                Phrase(
                    structure.bar_at(group[0].start).number,
                    end - begin,
                    len(group),
                    min(pitches),
                    max(pitches),
                )
            )
            group.clear()

    for note in notes:
        if group:
            before = group[-1]
            marked = any(before.start < mark <= note.start for mark in marks)
            if before.fermata or marked or note.start - (before.start + before.duration) >= BREATH:
                close()
        group.append(note)
    close()
    return result


def _breath_marks(
    elements: Sequence[music.Element], position: Fraction, scale: Fraction, found: list[Fraction]
) -> Fraction:
    """Collect the positions of the breath marks of a line. Return the end position."""
    for element in elements:
        if isinstance(element, music.Command):
            if element.name == "breathe":
                found.append(position)
        elif isinstance(element, music.Note | music.Rest):
            position += element.duration * scale
        elif isinstance(element, music.Group):
            if element.kind == "grace":
                continue
            if element.kind == "parallel":
                position = max(
                    _breath_marks(child.children, position, scale, found)
                    for child in element.children
                )
            elif element.kind in ("unfold", "tremolo"):
                for _ in range(element.count):
                    position = _breath_marks(element.children, position, scale, found)
            else:
                position = _breath_marks(element.children, position, scale * element.ratio, found)
    return position


def voice_summary(work: Work, player: str = "alto") -> dict[str, float]:
    """Return numbers of the line of a voice, for the comparison with the style profiles."""
    notes = [note for note in perform(work, player) if not note.grace]
    if not notes:
        return {}
    pitches = sorted(round(note.midi) for note in notes)
    moves = [
        abs(round(b.midi) - round(a.midi))
        for a, b in zip(notes[:-1], notes[1:], strict=True)
        if b.start - (a.start + a.duration) < 1 and round(b.midi) != round(a.midi)
    ]
    count = max(len(moves), 1)
    found = phrases(work, player)
    return {
        "lowest note": pitches[0],
        "highest note": pitches[-1],
        "median note": pitches[len(pitches) // 2],
        "steps (share of the moves)": sum(1 for move in moves if move <= 2) / count,
        "sixths and larger (share of the moves)": sum(1 for move in moves if move >= 8) / count,
        "longest phrase (seconds)": max(phrase.seconds for phrase in found),
    }
