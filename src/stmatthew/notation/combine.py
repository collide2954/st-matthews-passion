"""Two players of one instrument on one staff of the conductor score.

A score with one staff for each wind player has too many staves for a page.
The guidelines of the orchestra librarians ask for one staff for each pair of
players (for example flutes 1 and 2). This module makes the music of such a
staff from the music of the two players.

The staff has two voices. The music is divided into units: a unit is one bar
(or more than one bar, if a group of notes goes across a bar line). For each
unit, the module selects how the unit shows:

- `rest`: the two players are silent.
- `one`, `two`: one player has notes. The staff shows one line with the label "1." or "2.".
- `unison`: the two players have the same music. One line with the label "a 2".
- `chords`: the two players have the same rhythm and the same marks. One line
  of chords: player 1 has the upper note.
- `voices`: all other units. Two lines: the stems of player 1 go up, and the
  stems of player 2 go down.

A player who changes to a different instrument (for example flute 2 to alto
flute) gets a staff of its own for that instrument. The score shows that staff
only where it has notes.
"""

from __future__ import annotations

import bisect
import copy
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import pairwise
from typing import TYPE_CHECKING

from . import music, techniques

if TYPE_CHECKING:
    from .work import Work

# The pairs of players that share a staff in the conductor score.
# The score of this work has 17 staves: each player has a staff of its own, as in
# the scores of Bach. A pair that must share a staff goes into this list, for
# example ("fl1", "fl2").
PAIRS: tuple[tuple[str, str], ...] = ()

# After a silence of the two players of this length (in quarter notes), the label
# of the players ("1.", "2.", "a 2") is given again.
LABEL_AFTER_SILENCE = Fraction(8)

LABELS = {"one": "1.", "two": "2.", "unison": "a 2"}

# The voice in which the music of player 2 is, for each mode. Zero: no music.
_SECOND_VOICE = {"two": 2, "voices": 2, "unison": 1, "chords": 1}


def duration_text(duration: Fraction) -> str:
    """Return the LilyPond text of a duration in quarter notes, for example "4." or "1*7/8"."""
    for text, base in music.BASE_QUARTERS.items():
        for dots in range(4):
            if base * (2 - Fraction(1, 2**dots)) == duration:
                return text + "." * dots
    whole = duration / 4
    return f"1*{whole.numerator}" if whole.denominator == 1 else f"1*{whole}"


def timed(elements: list[music.Element]):
    """Give each note and each rest of the elements, in the sequence of the text."""
    for element in elements:
        if isinstance(element, music.Note | music.Rest):
            yield element
        elif isinstance(element, music.Group):
            yield from timed(element.children)


def has_notes(elements: list[music.Element] | None) -> bool:
    return bool(elements) and any(isinstance(item, music.Note) for item in timed(elements))


def _explicit(elements: list[music.Element]) -> list[music.Element]:
    """Return a copy of the elements in which each note and each rest has its duration text.

    A note with no duration text has the duration of the note before it. The
    units of a shared staff come from two players: thus each unit must be
    complete without the music before it.
    """
    return [_copy(element) for element in elements]


def copied(elements: list[music.Element]) -> list[music.Element]:
    """Return a copy of the elements: a change of the copy does not change the music."""
    return [_copy(element) for element in elements]


_DURATION_TEXTS: dict[Fraction, str] = {}


def _copy(element: music.Element) -> music.Element:
    """Return a copy of an element with its own lists. Each duration has its text."""
    if isinstance(element, music.Note | music.Rest):
        text = element.duration_text
        if not text:
            text = _DURATION_TEXTS.get(element.duration, "")
            if not text:
                text = _DURATION_TEXTS[element.duration] = duration_text(element.duration)
        if isinstance(element, music.Rest):
            return music.Rest(element.kind, element.duration, text, list(element.posts))
        pitches = list(element.pitches)
        return music.Note(pitches, element.chord, element.duration, text, list(element.posts))
    if isinstance(element, music.Group):
        children = [_copy(child) for child in element.children]
        return music.Group(element.kind, children, element.header, element.ratio, element.count)
    return element  # a command or a bar check: the code does not change these


def _atoms(
    elements: list[music.Element], start: Fraction, bar_lines: list[Fraction]
) -> list[tuple[Fraction, music.Element]]:
    """Return the elements with their positions, in pieces that are as small as possible.

    The function removes the bar checks, cuts a rest of many bars at each bar
    line, and writes out a repeat that goes across a bar line.
    """
    atoms: list[tuple[Fraction, music.Element]] = []
    position = start
    for element in elements:
        if isinstance(element, music.BarCheck):
            continue
        end = position + music.length(element)
        low = bisect.bisect_right(bar_lines, position)
        inside = bar_lines[low : bisect.bisect_left(bar_lines, end)]
        if isinstance(element, music.Group) and element.kind == "sequence":
            atoms.extend(_atoms(element.children, position, bar_lines))
        elif isinstance(element, music.Group) and element.kind == "unfold" and inside:
            step = (end - position) / element.count
            for number in range(element.count):
                children = [_copy(child) for child in element.children]
                atoms.extend(_atoms(children, position + number * step, bar_lines))
        elif isinstance(element, music.Rest) and element.kind == "R" and inside:
            edges = [position, *inside, end]
            for number, (first, last) in enumerate(pairwise(edges)):
                posts = list(element.posts) if number == 0 else []
                rest = music.Rest("R", last - first, duration_text(last - first), posts)
                atoms.append((first, rest))
        else:
            atoms.append((position, element))
        position = end
    return atoms


@dataclass
class Unit:
    """One bar of a shared staff, or more bars that the code cannot divide."""

    chunk: int  # the index of the section of the work
    start: Fraction
    end: Fraction
    first: list[music.Element] | None = None  # None: player 1 has no notes on this staff
    second: list[music.Element] | None = None
    mode: str = "rest"
    merged: list[music.Element] = field(default_factory=list)  # one line for the two players

    @property
    def length(self) -> Fraction:
        return self.end - self.start


@dataclass
class Extra:
    """The music of one player on a different instrument: a staff of its own."""

    player: str
    instrument: str
    chunks: list[music.Group]


@dataclass
class SharedStaff:
    """The result for one pair: the two voices for each section, and the extra staves."""

    first: str
    second: str
    chunks: list[tuple[list[music.Element], list[music.Element]]]
    extras: list[Extra]
    units: list[Unit] = field(default_factory=list, repr=False)


# ----------------------------------------------------------------------------
# The units of one player
# ----------------------------------------------------------------------------


def player_atoms(
    work: Work, player_id: str
) -> tuple[list[list[tuple[Fraction, music.Element]]], list[set[Fraction]]]:
    """Return the atoms of each section for one player, and where a cut is possible."""
    structure = work.structure
    starts = [bar.start for bar in structure.bars]
    all_atoms: list[list[tuple[Fraction, music.Element]]] = []
    all_cuts: list[set[Fraction]] = []
    for first_bar, chunk in work.chunks[player_id]:
        start = structure.bar(first_bar).start
        end = start + music.length(chunk)
        bar_lines = starts[first_bar : bisect.bisect_left(starts, end)]
        atoms = _atoms(_explicit(chunk.children), start, bar_lines)
        cuts = {position for position, _element in atoms} | {start, end}
        all_atoms.append(atoms)
        all_cuts.append(cuts & ({start, end} | set(bar_lines)))
    return all_atoms, all_cuts


def _slice(
    atoms: list[tuple[Fraction, music.Element]], edges: list[Fraction]
) -> list[list[music.Element]]:
    """Divide the atoms at the edges. An element with no duration goes with the note after it."""
    pieces: list[list[music.Element]] = [[] for _ in edges[:-1]]
    for position, element in atoms:
        index = min(bisect.bisect_right(edges, position) - 1, len(pieces) - 1)
        pieces[index].append(element)
    return pieces


def _route(
    player_id: str, pieces: list[list[music.Element]], instrument: str
) -> tuple[list[tuple[list[music.Element], str]], str]:
    """Remove the instrument changes. Return each piece with the instrument of its notes."""
    routed: list[tuple[list[music.Element], str]] = []
    for piece in pieces:
        kept: list[music.Element] = []
        name = ""
        for element in piece:
            if isinstance(element, music.Command) and element.name == "switch":
                instrument = element.arguments[0].strip('"')
                continue
            if not name and has_notes([element]):
                name = instrument
            elif name and name != instrument and has_notes([element]):
                raise ValueError(f"{player_id}: two instruments in one bar")
            kept.append(element)
        routed.append((kept, name))
    return routed, instrument


# ----------------------------------------------------------------------------
# One line for two players
# ----------------------------------------------------------------------------


@dataclass
class _Level:
    """The dynamic level of a player: the last dynamic mark, and if a hairpin came after it."""

    mark: str = ""
    moving: bool = False
    hairpin: str = ""  # the hairpin that is open: "<", ">", or empty

    def read(self, posts: list[music.Post]) -> None:
        for post in posts:
            if post.kind == "dynamic":
                self.hairpin = ""
                if post.value in music.DYNAMICS:
                    self.mark, self.moving = post.value, False
            elif post.kind == "hairpin":
                self.moving = True
                self.hairpin = "" if post.value == "!" else post.value

    def steady_at(self, mark: str) -> bool:
        """Return true if the player has this level, and no hairpin came after its mark."""
        return (self.mark, self.moving) == (mark, False)

    def same(self, other: _Level) -> bool:
        if self.hairpin != other.hairpin:
            return False
        if self.moving and other.moving:
            return True
        return (self.mark, self.moving) == (other.mark, other.moving)


def _marks(note: music.Note | music.Rest) -> list[str]:
    return [p.value for p in note.posts if p.kind == "dynamic" and p.value in music.DYNAMICS]


def _other_posts(note: music.Note | music.Rest) -> list[tuple[str, str]]:
    return sorted(
        (post.kind, post.text)
        for post in note.posts
        if not (post.kind == "dynamic" and post.value in music.DYNAMICS)
    )


class _Different(Exception):
    """The two players cannot share one line in this unit."""


def _merge_note(
    first: music.Note, second: music.Note, levels: tuple[_Level, _Level], kinds: set[str]
) -> music.Note:
    if first.duration != second.duration or first.chord or second.chord:
        raise _Different
    if _other_posts(first) != _other_posts(second):
        raise _Different
    one, two = levels
    marks_one, marks_two = _marks(first), _marks(second)
    posts = list(first.posts)
    if marks_one != marks_two:
        # One player has a dynamic mark, and the other player has that level already.
        if not marks_one and len(marks_two) == 1 and one.steady_at(marks_two[0]):
            posts.extend(p for p in second.posts if p.kind == "dynamic" and p.value == marks_two[0])
        elif not (not marks_two and len(marks_one) == 1 and two.steady_at(marks_one[0])):
            raise _Different
    one.read(first.posts)
    two.read(second.posts)
    one.read(posts)
    two.read(posts)
    upper, lower = first.pitches[0], second.pitches[0]
    if upper.pitch.midi == lower.pitch.midi:
        if (upper.pitch.name, upper.marks) != (lower.pitch.name, lower.marks):
            raise _Different
        kinds.add("unison")
        return music.Note([upper], False, first.duration, first.duration_text, posts)
    if upper.pitch.midi < lower.pitch.midi:
        raise _Different  # player 2 is above player 1: two voices show this
    kinds.add("chords")
    return music.Note([lower, upper], True, first.duration, first.duration_text, posts)


def _merge(
    first: list[music.Element],
    second: list[music.Element],
    levels: tuple[_Level, _Level],
    kinds: set[str],
) -> list[music.Element]:
    """Return one line for the music of two players, or raise `_Different`."""
    if len(first) != len(second):
        raise _Different
    merged: list[music.Element] = []
    for one, two in zip(first, second, strict=True):
        if type(one) is not type(two):
            raise _Different
        if isinstance(one, music.Note):
            merged.append(_merge_note(one, two, levels, kinds))
        elif isinstance(one, music.Rest):
            if (one.kind, one.duration) != (two.kind, two.duration):
                raise _Different
            levels[0].read(one.posts)
            levels[1].read(two.posts)
            merged.append(one)
        elif isinstance(one, music.Command):
            if (one.name, one.arguments) != (two.name, two.arguments):
                raise _Different
            merged.append(one)
        elif isinstance(one, music.Group):
            same = (one.kind, one.header, one.ratio, one.count) == (
                two.kind,
                two.header,
                two.ratio,
                two.count,
            )
            if not same or one.kind == "parallel":
                raise _Different
            children = _merge(one.children, two.children, levels, kinds)
            merged.append(music.Group(one.kind, children, one.header, one.ratio, one.count))
        else:
            merged.append(one)
    return merged


def _read_levels(elements: list[music.Element] | None, level: _Level) -> None:
    for item in timed(elements or []):
        level.read(item.posts)


@dataclass
class _Spans:
    """The slurs and other lines of a player that are open at a point of the music."""

    slurs: int = 0
    phrases: int = 0
    trill: bool = False
    text: bool = False
    joined: bool = False  # the last note has a tie or a glissando to the note after it

    def read(self, elements: list[music.Element] | None) -> None:
        for item in timed(elements or []):
            for post in item.posts:
                if post.kind == "slur":
                    self.slurs += 1 if post.value == "(" else -1
                elif post.kind == "phrasing":
                    self.phrases += 1 if post.value == "(" else -1
                elif post.kind == "command" and post.value == "startTrillSpan":
                    self.trill = True
                elif post.kind == "command" and post.value == "stopTrillSpan":
                    self.trill = False
                elif post.kind == "command" and post.value == "startTextSpan":
                    self.text = True
                elif post.kind == "command" and post.value == "stopTextSpan":
                    self.text = False
            self.joined = isinstance(item, music.Note) and any(
                post.kind == "tie" or (post.kind == "command" and post.value == "glissando")
                for post in item.posts
            )

    @property
    def open(self) -> bool:
        return self.slurs > 0 or self.phrases > 0 or self.trill or self.text or self.joined


# ----------------------------------------------------------------------------
# The units of a pair and their modes
# ----------------------------------------------------------------------------


def pair_units(work: Work, first_id: str, second_id: str) -> tuple[list[Unit], list[Extra]]:
    """Return the units of a shared staff with their modes, and the extra staves."""
    orchestra = work.orchestra
    primary = orchestra.player(first_id).instruments[0]
    if orchestra.player(second_id).instruments[0] != primary:
        raise ValueError(f"{first_id} and {second_id} do not have the same instrument")
    atoms_one, cuts_one = player_atoms(work, first_id)
    atoms_two, cuts_two = player_atoms(work, second_id)
    units: list[Unit] = []
    # For each unit: the music of a player on a different instrument.
    elsewhere: list[dict[tuple[str, str], list[music.Element]]] = []
    instruments = [primary, primary]
    for index, (one, two) in enumerate(zip(atoms_one, atoms_two, strict=True)):
        edges = sorted(cuts_one[index] & cuts_two[index])
        routed_one, instruments[0] = _route(first_id, _slice(one, edges), instruments[0])
        routed_two, instruments[1] = _route(second_id, _slice(two, edges), instruments[1])
        for number, (start, end) in enumerate(pairwise(edges)):
            unit = Unit(index, start, end)
            other: dict[tuple[str, str], list[music.Element]] = {}
            for player_id, routed, name in (
                (first_id, routed_one, "first"),
                (second_id, routed_two, "second"),
            ):
                elements, instrument = routed[number]
                if instrument == primary:
                    setattr(unit, name, elements)
                elif instrument:
                    other[(player_id, instrument)] = elements
            units.append(unit)
            elsewhere.append(other)
    _set_modes(units)
    extras: list[Extra] = []
    for key in dict.fromkeys(key for other in elsewhere for key in other):
        chunks = [music.Group("sequence", []) for _ in atoms_one]
        for unit, other in zip(units, elsewhere, strict=True):
            rest = music.Rest("R", unit.length, duration_text(unit.length))
            chunks[unit.chunk].children.extend([*other.get(key, [rest]), music.BarCheck()])
        extras.append(Extra(key[0], key[1], chunks))
    return units, extras


def _set_modes(units: list[Unit]) -> None:
    levels = (_Level(), _Level())
    for unit in units:
        if unit.first is None and unit.second is None:
            unit.mode = "rest"
        elif unit.second is None:
            unit.mode = "one"
        elif unit.first is None:
            unit.mode = "two"
        else:
            unit.mode = "voices"
            trial = (copy.copy(levels[0]), copy.copy(levels[1]))
            kinds: set[str] = set()
            try:
                # The first note decides if the two players have the same level.
                before = (copy.copy(levels[0]), copy.copy(levels[1]))
                merged = _merge(unit.first, unit.second, trial, kinds)
                _check_start(unit, before)
                if len(kinds) == 1:
                    unit.mode = kinds.pop()
                    unit.merged = merged
            except _Different:
                pass
        _read_levels(unit.first, levels[0])
        _read_levels(unit.second, levels[1])
    # A slur or a tie of player 2 cannot go from one voice to the other voice.
    spans = _Spans()
    open_after: list[bool] = []
    for unit in units:
        spans.read(unit.second)
        open_after.append(spans.open if unit.second is not None else False)
    changed = True
    while changed:
        changed = False
        for index in range(len(units) - 1):
            here, there = units[index], units[index + 1]
            sides = (_SECOND_VOICE.get(here.mode, 0), _SECOND_VOICE.get(there.mode, 0))
            if open_after[index] and 0 not in sides and sides[0] != sides[1]:
                for unit in (here, there):
                    if unit.mode in ("unison", "chords"):
                        unit.mode = "voices"
                        changed = True


def _check_start(unit: Unit, before: tuple[_Level, _Level]) -> None:
    """Raise `_Different` if the two players do not start the unit at the same dynamic level."""
    one, two = copy.copy(before[0]), copy.copy(before[1])
    first = _first_note(unit.first or [])
    second = _first_note(unit.second or [])
    if first is None or second is None:
        return
    marks = _marks(first) or _marks(second)
    if marks:
        return  # the mark is for the two players (the function `_merge_note` made sure of this)
    if not one.same(two):
        raise _Different


# ----------------------------------------------------------------------------
# The upper line is for player 1
# ----------------------------------------------------------------------------


def sounding(
    elements: list[music.Element], start: Fraction, scale: Fraction = Fraction(1)
) -> tuple[list[tuple[Fraction, Fraction, float]], Fraction]:
    """Return the start, the end, and the highest pitch of each note, and the end position."""
    notes: list[tuple[Fraction, Fraction, float]] = []
    position = start
    for element in elements:
        if isinstance(element, music.Note):
            end = position + element.duration * scale
            notes.append((position, end, max(item.pitch.midi for item in element.pitches)))
            position = end
        elif isinstance(element, music.Rest):
            position += element.duration * scale
        elif isinstance(element, music.Group) and element.kind == "parallel":
            ends = [position]
            for child in element.children:
                found, end = sounding(child.children, position, scale)
                notes.extend(found)
                ends.append(end)
            position = max(ends)
        elif isinstance(element, music.Group) and element.kind != "grace":
            for _ in range(element.count):
                found, position = sounding(element.children, position, scale * element.ratio)
                notes.extend(found)
    return notes, position


def tie_points(
    elements: list[music.Element], start: Fraction, scale: Fraction = Fraction(1)
) -> tuple[list[Fraction], Fraction]:
    """Return the positions at which a note ends that has a tie to the subsequent note."""
    points: list[Fraction] = []
    position = start
    for element in elements:
        if isinstance(element, music.Note | music.Rest):
            position += element.duration * scale
            if isinstance(element, music.Note) and any(p.kind == "tie" for p in element.posts):
                points.append(position)
        elif isinstance(element, music.Group) and element.kind == "parallel":
            ends = [position]
            for child in element.children:
                found, end = tie_points(child.children, position, scale)
                points.extend(found)
                ends.append(end)
            position = max(ends)
        elif isinstance(element, music.Group) and element.kind != "grace":
            for _ in range(element.count):
                found, position = tie_points(element.children, position, scale * element.ratio)
                points.extend(found)
    return points, position


def second_is_above(
    first: list[tuple[Fraction, Fraction, float]], second: list[tuple[Fraction, Fraction, float]]
) -> bool:
    """Return true if player 2 is above player 1 at each moment at which the two players sound."""
    above = below = 0
    for start, end, pitch in first:
        for other_start, other_end, other_pitch in second:
            if other_start < end and start < other_end:
                above += other_pitch > pitch
                below += other_pitch < pitch
    return above > 0 and below == 0


def exchanged_units(work: Work, first_id: str, second_id: str) -> list[int]:
    """Return the bars in which the two players make chords with player 2 on top.

    On a shared staff, the upper note of a chord is for player 1. A bar in
    this list shows as two voices that cross: the composer must exchange the
    music of the two players.
    """
    units, _extras = pair_units(work, first_id, second_id)
    bars: list[int] = []
    for unit in units:
        if unit.mode != "voices":
            continue
        try:
            kinds: set[str] = set()
            _merge(unit.second, unit.first, (_Level(), _Level()), kinds)
        except _Different:
            continue
        if kinds == {"chords"}:
            bars.append(work.structure.bar_at(unit.start).number)
    return bars


# ----------------------------------------------------------------------------
# The two voices of a shared staff
# ----------------------------------------------------------------------------


def _timeline(
    elements: list[music.Element], start: Fraction, scale: Fraction = Fraction(1)
) -> tuple[list[tuple[Fraction, music.Note | music.Rest]], Fraction]:
    """Return each note and each rest with its position, and the end position."""
    found: list[tuple[Fraction, music.Note | music.Rest]] = []
    position = start
    for element in elements:
        if isinstance(element, music.Note | music.Rest):
            found.append((position, element))
            position += element.duration * scale
        elif isinstance(element, music.Group) and element.kind == "grace":
            found.extend((position, item) for item in timed(element.children))
        elif isinstance(element, music.Group):
            for _ in range(element.count):
                inner, position = _timeline(element.children, position, scale * element.ratio)
                found.extend(inner)
    return found, position


def _events(elements: list[music.Element], start: Fraction) -> list[tuple[Fraction, music.Post]]:
    """Return the dynamic marks and the hairpins of the elements with their positions."""
    events: list[tuple[Fraction, music.Post]] = []
    seen: set[int] = set()
    for position, item in _timeline(elements, start)[0]:
        if id(item) in seen:
            continue
        seen.add(id(item))
        events.extend((position, p) for p in item.posts if p.kind in ("dynamic", "hairpin"))
    return events


def _hairpin_after(elements: list[music.Element], is_open: bool) -> bool:
    """Return true if a hairpin is open after the elements."""
    for item in timed(elements):
        for post in item.posts:
            if post.kind == "hairpin":
                is_open = post.value != "!"
            elif post.kind == "dynamic":
                is_open = False
    return is_open


def _first_note(elements: list[music.Element]) -> music.Note | None:
    return next((item for item in timed(elements) if isinstance(item, music.Note)), None)


def _silence(length: Fraction, kind: str, stop: bool) -> music.Rest:
    posts = [music.Post("hairpin", "\\!", "!")] if stop else []
    return music.Rest(kind, length, duration_text(length), posts)


def _flip(post: music.Post, voice: int) -> music.Post:
    """Return a text mark on the side of its voice: above for voice one, below for voice two."""
    sign = "^" if voice == 1 else "_"
    if post.kind == "text" and post.text[:1] in "^_-":
        return music.Post("text", sign + post.text[1:], post.value)
    technique = techniques.TECHNIQUES.get(post.value) if post.kind == "command" else None
    if technique is not None and post.text.lstrip("^_-") == f"\\{technique.name}":
        style = "\\italic " if technique.italic else ""
        return music.Post("text", f'{sign}\\markup {{ {style}"{technique.text}" }}', post.value)
    return post


@dataclass
class _Writer:
    """Write the units of a shared staff into two voices."""

    system_bars: frozenset[int]
    styles: list[str] = field(default_factory=lambda: ["", ""])
    open: list[bool] = field(default_factory=lambda: [False, False])  # a hairpin is open
    levels: tuple[_Level, _Level] = field(default_factory=lambda: (_Level(), _Level()))
    label: str = ""
    silence: Fraction = Fraction(0)
    dynamics_up: bool = False

    def style(self, voice: int, name: str) -> list[music.Element]:
        if self.styles[voice] == name:
            return []
        self.styles[voice] = name
        return [music.Command(name)]

    def labelled(self, elements: list[music.Element], mode: str) -> list[music.Element]:
        """Give the label of the players to the first note, if the label changes."""
        self.silence = Fraction(0)
        if mode not in LABELS:
            self.label = mode
            return elements
        if self.label != mode:
            note = _first_note(elements)
            if note is not None:
                note.posts.append(music.Post("text", f'^\\markup \\players "{LABELS[mode]}"'))
                self.label = mode
        return elements

    def write(
        self, unit: Unit, bar: int, one: list[music.Element], two: list[music.Element]
    ) -> None:
        if bar in self.system_bars:
            self.label = ""
        # The dynamic levels after this unit: from the music before a mark is removed.
        after = (copy.copy(self.levels[0]), copy.copy(self.levels[1]))
        _read_levels(unit.first, after[0])
        _read_levels(unit.second, after[1])
        first, second = self._lines(unit)
        up = unit.mode == "voices" and self._split(unit, first, second)
        if up != self.dynamics_up:
            one.append(music.Command("dynamicUp" if up else "dynamicNeutral"))
            self.dynamics_up = up
        for voice, line, target in ((0, first, one), (1, second, two)):
            if line is None:
                # No music in this voice. A hairpin that is open stops here.
                if voice == 0 and unit.mode == "rest":
                    target.extend(self.style(0, "oneVoice"))
                silent = "R" if (voice == 0 and unit.mode == "rest") else "s"
                target.append(_silence(unit.length, silent, self.open[voice]))
                self.open[voice] = False
            else:
                name = ("voiceOne", "voiceTwo")[voice] if unit.mode == "voices" else "oneVoice"
                target.extend(self.style(voice, name))
                target.extend(line)
                self.open[voice] = _hairpin_after(line, self.open[voice])
            target.append(music.BarCheck())
        if unit.mode == "rest":
            self.silence += unit.length
            if self.silence >= LABEL_AFTER_SILENCE:
                self.label = ""
        self.levels = after

    def _lines(self, unit: Unit) -> tuple[list[music.Element] | None, list[music.Element] | None]:
        """Return the music of voice one and of voice two for a unit."""
        if unit.mode == "rest":
            return None, None
        if unit.mode == "one":
            return self.labelled(unit.first, "one"), None
        if unit.mode == "two":
            line = self.labelled(unit.second, "two")
            self._open_again(line)
            return None, line
        if unit.mode in ("unison", "chords"):
            return self.labelled(unit.merged, unit.mode), None
        self.labelled([], "voices")
        return unit.first, unit.second

    def _open_again(self, line: list[music.Element]) -> None:
        """Player 2 is in a hairpin that voice one showed: voice two shows it from here."""
        hairpin = self.levels[1].hairpin
        note = _first_note(line)
        if not hairpin or self.open[1] or note is None:
            return
        if not any(post.kind in ("dynamic", "hairpin") for post in note.posts):
            note.posts.append(music.Post("hairpin", f"\\{hairpin}", hairpin))

    def _split(self, unit: Unit, first: list[music.Element], second: list[music.Element]) -> bool:
        """Remove the dynamic marks that the two voices have in common.

        Return true if the two players have different dynamics: then the
        marks of player 1 are above the staff, and nothing is removed.
        """
        events = (_events(first, unit.start), _events(second, unit.start))
        same_sequence = [(p.kind, p.value) for _t, p in events[0]] == [
            (p.kind, p.value) for _t, p in events[1]
        ]
        drop: list[set[int]] = [set(), set()]  # the marks that a voice does not show
        if same_sequence:
            # The same marks, possibly at different moments: the voice that has a mark
            # first shows it.
            for (time_one, post_one), (time_two, post_two) in zip(*events, strict=True):
                if time_one <= time_two:
                    drop[1].add(id(post_two))
                else:
                    drop[0].add(id(post_one))
        else:
            for voice, other in ((0, 1), (1, 0)):
                level = copy.copy(self.levels[other])
                theirs = list(events[other])
                for time, post in events[voice]:
                    while theirs and theirs[0][0] < time:
                        level.read([theirs.pop(0)[1]])
                    at_time = [p for t, p in theirs if t == time]
                    if any((p.kind, p.value) == (post.kind, post.value) for p in at_time):
                        if voice == 1:
                            drop[1].add(id(post))
                        continue
                    steady = post.kind == "dynamic" and level.steady_at(post.value)
                    if not steady and not (post.kind == "hairpin" and post.value == "!"):
                        self._sides(first, second)
                        return True
        self._remove(first, drop[0], 0)
        self._remove(second, drop[1], 1)
        self._shared_texts(unit, first, second)
        return False

    def _remove(self, line: list[music.Element], drop: set[int], voice: int) -> None:
        """Remove marks from a voice. A hairpin of the voice that is open stops at such a mark."""
        is_open = self.open[voice]
        seen: set[int] = set()
        for item in timed(line):
            if id(item) in seen:
                continue
            seen.add(id(item))
            kept: list[music.Post] = []
            for post in item.posts:
                if post.kind == "hairpin" and post.value == "!":
                    if is_open:
                        kept.append(post)
                    is_open = False
                elif id(post) in drop:
                    if post.kind == "dynamic" and is_open:
                        kept.append(music.Post("hairpin", "\\!", "!"))
                        is_open = False
                else:
                    kept.append(post)
                    if post.kind == "hairpin":
                        is_open = True
                    elif post.kind == "dynamic":
                        is_open = False
            item.posts = kept

    def _shared_texts(
        self, unit: Unit, first: list[music.Element], second: list[music.Element]
    ) -> None:
        """Remove a text mark of voice two that voice one has at the same moment."""
        texts: dict[Fraction, set[str]] = {}
        for position, item in _timeline(first, unit.start)[0]:
            texts.setdefault(position, set()).update(
                post.text for post in item.posts if _is_text(post)
            )
        for position, item in _timeline(second, unit.start)[0]:
            item.posts = [
                post
                for post in item.posts
                if not (_is_text(post) and post.text in texts.get(position, set()))
            ]

    @staticmethod
    def _sides(first: list[music.Element], second: list[music.Element]) -> None:
        """Put each text mark on the side of its voice."""
        for voice, line in ((1, first), (2, second)):
            for item in timed(line):
                item.posts = [_flip(post, voice) if _is_text(post) else post for post in item.posts]


def _is_text(post: music.Post) -> bool:
    return post.kind == "text" or (post.kind == "command" and post.value in techniques.TECHNIQUES)


def shared_staff(
    work: Work, first_id: str, second_id: str, system_bars: frozenset[int] = frozenset()
) -> SharedStaff:
    """Return the two voices of the staff that two players share.

    `system_bars` are the bars at which a system of the score starts: the
    label of the players ("1.", "2.", "a 2") is given again there.
    """
    units, extras = pair_units(work, first_id, second_id)
    chunks: list[tuple[list[music.Element], list[music.Element]]] = [
        ([], []) for _ in work.chunks[first_id]
    ]
    writer = _Writer(system_bars)
    for unit in units:
        one, two = chunks[unit.chunk]
        writer.write(unit, work.structure.bar_at(unit.start).number, one, two)
    return SharedStaff(first_id, second_id, chunks, extras, units)
