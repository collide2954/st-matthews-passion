"""Find music that a player cannot play.

The checks are:

- Each note must be in the range of the instrument.
- A wind instrument plays one note at a time.
- A player who changes to a different instrument must have the time to do it.
- The timpani player must have the time to tune a drum to a different note.
- One hand of a keyboard player or of the harp player must reach each of its chords.
- One hand of a keyboard player must have the time for each move, and it cannot play
  chords faster than a limit.
- A hairpin must not go over a silence: a player cannot make a rest louder.
- Two players who share a staff in the score (for example flutes 1 and 2): where
  they play chords, player 1 has the upper note.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from ..notation import combine, hairpins
from ..notation.pitch import from_midi
from ..notation.work import Work
from ..perform.events import PerfNote, perform

ONE_NOTE_FAMILIES = ("woodwinds", "brass")
HAND_FAMILIES = ("keyboards", "plucked")

# The smallest time in seconds for a change of instrument.
CHANGE_SECONDS = {"percussion": 4.0}
CHANGE_SECONDS_DEFAULT = 8.0

# The timpani: the number of drums, and the smallest time in seconds to tune
# a drum to a different note.
TIMPANI_DRUMS = 4
TIMPANI_SECONDS = 5.0


# The chord of one hand (a player with two staves has one staff for each hand): the
# largest number of notes, and the largest width in semitones. The harp player does
# not use the little finger. A rolled chord of a keyboard instrument can be wider:
# the hand moves, and the pedal of the piano holds the notes.
HAND_NOTES = {"harp": 4}
HAND_NOTES_DEFAULT = 5
HAND_SPAN = {"harp": 16}  # the harp: a major tenth
HAND_SPAN_DEFAULT = 14  # a keyboard instrument: a major ninth
ROLLED_SPAN = {"harp": 16}
ROLLED_SPAN_DEFAULT = 24

# The moves of one hand of a keyboard player. The model: the hand is a window of
# `HAND_REACH` semitones, and each stroke (the notes of the hand that start together)
# must be in the window. From one stroke to the subsequent stroke, the window moves by
# the smallest possible distance. A move of not more than `FREE_MOVE` semitones is a
# part of usual finger work (a scale, an arpeggio). A larger move needs time:
# `MOVE_SECONDS` plus `MOVE_SECONDS_FOR_SEMITONE` for each semitone. Examples: a fifth
# 0.13 s, an octave 0.19 s, two octaves 0.34 s. One hand cannot play chords faster
# than `CHORD_SECONDS` one after the other.
HAND_FAMILIES_WITH_MOVES = ("keyboards",)
HAND_REACH = 12
FREE_MOVE = 5
MOVE_SECONDS = 0.05
MOVE_SECONDS_FOR_SEMITONE = 0.012
CHORD_SECONDS = 0.14


@dataclass(frozen=True)
class Problem:
    """One problem in the music of a player."""

    player: str
    bar: int
    text: str

    def __str__(self) -> str:
        return f"{self.player}, bar {self.bar}: {self.text}"


def _free_after(note: PerfNote, percussion: bool) -> Fraction:
    """Return the time (in quarter notes) at which the player is free after a note.

    A percussion player is free immediately after a stroke: the instrument
    continues to sound without the player. A roll occupies the player to
    its end.
    """
    if percussion and not note.tremolo:
        return note.start
    return note.start + note.duration


def _timpani_problems(work: Work, player: str, notes: list[PerfNote]) -> list[Problem]:
    """Find the notes for which the timpani player has too little time to tune a drum.

    The model: a note that no drum has goes to the drum that the player did
    not use for the longest time. The time for the change of tuning starts
    at the last stroke on that drum (for a roll: at its end).
    """
    problems: list[Problem] = []
    structure = work.structure
    drums: dict[float, Fraction] = {}  # the note of each drum -> the time of its last use
    for note in notes:
        if note.instrument != "timpani":
            continue
        if note.midi not in drums and len(drums) >= TIMPANI_DRUMS:
            old = min(drums, key=lambda midi: drums[midi])
            seconds = structure.seconds(note.start) - structure.seconds(drums.pop(old))
            if seconds < TIMPANI_SECONDS:
                text = (
                    f"only {max(seconds, 0.0):.1f} s to tune a drum from "
                    f"{from_midi(old).name} to {from_midi(note.midi).name}"
                )
                problems.append(Problem(player, structure.bar_at(note.start).number, text))
        drums[note.midi] = _free_after(note, percussion=True)
    return problems


def _hand_problems(work: Work, player: str, notes: list[PerfNote]) -> list[Problem]:
    """Find the chords that one hand cannot reach."""
    chords: dict[Fraction, list[PerfNote]] = {}
    for note in notes:
        if not note.grace:
            chords.setdefault(note.start, []).append(note)
    problems = []
    for start, chord in sorted(chords.items()):
        keys = sorted({round(note.midi) for note in chord})
        if len(keys) < 2:
            continue
        instrument = chord[0].instrument
        rolled = all("arpeggio" in note.articulations for note in chord)
        widest = (
            ROLLED_SPAN.get(instrument, ROLLED_SPAN_DEFAULT)
            if rolled
            else HAND_SPAN.get(instrument, HAND_SPAN_DEFAULT)
        )
        most = HAND_NOTES.get(instrument, HAND_NOTES_DEFAULT)
        low, high = from_midi(keys[0]).name, from_midi(keys[-1]).name
        text = ""
        if len(keys) > most:
            text = f"a chord of {len(keys)} notes for one hand of the {instrument}"
        elif keys[-1] - keys[0] > widest:
            text = f"a chord from {low} to {high} is too wide for one hand of the {instrument}"
        if text:
            problems.append(Problem(player, work.structure.bar_at(start).number, text))
    return problems


def hand_move(first: list[int], second: list[int]) -> int:
    """Return the smallest move of the hand from one stroke to the subsequent stroke.

    Each stroke is the sorted list of its keys (MIDI numbers). The result is
    in semitones.
    """
    # The lowest key of the window can be between these two values for each stroke.
    first_low, first_high = min(first[-1] - HAND_REACH, first[0]), first[0]
    second_low, second_high = min(second[-1] - HAND_REACH, second[0]), second[0]
    return max(0, second_low - first_high, first_low - second_high)


def move_seconds(distance: int) -> float:
    """Return the time that a move of the hand needs."""
    if distance <= FREE_MOVE:
        return 0.0
    return MOVE_SECONDS + MOVE_SECONDS_FOR_SEMITONE * distance


def _move_problems(work: Work, player: str, notes: list[PerfNote]) -> list[Problem]:
    """Find the moves of one hand that are too fast, and chords that come too fast."""
    structure = work.structure
    strokes: dict[Fraction, set[int]] = {}
    for note in notes:
        if not note.grace:
            strokes.setdefault(note.start, set()).add(round(note.midi))
    ordered = [(start, sorted(keys)) for start, keys in sorted(strokes.items())]
    problems: list[Problem] = []
    seen: set[tuple[int, str]] = set()
    for (start, keys), (after, subsequent) in zip(ordered, ordered[1:], strict=False):
        seconds = structure.seconds(after) - structure.seconds(start)
        distance = hand_move(keys, subsequent)
        kind = ""
        if seconds + 1e-6 < move_seconds(distance):
            kind = "leap"
            low, high = from_midi(keys[0]).name, from_midi(subsequent[0]).name
            text = (
                f"the hand must move {distance} semitones in {seconds:.2f} s "
                f"(from {low} to {high}); it needs {move_seconds(distance):.2f} s"
            )
        elif len(keys) >= 2 and len(subsequent) >= 2 and seconds <= CHORD_SECONDS:
            kind = "chords"
            text = f"chords come after {seconds:.2f} s in one hand; the limit is {CHORD_SECONDS} s"
        bar = structure.bar_at(after).number
        if kind and (bar, kind) not in seen:
            seen.add((bar, kind))
            problems.append(Problem(player, bar, text))
    return problems


def _hairpin_problems(work: Work, player: str) -> list[Problem]:
    """Find the hairpins that go over a silence (the model stops them: see `hairpins.py`)."""
    base, _, hand = player.partition(".")
    other = f"{base}.{'lh' if hand == 'rh' else 'rh'}" if hand in ("rh", "lh") else ""
    spans = hairpins.sounding(work.music_of(other).children, Fraction(0)) if other else []
    return [
        Problem(player, work.structure.bar_at(start).number, "a hairpin goes over a silence")
        for start in hairpins.over_rests(work.music_of(player).children, Fraction(0), spans)
    ]


def _pair_problems(work: Work) -> list[Problem]:
    """Find the bars in which player 2 of a shared staff has the upper note of a chord."""
    present = {player.id for player in work.orchestra.players}
    problems: list[Problem] = []
    for first, second in combine.PAIRS:
        if first in present and second in present:
            text = f"{second} has the upper note: exchange the music of {first} and {second}"
            for bar in combine.exchanged_units(work, first, second):
                problems.append(Problem(second, bar, text))
    return problems


def check(work: Work) -> list[Problem]:
    """Return the problems in the work, in the sequence of the score."""
    problems: list[Problem] = _pair_problems(work)
    structure = work.structure
    for player in work.orchestra.players:
        seen: set[tuple[int, str]] = set()
        percussion = player.family == "percussion"
        smallest = CHANGE_SECONDS.get(player.family, CHANGE_SECONDS_DEFAULT)
        last_instrument = ""
        free = Fraction(0)
        notes = sorted(perform(work, player.id), key=lambda item: item.start)
        problems.extend(_timpani_problems(work, player.id, notes))
        problems.extend(_hairpin_problems(work, player.id))
        if player.id.endswith((".rh", ".lh")) and player.family in HAND_FAMILIES:
            problems.extend(_hand_problems(work, player.id, notes))
            if player.family in HAND_FAMILIES_WITH_MOVES:
                problems.extend(_move_problems(work, player.id, notes))
        for note in notes:
            bar = structure.bar_at(note.start).number
            if last_instrument and note.instrument != last_instrument:
                seconds = structure.seconds(note.start) - structure.seconds(free)
                if seconds < smallest:
                    text = (
                        f"only {max(seconds, 0.0):.1f} s for the change from the "
                        f"{last_instrument} to the {note.instrument}"
                    )
                    problems.append(Problem(player.id, bar, text))
                free = Fraction(0)
            last_instrument = note.instrument
            free = max(free, _free_after(note, percussion))
            instrument = work.orchestra.instruments.get(note.instrument)
            if instrument is not None and not note.harmonic:
                name = from_midi(note.midi).name
                if note.midi < instrument.low:
                    text = f"{name} is below the range of the {note.instrument}"
                elif note.midi > instrument.high:
                    text = f"{name} is above the range of the {note.instrument}"
                else:
                    text = ""
                if text and (bar, text) not in seen:
                    seen.add((bar, text))
                    problems.append(Problem(player.id, bar, text))
            if player.family in ONE_NOTE_FAMILIES and note.chord_size > 1:
                text = f"a chord for the {note.instrument}"
                if (bar, text) not in seen:
                    seen.add((bar, text))
                    problems.append(Problem(player.id, bar, text))
    return problems
