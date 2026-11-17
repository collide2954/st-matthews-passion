"""Stop each hairpin at a silence.

A player cannot change the loudness of a rest. Thus a hairpin (a crescendo or
a diminuendo mark) must be below sounding notes only. The owner of the project
found hairpins that went through bars of rest. They came from two faults:

- A hairpin had no end. The engraving program then continues it to the
  subsequent dynamic mark of the player, which can be many bars later.
- One hairpin was for a passage of some entries with long rests between them.

This module changes the music of one player when a section is complete:

1. A hairpin stops at the start of a silence of `LONG_REST` or more.
2. If the hairpin had a dynamic mark at its end, the entries after the silence
   keep the change of loudness. Each entry gets the dynamic mark for its
   position between the start and the end of the old hairpin (for example
   p, mp, mf, and then the f of the end). An entry of two or more notes gets a
   new hairpin also.
3. A hairpin that starts on a rest is removed.

For a player with two staves (piano, harp, celesta), a rest in one hand is
not a silence while the other hand plays.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from . import music

LONG_REST = Fraction(2)  # quarter notes


@dataclass
class State:
    """The dynamic marks of one player at the end of the music that the code read."""

    mark: str = "mf"  # the dynamic mark in effect
    direction: str = ""  # "<" or ">": a hairpin is open
    start: Fraction = Fraction(0)  # the position of the start of the open hairpin
    start_mark: str = "mf"  # the dynamic mark in effect at that position
    silence: Fraction = Fraction(0)  # the rests after the last note, while the hairpin is open
    first_rest: music.Rest | None = None  # the first rest of that silence


@dataclass
class _Event:
    """A note or a rest with its position. `element` is None for music in two voices."""

    element: music.Note | music.Rest | None
    start: Fraction
    duration: Fraction
    note: bool


def _events(
    elements: list[music.Element], position: Fraction, scale: Fraction, found: list[_Event]
) -> Fraction:
    """Collect the notes and the rests of the elements in time sequence. Return the end."""
    for element in elements:
        if isinstance(element, music.Note | music.Rest):
            duration = element.duration * scale
            found.append(_Event(element, position, duration, isinstance(element, music.Note)))
            position += duration
        elif isinstance(element, music.Group):
            if element.kind == "grace":
                continue
            if element.kind == "parallel":
                # Two voices on one staff: the code does not change their marks.
                duration = music.length(element) * scale
                found.append(_Event(None, position, duration, True))
                position += duration
            elif element.kind in ("unfold", "tremolo"):
                for _ in range(element.count):
                    position = _events(element.children, position, scale, found)
            else:
                position = _events(element.children, position, scale * element.ratio, found)
    return position


def sounding(elements: list[music.Element], begin: Fraction) -> list[tuple[Fraction, Fraction]]:
    """Return the start and the end of each note of the elements."""
    found: list[_Event] = []
    _events(elements, begin, Fraction(1), found)
    return [(event.start, event.start + event.duration) for event in found if event.note]


def _marks(event: _Event) -> tuple[list[str], bool, str]:
    """Return the dynamic marks of an event, if a hairpin ends on it, and a hairpin start."""
    posts = event.element.posts if event.element is not None else []
    marks = [post.value for post in posts if post.kind == "dynamic"]
    stops = any(post.kind == "hairpin" and post.value == "!" for post in posts)
    starts = next(
        (post.value for post in posts if post.kind == "hairpin" and post.value in "<>"), ""
    )
    return marks, stops, starts


def _covered(spans: list[tuple[Fraction, Fraction]], start: Fraction, end: Fraction) -> bool:
    """Return true if a note of the other hand sounds in the time from start to end."""
    return any(first < end and last > start for first, last in spans)


def stop_at_rests(
    elements: list[music.Element],
    begin: Fraction,
    state: State,
    other_hand: list[tuple[Fraction, Fraction]] | None = None,
) -> None:
    """Change the music of one player for one section (see the text of the module).

    `begin` is the position of the first element in the work. `state` has the
    marks of the player from the sections before; the function changes it.
    `other_hand` has the notes of the other staff of a player with two staves.
    """
    spans = other_hand or []
    events: list[_Event] = []
    _events(elements, begin, Fraction(1), events)
    for index, event in enumerate(events):
        marks, stops, starts = _marks(event)
        if marks or stops:
            state.direction, state.first_rest, state.silence = "", None, Fraction(0)
        for mark in marks:
            if mark in music.DYNAMICS:
                state.mark = mark
        if event.note:
            state.first_rest, state.silence = None, Fraction(0)
            if starts:
                state.direction, state.start, state.start_mark = starts, event.start, state.mark
            continue
        rest = event.element
        if starts:
            # A hairpin cannot start on a rest.
            rest.posts[:] = [
                post for post in rest.posts if not (post.kind == "hairpin" and post.value in "<>")
            ]
        if not state.direction:
            continue
        if _covered(spans, event.start, event.start + event.duration):
            state.first_rest, state.silence = None, Fraction(0)
            continue
        if state.first_rest is None:
            state.first_rest = rest
        state.silence += event.duration
        if state.silence >= LONG_REST:
            _cut(state, events, index, spans)


def _cut(
    state: State, events: list[_Event], index: int, spans: list[tuple[Fraction, Fraction]]
) -> None:
    """Stop the open hairpin at the start of the silence, and mark the entries after it."""
    rest = state.first_rest
    if not any(post.kind == "hairpin" and post.value == "!" for post in rest.posts):
        rest.posts.append(music.Post("hairpin", "\\!", "!"))
    direction, begin, first_mark = state.direction, state.start, state.start_mark
    state.direction, state.first_rest, state.silence = "", None, Fraction(0)

    # The entries after the silence, to the dynamic mark at which the hairpin ended.
    entries: list[list[_Event]] = [[]]
    goal: tuple[Fraction, str] | None = None
    silence = Fraction(0)
    for event in events[index + 1 :]:
        marks, stops, starts = _marks(event)
        if marks or stops:
            named = [mark for mark in marks if mark in music.DYNAMICS]
            if named and event.note:
                goal = (event.start, named[0])
            break
        if starts or event.element is None:
            break  # a new hairpin of the composer, or music in two voices
        if event.note:
            if silence >= LONG_REST and entries[-1]:
                entries.append([])
            entries[-1].append(event)
            silence = Fraction(0)
        elif not _covered(spans, event.start, event.start + event.duration):
            silence += event.duration
    if goal is None or first_mark not in music.DYNAMICS:
        return
    first_level, last_level = music.DYNAMICS.index(first_mark), music.DYNAMICS.index(goal[1])
    if first_level == last_level or goal[0] <= begin:
        return
    step = 1 if last_level > first_level else -1
    shown = first_level
    for entry in entries:
        if not entry:
            continue
        note = entry[0].element
        share = (entry[0].start - begin) / (goal[0] - begin)
        level = round(first_level + float(share) * (last_level - first_level))
        # The mark of the end stays new: an entry before it is one mark below it or less.
        level = min(level, last_level - 1) if step > 0 else max(level, last_level + 1)
        if (level - shown) * step > 0:
            mark = music.DYNAMICS[level]
            note.posts.insert(0, music.Post("dynamic", f"\\{mark}", mark))
            shown = level
        if len(entry) >= 2:
            note.posts.append(music.Post("hairpin", f"\\{direction}", direction))


def over_rests(
    elements: list[music.Element],
    begin: Fraction = Fraction(0),
    other_hand: list[tuple[Fraction, Fraction]] | None = None,
) -> list[Fraction]:
    """Return the start of each hairpin that goes over a silence of `LONG_REST` or more.

    The function does not change the music. The check of the work uses it.
    """
    spans = other_hand or []
    events: list[_Event] = []
    _events(elements, begin, Fraction(1), events)
    found: list[Fraction] = []
    start: Fraction | None = None
    silence = Fraction(0)
    for event in events:
        marks, stops, starts = _marks(event)
        if marks or stops:
            start = None
        if event.note:
            silence = Fraction(0)
            if starts:
                start = event.start
        elif starts:
            found.append(event.start)  # a hairpin that starts on a rest
        elif start is not None and not _covered(spans, event.start, event.start + event.duration):
            silence += event.duration
            if silence >= LONG_REST:
                found.append(start)
                start = None
    return found
