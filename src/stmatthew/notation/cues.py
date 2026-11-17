"""Cues in the parts.

After a long rest, a player must know where the music is. The guidelines of
the orchestra librarians ask for a cue: in the bars before the entry, the part
shows some notes of a different instrument in small type. The player does not
play these notes.

This module finds the entries after a long rest, and it selects an instrument
for each cue. The player must hear that instrument clearly: thus the module
prefers an instrument that is loud, that has many notes, and that plays until
the entry.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import TYPE_CHECKING

from . import combine, music

if TYPE_CHECKING:
    from .work import Work

# A cue comes after a rest of this many bars or more.
LONG_REST_BARS = 8
# A cue also comes after a rest of this many seconds, if the rest has `SHORT_REST_BARS` or more.
LONG_REST_SECONDS = 25.0
SHORT_REST_BARS = 4
# A cue shows this many seconds of music or more, but not more than `MOST_CUE_BARS`.
CUE_SECONDS = 5.0
MOST_CUE_BARS = 4

# How clearly a player hears a family of instruments (0 to 1).
FAMILY_WEIGHT = {
    "brass": 0.8,
    "woodwinds": 0.8,
    "strings": 0.7,
    "keyboards": 0.6,
    "plucked": 0.5,
    "percussion": 0.4,
}

# The short name of an instrument in a cue, where it is not the usual instrument of its player.
INSTRUMENT_SHORT = {
    "flute": "Fl.",
    "alto flute": "A. Fl.",
    "piccolo": "Picc.",
    "oboe": "Ob.",
    "English horn": "E. Hn.",
    "ocarina": "Oc.",
    "clarinet in B-flat": "Cl.",
    "clarinet in E-flat": "E-fl. Cl.",
    "bass clarinet": "B. Cl.",
    "bassoon": "Bn.",
    "contrabassoon": "Cbn.",
    "timpani": "Timp.",
    "vibraphone": "Vib.",
    "marimba": "Mar.",
    "glockenspiel": "Glock.",
    "crotales": "Crot.",
    "xylophone": "Xyl.",
    "tubular bells": "Tub. Bells",
    "tuned gongs": "Gongs",
    "singing bowls": "Bowls",
}

# The middle of the staff for each clef: the MIDI number of the written note.
CLEF_CENTRE = {"treble": 71, "bass": 50, "alto": 60, "tenor": 57}


@dataclass
class Cue:
    """A cue for one part: the notes of a different player before an entry."""

    start: Fraction  # the start of the first bar of the cue
    end: Fraction  # the start of the bar of the entry
    source: str  # the player whose notes the cue shows
    label: str  # the short name of the instrument of the cue
    elements: list[music.Element]  # the notes of the cue, with the real sound


def _part_of(player_id: str) -> str:
    return player_id.split(".")[0]


def long_rests(work: Work, part_id: str) -> list[tuple[int, int]]:
    """Return the long rests of a part: the first bar of the rest and the bar of the entry."""
    structure = work.structure
    spans: list[tuple[Fraction, Fraction]] = []
    for player in work.orchestra.players:
        if _part_of(player.id) == part_id:
            notes, _end = combine.sounding(work.music_of(player.id).children, Fraction(0))
            spans.extend((start, end) for start, end, _pitch in notes)
    rests: list[tuple[int, int]] = []
    free = Fraction(0)  # the end of the last note
    for start, end in sorted(spans):
        if start > free:
            bar = structure.bar_at(free)
            first = bar.number if bar.start == free else bar.number + 1
            entry = structure.bar_at(start).number
            count = entry - first
            seconds = structure.seconds(structure.bar(entry).start) - structure.seconds(
                structure.bar(min(first, entry)).start
            )
            long_enough = count >= LONG_REST_BARS or (
                count >= SHORT_REST_BARS and seconds >= LONG_REST_SECONDS
            )
            if long_enough:
                rests.append((first, entry))
        free = max(free, end)
    return rests


def cue_bars(work: Work, first: int, entry: int) -> int:
    """Return the number of bars of the cue before the bar `entry`."""
    structure = work.structure
    end = structure.seconds(structure.bar(entry).start)
    most = min(MOST_CUE_BARS, entry - first)
    for count in range(1, most + 1):
        if end - structure.seconds(structure.bar(entry - count).start) >= CUE_SECONDS:
            return count
    return most


def _cue_elements(elements: list[music.Element]) -> list[music.Element]:
    """Return the notes for a cue: one note at a time, with ties, and no other marks."""
    result: list[music.Element] = []
    for element in elements:
        if isinstance(element, music.Note):
            top = max(element.pitches, key=lambda item: item.pitch.midi)
            ties = [post for post in element.posts if post.kind == "tie"]
            pitches = [music.NotePitch(top.pitch)]
            result.append(music.Note(pitches, False, element.duration, element.duration_text, ties))
        elif isinstance(element, music.Rest):
            # A full-bar rest of the cue instrument is empty: the part has its own rest.
            kind = "s" if element.kind == "R" else element.kind
            result.append(music.Rest(kind, element.duration, element.duration_text))
        elif isinstance(element, music.Group) and element.kind == "parallel":
            result.extend(_cue_elements(element.children[0].children))
        elif isinstance(element, music.Group) and element.kind != "grace":
            children = _cue_elements(element.children)
            result.append(
                music.Group(element.kind, children, element.header, element.ratio, element.count)
            )
    return result


def _attacks(elements: list[music.Element], held: bool) -> int:
    """Return the number of notes that start. `held` is true if a tie comes into the music."""
    count = 0
    for item in combine.timed(elements):
        if isinstance(item, music.Note):
            count += not held
            held = any(post.kind == "tie" for post in item.posts)
        else:
            held = False
    return count


def _tied_at_end(elements: list[music.Element]) -> bool:
    notes = list(combine.timed(elements))
    return bool(notes) and any(post.kind == "tie" for post in notes[-1].posts)


class _Sources:
    """The music of all players, in pieces with their positions."""

    def __init__(self, work: Work) -> None:
        from ..perform.events import perform_all  # at call time: that module imports this package

        self.work = work
        self.atoms: dict[str, list[tuple[Fraction, music.Element]]] = {}
        self.positions: dict[str, list[Fraction]] = {}
        for player in work.orchestra.players:
            chunks, _cuts = combine.player_atoms(work, player.id)
            flat = [atom for chunk in chunks for atom in chunk]
            self.atoms[player.id] = flat
            self.positions[player.id] = [position for position, _element in flat]
        # The notes as the players play them, in the sequence of their starts.
        self.notes = {
            player_id: sorted(notes, key=lambda note: note.start)
            for player_id, notes in perform_all(work).items()
        }
        self.starts = {
            player_id: [note.start for note in notes] for player_id, notes in self.notes.items()
        }
        self.bar_lines = frozenset(bar.start for bar in work.structure.bars)

    def window(self, player_id: str, start: Fraction, end: Fraction) -> list[music.Element] | None:
        """Return the music of a player from `start` to `end`, or None if it cannot be cut there."""
        positions = self.positions[player_id]
        low = bisect.bisect_left(positions, start)
        high = bisect.bisect_left(positions, end)
        elements = [element for _position, element in self.atoms[player_id][low:high]]
        length = sum((music.length(element) for element in elements), Fraction(0))
        return elements if length == end - start else None

    def playing(self, player_id: str, start: Fraction, end: Fraction) -> list:
        """Return the notes of a player that sound in the time from `start` to `end`."""
        notes, starts = self.notes[player_id], self.starts[player_id]
        low = bisect.bisect_left(starts, start)
        high = bisect.bisect_left(starts, end)
        # Some notes that started before can sound in this time.
        before = [
            note for note in notes[max(low - 12, 0) : low] if note.start + note.duration > start
        ]
        return before + notes[low:high]

    def held_into(self, player_id: str, start: Fraction) -> bool:
        """Return true if a note of the player has a tie into the position `start`."""
        low = bisect.bisect_left(self.positions[player_id], start)
        before = [element for _position, element in self.atoms[player_id][max(low - 2, 0) : low]]
        return _tied_at_end(before)

    def with_bar_checks(
        self, player_id: str, start: Fraction, end: Fraction
    ) -> list[music.Element]:
        """Return the cue notes of a player with a bar check after each bar."""
        positions = self.positions[player_id]
        low = bisect.bisect_left(positions, start)
        high = bisect.bisect_left(positions, end)
        result: list[music.Element] = []
        for position, element in self.atoms[player_id][low:high]:
            new_bar = position > start and position in self.bar_lines and music.length(element)
            if new_bar and result and not isinstance(result[-1], music.BarCheck):
                result.append(music.BarCheck())
            result.extend(_cue_elements([element]))
        return result


def _label(work: Work, player_id: str, instrument: str) -> str:
    player = work.orchestra.player(player_id)
    if instrument == player.instruments[0] and player.family != "percussion":
        return player.short
    return INSTRUMENT_SHORT.get(instrument, instrument[:1].upper() + instrument[1:])


def _best_source(
    sources: _Sources, part_id: str, family: str, start: Fraction, end: Fraction
) -> Cue | None:
    """Return the cue for the time from `start` to `end`, from the player that is best to hear.

    The cue starts with the first bar in which that player has a note.
    """
    work = sources.work
    best: tuple[float, str, str] | None = None
    for player in work.orchestra.players:
        if _part_of(player.id) == part_id:
            continue
        elements = sources.window(player.id, start, end)
        if elements is None or not combine.has_notes(elements):
            continue
        playing = sources.playing(player.id, start, end)
        if not playing:
            continue
        instrument = playing[-1].instrument
        if work.orchestra.instruments.get(instrument) is None:
            continue  # an instrument with no pitch
        attacks = _attacks(elements, sources.held_into(player.id, start))
        notes, _end = combine.sounding(elements, start)
        to_the_entry = max(last for _first, last, _pitch in notes) >= end - Fraction(1)
        level = max(note.level for note in playing)
        score = (
            2.0 * level
            + 1.2 * min(attacks, 8) / 8
            + (1.0 if to_the_entry else 0.0)
            + FAMILY_WEIGHT.get(player.family, 0.5)
            + (0.4 if player.family == family else 0.0)
            - (1.5 if attacks == 0 else 0.0)
        )
        if best is None or score > best[0]:
            best = (score, player.id, instrument)
    if best is None:
        return None
    _score, player_id, instrument = best
    notes, _end = combine.sounding(sources.window(player_id, start, end) or [], start)
    first_note = min(first for first, _last, _pitch in notes)
    start = max(line for line in sources.bar_lines | {start} if start <= line <= first_note)
    elements = sources.with_bar_checks(player_id, start, end)
    # A tie at the end of the cue goes to a note that the cue does not show.
    timed = [item for item in combine.timed(elements) if isinstance(item, music.Note)]
    if timed:
        timed[-1].posts[:] = [post for post in timed[-1].posts if post.kind != "tie"]
    return Cue(start, end, player_id, _label(work, player_id, instrument), elements)


def find_cues(work: Work) -> dict[str, list[Cue]]:
    """Return the cues of each part of the work."""
    sources = _Sources(work)
    structure = work.structure
    cues: dict[str, list[Cue]] = {}
    families = {_part_of(player.id): player.family for player in work.orchestra.players}
    for part_id, family in families.items():
        found: list[Cue] = []
        for first, entry in long_rests(work, part_id):
            count = cue_bars(work, first, entry)
            start, end = structure.bar(entry - count).start, structure.bar(entry).start
            cue = _best_source(sources, part_id, family, start, end)
            if cue is not None:
                found.append(cue)
        cues[part_id] = found
    return cues


def fitted(elements: list[music.Element], clef: str, shift: int) -> list[music.Element]:
    """Return the notes of a cue in the best octave for a staff.

    `clef` is the clef of the cue, and `shift` is the number of semitones
    from the real sound up to the written note of the part.
    """
    notes = [item for item in combine.timed(elements) if isinstance(item, music.Note)]
    written = sorted(note.pitches[0].pitch.midi + shift for note in notes)
    if not written:
        return elements
    octaves = round((CLEF_CENTRE[clef] - written[len(written) // 2]) / 12)
    for note in notes:
        pitch = note.pitches[0].pitch
        note.pitches = [music.NotePitch(replace(pitch, octave=pitch.octave + octaves))]
    return elements
