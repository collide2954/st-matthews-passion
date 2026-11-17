"""The sampler: play the performance notes of one player with recorded samples."""

from __future__ import annotations

import zlib
from collections import OrderedDict
from dataclasses import dataclass, replace
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import numpy as np

from ..notation.structure import Structure
from ..perform.events import PerfNote
from . import dsp
from .instruments import Sound, sound_of
from .library import Sample, build_index

REFERENCE_LEVEL = 0.2  # root mean square of the loudest playing of the loudest instrument
GRACE_SECONDS = 0.085
SOLO_GAIN = 0.56  # one player relative to the section (-5 dB)
FILTER_TAIL = 2400  # samples of silence after a note, for the end of the filter sound
CACHE_BYTES = 1_500_000_000

# Filters for playing techniques that the sample libraries do not have.
BUS_FILTERS = {
    "mute": [
        dsp.peaking(1800.0, -5.0, 0.9),
        dsp.peaking(3200.0, -7.0, 1.2),
        dsp.shelf(5000.0, -4.0, high=True),
    ],
    "sul ponticello": [
        dsp.shelf(350.0, -7.0, high=False),
        dsp.peaking(3500.0, 6.0, 0.8),
        dsp.shelf(6000.0, 4.0, high=True),
    ],
    "sul tasto": [dsp.shelf(2000.0, -7.0, high=True), dsp.peaking(3000.0, -3.0, 1.0)],
    "brass mute": [dsp.shelf(400.0, -9.0, high=False), dsp.peaking(2200.0, 5.0, 1.0)],
    "thin": [dsp.highpass(600.0, 2), dsp.shelf(4000.0, 3.0, high=True)],
}


# How much brighter the loudest playing is than a middle loudness, for each
# family: (frequency of the high shelf in Hz, change in dB).
BRIGHTNESS = {
    "strings": (2500.0, 5.0),
    "woodwinds": (2000.0, 4.0),
    "brass": (1500.0, 9.0),
    "percussion": (3000.0, 3.0),
    "plucked": (2500.0, 4.0),
    "keyboards": (2500.0, 4.0),
}
MIDDLE_LEVEL = 0.6  # the loudness with no change of the brightness (mezzo forte)


@lru_cache(maxsize=256)
def _tilt(frequency: float, gain_db: int) -> np.ndarray:
    return dsp.shelf(frequency, float(gain_db), high=True)


def brightness_filter(sound: Sound, level: float) -> np.ndarray | None:
    """Return the high shelf filter for the loudness of a note (None = no change)."""
    frequency, family_db = BRIGHTNESS.get(sound.family, (2500.0, 4.0))
    full = family_db if sound.bright_db is None else sound.bright_db
    gain = int(round(full * (level - MIDDLE_LEVEL) / (1.0 - MIDDLE_LEVEL)))
    return _tilt(frequency, gain) if gain else None


def _equalizer(sound: Sound) -> list[np.ndarray]:
    """Return the filters of the equalization of an instrument."""
    filters = []
    for kind, frequency, gain, *rest in sound.eq:
        if kind == "peak":
            filters.append(dsp.peaking(frequency, gain, rest[0] if rest else 1.0))
        else:
            filters.append(dsp.shelf(frequency, gain, high=kind == "high"))
    return filters


class _AudioCache:
    """Keep loaded and pitch-shifted samples in memory, up to a size limit."""

    def __init__(self, limit: int = CACHE_BYTES) -> None:
        self.limit = limit
        self.size = 0
        self.items: OrderedDict[tuple[str, int], np.ndarray] = OrderedDict()

    def get(self, sample: Sample, cents: int) -> np.ndarray:
        key = (sample.path, cents)
        if key in self.items:
            self.items.move_to_end(key)
            return self.items[key]
        if cents == 0:
            audio = dsp.load_mono(Path(sample.path))[sample.onset :]
        else:
            audio = dsp.shift_pitch(self.get(sample, 0), cents / 100.0)
        self.items[key] = audio
        self.size += audio.nbytes
        while self.size > self.limit and len(self.items) > 1:
            _, removed = self.items.popitem(last=False)
            self.size -= removed.nbytes
        return audio


CACHE = _AudioCache()


@dataclass
class _Choice:
    sample: Sample
    weight: float


class Voicebank:
    """The samples of one instrument, ready for the selection of a note."""

    def __init__(self, sound: Sound) -> None:
        self.sound = sound
        self.groups: dict[str, dict[int, list[Sample]]] = {}
        for key, sources in sound.sources.items():
            by_pitch: dict[int, list[Sample]] = {}
            for source in sources:
                samples = build_index(source)
                if sound.unpitched and source.layers:
                    # One instrument with loudness layers: the written pitch has no effect.
                    by_pitch.setdefault(60, []).extend(samples)
                    continue
                if sound.unpitched:
                    # The written notes c', d', e' ... select the samples in sequence.
                    steps = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76]
                    for number, sample in enumerate(sorted(samples, key=lambda s: s.path)):
                        by_pitch.setdefault(steps[number % len(steps)], []).append(sample)
                    continue
                for sample in samples:
                    by_pitch.setdefault(sample.nominal, []).append(sample)
            if by_pitch:
                self.groups[key] = by_pitch
        if "sustain" not in self.groups:
            raise RuntimeError("an instrument has no sustain samples")
        self.filters = [dsp.highpass(sound.lowcut_hz, 2), *_equalizer(sound)]

    def has(self, key: str) -> bool:
        return key in self.groups

    def pitches(self, key: str, midi: float) -> list[int]:
        """Return the sampled pitches of a key, nearest to the target first."""
        return sorted(self.groups[key], key=lambda nominal: abs(nominal - midi))[
            : 1 if self.sound.unpitched else None
        ]

    def choose(self, key: str, nominal: int, level: float, number: int = 0) -> list[_Choice]:
        """Return one or two samples (loudness layers) for a loudness level.

        If the instrument has more than one recording of a note, `number`
        selects the recording. Thus repeated notes do not sound the same.
        """
        samples = self.groups[key][nominal]
        layers = sorted({sample.layer for sample in samples})

        def take(layer: float) -> Sample:
            takes = [sample for sample in samples if sample.layer == layer]
            return takes[number % len(takes)]

        lower = [layer for layer in layers if layer <= level]
        upper = [layer for layer in layers if layer >= level]
        if not lower:
            return [_Choice(take(upper[0]), 1.0)]
        if not upper:
            return [_Choice(take(lower[-1]), 1.0)]
        low, high = lower[-1], upper[0]
        if low == high:
            return [_Choice(take(low), 1.0)]
        share = (level - low) / (high - low)
        return [_Choice(take(low), float(np.cos(share * np.pi / 2))),
                _Choice(take(high), float(np.sin(share * np.pi / 2)))]  # fmt: skip


def level_to_rms(sound: Sound, level: float) -> float:
    """Return the target loudness (root mean square) for a dynamic level."""
    decibels = sound.loud_db - sound.range_db * (1.0 - min(max(level, 0.0), 1.0))
    return REFERENCE_LEVEL * dsp.db(decibels)


def _articulation_key(note: PerfNote, bank: Voicebank, seconds: float) -> tuple[str, str]:
    """Return the sample key and the filter bus for a note."""
    sound = bank.sound
    attack = note.get("attack")
    bus = "normal"
    key = "sustain"
    if sound.family == "strings":
        if attack == "pizzicato":
            key = "pizzicato"
        elif attack == "col legno":
            key = "collegno"
        elif note.harmonic:
            key = "harmonics"
        elif note.tremolo:
            key = "tremolo"
        elif attack == "spiccato" or (
            not note.legato
            and seconds < 0.3
            and ("staccato" in note.articulations or "staccatissimo" in note.articulations)
        ):
            key = "short"
        elif note.get("desk") == "solo" and bank.has("solo"):
            key = "solo"
        elif note.get("vibrato") == "none" and bank.has("nonvib"):
            key = "nonvib"
        if note.get("mute") in ("on", "practice"):
            bus = "mute"
        elif note.get("place") == "sul ponticello":
            bus = "sul ponticello"
        elif note.get("place") == "sul tasto":
            bus = "sul tasto"
    elif sound.family in ("woodwinds", "brass"):
        short = "staccato" in note.articulations or "staccatissimo" in note.articulations
        if short and seconds < 0.35 and not note.legato:
            key = "short"
        elif note.get("vibrato") == "none" and bank.has("nonvib"):
            key = "nonvib"
        muted = note.get("mute") == "on" or "stopped" in note.articulations
        if muted:
            if bank.has("mute") and key != "short":
                key = "mute"
            else:
                bus = "brass mute"
    else:
        if note.tremolo and bank.has("tremolo"):
            key = "tremolo"
        elif attack == "bowed" and bank.has("bowed"):
            key = "bowed"
        elif note.get("mallet") == "hard" and bank.has("hard"):
            key = "hard"
    if not bank.has(key):
        if key == "harmonics":
            bus = "thin"
        key = "sustain"
    return key, bus


def _sounding_seconds(note: PerfNote, seconds: float) -> float:
    """Return how long the player holds the note."""
    if "staccatissimo" in note.articulations:
        return max(0.05, 0.25 * seconds)
    if "staccato" in note.articulations:
        return max(0.07, 0.45 * seconds)
    if "portato" in note.articulations:
        return 0.78 * seconds
    if note.legato or "tenuto" in note.articulations:
        return seconds
    return max(0.06, seconds - min(0.05, 0.1 * seconds))


class _Stem:
    """A one-channel signal that becomes longer when a note needs more time."""

    def __init__(self) -> None:
        self.data = np.zeros(dsp.RATE * 20, dtype=np.float32)
        self.length = 0

    def add(self, offset: int, body: np.ndarray) -> None:
        end = offset + len(body)
        if end > len(self.data):
            longer = np.zeros(max(end, 2 * len(self.data)), dtype=np.float32)
            longer[: self.length] = self.data[: self.length]
            self.data = longer
        self.data[offset:end] += body
        self.length = max(self.length, end)

    def sound(self) -> np.ndarray:
        return self.data[: self.length]


@dataclass
class Prepared:
    """The notes of one player, ready for the sampler."""

    player: str
    notes: list[PerfNote]  # in the sequence of the voices, with rolls as single strokes
    starts: np.ndarray  # start of each note in seconds
    ends: np.ndarray
    banks: dict[str, Voicebank]


def prepare(notes: list[PerfNote], structure: Structure) -> Prepared | None:
    """Put the notes of one player in sequence and calculate their times."""
    if not notes:
        return None
    banks: dict[str, Voicebank] = {}
    for note in notes:
        if note.instrument not in banks:
            banks[note.instrument] = Voicebank(sound_of(note.instrument))
    ordered = sorted(
        _expand_rolls(notes, structure, banks), key=lambda n: (n.voice, n.start, -n.grace)
    )
    starts = np.array([structure.seconds(note.start) for note in ordered])
    ends = np.array([structure.seconds(note.start + note.duration) for note in ordered])
    return Prepared(notes[0].player, ordered, starts, ends, banks)


def render_player(
    prepared: Prepared,
    window: tuple[float, float] | None = None,
    origin: int = 0,
) -> list[np.ndarray]:
    """Return the sound of one player.

    The result is a list of one-channel signals. A string section gives one
    signal for each group of players in the section, thus the mixer can put
    the groups at different places on the stage.

    If `window` is given, the function plays only the notes that start in
    this time (seconds). The first sample of each signal is the sample
    `origin` of the work. A signal continues until its last note stops: the
    signals can have different lengths. The result does not change if the
    work is rendered in one window or in many windows.
    """
    stems: dict[int, _Stem] = {}
    banks = prepared.banks
    ordered = prepared.notes
    seed = zlib.crc32(prepared.player.encode())
    if window is None:
        selected = np.arange(len(ordered))
    else:
        selected = np.flatnonzero((prepared.starts >= window[0]) & (prepared.starts < window[1]))

    for index in selected:
        note = ordered[index]
        random = np.random.default_rng([seed, int(index)])
        bank = banks[note.instrument]
        sound = bank.sound

        start = float(prepared.starts[index])
        end = float(prepared.ends[index])
        if note.grace:
            start -= note.grace * GRACE_SECONDS
            end = start + GRACE_SECONDS
        seconds = end - start
        key, bus = _articulation_key(note, bank, seconds)
        note_filters = [*BUS_FILTERS.get(bus, []), *bank.filters]
        tilt = brightness_filter(sound, 0.5 * (note.level + note.level_end) + note.accent)
        if tilt is not None:
            note_filters.append(tilt)
        held = _sounding_seconds(note, seconds)

        following = ordered[index + 1] if index + 1 < len(ordered) else None
        glide = 0.0
        if note.glissando and following is not None and following.voice == note.voice:
            glide = following.midi - note.midi

        decays = sound.decays or key in ("pizzicato", "collegno", "short")
        ring = note.get("ring") == "on" or sound.family == "percussion"
        level = note.level
        divisi = 1.0 / np.sqrt(note.chord_size) if sound.family == "strings" else 1.0

        voices = sound.ensemble if key in ("sustain", "tremolo", "short", "pizzicato") else 1
        if note.get("desk") == "solo":
            voices = 1  # one player of the section plays alone
            divisi = SOLO_GAIN
        nearest = bank.pitches(key, note.midi)
        plan: list[tuple[str, int, float]] = []  # sample key, sampled pitch, weight
        for number in range(voices):
            candidates = [p for p in nearest if abs(p - note.midi) <= sound.max_shift]
            if not candidates:
                candidates = nearest[:1]
            plan.append(
                (key, candidates[min(number, len(candidates) - 1)], 1.0 if number == 0 else 0.7)
            )
        if key == "sustain" and bank.has("second") and voices > 1:
            second = bank.pitches("second", note.midi)
            if second and abs(second[0] - note.midi) <= sound.max_shift:
                plan.append(("second", second[0], 0.6))
        norm = float(np.sqrt(sum(weight**2 for _, _, weight in plan)))

        for voice_number, (sample_key, nominal, weight) in enumerate(plan):
            jitter = float(np.clip(random.normal(0.0, sound.timing_ms / 1000.0), -0.03, 0.03))
            spread = float(random.uniform(0.0, 0.018)) if voice_number else 0.0
            detune = float(random.normal(0.0, sound.detune_cents if voices > 1 else 2.0))
            for choice in bank.choose(sample_key, nominal, level, int(index) + voice_number):
                sample = choice.sample
                cents = int(round(((note.midi - sample.midi) * 100.0 + detune) / 5.0)) * 5
                if sound.unpitched:
                    cents = 0
                audio = CACHE.get(sample, cents)
                scale = 2.0 ** (cents / 1200.0)
                loop = None
                if sample.loop_end > 0:
                    loop = (
                        int(sample.loop_start / scale),
                        int(sample.loop_end / scale),
                        int(sample.loop_fade / scale),
                    )
                release = int(sound.release * dsp.RATE)
                lead = 0.0 if decays else sound.lead
                skip = 0
                fade_in = 0
                if note.legato and not decays:
                    skip = int(0.09 * dsp.RATE)
                    fade_in = int(0.05 * dsp.RATE)
                    lead = 0.02
                if decays:
                    wanted = len(audio) if ring or held > 3.0 else int((held + 0.25) * dsp.RATE)
                    if "roll" in note.articulations:
                        wanted = int(ROLL_RING_SECONDS * dsp.RATE)
                        ring = False
                    body = audio[: max(wanted, 1)].copy()
                    if not ring and len(body) < len(audio):
                        body = dsp.fade(body, 0, min(len(body), int(0.25 * dsp.RATE)))
                else:
                    wanted = int((held + lead) * dsp.RATE) + release
                    body = dsp.sustain(audio[skip:], wanted, _shift_loop(loop, skip)).copy()
                    body = dsp.fade(body, fade_in, min(release, len(body)))
                if glide and len(body) > 16:
                    curve = np.zeros(len(body), dtype=np.float64)
                    begin = int(0.3 * len(body))
                    curve[begin:] = np.linspace(0.0, glide, len(body) - begin)
                    body = dsp.bend(body, curve)

                gain_start = level_to_rms(sound, note.level) / max(sample.level, 1e-6)
                gain_end = level_to_rms(sound, note.level_end) / max(sample.level, 1e-6)
                scale_all = np.float32(choice.weight * weight / norm * divisi)
                if abs(gain_end - gain_start) < 1e-9 * max(gain_start, 1e-9):
                    body *= np.float32(gain_start) * scale_all
                else:
                    # A change of loudness in a note: a straight line in decibels.
                    ramp = np.linspace(np.log(gain_start), np.log(gain_end), len(body))
                    body *= np.exp(ramp).astype(np.float32) * scale_all
                if note.accent > 0:
                    boost = level_to_rms(sound, min(1.0, note.level + note.accent)) / level_to_rms(
                        sound, note.level
                    )
                    span = min(len(body), int(0.9 * dsp.RATE))
                    decay = np.exp(-np.arange(span) / (0.18 * dsp.RATE))
                    body[:span] *= (1.0 + (boost - 1.0) * decay).astype(np.float32)
                # The filters of the technique and of the instrument, on this note only.
                padded = np.concatenate([body, np.zeros(FILTER_TAIL, dtype=np.float32)])
                body = dsp.apply(padded, *note_filters)

                offset = int(round((start - lead + jitter + spread) * dsp.RATE)) - origin
                if offset < 0:
                    body = body[-offset:]
                    offset = 0
                if len(body):
                    if voice_number not in stems:
                        stems[voice_number] = _Stem()
                    stems[voice_number].add(offset, body)

    return [stems[number].sound() for number in sorted(stems)]


ROLL_STROKES_PER_SECOND = 13.0
ROLL_RING_SECONDS = 1.2  # how long one stroke in a roll sounds


def _expand_rolls(
    notes: list[PerfNote], structure: Structure, banks: dict[str, Voicebank]
) -> list[PerfNote]:
    """Change a roll on an instrument with no roll samples into its single strokes."""
    result: list[PerfNote] = []
    random = np.random.default_rng(7)
    for note in notes:
        bank = banks[note.instrument]
        if not (note.tremolo and bank.sound.decays and not bank.has("tremolo")):
            result.append(note)
            continue
        quarters_per_second = structure.bpm_at(note.start) / 60.0
        step = Fraction(quarters_per_second / ROLL_STROKES_PER_SECOND).limit_denominator(96)
        count = max(2, int(note.duration / step))
        for number in range(count):
            share = number / count
            level = note.level + (note.level_end - note.level) * share
            wobble = float(random.uniform(0.9, 1.0))
            result.append(
                replace(
                    note,
                    start=note.start + number * step,
                    duration=step,
                    level=level * wobble,
                    level_end=level * wobble,
                    tremolo=False,
                    accent=note.accent if number == 0 else 0.0,
                    # Only the last stroke of a roll rings to its end.
                    articulations=note.articulations
                    | (frozenset({"roll"}) if number < count - 1 else frozenset()),
                )
            )
    return result


def _shift_loop(loop: tuple[int, int, int] | None, skip: int) -> tuple[int, int, int] | None:
    """Move the loop points for a sample that starts `skip` samples later."""
    if loop is None:
        return None
    start, end, crossfade = loop
    if start - skip - crossfade < 0:
        return None
    return start - skip, end - skip, crossfade
