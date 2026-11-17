"""Change the written music of a player into performance notes.

A performance note has a start, a duration, a pitch, a loudness, and the
playing state of the player (for example plucked, muted, or with tremolo).
The audio code and the video code read these notes.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from fractions import Fraction

from ..notation import music
from ..notation.techniques import TECHNIQUES
from ..notation.work import Work

# Loudness of each dynamic mark, from 0 (silence) to 1 (the loudest sound).
DYNAMIC_LEVEL = {
    "ppppp": 0.06,
    "pppp": 0.11,
    "ppp": 0.18,
    "pp": 0.27,
    "p": 0.38,
    "mp": 0.49,
    "mf": 0.59,
    "f": 0.71,
    "ff": 0.83,
    "fff": 0.93,
    "ffff": 0.98,
    "fffff": 1.0,
}
HAIRPIN_STEP = 0.12  # change of loudness for a hairpin with no dynamic mark at its end
ACCENT_BOOST = {"sf": 0.2, "sff": 0.28, "sfz": 0.22, "sffz": 0.3, "fz": 0.18, "rfz": 0.15}
SOFT_AFTER_ATTACK = {"fp": "p", "sfp": "p", "sfpp": "pp", "ffp": "p"}

DEFAULT_STATE = {
    "attack": "arco",
    "place": "ordinario",
    "mute": "off",
    "vibrato": "normal",
    "desk": "tutti",
    "tongue": "normal",
    "tone": "normal",
    "ring": "off",
    "mallet": "normal",
    "motor": "off",
}


@dataclass(frozen=True)
class PerfNote:
    """One note as the player plays it. Times are in quarter notes."""

    player: str
    instrument: str
    start: Fraction
    duration: Fraction
    midi: float
    level: float  # loudness at the start of the note, 0 to 1
    level_end: float  # loudness at the end of the note
    accent: float = 0.0  # more loudness on the attack only
    articulations: frozenset[str] = frozenset()
    legato: bool = False  # the note follows the note before it under a slur
    tremolo: bool = False
    trill: bool = False
    harmonic: bool = False
    glissando: bool = False  # a slide from this note to the subsequent note
    fermata: bool = False
    grace: int = 0  # 0 = normal note; n = grace note number n before the main note
    grace_count: int = 0  # number of grace notes in the group
    voice: int = 0  # voice number on the staff (0 = only or upper voice)
    chord_size: int = 1
    state: tuple[tuple[str, str], ...] = ()

    def get(self, key: str) -> str:
        """Return one value of the playing state, for example `get("attack")`."""
        return dict(self.state).get(key, DEFAULT_STATE.get(key, ""))


@dataclass
class _Voice:
    """The running state of one voice while the code reads its music."""

    player: str
    instrument: str
    voice: int = 0
    level: float = DYNAMIC_LEVEL["mf"]
    state: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_STATE))
    slur_depth: int = 0
    slur_has_note: bool = False
    hairpin: tuple[Fraction, float, int] | None = None  # start position, start level, direction
    hairpin_notes: list[int] = field(default_factory=list)  # indexes of notes in the hairpin
    open_ties: dict[float, int] = field(default_factory=dict)  # midi -> index of the open note
    trill_span: bool = False


def perform(work: Work, player_id: str) -> list[PerfNote]:
    """Return the performance notes of one player, in time sequence.

    Many parts of the build ask for the notes of a player. The function keeps
    the result while the music of the player does not change.
    """
    chunks = work.chunks.get(player_id, [])
    # The music of a player changes when a section is added or closed.
    key = (work.revision, len(chunks), id(chunks[-1][1]) if chunks else 0)
    cache: dict = work.__dict__.setdefault("_performed", {})
    if player_id in cache and cache[player_id][0] == key:
        return list(cache[player_id][1])
    first = work.orchestra.player(player_id).instruments[0]
    voice = _Voice(player_id, first)
    notes: list[PerfNote] = []
    _walk(work.music_of(player_id).children, Fraction(0), Fraction(1), voice, notes, grace=False)
    _close_hairpin(voice, notes, voice.level)
    notes.sort(key=lambda n: (n.start, -n.grace, n.midi))
    cache[player_id] = (key, notes)
    return list(notes)


def perform_all(work: Work) -> dict[str, list[PerfNote]]:
    """Return the performance notes of all players."""
    return {player.id: perform(work, player.id) for player in work.orchestra.players}


def _walk(
    elements: list[music.Element],
    position: Fraction,
    scale: Fraction,
    voice: _Voice,
    notes: list[PerfNote],
    *,
    grace: bool,
) -> Fraction:
    index = 0
    while index < len(elements):
        element = elements[index]
        index += 1
        if isinstance(element, music.Command):
            if element.name == "switch":
                voice.instrument = element.arguments[0].strip('"')
                voice.state = dict(DEFAULT_STATE)
        elif isinstance(element, music.Rest):
            _rest(element, voice, notes)
            position += element.duration * scale
            voice.open_ties.clear()
        elif isinstance(element, music.Note):
            _play(element, position, scale, voice, notes, grace_number=0, grace_count=0)
            position += element.duration * scale
        elif isinstance(element, music.Group):
            if element.kind == "grace":
                members = [e for e in element.children if isinstance(e, music.Note)]
                # A dynamic mark on the main note is also for its grace notes.
                following = elements[index] if index < len(elements) else None
                if isinstance(following, music.Note):
                    for post in following.posts:
                        if post.kind == "dynamic" and post.value in DYNAMIC_LEVEL:
                            _close_hairpin(voice, notes, DYNAMIC_LEVEL[post.value])
                            voice.level = DYNAMIC_LEVEL[post.value]
                for number, member in enumerate(members):
                    _play(
                        member,
                        position,
                        scale,
                        voice,
                        notes,
                        grace_number=len(members) - number,
                        grace_count=len(members),
                    )
            elif element.kind == "parallel":
                end = position
                for number, child in enumerate(element.children):
                    branch = replace(
                        voice,
                        voice=number,
                        state=dict(voice.state),
                        open_ties={},
                        hairpin=None,
                        hairpin_notes=[],
                        slur_depth=0,
                        slur_has_note=False,
                    )
                    end = _walk(child.children, position, scale, branch, notes, grace=grace)
                    _close_hairpin(branch, notes, branch.level)
                    if number == 0:
                        voice.level = branch.level
                        voice.state = branch.state
                position = end
            elif element.kind == "tremolo":
                position = _play_alternation(element, position, scale, voice, notes)
            elif element.kind == "unfold":
                for _ in range(element.count):
                    position = _walk(element.children, position, scale, voice, notes, grace=grace)
            else:
                position = _walk(
                    element.children, position, scale * element.ratio, voice, notes, grace=grace
                )
    return position


def _play_alternation(
    group: music.Group, position: Fraction, scale: Fraction, voice: _Voice, notes: list[PerfNote]
) -> Fraction:
    """Play `\\repeat tremolo`: the notes of the group go in alternation."""
    for _ in range(group.count):
        for element in group.children:
            if isinstance(element, music.Note):
                _play(element, position, scale, voice, notes, grace_number=0, grace_count=0)
                position += element.duration * scale
    return position


def _close_hairpin(voice: _Voice, notes: list[PerfNote], target: float | None) -> None:
    """End the open hairpin. Give each note in it its loudness on the line to the target."""
    if voice.hairpin is None:
        return
    start, start_level, direction = voice.hairpin
    if target is None or (target - start_level) * direction <= 0:
        target = min(1.0, max(0.03, start_level + direction * HAIRPIN_STEP))
    members = [notes[i] for i in voice.hairpin_notes]
    if members:
        end = max(n.start + n.duration for n in members)
        span = float(end - start) or 1.0
        for i in voice.hairpin_notes:
            note = notes[i]
            begin = start_level + (target - start_level) * float(note.start - start) / span
            finish = (
                start_level
                + (target - start_level) * float(note.start + note.duration - start) / span
            )
            notes[i] = replace(note, level=begin, level_end=finish)
    voice.level = target
    voice.hairpin = None
    voice.hairpin_notes = []


def _rest(element: music.Rest, voice: _Voice, notes: list[PerfNote]) -> None:
    """Apply the marks on a rest: a dynamic mark, the end of a hairpin, a technique."""
    for post in element.posts:
        if post.kind == "dynamic" and post.value in DYNAMIC_LEVEL:
            _close_hairpin(voice, notes, DYNAMIC_LEVEL[post.value])
            voice.level = DYNAMIC_LEVEL[post.value]
        elif post.kind == "hairpin" and post.value == "!":
            _close_hairpin(voice, notes, None)
        elif post.kind == "command":
            technique = TECHNIQUES.get(post.value)
            if technique and technique.state:
                voice.state[technique.state] = technique.value


def _play(
    element: music.Note,
    position: Fraction,
    scale: Fraction,
    voice: _Voice,
    notes: list[PerfNote],
    *,
    grace_number: int,
    grace_count: int,
) -> None:
    posts = list(element.posts)
    kinds = [post.kind for post in posts]
    commands = {post.value for post in posts if post.kind == "command"}

    # A dynamic mark at this note ends an open hairpin and sets the new loudness.
    accent = 0.0
    soft_after = None
    for post in posts:
        if post.kind == "dynamic":
            if post.value in DYNAMIC_LEVEL:
                _close_hairpin(voice, notes, DYNAMIC_LEVEL[post.value])
                voice.level = DYNAMIC_LEVEL[post.value]
            elif post.value in ACCENT_BOOST:
                accent = max(accent, ACCENT_BOOST[post.value])
            elif post.value in SOFT_AFTER_ATTACK:
                accent = max(accent, 0.25)
                soft_after = DYNAMIC_LEVEL[SOFT_AFTER_ATTACK[post.value]]
    if any(post.kind == "hairpin" and post.value == "!" for post in posts):
        _close_hairpin(voice, notes, None)

    # Techniques change the state of the player from this note on.
    for name in commands:
        technique = TECHNIQUES.get(name)
        if technique and technique.state:
            voice.state[technique.state] = technique.value
        # "ord." also stops spiccato and col legno: the player uses the bow as usual.
        if name == "ord" and voice.state.get("attack") in ("spiccato", "col legno"):
            voice.state["attack"] = "arco"
    if "startTrillSpan" in commands:
        voice.trill_span = True

    articulations = {post.value for post in posts if post.kind == "articulation"}
    articulations |= commands & {
        "staccato", "accent", "tenuto", "marcato", "staccatissimo", "portato", "arpeggio",
    }  # fmt: skip
    if "accent" in articulations:
        accent = max(accent, 0.1)
    if "marcato" in articulations:
        accent = max(accent, 0.16)

    legato = voice.slur_depth > 0 and voice.slur_has_note
    duration = element.duration * scale
    level = soft_after if soft_after is not None else voice.level
    tied_into = bool(voice.open_ties)
    still_open: dict[float, int] = {}
    harmonic_all = "flageolet" in commands

    for note_pitch in element.pitches:
        midi = note_pitch.pitch.midi
        if midi in voice.open_ties:
            # The note continues a tied note: make the earlier note longer.
            earlier_index = voice.open_ties[midi]
            earlier = notes[earlier_index]
            notes[earlier_index] = replace(earlier, duration=earlier.duration + duration)
            if "tie" in kinds:
                still_open[midi] = earlier_index
            continue
        harmonic = harmonic_all or any(p.value == "harmonic" for p in note_pitch.posts)
        notes.append(
            PerfNote(
                player=voice.player,
                instrument=voice.instrument,
                start=position,
                duration=duration,
                midi=midi,
                level=level,
                level_end=level,
                accent=accent,
                articulations=frozenset(articulations),
                legato=legato and not tied_into,
                tremolo="tremolo" in kinds,
                trill=voice.trill_span or bool(commands & {"trill", "prall", "mordent"}),
                harmonic=harmonic,
                glissando="glissando" in commands,
                fermata=bool(commands & {"fermata", "shortfermata", "longfermata"}),
                grace=grace_number,
                grace_count=grace_count,
                voice=voice.voice,
                chord_size=len(element.pitches),
                state=tuple(sorted(voice.state.items())),
            )
        )
        if voice.hairpin is not None:
            voice.hairpin_notes.append(len(notes) - 1)
        if "tie" in kinds:
            still_open[midi] = len(notes) - 1
    voice.open_ties = still_open

    # Slurs and hairpins that start or stop at this note.
    for post in posts:
        if post.kind == "slur":
            if post.value == "(":
                voice.slur_depth += 1
                voice.slur_has_note = True
            else:
                voice.slur_depth = max(0, voice.slur_depth - 1)
                if voice.slur_depth == 0:
                    voice.slur_has_note = False
        elif post.kind == "hairpin" and post.value in "<>":
            _close_hairpin(voice, notes, None)
            direction = 1 if post.value == "<" else -1
            voice.hairpin = (position, voice.level, direction)
            voice.hairpin_notes = [
                i for i in range(len(notes)) if notes[i].start == position and i >= len(notes) - 8
            ]
    if voice.slur_depth > 0:
        voice.slur_has_note = True
    if "stopTrillSpan" in commands:
        voice.trill_span = False
    if soft_after is not None:
        voice.level = soft_after
