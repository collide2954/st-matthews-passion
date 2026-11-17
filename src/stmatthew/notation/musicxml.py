"""Write the work as a MusicXML file, for a playback program.

MuseScore reads this file and plays it with its sample libraries. The file
is for the sound only: it is not the printed score. Thus:

- All parts are at sounding pitch.
- Each instrument of a player is one part. A player who changes the
  instrument has two or more parts.
- The tempo is given at each bar line, and at each quarter note where the
  tempo changes gradually. Thus the time of each bar is the same as in the
  tempo plan of the work.
- Rests are not written: the reader fills the empty time.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from fractions import Fraction
from xml.sax.saxutils import escape

from . import music, playback
from .techniques import TECHNIQUES
from .work import Work

DIVISIONS = 6720  # parts of a quarter note: 64th notes, triplets, quintuplets, septuplets

# Instrument of the work: the name of the part and the MusicXML sound identifier.
SOUNDS = {
    "piccolo": ("Piccolo", "wind.flutes.piccolo"),
    "flute": ("Flute", "wind.flutes.flute"),
    "alto flute": ("Alto Flute", "wind.flutes.flute.alto"),
    "oboe": ("Oboe", "wind.reed.oboe"),
    "English horn": ("English Horn", "wind.reed.english-horn"),
    "clarinet in E-flat": ("E♭ Clarinet", "wind.reed.clarinet.eflat"),
    "clarinet in B-flat": ("B♭ Clarinet", "wind.reed.clarinet.bflat"),
    "bass clarinet": ("Bass Clarinet", "wind.reed.clarinet.bass"),
    # Muse Sounds have no contrabass clarinet: the contrabassoon has the same range.
    "contrabass clarinet": ("Contrabassoon", "wind.reed.contrabassoon"),
    "bassoon": ("Bassoon", "wind.reed.bassoon"),
    "contrabassoon": ("Contrabassoon", "wind.reed.contrabassoon"),
    "horn in F": ("Horn in F", "brass.french-horn"),
    "trumpet in C": ("C Trumpet", "brass.trumpet.c"),
    "tenor trombone": ("Trombone", "brass.trombone.tenor"),
    "bass trombone": ("Bass Trombone", "brass.trombone.bass"),
    "tuba": ("Tuba", "brass.tuba"),
    "timpani": ("Timpani", "drum.timpani"),
    "vibraphone": ("Vibraphone", "pitched-percussion.vibraphone"),
    "marimba": ("Marimba", "pitched-percussion.marimba"),
    "glockenspiel": ("Glockenspiel", "pitched-percussion.glockenspiel"),
    "crotales": ("Crotales", "metal.crotales"),
    "xylophone": ("Xylophone", "pitched-percussion.xylophone"),
    "tubular bells": ("Tubular Bells", "pitched-percussion.tubular-bells"),
    "tuned gongs": ("Tubular Bells", "pitched-percussion.tubular-bells"),
    "harp": ("Harp", "pluck.harp"),
    "celesta": ("Celesta", "keyboard.celesta"),
    "piano": ("Piano", "keyboard.piano"),
    "violin": ("Violins", "strings.group"),
    "viola": ("Violas", "strings.group"),
    "violoncello": ("Violoncellos", "strings.group"),
    "double bass": ("Contrabasses", "strings.group"),
}

# Unpitched percussion: the name of the part, the sound identifier, and the
# drum of the playback program for each written note (MIDI number). The
# entry `None` is for all other written notes.
UNPITCHED = {
    "bass drum": ("Bass Drum", "drum.bass-drum", {None: 36}),
    "tam-tams": ("Tam-tam", "metal.tamtam", {None: 52}),
    "suspended cymbals": ("Suspended Cymbal", "metal.cymbal.crash", {None: 57}),
    "crash cymbals": ("Hand Cymbals", "metal.cymbal.crash", {None: 57}),
    "wood blocks": ("Wood Blocks", "wood.wood-block", {60: 77, None: 76}),
    "triangle": ("Triangle", "metal.triangle", {None: 81}),
    "snare drum": ("Snare Drum", "drum.snare-drum", {None: 38}),
    # Six drums: the written notes a, b, c', d', e', f' are the drums from low to high.
    "tom-toms": (
        "Concert Toms",
        "drum.tom-tom",
        {57: 41, 59: 43, 60: 45, 62: 47, 64: 48, 65: 50, None: 45},
    ),
    "taiko": ("Taiko", "drum.taiko", {None: 87}),
}

# One player of a string section alone.
SOLO_SOUNDS = {
    "violin": ("Violin", "strings.violin"),
    "viola": ("Viola", "strings.viola"),
    "violoncello": ("Violoncello", "strings.cello"),
    "double bass": ("Contrabass", "strings.contrabass"),
}

TYPE_NAMES = {
    Fraction(16): "long",
    Fraction(8): "breve",
    Fraction(4): "whole",
    Fraction(2): "half",
    Fraction(1): "quarter",
    Fraction(1, 2): "eighth",
    Fraction(1, 4): "16th",
    Fraction(1, 8): "32nd",
    Fraction(1, 16): "64th",
}
STEP_LETTERS = "CDEFGAB"
ARTICULATIONS = {
    "staccato": "staccato",
    "accent": "accent",
    "tenuto": "tenuto",
    "marcato": "strong-accent",
    "staccatissimo": "staccatissimo",
    "portato": "detached-legato",
}
DYNAMIC_ELEMENTS = {
    "ppppp", "pppp", "ppp", "pp", "p", "mp", "mf", "f", "ff", "fff", "ffff", "fffff",
    "sf", "sfz", "sffz", "fz", "rfz", "fp", "sfp", "sfpp", "pf",
}  # fmt: skip

# Playing techniques that the playback program knows: the words in the
# file, and the attribute of the `sound` element (if there is one).
TECHNIQUE_WORDS = {
    "pizz": ("pizz.", 'pizzicato="yes"'),
    "arco": ("arco", 'pizzicato="no"'),
    "collegno": ("col legno", ""),
    "sulpont": ("sul pont.", ""),
    "sultasto": ("sul tasto", ""),
    "ord": ("ord.", ""),
    "consord": ("con sord.", ""),
    "senzasord": ("senza sord.", ""),
}


def can_play(instrument: str) -> bool:
    """Return true if the playback program has a sound for the instrument."""
    return instrument in SOUNDS or instrument in UNPITCHED


@dataclass
class _Event:
    """One note of a player, with its place in the work."""

    start: Fraction  # quarter notes from the start of the work
    length: Fraction  # sounding length in quarter notes (0 for a grace note)
    written: Fraction  # written length, before the factor of a tuplet
    ratio: Fraction  # factor of the tuplet (1 = no tuplet)
    note: music.Note
    voice: int
    grace: bool
    instrument: str
    solo: bool
    tuplet: str = ""  # "start" or "stop": the first and the last note of a tuplet
    dynamic: str = ""  # the dynamic mark in effect at the note
    short: bool = False  # the player makes short strokes (spiccato)
    plucked: bool = False  # the player plucks the string (pizzicato)
    taper: Fraction = Fraction(0)  # the length of the end of the note that gets softer
    plain_attack: bool = False  # the note is too long for an accent of the playback program
    play_dynamic: str = ""  # the dynamic mark for the playback program (empty: as written)
    play_way: str = ""  # a different articulation for the playback program (empty: as written)


@dataclass
class _State:
    """The state of a player while the code reads the music."""

    instrument: str
    solo: bool = False
    dynamic: str = ""
    short: bool = False
    plucked: bool = False
    techniques: dict[str, str] = field(default_factory=dict)  # state -> technique name
    # The changes of the sustain pedal: the position, and "start" or "stop".
    pedals: list[tuple[Fraction, str]] = field(default_factory=list)


def _walk(
    elements: list[music.Element],
    position: Fraction,
    scale: Fraction,
    voice: int,
    state: _State,
    events: list[_Event],
    *,
    grace: bool = False,
) -> Fraction:
    for element in elements:
        if isinstance(element, music.Command):
            if element.name == "switch":
                state.instrument = element.arguments[0].strip('"')
                state.solo = False
                state.techniques = {}
        elif isinstance(element, music.Rest):
            _read_marks(element.posts, state)
            _read_pedal(element.posts, position, state)
            position += element.duration * scale
        elif isinstance(element, music.Note):
            _read_marks(element.posts, state)
            _read_pedal(element.posts, position, state)
            length = Fraction(0) if grace else element.duration * scale
            events.append(
                _Event(position, length, element.duration, scale, element, voice, grace,
                       state.instrument, state.solo and state.instrument in SOLO_SOUNDS,
                       dynamic=state.dynamic, short=state.short, plucked=state.plucked)
            )  # fmt: skip
            position += length
        elif isinstance(element, music.Group):
            if element.kind == "grace":
                _walk(element.children, position, scale, voice, state, events, grace=True)
            elif element.kind == "parallel":
                end = position
                for number, child in enumerate(element.children):
                    end = max(end, _walk(child.children, position, scale, number, state, events))
                position = end
            elif element.kind in ("unfold", "tremolo"):
                for _ in range(element.count):
                    position = _walk(element.children, position, scale, voice, state, events)
            elif element.kind == "tuplet":
                first = len(events)
                position = _walk(
                    element.children, position, scale * element.ratio, voice, state, events
                )
                inside = [event for event in events[first:] if not event.grace]
                if inside:
                    inside[0].tuplet = "start"
                    inside[-1].tuplet = "stop"
            else:
                position = _walk(element.children, position, scale, voice, state, events)
    return position


PEDAL_COMMANDS = {"sustainOff": "stop", "sustainOn": "start"}


def _read_pedal(posts: list[music.Post], position: Fraction, state: _State) -> None:
    """Keep the changes of the sustain pedal (the pedal marks of a piano part)."""
    for post in posts:
        if post.kind == "command" and post.value in PEDAL_COMMANDS:
            state.pedals.append((position, PEDAL_COMMANDS[post.value]))


def _read_marks(posts: list[music.Post], state: _State) -> None:
    """Keep the dynamic mark and the techniques in effect."""
    for post in posts:
        if post.kind == "dynamic" and post.value in DYNAMIC_ELEMENTS:
            state.dynamic = post.value
        elif post.kind == "command":
            technique = TECHNIQUES.get(post.value)
            if post.value in ("spicc", "arco", "pizz", "collegno", "ord"):
                # Spiccato and pizzicato stay until a different way to play comes.
                state.short = post.value == "spicc"
                if post.value != "ord":
                    state.plucked = post.value == "pizz"
            if technique and technique.state == "desk":
                state.solo = technique.value == "solo"
            elif technique and technique.state and post.value in TECHNIQUE_WORDS:
                state.techniques[technique.state] = post.value


def _note_type(written: Fraction) -> tuple[str, int]:
    """Return the note value and the number of dots for a written length."""
    for dots in range(3):
        base = written / (2 - Fraction(1, 2**dots))
        if base in TYPE_NAMES:
            return TYPE_NAMES[base], dots
    # A length with no usual note value: the nearest shorter note value.
    for base in sorted(TYPE_NAMES, reverse=True):
        if base <= written:
            return TYPE_NAMES[base], 0
    return "64th", 0


def _pitch_xml(pitch) -> str:
    alter = float(pitch.alter)
    text = f"<step>{STEP_LETTERS[pitch.step]}</step>"
    if alter:
        text += f"<alter>{alter:g}</alter>"
    return f"<pitch>{text}<octave>{pitch.octave}</octave></pitch>"


def _direction(inner: str, sound: str = "") -> str:
    tail = f"<sound {sound}/>" if sound else ""
    return f"<direction><direction-type>{inner}</direction-type>{tail}</direction>"


def _marks_before(event: _Event, hairpin_open: bool) -> tuple[list[str], bool]:
    """Return the directions before a note, and if a hairpin is open after it."""
    result: list[str] = []
    posts = event.note.posts
    dynamics = [p.value for p in posts if p.kind == "dynamic" and p.value in DYNAMIC_ELEMENTS]
    # The mark in effect at the note gets the mark that the playback program must play.
    dynamics = [
        event.play_dynamic if name == event.dynamic and event.play_dynamic else name
        for name in dynamics
    ]
    hairpins = [p.value for p in posts if p.kind == "hairpin"]
    if hairpin_open and (dynamics or hairpins):
        result.append(_direction('<wedge type="stop"/>'))
        hairpin_open = False
    for name in dynamics:
        result.append(_direction(f"<dynamics><{name}/></dynamics>"))
    for value in hairpins:
        if value in "<>":
            kind = "crescendo" if value == "<" else "diminuendo"
            result.append(_direction(f'<wedge type="{kind}"/>'))
            hairpin_open = True
    for post in posts:
        if post.kind == "command" and post.value in TECHNIQUE_WORDS:
            words, sound = TECHNIQUE_WORDS[post.value]
            result.append(_direction(f"<words>{escape(words)}</words>", sound))
    return result, hairpin_open


# All note lengths that have a usual note value, with zero to two dots.
PIECE_LENGTHS = sorted(
    {base * (2 - Fraction(1, 2**dots)) for base in TYPE_NAMES for dots in range(3)}, reverse=True
)


def _pieces(length: Fraction) -> list[Fraction]:
    """Divide a length into lengths that have a usual note value (the longest first)."""
    result = []
    while length > 0:
        piece = next((value for value in PIECE_LENGTHS if value <= length), None)
        if piece is None:
            raise ValueError(f"no note value for the length {length}")
        result.append(piece)
        length -= piece
    return result


def _note_xml(
    event: _Event,
    index: int,
    length: Fraction,
    ties: tuple[bool, bool],
    drum: str = "",
    *,
    marks: bool = True,
    slide: tuple[bool, bool] = (False, False),
) -> str:
    """Return one note of a chord (or a single note) as MusicXML.

    `drum` is the identifier of the drum, for a note of unpitched percussion.
    If `marks` is false, the note is a continuation of a longer note: it has
    only its ties. `slide` tells if a slide to the subsequent note starts at
    this note, and if a slide from the note before stops at this note.
    """
    note = event.note
    pitch = note.pitches[index].pitch
    kinds = {post.kind for post in note.posts}
    commands = {post.value for post in note.posts if post.kind == "command"}
    parts = ["<note>"]
    if event.grace:
        parts.append("<grace/>")
    if index:
        parts.append("<chord/>")
    if drum:
        parts.append(
            "<unpitched><display-step>E</display-step><display-octave>4</display-octave>"
            "</unpitched>"
        )
    else:
        parts.append(_pitch_xml(pitch))
    if not event.grace:
        parts.append(f"<duration>{int(length * DIVISIONS)}</duration>")
    tie_stop, tie_start = ties
    if tie_stop:
        parts.append('<tie type="stop"/>')
    if tie_start:
        parts.append('<tie type="start"/>')
    if drum:
        parts.append(f'<instrument id="{drum}"/>')
    parts.append(f"<voice>{event.voice + 1}</voice>")
    whole = length == event.written * event.ratio or event.grace
    name, dots = _note_type(event.written if whole else length)
    parts.append(f"<type>{name}</type>" + "<dot/>" * dots)
    if event.ratio != 1 and whole:
        parts.append(
            f"<time-modification><actual-notes>{event.ratio.denominator}</actual-notes>"
            f"<normal-notes>{event.ratio.numerator}</normal-notes></time-modification>"
        )
    notations: list[str] = []
    if tie_stop:
        notations.append('<tied type="stop"/>')
    if tie_start:
        notations.append('<tied type="start"/>')
    if index == 0 and marks:
        for post in note.posts:
            if post.kind == "slur":
                kind = "start" if post.value == "(" else "stop"
                notations.append(f'<slur type="{kind}" number="1"/>')
            elif post.kind == "phrasing":
                kind = "start" if post.value == "(" else "stop"
                notations.append(f'<slur type="{kind}" number="2"/>')
        if event.tuplet:
            notations.append(f'<tuplet type="{event.tuplet}"/>')
        names = [post.value for post in note.posts if post.kind == "articulation"]
        names += [name for name in ARTICULATIONS if name in commands]
        if event.plain_attack:
            names = [name for name in names if name not in ACCENT_MARKS]
        # Spiccato: each short note is a short stroke.
        if _is_short_stroke(event) and not (set(names) & set(SHORT_MARKS)):
            names.append("staccato")
        # A different articulation for the playback program (see `playback.py`).
        if event.play_way == "long":
            names = [name for name in names if name not in (*ACCENT_MARKS, *SHORT_MARKS)]
        elif event.play_way == "accent":
            names = [name for name in names if name != "marcato"] + ["accent"]
        articulations = "".join(
            f"<{ARTICULATIONS[name]}/>" for name in dict.fromkeys(names) if name in ARTICULATIONS
        )
        if articulations:
            notations.append(f"<articulations>{articulations}</articulations>")
        if "tremolo" in kinds:
            value = next(post.value for post in note.posts if post.kind == "tremolo")
            strokes = {"8": 1, "16": 2, "32": 3, "64": 4}.get(value, 3)
            notations.append(f'<ornaments><tremolo type="single">{strokes}</tremolo></ornaments>')
        technical = ""
        if "stopped" in commands or "stopped" in names:
            technical += "<stopped/>"
        if "flageolet" in commands:
            technical += "<harmonic/>"
        if technical:
            notations.append(f"<technical>{technical}</technical>")
    if marks and "arpeggio" in commands and len(note.pitches) > 1:
        notations.append("<arpeggiate/>")  # each note of a rolled chord has this mark
    if slide[1]:
        notations.append('<slide type="stop" number="1"/>')
    if slide[0]:
        notations.append('<slide type="start" line-type="solid" number="1"/>')
    if notations:
        parts.append("<notations>" + "".join(notations) + "</notations>")
    parts.append("</note>")
    return "".join(parts)


# Instruments that ring after the stroke, and the time in seconds that the
# sound needs. The playback program stops a note at the end of its written
# length. Thus a note of these instruments gets a longer length in the file:
# to the subsequent note of the voice, but not more than this time.
RING_SECONDS = {
    "harp": 6.0,
    "celesta": 3.0,
    "piano": 5.0,
    "vibraphone": 8.0,
    "glockenspiel": 4.0,
    "crotales": 8.0,
    "tubular bells": 9.0,
    "tuned gongs": 12.0,
    "timpani": 2.5,
    "tam-tams": 20.0,
    "suspended cymbals": 10.0,
    "crash cymbals": 7.0,
    "bass drum": 3.0,
    "triangle": 5.0,
    "taiko": 2.5,
    "tom-toms": 1.5,
}

# The longest note with an accent or a marcato mark that Muse Sounds can play, in
# seconds. A longer note with such a mark stops before its end: the sound of the
# accent has a fixed length. A measurement with a note of 12 s gave: trombone 4.6 s,
# double basses 6.5 s, violins 7.4 s. The other instruments have no limit. The
# values here are a little smaller. A longer note has no such mark in the file.
ACCENT_SECONDS = {"tenor trombone": 3.9, "double bass": 5.5, "violin": 6.3}
ACCENT_MARKS = ("accent", "marcato")
SHORT_MARKS = ("staccato", "staccatissimo")

# The loudest dynamic mark at which the last note of a phrase gets softer at its end.
TAPER_MARKS = {"ppppp", "pppp", "ppp", "pp", "p", "mp", "mf"}
TAPER_LENGTH = Fraction(2)  # shortest note that gets softer at its end (quarter notes)
TAPER_REST = Fraction(1)  # shortest rest after the note (quarter notes)
TAPER_SECONDS = 1.2  # the time at the end of the note in which it gets softer


def _is_short_stroke(event: _Event) -> bool:
    """Return true if the note is a short stroke of the bow (spiccato)."""
    posts = event.note.posts
    return (
        event.short
        and event.written <= 1
        and not any(post.kind in ("tremolo", "slur") for post in posts)
    )


def _way(event: _Event) -> str:
    """Return the way to play of a note, as the table of the measured levels names it."""
    posts = event.note.posts
    commands = {post.value for post in posts if post.kind == "command"}
    names = {post.value for post in posts if post.kind == "articulation"}
    names |= {name for name in ARTICULATIONS if name in commands}
    if event.plain_attack:
        names -= set(ACCENT_MARKS)
    if any(post.kind == "tremolo" for post in posts):
        return "long"
    if "marcato" in names:
        return "marcato"
    if "accent" in names:
        return "accent"
    if names & set(SHORT_MARKS) or _is_short_stroke(event):
        return "staccato"
    if event.plucked:
        return "pizzicato"
    return "long"


def _calibrate(events: list[_Event], levels: playback.Levels | None, brass: bool) -> None:
    """Give each note the dynamic mark and the articulation for the playback program."""
    for event in events:
        if not event.dynamic:
            continue
        way = _way(event)
        mark, new_way = playback.played(levels, event.dynamic, way, brass)
        event.play_dynamic = mark
        event.play_way = new_way if new_way != way else ""


def _shape(events: list[_Event], work: Work) -> None:
    """Make the notes of one part more natural for the playback.

    - A note of an instrument that rings gets the length of its ring.
    - The last long note of a phrase of a wind or string instrument gets
      softer in its last second, as a player does it. A measurement of the
      sound of MuseScore gave a decrease of 5 to 10 dB at mf.
    - A note that is too long for an accent of the playback program (see
      `ACCENT_SECONDS`) gets no accent.
    """
    structure = work.structure
    by_voice: dict[int, list[_Event]] = {}
    for event in events:
        if not event.grace:
            by_voice.setdefault(event.voice, []).append(event)
    for voice_events in by_voice.values():
        for index, event in enumerate(voice_events):
            following = voice_events[index + 1] if index + 1 < len(voice_events) else None
            limit = following.start if following else structure.length
            end = event.start + event.length
            kinds = {post.kind for post in event.note.posts}
            names = {post.value for post in event.note.posts}
            longest = ACCENT_SECONDS.get(event.instrument)
            if longest and names & set(ACCENT_MARKS):
                # The full length of the note, with the notes that are tied to it.
                last, place = event, index
                while place + 1 < len(voice_events) and any(
                    post.kind == "tie" for post in last.note.posts
                ):
                    place += 1
                    last = voice_events[place]
                seconds = structure.seconds(last.start + last.length) - structure.seconds(
                    event.start
                )
                event.plain_attack = seconds > longest
            ring = RING_SECONDS.get(event.instrument)
            dry = bool(names & {"staccato", "staccatissimo", "damp"}) or "tremolo" in kinds
            if ring and event.ratio == 1 and not dry and "tie" not in kinds:
                quarters = Fraction(ring * structure.bpm_at(event.start) / 60.0).limit_denominator(
                    2
                )
                wanted = min(limit, event.start + max(quarters, event.length))
                wanted = Fraction(int(wanted * 2), 2)  # an eighth note is the smallest step
                if wanted > end and ((wanted - event.start) * 16).denominator == 1:
                    event.length = wanted - event.start
            elif (
                ring is None
                and event.instrument not in UNPITCHED
                and event.length >= TAPER_LENGTH
                and limit - end >= TAPER_REST
                and event.dynamic in TAPER_MARKS
                and not event.plucked
                and event.ratio == 1
                and "hairpin" not in kinds
                and "tie" not in kinds
            ):
                # The end of the note: about `TAPER_SECONDS`, in steps of an eighth note,
                # and not more than half of the note.
                quarters = TAPER_SECONDS * structure.bpm_at(event.start) / 60.0
                steps = max(1, round(quarters * 2))
                event.taper = min(Fraction(steps, 2), event.length / 2)


def _tempo_points(work: Work, first: Fraction, last: Fraction) -> dict[Fraction, float]:
    """Return the tempo at each bar line, and at each quarter note of a gradual change.

    Each value is the mean tempo from its point to the subsequent point. Thus
    the time of each point is the same as in the tempo plan of the work.
    """
    structure = work.structure
    points: set[Fraction] = set()
    for bar in structure.bars:
        if first <= bar.start < last:
            points.add(bar.start)
    ordered = structure.tempo_points
    for index, point in enumerate(ordered):
        if first <= point.position < last:
            points.add(point.position)
        if point.glide and index + 1 < len(ordered):
            position = point.position
            while position < ordered[index + 1].position:
                if first <= position < last:
                    points.add(position)
                position += 1
    result: dict[Fraction, float] = {}
    places = sorted(points) + [last]
    for start, end in zip(places[:-1], places[1:], strict=True):
        seconds = structure.seconds(end) - structure.seconds(start)
        result[start] = 60.0 * float(end - start) / seconds
    return result


def score(
    work: Work,
    bars: tuple[int, int] | None = None,
    instruments: set[str] | None = None,
    players: set[str] | None = None,
    levels: dict[str, playback.Levels] | None = None,
) -> tuple[str, list[str]]:
    """Return the MusicXML text of the work, and the names of the parts in it.

    `bars` gives the first and the last bar (default: the full work).
    `instruments` gives the instruments that are in the file (default: all
    instruments that the playback program can play). `players` gives the
    players that are in the file (default: all players). `levels` are the
    measured levels of the playback program (default: the table of
    `playback.py`; an empty table gives the marks of the score).
    """
    if levels is None:
        levels = playback.load()
    structure = work.structure
    first_bar, last_bar = bars or (1, len(structure.bars))
    measures = structure.bars[first_bar - 1 : last_bar]
    begin, end = measures[0].start, measures[-1].end
    tempos = _tempo_points(work, begin, end)

    # The parts: one for each instrument of each player (and one for a solo player).
    parts: dict[tuple[str, str, bool], list[_Event]] = {}
    starts: dict[tuple[str, str, bool], _State] = {}
    # The pedal marks of an instrument with two staves are for its two hands.
    pedals: dict[str, list[tuple[Fraction, str]]] = {}
    for player in work.orchestra.players:
        if players is not None and player.id not in players:
            continue
        state = _State(player.instruments[0])
        events: list[_Event] = []
        _walk(work.music_of(player.id).children, Fraction(0), Fraction(1), 0, state, events)
        pedals.setdefault(player.id.split(".")[0], []).extend(state.pedals)
        running = _State(player.instruments[0])
        for event in events:
            key = (player.id, event.instrument, event.solo)
            wanted = can_play(event.instrument) and (
                instruments is None or event.instrument in instruments
            )
            if event.start < begin:
                _read_marks(event.note.posts, running)
            elif event.start < end and wanted:
                if key not in parts:
                    parts[key] = []
                    starts[key] = _State(
                        event.instrument, event.solo, running.dynamic, dict(running.techniques)
                    )
                parts[key].append(event)
                _read_marks(event.note.posts, running)
            elif event.start < end:
                _read_marks(event.note.posts, running)

    names: list[str] = []
    part_list: list[str] = []
    bodies: list[str] = []
    for number, (key, events) in enumerate(parts.items(), start=1):
        player_id, instrument, solo = key
        drums: dict[float | None, str] = {}
        if instrument in UNPITCHED:
            name, sound, table = UNPITCHED[instrument]
            # One instrument of the part for each drum, as MusicXML specifies it.
            pitches = sorted(set(table.values()))
            instruments_xml = "".join(
                f'<score-instrument id="P{number}-I{pitch}"><instrument-name>{escape(name)}'
                f"</instrument-name><instrument-sound>{sound}</instrument-sound>"
                f"</score-instrument>"
                for pitch in pitches
            ) + "".join(
                f'<midi-instrument id="P{number}-I{pitch}"><midi-channel>10</midi-channel>'
                f"<midi-program>1</midi-program><midi-unpitched>{pitch + 1}</midi-unpitched>"
                f"</midi-instrument>"
                for pitch in pitches
            )
            drums = {written: f"P{number}-I{pitch}" for written, pitch in table.items()}
        else:
            name, sound = (SOLO_SOUNDS if solo else SOUNDS)[instrument]
            tags = "<solo/>" if solo or sound != "strings.group" else "<ensemble/>"
            instruments_xml = (
                f'<score-instrument id="P{number}-I1"><instrument-name>{escape(name)}'
                f"</instrument-name><instrument-sound>{sound}</instrument-sound>{tags}"
                f"</score-instrument>"
            )
        names.append(f"{name} ({player_id})")
        part_list.append(
            f'<score-part id="P{number}"><part-name>{escape(name)}</part-name>'
            f"{instruments_xml}</score-part>"
        )
        _shape(events, work)
        brass = work.orchestra.player(player_id).family == "brass"
        _calibrate(events, levels.get(name), brass)
        marks = _pedal_marks(pedals.get(player_id.split(".")[0], []), begin, end)
        bodies.append(
            _part_xml(
                number, events, measures, tempos if number == 1 else {}, starts[key], drums,
                marks,
            )
        )  # fmt: skip
    text = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
        '"http://www.musicxml.org/dtds/partwise.dtd">\n'
        '<score-partwise version="4.0">\n'
        f"<work><work-title>{escape(work.title)}</work-title></work>\n"
        "<part-list>\n" + "\n".join(part_list) + "\n</part-list>\n" + "\n".join(bodies) + "\n"
        "</score-partwise>\n"
    )
    return text, names


def pedal_changes(work: Work, player_id: str) -> list[tuple[Fraction, str]]:
    """Return the pedal marks of one player: the position, and "start" or "stop"."""
    state = _State(work.orchestra.player(player_id).instruments[0])
    _walk(work.music_of(player_id).children, Fraction(0), Fraction(1), 0, state, [])
    return state.pedals


def _pedal_marks(
    changes: list[tuple[Fraction, str]], begin: Fraction, end: Fraction
) -> list[tuple[Fraction, str]]:
    """Return the changes of the sustain pedal from `begin` to `end`, in time sequence.

    A release comes before a push at the same moment. A release with no push
    before it, and a push while the pedal is down, are not in the result. If
    the pedal is down at `begin`, the result starts with a push at `begin`.
    """
    marks: list[tuple[Fraction, str]] = []
    down = False
    started = False
    for position, kind in sorted(changes, key=lambda change: (change[0], change[1] != "stop")):
        if position >= end:
            break
        if position >= begin and not started:
            started = True
            if down:
                marks.append((begin, "start"))
        if (kind == "start") == down:
            continue  # no change of the state
        down = kind == "start"
        if position >= begin:
            marks.append((position, kind))
    if not started and down:
        marks.append((begin, "start"))
    return marks


def _part_xml(
    number: int, events: list[_Event], measures, tempos, start: _State, drums=None, pedals=()
) -> str:
    lines = [f'<part id="P{number}">']
    clef = (
        "<clef><sign>percussion</sign></clef>"
        if drums
        else "<clef><sign>G</sign><line>2</line></clef>"
    )
    by_voice: dict[int, list[_Event]] = {}
    for event in events:
        by_voice.setdefault(event.voice, []).append(event)
    tied_in: dict[int, set[float]] = {voice: set() for voice in by_voice}
    hairpins: dict[int, bool] = {voice: False for voice in by_voice}
    restate: dict[int, bool] = {voice: False for voice in by_voice}
    sounding: dict[int, str] = {voice: "" for voice in by_voice}  # the mark that plays now
    slides: dict[int, bool] = {voice: False for voice in by_voice}  # a slide is open
    carried: dict[int, tuple[_Event, Fraction] | None] = {voice: None for voice in by_voice}
    cursors = {voice: 0 for voice in by_voice}
    previous = None
    first_note = True

    def write(event: _Event, length: Fraction, *, head: bool, tail: bool, voice: int) -> None:
        """Write a note (or a part of a long note) as one or more tied notes."""
        pieces = (
            [length] if length == event.written * event.ratio or event.grace else _pieces(length)
        )
        written_tie = any(post.kind == "tie" for post in event.note.posts)
        slides_away = not event.grace and any(
            post.kind == "command" and post.value == "glissando" for post in event.note.posts
        )
        for count, piece in enumerate(pieces):
            first_piece = head and count == 0
            last_piece = tail and count == len(pieces) - 1
            # A slide stops at the start of a note, and it starts at the end of a note.
            stop = first_piece and slides[voice] and not event.grace
            start = last_piece and slides_away
            if stop:
                slides[voice] = False
            if start:
                slides[voice] = True
            for pitch_index, note_pitch in enumerate(event.note.pitches):
                midi = note_pitch.pitch.midi
                tie_in = (not first_piece) or midi in tied_in[voice]
                tie_out = (not last_piece) or written_tie
                drum = drums.get(midi, drums[None]) if drums else ""
                top = pitch_index == 0
                lines.append(
                    _note_xml(
                        event, pitch_index, piece, (tie_in, tie_out), drum,
                        marks=first_piece, slide=(start and top, stop and top),
                    )
                )  # fmt: skip
        if tail and not event.grace:
            tied_in[voice] = {p.pitch.midi for p in event.note.pitches} if written_tie else set()

    for bar in measures:
        lines.append(f'<measure number="{bar.number}">')
        metre = (bar.numerator, bar.denominator)
        if previous != metre:
            head = f"<divisions>{DIVISIONS}</divisions><key><fifths>0</fifths></key>"
            lines.append(
                f"<attributes>{head if previous is None else ''}<time><beats>{bar.numerator}"
                f"</beats><beat-type>{bar.denominator}</beat-type></time>"
                + (clef if previous is None else "")
                + "</attributes>"
            )
            previous = metre
        # The tempo points of this bar (only the first part has them).
        moved = Fraction(0)
        for position in sorted(p for p in tempos if bar.start <= p < bar.end):
            offset = position - bar.start
            if offset > moved:
                lines.append(_forward(offset - moved))
                moved = offset
            lines.append(f'<direction><direction-type><words></words></direction-type>'
                         f'<sound tempo="{tempos[position]:.4f}"/></direction>')  # fmt: skip
        if moved:
            lines.append(_backup(moved))
        # The changes of the sustain pedal in this bar. A release comes before a new
        # push at the same moment.
        moved = Fraction(0)
        for position, kind in pedals:
            if bar.start <= position < bar.end:
                offset = position - bar.start
                if offset > moved:
                    lines.append(_forward(offset - moved))
                    moved = offset
                lines.append(_direction(f'<pedal type="{kind}" line="yes"/>'))
        if moved:
            lines.append(_backup(moved))
        bar_length = bar.end - bar.start
        for voice, voice_events in by_voice.items():
            cursor = bar.start
            index = cursors[voice]
            wrote = False
            # A long note from the bar before continues.
            if carried[voice] is not None:
                event, remaining = carried[voice]
                length = min(remaining, bar_length)
                ends = remaining <= bar_length
                write(event, length, head=False, tail=ends, voice=voice)
                carried[voice] = None if ends else (event, remaining - length)
                cursor += length
                wrote = True
            while index < len(voice_events) and voice_events[index].start < bar.end:
                event = voice_events[index]
                index += 1
                if event.start > cursor:
                    lines.append(_forward(event.start - cursor))
                    cursor = event.start
                in_hairpin = hairpins[voice]
                before, hairpins[voice] = _marks_before(event, hairpins[voice])
                has_dynamic = any(
                    p.kind == "dynamic" and p.value in DYNAMIC_ELEMENTS for p in event.note.posts
                )
                mark = event.play_dynamic or event.dynamic
                if has_dynamic:
                    sounding[voice] = mark
                elif mark and (restate[voice] or (mark != sounding[voice] and not in_hairpin)):
                    # The phrase before became softer at its end, or the playback program
                    # needs a different mark for this note: give the dynamic mark.
                    if not first_note or not start.dynamic:
                        before.insert(0, _direction(f"<dynamics><{mark}/></dynamics>"))
                    sounding[voice] = mark
                restate[voice] = False
                if first_note:
                    before = _state_marks(replace(start, dynamic=mark or start.dynamic)) + before
                    sounding[voice] = mark or start.dynamic
                    first_note = False
                lines.extend(before)
                length = min(event.length, bar.end - cursor)
                ends = length == event.length
                taper = event.taper if ends and not hairpins[voice] else Fraction(0)
                if taper:
                    # The note is two tied notes: the second note gets softer.
                    write(event, length - taper, head=True, tail=False, voice=voice)
                    lines.append(_direction('<wedge type="diminuendo"/>'))
                    write(event, taper, head=False, tail=True, voice=voice)
                    lines.append(_direction('<wedge type="stop"/>'))
                    restate[voice] = True
                else:
                    write(event, length, head=True, tail=ends, voice=voice)
                if not event.grace:
                    cursor += length
                    if not ends:
                        carried[voice] = (event, event.length - length)
                wrote = True
            cursors[voice] = index
            if cursor < bar.end and wrote:
                lines.append(_forward(bar.end - cursor))
            if wrote or voice == 0:
                if not wrote:
                    lines.append(
                        f'<note><rest measure="yes"/><duration>{int(bar_length * DIVISIONS)}'
                        f"</duration><voice>1</voice></note>"
                    )
                lines.append(_backup(bar_length))
        if lines[-1].startswith("<backup>"):
            lines.pop()
        lines.append("</measure>")
    lines.append("</part>")
    return "\n".join(lines)


def _state_marks(state: _State) -> list[str]:
    """Return the directions for the state at the first note of an excerpt."""
    result = []
    if state.dynamic:
        result.append(_direction(f"<dynamics><{state.dynamic}/></dynamics>"))
    for name in state.techniques.values():
        words, sound = TECHNIQUE_WORDS[name]
        if name not in ("arco", "ord", "senzasord"):
            result.append(_direction(f"<words>{escape(words)}</words>", sound))
    return result


def _forward(length: Fraction) -> str:
    return f"<forward><duration>{int(length * DIVISIONS)}</duration></forward>"


def _backup(length: Fraction) -> str:
    return f"<backup><duration>{int(length * DIVISIONS)}</duration></backup>"
