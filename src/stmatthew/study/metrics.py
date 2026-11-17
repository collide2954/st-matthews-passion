"""Measurements on lists of tones.

A tone is one sounding note with a start time, a duration, and a MIDI pitch.
The time unit is free. The Verklärte Nacht data use quarter notes. The
performance MIDI data use seconds.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from . import pcsets


@dataclass
class Tone:
    """One sounding note."""

    start: float
    duration: float
    midi: int
    layer: str = ""  # stave and voice, or track name
    loudness: float = 0.0  # MIDI volume or velocity, 0 to 127

    @property
    def end(self) -> float:
        return self.start + self.duration


def slices(tones: Iterable[Tone]) -> list[tuple[float, tuple[int, ...]]]:
    """Cut the music at each note start and note end.

    Return a list of (duration, sounding MIDI pitches) for each cut segment.
    Segments with no sound are part of the list, with an empty pitch tuple.
    """
    events: list[tuple[float, int, int]] = []
    for tone in tones:
        if tone.duration > 0:
            events.append((tone.start, 1, tone.midi))
            events.append((tone.end, 0, tone.midi))
    events.sort()
    result: list[tuple[float, tuple[int, ...]]] = []
    active: Counter[int] = Counter()
    previous = events[0][0] if events else 0.0
    for time, is_start, midi in events:
        if time > previous:
            result.append((time - previous, tuple(sorted(active))))
            previous = time
        if is_start:
            active[midi] += 1
        else:
            active[midi] -= 1
            if active[midi] <= 0:
                del active[midi]
    return result


def sonority_shares(tones: Iterable[Tone]) -> dict[str, float]:
    """Return the share of sounding time for each sonority name."""
    totals: dict[str, float] = defaultdict(float)
    sounding = 0.0
    for duration, pitches in slices(tones):
        if not pitches:
            continue
        sounding += duration
        totals[pcsets.chord_name(pitches)] += duration
    return {name: value / sounding for name, value in totals.items()} if sounding else {}


def weighted_percentile(values: Sequence[tuple[float, float]], fraction: float) -> float:
    """Return a percentile of (value, weight) pairs."""
    ordered = sorted(values)
    total = sum(weight for _, weight in ordered)
    running = 0.0
    for value, weight in ordered:
        running += weight
        if running >= fraction * total:
            return value
    return ordered[-1][0] if ordered else 0.0


def skyline(tones: Sequence[Tone], *, window: float = 0.0) -> list[Tone]:
    """Return the top line: the highest tone of each group of simultaneous starts.

    Tones that start in an interval of `window` time units are one group.
    """
    ordered = sorted(tones, key=lambda t: (t.start, -t.midi))
    line: list[Tone] = []
    group_start = None
    for tone in ordered:
        if group_start is None or tone.start - group_start > window:
            line.append(tone)
            group_start = tone.start
        elif tone.midi > line[-1].midi:
            line[-1] = tone
    return line


def melodic_intervals(line: Sequence[Tone], *, max_gap: float) -> list[int]:
    """Return the signed intervals in semitones between successive tones of a line.

    The function ignores an interval if the silence before the second tone is
    longer than `max_gap`.
    """
    intervals = []
    for earlier, later in zip(line, line[1:], strict=False):
        if later.start - earlier.end <= max_gap:
            intervals.append(later.midi - earlier.midi)
    return intervals


INTERVAL_BINS = [
    ("repeated note", (0, 0)),
    ("semitone", (1, 1)),
    ("whole tone", (2, 2)),
    ("minor or major third", (3, 4)),
    ("fourth or fifth", (5, 7)),
    ("sixth or seventh", (8, 11)),
    ("octave or larger", (12, 127)),
]


def interval_profile(intervals: Sequence[int]) -> dict[str, float]:
    """Return the share of each interval size class, and direction data."""
    if not intervals:
        return {}
    count = len(intervals)
    profile: dict[str, float] = {}
    for name, (low, high) in INTERVAL_BINS:
        profile[name] = sum(1 for i in intervals if low <= abs(i) <= high) / count
    # The tritone is part of the "fourth or fifth" class. Show it separately also.
    profile["tritone"] = sum(1 for i in intervals if abs(i) == 6) / count
    moving = [i for i in intervals if i != 0]
    if moving:
        profile["descending share of moves"] = sum(1 for i in moving if i < 0) / len(moving)
        profile["mean size of moves (semitones)"] = sum(abs(i) for i in moving) / len(moving)
    return profile


def entropy_bits(weights: Iterable[float]) -> float:
    """Return the Shannon entropy in bits of a weight list."""
    values = [w for w in weights if w > 0]
    total = sum(values)
    return -sum((w / total) * math.log2(w / total) for w in values) if total else 0.0


def pitch_class_weights(tones: Iterable[Tone]) -> list[float]:
    """Return the duration of each of the 12 pitch classes."""
    weights = [0.0] * 12
    for tone in tones:
        weights[tone.midi % 12] += tone.duration
    return weights


def fingerprint(
    tones: Sequence[Tone],
    *,
    line: Sequence[Tone],
    max_gap: float,
    window: float,
) -> dict[str, float]:
    """Return a set of style numbers for a list of tones.

    `line` is the top line for the melodic interval data.
    `window` is the length of the time window for the pitch-class turnover.
    """
    cut = slices(tones)
    sounding = [(duration, pitches) for duration, pitches in cut if pitches]
    sounding_time = sum(duration for duration, _ in sounding)
    total_time = sum(duration for duration, _ in cut)
    if not sounding_time:
        return {}

    chords = [(d, p) for d, p in sounding if len({x % 12 for x in p}) >= 3]
    chord_time = sum(d for d, _ in chords)
    whole_tone = [frozenset(range(0, 12, 2)), frozenset(range(1, 12, 2))]

    def share(test) -> float:
        return sum(d for d, p in chords if test({x % 12 for x in p})) / chord_time

    result = {
        "silence share of time": 1 - sounding_time / total_time,
        "mean pitch classes that sound together": sum(
            d * len({x % 12 for x in p}) for d, p in sounding
        )
        / sounding_time,
        "mean notes that sound together": sum(d * len(p) for d, p in sounding) / sounding_time,
        "share of sounding time with 3 or more pitch classes": chord_time / sounding_time,
    }
    if chord_time:
        result.update(
            {
                "chords: share built from thirds": share(
                    lambda pcs: pcsets.is_tertian(pcsets.chord_name(pcs))
                ),
                "chords: share with a semitone clash": share(pcsets.has_semitone),
                "chords: share with a 3-semitone cluster": share(pcsets.has_chromatic_cluster),
                "chords: share in one whole-tone scale": share(
                    lambda pcs: any(pcs <= scale for scale in whole_tone)
                ),
                "chords: mean pitch classes": sum(d * len({x % 12 for x in p}) for d, p in chords)
                / chord_time,
            }
        )

    families: dict[str, float] = dict.fromkeys(pcsets.CHORD_FAMILIES, 0.0)
    for duration, pitches in sounding:
        family = pcsets.chord_family(pcsets.chord_name(pitches))
        if family:
            families[family] += duration
    for family, value in families.items():
        result[f"share of sounding time: {family}"] = value / sounding_time

    weights = pitch_class_weights(tones)
    result["pitch-class entropy (bits, maximum 3.585)"] = entropy_bits(weights)

    # Pitch-class turnover: distinct pitch classes that start in each window.
    start = min(t.start for t in tones)
    windows: dict[int, set[int]] = defaultdict(set)
    for tone in tones:
        windows[int((tone.start - start) // window)].add(tone.midi % 12)
    result["mean distinct pitch classes in one window"] = sum(
        len(v) for v in windows.values()
    ) / len(windows)
    result["share of windows with 10 or more pitch classes"] = sum(
        1 for v in windows.values() if len(v) >= 10
    ) / len(windows)

    pitches = [(float(t.midi), float(t.duration)) for t in tones]
    low = weighted_percentile(pitches, 0.05)
    high = weighted_percentile(pitches, 0.95)
    result["pitch, 5th percentile (MIDI)"] = low
    result["pitch, median (MIDI)"] = weighted_percentile(pitches, 0.5)
    result["pitch, 95th percentile (MIDI)"] = high
    result["pitch span, 5th to 95th percentile (semitones)"] = high - low
    result["lowest pitch (MIDI)"] = min(t.midi for t in tones)
    result["highest pitch (MIDI)"] = max(t.midi for t in tones)
    widths = [(float(p[-1] - p[0]), d) for d, p in sounding if len(p) >= 2]
    if widths:
        result["median width of simultaneous notes (semitones)"] = weighted_percentile(widths, 0.5)
        result["90th percentile width of simultaneous notes (semitones)"] = weighted_percentile(
            widths, 0.9
        )

    for name, value in interval_profile(melodic_intervals(line, max_gap=max_gap)).items():
        result[f"top line: {name}"] = value
    return result
