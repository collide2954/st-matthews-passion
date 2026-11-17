"""Read the open data files of the study: Humdrum kern files and MIDI files.

The readers only read data. They do not run a program on a downloaded file.
The time unit of all results is the quarter note.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

import mido

from .metrics import Tone

# ----------------------------------------------------------------------------
# Humdrum kern (the four-part chorales)
# ----------------------------------------------------------------------------

_KERN_STEPS = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
_KERN_NOTE = re.compile(r"(\d+)(\.*)([A-Ga-g]+)(#+|-+|n)?")
_KERN_REST = re.compile(r"(\d+)(\.*)r")


@dataclass
class ChoraleNote:
    """One note of one voice of a chorale."""

    voice: int  # 0 = bass, 1 = tenor, 2 = alto, 3 = soprano
    start: Fraction
    duration: Fraction
    midi: int
    step: int  # 0 = C ... 6 = B: the letter of the written note
    bar: int
    fermata: bool = False

    @property
    def end(self) -> Fraction:
        return self.start + self.duration


@dataclass
class Chorale:
    """One chorale setting in four parts."""

    name: str  # the file name with no extension
    title: str
    catalogue: str  # for example "BWV 244/54"
    tonic: int  # pitch class of the key
    minor: bool
    metre: str
    notes: list[ChoraleNote] = field(default_factory=list)

    def voice(self, index: int) -> list[ChoraleNote]:
        return sorted((n for n in self.notes if n.voice == index), key=lambda n: n.start)

    def tones(self) -> list[Tone]:
        return [Tone(float(n.start), float(n.duration), n.midi, str(n.voice)) for n in self.notes]

    @property
    def length(self) -> Fraction:
        return max((n.end for n in self.notes), default=Fraction(0))


def _kern_duration(number: str, dots: str) -> Fraction:
    base = Fraction(8) if number == "0" else Fraction(4, int(number))
    return base * (2 - Fraction(1, 2 ** len(dots)))


def _kern_pitch(letters: str, accidental: str | None) -> tuple[int, int]:
    """Return the MIDI number and the step of a kern pitch (c = middle C, C = the C below)."""
    letter = letters[0].lower()
    octave = 3 + len(letters) if letters[0].islower() else 4 - len(letters)
    alter = 0
    if accidental and accidental != "n":
        alter = len(accidental) if accidental[0] == "#" else -len(accidental)
    midi = 12 * (octave + 1) + _KERN_STEPS[letter] + alter
    return midi, "cdefgab".index(letter)


def read_kern(path: Path) -> Chorale:
    """Read a chorale in the kern format (four spines: bass, tenor, alto, soprano)."""
    return parse_kern(path.read_text(encoding="utf-8", errors="replace"), path.stem)


def parse_kern(text: str, name: str = "") -> Chorale:
    """Parse the text of a kern file."""
    chorale = Chorale(name, "", "", 0, False, "")
    spines: list[int] = []  # the voice of each field of a line
    ends: dict[int, Fraction] = {}  # the end of the last note or rest of each field
    open_ties: dict[tuple[int, int], ChoraleNote] = {}
    bar = 0
    for line in text.splitlines():
        if not line:
            continue
        if line.startswith("!!!"):
            key, _, value = line[3:].partition(":")
            value = value.strip()
            if key.startswith("OTL") and not chorale.title:
                chorale.title = value
            elif key == "SCT":
                chorale.catalogue = value
            continue
        if line.startswith("!"):
            continue
        fields = line.split("\t")
        if line.startswith("**"):
            spines = list(range(len(fields)))
            ends = dict.fromkeys(range(len(fields)), Fraction(0))
            continue
        if line.startswith("*"):
            if any(item in ("*^", "*v") for item in fields):
                # A voice divides into two fields, or two fields join.
                new_spines: list[int] = []
                new_ends: dict[int, Fraction] = {}
                index = 0
                while index < len(fields):
                    item, voice, end = fields[index], spines[index], ends[index]
                    if item == "*^":
                        for _ in range(2):
                            new_ends[len(new_spines)] = end
                            new_spines.append(voice)
                    elif item == "*v":
                        while index + 1 < len(fields) and fields[index + 1] == "*v":
                            index += 1
                            end = max(end, ends[index])
                        new_ends[len(new_spines)] = end
                        new_spines.append(voice)
                    else:
                        new_ends[len(new_spines)] = end
                        new_spines.append(voice)
                    index += 1
                spines, ends = new_spines, new_ends
                continue
            for item in fields:
                found = re.fullmatch(r"\*([A-Ga-g][#-]?):.*", item)
                if found:
                    letter = found.group(1)
                    tonic = _KERN_STEPS[letter[0].lower()]
                    tonic += {"#": 1, "-": -1}.get(letter[1:], 0)
                    chorale.tonic, chorale.minor = tonic % 12, letter[0].islower()
                found = re.fullmatch(r"\*M(\d+/\d+)", item)
                if found and not chorale.metre:
                    chorale.metre = found.group(1)
            continue
        if line.startswith("="):
            found = re.match(r"=+(\d+)", line)
            if found:
                bar = int(found.group(1))
            continue
        started = [ends[i] for i, item in enumerate(fields) if item != "."]
        if not started:
            continue
        now = min(started)
        for index, item in enumerate(fields):
            if item == ".":
                continue
            voice = spines[index]
            longest = Fraction(0)
            for token in item.split(" "):
                if "q" in token:
                    continue  # a grace note takes no time
                rest = _KERN_REST.search(token)
                if rest:
                    longest = max(longest, _kern_duration(rest.group(1), rest.group(2)))
                    continue
                found = _KERN_NOTE.search(token)
                if not found:
                    continue
                duration = _kern_duration(found.group(1), found.group(2))
                longest = max(longest, duration)
                midi, step = _kern_pitch(found.group(3), found.group(4))
                key = (voice, midi)
                if ("_" in token or "]" in token) and key in open_ties:
                    open_ties[key].duration += duration
                    open_ties[key].fermata = open_ties[key].fermata or ";" in token
                    if "]" in token:
                        del open_ties[key]
                    continue
                note = ChoraleNote(voice, now, duration, midi, step, bar, ";" in token)
                chorale.notes.append(note)
                if "[" in token:
                    open_ties[key] = note
            ends[index] = now + longest
    return chorale


# ----------------------------------------------------------------------------
# MIDI (the movements of the Passion and of related works)
# ----------------------------------------------------------------------------


@dataclass
class Movement:
    """One movement from a MIDI file. Each track is one line of the score."""

    name: str
    numerator: int
    denominator: int
    quarters_per_minute: float
    tracks: list[list[Tone]]

    @property
    def bar_quarters(self) -> float:
        return 4.0 * self.numerator / self.denominator

    @property
    def length(self) -> float:
        return max((tone.end for track in self.tracks for tone in track), default=0.0)

    @property
    def seconds(self) -> float:
        return 60.0 * self.length / self.quarters_per_minute

    def all_tones(self) -> list[Tone]:
        return [tone for track in self.tracks for tone in track]


def read_midi(path: Path) -> Movement:
    """Read a MIDI file. The first track has the metre and the tempo; it has no notes."""
    midi = mido.MidiFile(path)
    numerator, denominator, tempo = 4, 4, 500000
    signatures = [m for m in midi.tracks[0] if m.type == "time_signature"]
    if signatures:
        # Some files have a short first bar with its own signature: use the last one.
        numerator, denominator = signatures[-1].numerator, signatures[-1].denominator
    tempos = [m.tempo for m in midi.tracks[0] if m.type == "set_tempo"]
    if tempos:
        tempo = tempos[0]
    tracks: list[list[Tone]] = []
    for index, track in enumerate(midi.tracks[1:], start=1):
        tones: list[Tone] = []
        sounding: dict[int, list[tuple[int, int]]] = {}
        ticks = 0
        for message in track:
            ticks += message.time
            if message.type == "note_on" and message.velocity > 0:
                sounding.setdefault(message.note, []).append((ticks, message.velocity))
            elif message.type in ("note_off", "note_on") and sounding.get(message.note):
                start, velocity = sounding[message.note].pop(0)
                tones.append(
                    Tone(
                        start / midi.ticks_per_beat,
                        (ticks - start) / midi.ticks_per_beat,
                        message.note,
                        str(index),
                        float(velocity),
                    )
                )
        tones.sort(key=lambda tone: (tone.start, tone.midi))
        tracks.append(tones)
    return Movement(path.stem, numerator, denominator, mido.tempo2bpm(tempo), tracks)


# ----------------------------------------------------------------------------
# Figured bass (the figures in the text of a LilyPond source)
# ----------------------------------------------------------------------------

_FIGURE_BLOCK = re.compile(r"\\figuremode\s*\{(.*?)\n\}", flags=re.S)
_FIGURE = re.compile(r"<([^<>]*)>")


def read_figures(path: Path) -> list[str]:
    """Return the figures of the figured bass in a LilyPond source, as text.

    The function reads the file as text. Each item is the content of one
    figure, with its numbers from the top to the bottom, for example "6 5".
    An accidental has the sign "+" (raised), "-" (lowered), or "!" (natural).
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    figures: list[str] = []
    for block in _FIGURE_BLOCK.findall(text):
        block = re.sub(r"%[^\n]*", "", block)
        for content in _FIGURE.findall(block):
            parts = [part for part in content.split() if part and not part.startswith("\\")]
            cleaned = [part.replace("_", "") for part in parts]
            cleaned = [part for part in cleaned if part]
            if cleaned:
                figures.append(" ".join(cleaned))
    return figures
