"""Change music text with code: transposition, inversion, repetition, and voicing.

These tools do the "developing variation" of the work. The composer writes a
theme one time. The tools make its other forms: at a different pitch, upside
down, or for a different instrument. Other tools divide a chord progression
between players, and make a figure from each chord.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import replace
from fractions import Fraction

from ..notation import music
from ..notation.pitch import NAMES, STEP_SEMITONES, Interval, Pitch
from ..notation.work import Section


def _map_pitches(elements: list[music.Element], change) -> list[music.Element]:
    result: list[music.Element] = []
    for element in elements:
        if isinstance(element, music.Note):
            pitches = [replace(p, pitch=change(p.pitch)) for p in element.pitches]
            result.append(replace(element, pitches=pitches))
        elif isinstance(element, music.Group):
            result.append(replace(element, children=_map_pitches(element.children, change)))
        else:
            result.append(element)
    return result


def _apply(text: str, change) -> str:
    parsed = music.parse(text)
    return music.body_to_lilypond(music.Group("sequence", _map_pitches(parsed.children, change)))


def tr(text: str, semitones: int, steps: int | None = None) -> str:
    """Return the music moved by a number of semitones.

    `steps` is the number of scale steps of the interval. If it is not given,
    the function selects the usual interval for the number of semitones.
    """
    if semitones == 0 and not steps:
        return text
    interval = Interval(round(semitones * 7 / 12) if steps is None else steps, semitones)
    return _apply(text, lambda pitch: pitch.transposed(interval).simplified())


def octave(text: str, count: int) -> str:
    """Return the music moved by a number of octaves (negative = down)."""
    return tr(text, 12 * count, 7 * count)


def invert(text: str, axis: str) -> str:
    """Return the mirror of the music around the pitch `axis`.

    A step up becomes the same step down. This is the method of the mirror
    form of the walking theme.
    """
    centre = Pitch.parse(axis)

    def mirror(pitch: Pitch) -> Pitch:
        index = 2 * (centre.step + 7 * centre.octave) - (pitch.step + 7 * pitch.octave)
        octave_number, step = divmod(index, 7)
        natural = 12 * (octave_number + 1) + STEP_SEMITONES[step]
        target = 2 * centre.midi - pitch.midi
        return Pitch(
            step, Fraction(target - natural).limit_denominator(2), octave_number
        ).simplified()

    return _apply(text, mirror)


def run(scale: str, start: str, count: int, value: int = 16, *, down: bool = False) -> str:
    """Return a fast line through the notes of a scale, one step for each note.

    `scale` has the note names of the scale in one octave, for example
    "d e fis gis a b cis". `start` is the first note, with its octave marks:
    it must be a note of the scale. `value` is the note value (16 = sixteenth
    notes). The line goes up, or down if `down` is true.
    """
    degrees = sorted(NAMES[name] for name in scale.split())
    first_pitch = Pitch.parse(start)
    places = [
        index
        for index, (step, alter) in enumerate(degrees)
        if (step, alter) == (first_pitch.step, first_pitch.alter)
    ]
    if not places:
        raise ValueError(f"the note {start} is not in the scale {scale}")
    index, octave_number = places[0], first_pitch.octave
    notes = []
    for number in range(count):
        step, alter = degrees[index]
        name = Pitch(step, alter, octave_number).name
        notes.append(name + (str(value) if number == 0 else ""))
        index += -1 if down else 1
        if index >= len(degrees):
            index, octave_number = 0, octave_number + 1
        elif index < 0:
            index, octave_number = len(degrees) - 1, octave_number - 1
    return " ".join(notes)


def sweep(
    scale: str, start: str, sizes: Sequence[int], *, down: bool = False
) -> list[tuple[str, int, int]]:
    """Return a fast, free line through a scale as groups: one group for each eighth note.

    `sizes` gives the number of notes of each group. A group of 4 notes is
    thirty-second notes. A group of a different size is a tuplet in the time
    of 4 thirty-second notes. Sizes that become larger make a written
    acceleration: the line does not sound as a metric figure.

    Each item of the result has the text of a group, and its lowest note and
    its highest note (MIDI numbers). With these, a composer can give each
    group to one hand of a keyboard player.
    """
    names = run(scale, start, sum(sizes), 32, down=down).split()
    names[0] = names[0][:-2]  # the first note of `run` has the note value
    groups = []
    position = 0
    for size in sizes:
        chosen = names[position : position + size]
        position += size
        keys = [round(Pitch.parse(name).midi) for name in chosen]
        group = " ".join([chosen[0] + "32", *chosen[1:]])
        if size != 4:
            group = rf"\tuplet {size}/4 {{ {group} }}"
        groups.append((group, min(keys), max(keys)))
    return groups


def times(text: str, count: int) -> str:
    """Return the music repeated a number of times."""
    return " ".join([text.strip()] * count)


def rests(numerator: int, denominator: int, bars: int = 1) -> str:
    """Return full-bar rests for a number of bars of one metre."""
    return f"R1*{numerator * bars}/{denominator} |"


def _first_event(elements: list[music.Element]) -> music.Note | music.Rest | None:
    for element in elements:
        if isinstance(element, music.Note | music.Rest):
            return element
        if isinstance(element, music.Group) and element.kind != "parallel":
            found = _first_event(element.children)
            if found:
                return found
    return None


def _first_note(elements: list[music.Element]) -> music.Note | None:
    for element in elements:
        if isinstance(element, music.Note):
            return element
        if isinstance(element, music.Group) and element.kind != "parallel":
            found = _first_note(element.children)
            if found:
                return found
    return None


def _posts(marks: str) -> list[music.Post]:
    """Parse marks, for example `\\pp\\senzasord`, into events."""
    if not marks.strip():
        return []
    return music.parse("c4" + marks).children[0].posts


def first(text: str, marks: str, *, note: bool = False) -> str:
    """Return the music with marks added to its first note or rest.

    If `note` is true, the marks go on the first note, not on a rest before it.
    """
    parsed = music.parse(text)
    target = _first_note(parsed.children) if note else _first_event(parsed.children)
    if target is None:
        raise ValueError("the music has no note for the marks")
    target.posts[:0] = _posts(marks)
    return music.body_to_lilypond(parsed)


def _strip(elements: list[music.Element], kinds: frozenset[str]) -> None:
    for element in elements:
        if isinstance(element, music.Note | music.Rest):
            element.posts[:] = [
                post
                for post in element.posts
                if not (
                    post.kind in kinds
                    or (post.kind == "command" and "technique" in kinds
                        and post.value in music.TECHNIQUE_NAMES)
                )
            ]  # fmt: skip
        elif isinstance(element, music.Group):
            _strip(element.children, kinds)


def plain(text: str, *kinds: str) -> str:
    """Return the music without its dynamic marks and hairpins.

    Other kinds of marks can be given: "slur", "articulation", "text",
    "technique", "tie", "phrasing".
    """
    parsed = music.parse(text)
    _strip(parsed.children, frozenset(kinds or ("dynamic", "hairpin")))
    return music.body_to_lilypond(parsed)


def dyn(text: str, marks: str) -> str:
    """Return the music with new dynamic marks on its first note, and no other dynamics."""
    return first(plain(text), marks, note=True)


def lines(text: str) -> list[str]:
    """Divide a chord progression into its voices, from the lowest to the highest.

    Each chord must have the same number of notes. A single note or a rest
    goes to all voices. Each voice keeps the marks of the chords.
    """
    parsed = music.parse(text)
    sizes = {len(e.pitches) for e in _notes(parsed.children) if len(e.pitches) > 1}
    if len(sizes) > 1:
        raise ValueError(f"the chords have different numbers of notes: {sorted(sizes)}")
    count = sizes.pop() if sizes else 1
    result = []
    for index in range(count):
        voice = _pick(parsed.children, index)
        result.append(music.body_to_lilypond(music.Group("sequence", voice)))
    return result


def _notes(elements: list[music.Element]) -> list[music.Note]:
    found: list[music.Note] = []
    for element in elements:
        if isinstance(element, music.Note):
            found.append(element)
        elif isinstance(element, music.Group):
            found.extend(_notes(element.children))
    return found


def _pick(elements: list[music.Element], index: int) -> list[music.Element]:
    result: list[music.Element] = []
    for element in elements:
        if isinstance(element, music.Note):
            pitch = element.pitches[index if len(element.pitches) > 1 else 0]
            result.append(replace(element, pitches=[pitch], chord=False))
        elif isinstance(element, music.Group):
            result.append(replace(element, children=_pick(element.children, index)))
        else:
            result.append(element)
    return result


_PLACEHOLDER = re.compile(r"(?<![A-Za-z\\\"])([A-HX])([',]*)(?![A-Za-z\"])")


def _shifted(pitch: Pitch, marks: str) -> str:
    moved = replace(pitch, octave=pitch.octave + marks.count("'") - marks.count(","))
    return moved.name


def fill(chords: str, pattern: str | dict[int, str]) -> str:
    """Make a figure from each chord of a progression.

    In the pattern, the letters A to H are the notes of the chord from the
    lowest to the highest, and X is the full chord. A `'` or a `,` after a
    letter moves the note by an octave. The marks of each chord go on the
    first note of its figure. Rests and bar checks of the progression stay.

    The pattern can be a table: the length of the chord in quarter notes
    selects the pattern. Thus a progression with long and short chords can
    have a figure for each length.
    """
    parsed = music.parse(chords)
    parts: list[str] = []
    patterns = pattern
    for element in parsed.children:
        if isinstance(element, music.Note):
            pitches = [p.pitch for p in element.pitches]
            if isinstance(patterns, dict):
                if element.duration not in patterns:
                    raise ValueError(f"no pattern for a chord of {element.duration} quarter notes")
                pattern = patterns[int(element.duration)]

            def substitute(match: re.Match[str], pitches: list[Pitch] = pitches) -> str:
                letter, marks = match.group(1), match.group(2)
                if letter == "X":
                    names = " ".join(_shifted(pitch, marks) for pitch in pitches)
                    return f"<{names}>"
                number = ord(letter) - ord("A")
                if number >= len(pitches):
                    raise ValueError(f"the chord has no note {letter}")
                return _shifted(pitches[number], marks)

            figure = music.parse(_PLACEHOLDER.sub(substitute, pattern))
            marks = [p for p in element.posts if p.kind in ("dynamic", "hairpin", "command")]
            target = _first_note(figure.children)
            if marks and target is not None:
                target.posts[:0] = marks
            parts.append(music.body_to_lilypond(figure))
        elif isinstance(element, music.Rest | music.BarCheck):
            parts.append(music.body_to_lilypond(music.Group("sequence", [element])))
        else:
            raise ValueError("fill() accepts only chords, rests, and bar checks")
    return " ".join(parts)


def put(section: Section, players: str, text: str, marks: str = "") -> None:
    """Write the same music for some players.

    `players` is a list of player identifiers with spaces between them. A
    number after a colon moves the music of that player by octaves, for
    example "fl1:1 ob1 bn1:-1". `marks` go on the first note of each player.
    """
    for entry in players.split():
        player, _, shift = entry.partition(":")
        music_text = octave(text, int(shift)) if shift else text
        if marks:
            music_text = first(music_text, marks, note=True)
        section.write(player, music_text)


def spread(section: Section, players: str, chords: str, marks: str = "") -> None:
    """Divide a chord progression between players: the first player gets the lowest voice."""
    names = players.split()
    voices = lines(chords)
    if len(voices) != len(names):
        raise ValueError(f"{len(voices)} voices for {len(names)} players")
    for entry, voice in zip(names, voices, strict=True):
        put(section, entry, voice, marks)


def _doubled(elements: list[music.Element], shift: int) -> list[music.Element]:
    result: list[music.Element] = []
    for element in elements:
        if isinstance(element, music.Note):
            extra = [
                replace(p, pitch=replace(p.pitch, octave=p.pitch.octave + shift), posts=[])
                for p in element.pitches
            ]
            pitches = extra + element.pitches if shift < 0 else element.pitches + extra
            result.append(replace(element, pitches=pitches, chord=True))
        elif isinstance(element, music.Group):
            result.append(replace(element, children=_doubled(element.children, shift)))
        else:
            result.append(element)
    return result


def double(text: str, shift: int = -1) -> str:
    """Return the music in octaves: each note gets a second note `shift` octaves from it."""
    parsed = music.parse(text)
    return music.body_to_lilypond(music.Group("sequence", _doubled(parsed.children, shift)))


_DURATION_TEXT = {
    Fraction(6): "1.", Fraction(4): "1", Fraction(3): "2.", Fraction(2): "2",
    Fraction(3, 2): "4.", Fraction(1): "4", Fraction(3, 4): "8.", Fraction(1, 2): "8",
}  # fmt: skip


def _swell(bar: str, start: str, end: str) -> str:
    """Return one bar with marks on its first note and on its last note.

    If the bar has only one note, the note becomes two tied notes: thus the
    second mark has a note.
    """
    parsed = music.parse(bar)
    notes = [element for element in parsed.children if isinstance(element, music.Note)]
    if not notes or len(notes) != len(parsed.children):
        raise ValueError(f"a bar of a colour chain must have only notes and chords: {bar!r}")
    if len(notes) == 1 and end:
        note = notes[0]
        half = _DURATION_TEXT[note.duration / 2]
        head = replace(note, duration=note.duration / 2, duration_text=half, posts=[*note.posts])
        tail = replace(note, duration=note.duration / 2, duration_text=half, posts=[])
        head.posts.extend(_posts("~"))
        notes = [head, tail]
        parsed = music.Group("sequence", notes)
    notes[0].posts[:0] = _posts(start)
    if end:
        notes[-1].posts[:0] = _posts(end)
    return music.body_to_lilypond(parsed)


def relay(
    chords: str, groups: int, level: str = r"\p", soft: str = r"\ppp", rest: str = "R1"
) -> list[str]:
    """Divide a chord progression between groups of players that overlap: a chain of colours.

    A new group starts in each bar. A group plays for two bars: it becomes
    louder in its first bar and softer in its second bar. Thus each chord
    has two colours at the same time: one colour comes and one colour goes.
    This is the idea of "Farben" (Schoenberg, Five Pieces op. 16 no. 3).

    Return the music of each group. `rest` is the full-bar rest of the metre.
    """
    parts = [bar.strip() for bar in chords.split("|") if bar.strip()]
    result: list[list[str]] = [[] for _ in range(groups)]
    for index, bar in enumerate(parts):
        last = index == len(parts) - 1
        for group in range(groups):
            if group == index % groups:
                # The group starts. In the last bar it also closes the crescendo.
                result[group].append(_swell(bar, soft + r"\<", level if last else ""))
            elif index > 0 and group == (index - 1) % groups:
                result[group].append(_swell(bar, level + r"\>", soft))
            else:
                result[group].append(rest)
    return [" | ".join(bars_of_group) + " |" for bars_of_group in result]


def stack(*voices: str) -> str:
    """Return chords from lines that have the same rhythm. The first line is the lowest voice."""
    parsed = [music.parse(voice).children for voice in voices]
    result: list[music.Element] = []
    for elements in zip(*parsed, strict=True):
        head = elements[0]
        if isinstance(head, music.Note):
            pitches = [pitch for element in elements for pitch in element.pitches]
            result.append(replace(head, pitches=pitches, chord=True))
        else:
            result.append(head)
    return music.body_to_lilypond(music.Group("sequence", result))


def figure(tokens: Sequence[tuple[str, str] | None], grouping: tuple[int, ...] = (2, 2, 3)) -> str:
    """Return one bar of eighth notes.

    `tokens` has one item for each eighth note of the bar: a note (the text
    of its pitch and its marks) or None (a rest). Adjacent rests in one
    beat group become one rest. `grouping` gives the beat groups of the bar.
    """
    if sum(grouping) != len(tokens):
        raise ValueError(f"{len(tokens)} eighth notes for the grouping {grouping}")
    if all(token is None for token in tokens):
        return f"R1*{len(tokens)}/8 |"
    parts: list[str] = []
    position = 0
    for size in grouping:
        group = tokens[position : position + size]
        index = 0
        while index < size:
            token = group[index]
            if token is None:
                run = 1
                while index + run < size and group[index + run] is None:
                    run += 1
                parts.append({1: "r8", 2: "r4", 3: "r4."}[run])
                index += run
            else:
                parts.append(f"{token[0]}8{token[1]}")
                index += 1
        position += size
    return " ".join(parts) + " |"


def bars(count: int, rest: str, entries: dict[int, str]) -> str:
    """Return `count` bars: the music of `entries` (bar number: music), and rests.

    `rest` is the full-bar rest of the metre, for example "R1*7/8 |".
    """
    return " ".join(entries.get(number, rest) for number in range(1, count + 1))


class Block:
    """Collect the music of a section phrase by phrase, then write it.

    A section has one or more phrases. For each phrase, the composer gives
    the music of some players. A player with no music in a phrase gets the
    rest of that phrase.
    """

    def __init__(self, section: Section, *phrase_rests: str) -> None:
        self.section = section
        self.phrase_rests = phrase_rests
        self.music: dict[str, dict[int, str]] = {}

    def add(self, players: str, phrase: int, text: str, marks: str = "") -> None:
        """Give the music of some players for one phrase (the first phrase is 1).

        `players` and `marks` are the same as for `put()`.
        """
        if not 1 <= phrase <= len(self.phrase_rests):
            raise ValueError(f"the section has no phrase {phrase}")
        for entry in players.split():
            player, _, shift = entry.partition(":")
            music_text = octave(text, int(shift)) if shift else text
            if marks:
                music_text = first(music_text, marks, note=True)
            phrases = self.music.setdefault(player, {})
            if phrase in phrases:
                raise ValueError(f"{player}: music written two times for phrase {phrase}")
            phrases[phrase] = music_text

    def spread(self, players: str, phrase: int, chords: str, marks: str = "") -> None:
        """Divide a chord progression between players: the first player gets the lowest voice."""
        names = players.split()
        voices = lines(chords)
        if len(voices) != len(names):
            raise ValueError(f"{len(voices)} voices for {len(names)} players")
        for entry, voice in zip(names, voices, strict=True):
            self.add(entry, phrase, voice, marks)

    def start(self, player: str, prefix: str) -> None:
        """Put a command (for example a change of instrument) before the music of a player."""
        phrases = self.music.setdefault(player, {})
        phrases[1] = prefix + " " + phrases.get(1, self.phrase_rests[0])

    def close(self) -> None:
        """Write the music of all players and close the section."""
        for player, phrases in self.music.items():
            text = " ".join(
                phrases.get(number, rest) for number, rest in enumerate(self.phrase_rests, start=1)
            )
            self.section.write(player, text)
        self.section.close()


_REST_NAMES = {
    Fraction(4): "1",
    Fraction(2): "2",
    Fraction(1): "4",
    Fraction(1, 2): "8",
    Fraction(1, 4): "16",
    Fraction(1, 8): "32",
}


def _rests_between(
    start: Fraction, end: Fraction, bar: Fraction, beat: Fraction, metre: str
) -> str:
    """Return rests from `start` to `end` (quarter notes). Each bar ends with a bar check."""
    parts: list[str] = []
    position = start
    while position < end:
        in_bar = position % bar
        if in_bar == 0 and end - position >= bar:
            count = (end - position) // bar
            parts.append(f"R1*{metre}*{count} |" if count > 1 else f"R1*{metre} |")
            position += count * bar
            continue
        bar_end = position - in_bar + bar
        limit = min(end, bar_end)
        for value in _REST_NAMES:
            fits = in_bar % value == 0 and position + value <= limit
            # A rest longer than one beat starts on a beat.
            if fits and (value <= beat or in_bar % beat == 0):
                parts.append(f"r{_REST_NAMES[value]}")
                position += value
                break
        else:
            raise ValueError(f"no rest fits at {position} quarter notes")
        if position == bar_end:
            parts.append("|")
    return " ".join(parts)


def scatter(
    count: int, numerator: int, denominator: int, events: dict[tuple[int, float], str]
) -> str:
    """Return `count` bars with short figures at the given places, and rests between them.

    A key of `events` is (bar, beat). The bar is the bar number in the
    section (the first bar is 1). The beat is in quarter notes: 1 is the
    start of the bar, 1.5 is one eighth note later. The first note of each
    figure must have a duration.
    """
    bar = Fraction(4 * numerator, denominator)
    beat = Fraction(4, denominator)
    metre = f"{numerator}/{denominator}"
    total = count * bar
    placed = sorted(
        ((number - 1) * bar + Fraction(position - 1).limit_denominator(8), text)
        for (number, position), text in events.items()
    )
    parts: list[str] = []
    cursor = Fraction(0)
    for start, text in placed:
        if start < cursor:
            raise ValueError(f"two figures at the same time ({float(start)} quarter notes)")
        parts.append(_rests_between(cursor, start, bar, beat, metre))
        parts.append(text.strip())
        cursor = start + music.length(music.parse(text))
        if cursor % bar == 0 and not text.strip().endswith("|"):
            parts.append("|")
    if cursor > total:
        raise ValueError("the last figure is longer than the section")
    parts.append(_rests_between(cursor, total, bar, beat, metre))
    return " ".join(part for part in parts if part)
