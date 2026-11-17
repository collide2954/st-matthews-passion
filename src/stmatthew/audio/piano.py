"""Render the piano with the samples of the Salamander Grand Piano.

The owner of the project asked for a better piano sound: the piano has a
solo part in the work (the piano interlude). The grand piano of Muse Keys
is a small library (190 MB for the full instrument). The Salamander Grand
Piano is a Yamaha C5 concert grand with 16 dynamic levels for each sampled
note (48 kHz, 24 bit, 1.2 GB). Its author is Alexander Holm, and its licence
is Creative Commons Attribution 3.0.

This module plays the piano part of the work with these samples:

- Each third key of the piano has samples. A key between two sampled keys
  uses the nearest sample, at a different speed.
- The loudness of a note selects one of the 16 dynamic levels. Thus a loud
  note has the bright tone of a hard stroke, not only more level.
- The sustain pedal of the score holds the notes. With no pedal, the damper
  stops the string when the key goes up. The highest keys have no dampers.
- A new stroke on a key that sounds stops the old sound of that key.
- The notes of a rolled chord start one after the other, from the lowest.
- The noise of a key that goes up, and the noise of the pedal, are in the
  sound at a low level, as in a real recording.
- Each stroke has a small difference of time and of loudness, as the strokes
  of a pianist have.

The result is a dry signal near the strings. Two functions put it in the
hall. `place()` is for the soloist at the front of the stage: a narrower
stereo picture, and some reverberation. `place_in_orchestra()` is for the
piano as an instrument of the orchestra, at its seat.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from functools import cache
from pathlib import Path

import numpy as np
import soundfile
import soxr

from ..notation.work import Work
from ..perform.events import PerfNote, perform
from . import dsp, space

LIBRARY_DIR = Path(".cache/samples/salamander")
SAMPLES_DIR = LIBRARY_DIR / "Samples"
DATA_DIR = LIBRARY_DIR / "Data"
PLAYERS = ("pno.rh", "pno.lh")

# The highest MIDI velocity of each of the 16 dynamic levels (from the SFZ file of the
# library), and the sampled keys: A0 (21), then each third key to C8 (108).
LAYER_TOP = (26, 34, 36, 43, 46, 50, 56, 64, 72, 80, 88, 96, 104, 112, 120, 127)
CENTRES = tuple(range(21, 109, 3))
NOTE_NAMES = ("A", "C", "D#", "F#")
VELOCITY_TRACK = 0.27  # the part of the level that follows the velocity (SFZ: amp_veltrack)
# More change of the level for soft notes, in dB for a velocity. A measurement of a
# chord showed that the samples have only 6 dB between the marks p and f. The
# other instruments of the audio have 18 to 19 dB (the table of `playback.py`).
# With this table the piano has: ppp -28, pp -24, p -17, mp -12, mf -6 dB from f.
SOFT_TRIM = ((20, -11.0), (48, -11.0), (64, -7.7), (78, -3.9), (94, 0.0), (127, 0.0))
FIRST_KEY_WITH_NO_DAMPER = 89  # F6: the keys from here have no dampers

# The time in which the damper stops a string (the level goes down by 8.7 dB in this
# time). Low strings are heavy: they stop more slowly.
DAMP_SECONDS = {21: 0.11, 48: 0.075, 72: 0.05, 88: 0.04}
RESTRIKE_SECONDS = 0.02  # a new stroke on the same key stops the old sound in this time
STACCATO_SECONDS = 0.11  # the longest time that the key is down for a staccato note
ROLL_STEP_SECONDS = 0.045  # a rolled chord: the time from one note to the subsequent note
ROLL_SECONDS = 0.35  # a rolled chord: the longest time from its first note to its last note
FAST_SECONDS = 0.3  # a note with no slur that is shorter than this is a fast note
FAST_SHARE = 0.55  # the part of a fast note for which the key is down
KEY_NOISE_DB = -34.0  # the noise of a key that goes up
PEDAL_NOISE_DB = -27.0  # the noise of the pedal
LONGEST_SECONDS = 14.0  # a sample is not longer than this in the memory
CACHE_BYTES = 1_200_000_000

# The piano as the soloist, at the front of the stage: the width of its stereo picture
# (1 = as recorded near the strings), and the level of the hall reverberation in
# relation to the direct sound.
WIDTH = 0.45
REVERB_DB = -15.0
# The piano as an instrument of the orchestra: it is at its seat, and it gets the hall
# as the other instruments of the sampler do (the same value as `mix.REVERB_GAIN_DB`).
ORCHESTRA_REVERB_DB = -9.0

# A pianist does not play as a machine. Each stroke comes some milliseconds before or
# after its exact time, the notes of a chord do not start at exactly the same time, and
# each note is a little louder or softer. The owner of the project heard the exact fast
# lines of the last chord as "rigid". The values are standard deviations.
TIMING_MS = 6.0  # the time of a stroke
CHORD_MS = 2.0  # the time of one note in relation to the other notes of its stroke
VELOCITY_SPREAD = 3.0  # the velocity of a note
LARGEST_SHIFT_MS = 15.0
HUMAN_SEED = 20261115


def available() -> bool:
    """Return true if the samples of the library are on this computer."""
    return (SAMPLES_DIR / "C4v8.flac").exists()


def velocity(level: float, accent: float = 0.0) -> int:
    """Return the MIDI velocity for a loudness (0 to 1) and an accent.

    The marks of the score have these velocities: ppp 20, pp 33, p 48,
    mp 64, mf 78, f 94, ff 111, fff 125.
    """
    return int(np.clip(round(140.0 * (level + 0.5 * accent) - 5.0), 1, 127))


def _defines(path: Path, prefix: str) -> dict[int, int]:
    """Read the numbers `#define $<prefix>NN value` of a data file of the library."""
    found = re.findall(rf"#define \${prefix}(\d+) (-?\d+)", path.read_text(encoding="utf-8"))
    return {int(number): int(value) for number, value in found}


class _Library:
    """The samples, with the tuning and the start position of each sample."""

    def __init__(self) -> None:
        self.tune = _defines(DATA_DIR / "tune_ret.txt", "TUNE")  # cents, for each sampled key
        self.offsets = {
            layer: _defines(DATA_DIR / f"vel_{layer:02d}.txt", "OFF") for layer in range(1, 17)
        }
        self.cache: OrderedDict[tuple, np.ndarray] = OrderedDict()
        self.bytes = 0

    @staticmethod
    def name(centre: int) -> str:
        index = (centre - 21) // 3
        octave = (index + 3) // 4  # A0, C1, D#1, F#1, A1, C2, ...
        return f"{NOTE_NAMES[index % 4]}{octave}"

    def _keep(self, key: tuple, audio: np.ndarray) -> np.ndarray:
        self.cache[key] = audio
        self.bytes += audio.nbytes
        while self.bytes > CACHE_BYTES and len(self.cache) > 1:
            _old, removed = self.cache.popitem(last=False)
            self.bytes -= removed.nbytes
        return audio

    def note(self, midi: int, layer: int) -> np.ndarray:
        """Return the sound of a key at one dynamic level (two channels, from the stroke)."""
        key = ("note", midi, layer)
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        centre = min(CENTRES, key=lambda value: abs(value - midi))
        region = (centre - 21) // 3 + 1
        path = SAMPLES_DIR / f"{self.name(centre)}v{layer}.flac"
        start = self.offsets[layer].get(region, 0)
        frames = int(LONGEST_SECONDS * 1.07 * dsp.RATE)
        audio, _rate = soundfile.read(path, start=start, frames=frames, dtype="float32")
        semitones = (midi - centre) + self.tune.get(region, 0) / 100.0
        if abs(semitones) > 1e-4:
            ratio = 2.0 ** (semitones / 12.0)
            audio = soxr.resample(audio, dsp.RATE * ratio, dsp.RATE).astype(np.float32)
        audio = audio[: int(LONGEST_SECONDS * dsp.RATE)].copy()
        audio[:48] *= np.linspace(0.0, 1.0, 48, dtype=np.float32)[:, None]
        fade = min(len(audio), dsp.RATE // 2)
        audio[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)[:, None]
        return self._keep(key, audio)

    def noise(self, name: str) -> np.ndarray:
        key = ("noise", name)
        if key not in self.cache:
            audio, _rate = soundfile.read(SAMPLES_DIR / f"{name}.flac", dtype="float32")
            self._keep(key, audio)
        return self.cache[key]


@cache
def _library() -> _Library:
    """Return the library. All renders use the same one: the samples stay in the memory."""
    return _Library()


def _layer(value: int) -> int:
    """Return the dynamic level (1 to 16) of a MIDI velocity."""
    return next(index for index, top in enumerate(LAYER_TOP, start=1) if value <= top)


def _gain(value: int) -> float:
    """Return the level factor of a velocity in its dynamic level (SFZ: amp_veltrack)."""
    track = 1.0 - VELOCITY_TRACK * (1.0 - (value / 127.0) ** 2)
    trim = np.interp(value, [row[0] for row in SOFT_TRIM], [row[1] for row in SOFT_TRIM])
    return float(track * 10.0 ** (trim / 20.0))


def _damp_seconds(midi: int) -> float:
    keys = sorted(DAMP_SECONDS)
    return float(np.interp(midi, keys, [DAMP_SECONDS[key] for key in keys]))


def pedal_spans(work: Work) -> list[tuple[float, float]]:
    """Return the times in seconds in which the sustain pedal is down."""
    from ..notation import musicxml  # the reader of the pedal marks is there

    structure = work.structure
    changes = []
    for player in PLAYERS:
        changes.extend(musicxml.pedal_changes(work, player))
    marks = musicxml._pedal_marks(changes, type(structure.length)(0), structure.length)
    spans, start = [], None
    for position, kind in marks:
        if kind == "start":
            start = structure.seconds(position)
        elif start is not None:
            spans.append((start, structure.seconds(position)))
            start = None
    if start is not None:
        spans.append((start, structure.duration_seconds))
    return spans


def _key_up(note: PerfNote, start: float, end: float) -> float:
    """Return the time at which the key goes up."""
    if note.articulations & {"staccato", "staccatissimo"}:
        limit = STACCATO_SECONDS * (0.6 if "staccatissimo" in note.articulations else 1.0)
        return start + min(0.5 * (end - start), limit)
    if note.legato or "tenuto" in note.articulations:
        return end
    if end - start < FAST_SECONDS:
        # A fast note with no slur (a toccata): the finger leaves the key early.
        return start + FAST_SHARE * (end - start)
    return start + max(0.9 * (end - start), min(end - start, 0.05))


def notes_of(work: Work) -> list[tuple[float, float, int, int]]:
    """Return the piano notes of the work: the start, the key-up time, the key, the velocity."""
    structure = work.structure
    found = []
    rolled: dict[float, list[tuple[float, float, int, int]]] = {}
    for player in PLAYERS:
        notes = [note for note in perform(work, player) if note.instrument == "piano"]
        for index, note in enumerate(notes):
            start = structure.seconds(note.start)
            end = structure.seconds(note.start + note.duration)
            if note.glissando:
                # A glissando: the white keys from this note to the subsequent note.
                target = next(
                    (
                        other
                        for other in notes[index + 1 :]
                        if other.start >= note.start + note.duration
                    ),
                    None,
                )
                if target is not None:
                    value = velocity(0.5 * (note.level + note.level_end), note.accent)
                    found.extend(
                        _glissando(start, end, round(note.midi), round(target.midi), value)
                    )
                    continue
            if note.grace:
                start = max(0.0, start - 0.07 * note.grace)
                end = start + 0.09
            value = velocity(0.5 * (note.level + note.level_end), note.accent)
            item = (start, _key_up(note, start, end), round(note.midi), value)
            if "arpeggio" in note.articulations:
                rolled.setdefault(round(start, 4), []).append(item)
            else:
                found.append(item)
    for chord in rolled.values():
        found.extend(_roll(chord))
    found = [_human(*note) for note in found]
    found.sort()
    return found


def _roll(chord: list[tuple[float, float, int, int]]) -> list[tuple[float, float, int, int]]:
    """Return the notes of a rolled chord: they start one after the other, from the lowest.

    The notes of the two hands that start at the same time are one roll.
    """
    step = min(ROLL_STEP_SECONDS, ROLL_SECONDS / max(len(chord) - 1, 1))
    ordered = sorted(chord, key=lambda note: note[2])
    return [
        (start + number * step, max(key_up, start + number * step + 0.05), midi, value)
        for number, (start, key_up, midi, value) in enumerate(ordered)
    ]


def _human(start: float, key_up: float, midi: int, value: int) -> tuple[float, float, int, int]:
    """Return a note with the small differences of time and loudness of a pianist.

    The differences come from the time and the key of the note. Thus each
    render of the same music gives the same sound.
    """
    place = int(round(start * 1000.0))
    stroke = np.random.default_rng([HUMAN_SEED, place])
    own = np.random.default_rng([HUMAN_SEED, place, midi])
    shift = stroke.normal(0.0, TIMING_MS) + own.normal(0.0, CHORD_MS)
    shift = float(np.clip(shift, -LARGEST_SHIFT_MS, LARGEST_SHIFT_MS)) / 1000.0
    shift = max(shift, -start)
    louder = float(own.normal(0.0, VELOCITY_SPREAD))
    return start + shift, key_up + shift, midi, int(np.clip(round(value + louder), 1, 127))


WHITE_KEYS = (0, 2, 4, 5, 7, 9, 11)


def _glissando(
    start: float, end: float, first: int, last: int, value: int
) -> list[tuple[float, float, int, int]]:
    """Return the notes of a glissando on the white keys, from `first` to before `last`."""
    step = 1 if last >= first else -1
    keys = [key for key in range(first, last, step) if key % 12 in WHITE_KEYS] or [first]
    length = (end - start) / len(keys)
    return [
        (start + number * length, start + (number + 1.5) * length, key, value)
        for number, key in enumerate(keys)
    ]


Prepared = tuple[list[tuple[float, float]], list[tuple[float, float, int, int]]]


def prepare(work: Work) -> Prepared:
    """Return the pedal spans and the notes of the piano part, for more than one render."""
    return pedal_spans(work), notes_of(work)


def render(
    work: Work,
    begin: float = 0.0,
    seconds: float | None = None,
    prepared: Prepared | None = None,
) -> np.ndarray:
    """Render the piano part: a dry signal with two channels.

    `begin` is the time of the first sample, in seconds from the start of the
    work. `seconds` is the length (default: to the end of the work, with
    time for the last sound). `prepared` is the result of `prepare()`: a
    caller that renders the work in parts gives it, and saves time.
    """
    total = work.structure.duration_seconds + 8.0 - begin if seconds is None else seconds
    length = int(total * dsp.RATE)
    out = np.zeros((length, 2), dtype=np.float32)
    library = _library()
    spans, notes = prepared or prepare(work)

    def damper_time(key_up: float) -> float:
        """Return the time at which the damper comes down on the string."""
        for start, end in spans:
            if start <= key_up < end:
                return end
        return key_up

    # The time of the subsequent stroke on each key: it stops the sound of the key.
    following: dict[int, float] = {}
    plan = []
    for start, key_up, midi, value in reversed(notes):
        plan.append((start, key_up, midi, value, following.get(midi)))
        following[midi] = start
    for start, key_up, midi, value, restrike in reversed(plan):
        if start + LONGEST_SECONDS < begin or start >= begin + total:
            continue
        audio = library.note(midi, _layer(value))
        stop, tau = None, RESTRIKE_SECONDS
        if midi < FIRST_KEY_WITH_NO_DAMPER:
            stop, tau = damper_time(key_up), _damp_seconds(midi)
        if restrike is not None and (stop is None or restrike < stop):
            stop, tau = restrike, RESTRIKE_SECONDS
        count = len(audio)
        if stop is not None:
            count = min(count, int((stop - start + 9.0 * tau) * dsp.RATE))
        voice = audio[:count] * np.float32(_gain(value))
        if stop is not None:
            first = max(int((stop - start) * dsp.RATE), 0)
            if first < count:
                steps = np.arange(count - first, dtype=np.float32) / dsp.RATE
                voice[first:] *= np.exp(-steps / tau)[:, None]
        _add(out, voice, int(round((start - begin) * dsp.RATE)))
        if stop is not None and stop is not restrike and 21 <= midi <= 108:
            noise = library.noise(f"rel{midi - 20}") * np.float32(dsp.db(KEY_NOISE_DB))
            _add(out, noise, int(round((stop - begin) * dsp.RATE)))
    for number, (start, end) in enumerate(spans):
        level = np.float32(dsp.db(PEDAL_NOISE_DB))
        _add(out, library.noise(f"pedalD{number % 2 + 1}") * level, int((start - begin) * dsp.RATE))
        _add(out, library.noise(f"pedalU{number % 2 + 1}") * level, int((end - begin) * dsp.RATE))
    return out


def _add(out: np.ndarray, sound: np.ndarray, start: int) -> None:
    """Add a sound to the output at a sample position (parts outside the output are cut)."""
    skip = max(0, -start)
    start = max(start, 0)
    stop = min(len(out), start + len(sound) - skip)
    if stop > start:
        out[start:stop] += sound[skip : skip + stop - start]


def place_in_orchestra(dry: np.ndarray) -> np.ndarray:
    """Put the dry piano at its seat in the orchestra (the hall model of `space.py`).

    The piano is then one instrument of the orchestra: it is on the left, at
    the back, with the first reflections and the reverberation of the hall.
    """
    stage = space.Stage(len(dry))
    stage.add(0.5 * (dry[:, 0] + dry[:, 1]), space.seat_of("pno"))
    return stage.mix(dsp.db(ORCHESTRA_REVERB_DB))


def place(dry: np.ndarray) -> np.ndarray:
    """Put the dry piano on the stage: a narrower stereo picture and the hall.

    The piano of a concerto is at the front of the stage, in the middle. A
    recording has it nearer than the orchestra: more direct sound, less hall.
    """
    middle = 0.5 * (dry[:, 0] + dry[:, 1])
    side = 0.5 * (dry[:, 0] - dry[:, 1]) * np.float32(WIDTH)
    direct = np.stack([middle + side, middle - side], axis=1)
    hall = space.reverberate(middle * np.float32(dsp.db(REVERB_DB)))
    result = np.zeros((max(len(direct), len(hall)), 2), dtype=np.float32)
    result[: len(direct)] += direct
    result[: len(hall)] += hall
    return result
