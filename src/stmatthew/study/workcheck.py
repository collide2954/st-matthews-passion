"""Measure the new work with the methods of the style study.

The study measures the reference works. This module measures the new work
in the same way. Thus the report can show the distance between the work and
the reference works, and between the work and the style profiles.

The module measures three items:

- Literal repetition: how frequently a bar comes again with no change.
- Harmony: the same numbers as the comparison of the reference works.
- The instruments: how much of its range and of its techniques each player
  uses.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from fractions import Fraction
from pathlib import Path

from ..notation.musicxml import UNPITCHED
from ..notation.work import Work
from ..perform.events import DEFAULT_STATE, perform
from . import metrics
from .metrics import Tone

OUTPUT_DIR = Path("research/measured")
SPAN = 8  # a bar is a repetition if it is the same as one of this number of bars before it
BLOCK = 4  # the length of a block of bars

# One note for the repetition measurement: bar, voice, position in the bar,
# length, MIDI note. The unit of the position and the length is the quarter note.
BarNote = tuple[int, str, Fraction, Fraction, int]

REPETITION_MEASURES = [
    "full texture: bar is the same as the bar before",
    "full texture: bar is the same as one of the 8 bars before",
    "full texture: bar is the same at a different pitch",
    "full texture: bar has the same rhythm with different notes",
    "one voice: bar is the same as one of its 8 bars before",
    "one voice: bar is the same at a different pitch",
    "bars in a block of 4 bars that is the same as an earlier block",
]

HARMONY_MEASURES = [
    "chords: share built from thirds",
    "chords: share with a semitone clash",
    "chords: share with a 3-semitone cluster",
    "chords: share in one whole-tone scale",
    "chords: mean pitch classes",
    "share of sounding time: major and minor triads",
    "share of sounding time: vagrant chords",
    "share of sounding time: dominant chords",
    "share of sounding time: other seventh and ninth chords",
    "mean pitch classes that sound together",
    "mean distinct pitch classes in one window",
]

FLAGS = ("harmonic", "tremolo", "trill", "glissando")


def _at_lowest(items: Iterable[tuple], index: int) -> frozenset:
    """Return the items with their pitches as distances from the lowest pitch."""
    items = list(items)
    low = min(item[index] for item in items)
    return frozenset((*item[:index], item[index] - low) for item in items)


def repetition(notes: Iterable[BarNote]) -> dict[str, float]:
    """Measure how frequently a bar comes again with no change.

    The values are shares of the bars that have notes. "The same" means the
    same notes at the same positions with the same lengths, in the same
    voices. A voice is one player, or one voice of a piano arrangement.
    """
    full: dict[int, set] = defaultdict(set)
    voices: dict[str, dict[int, set]] = defaultdict(lambda: defaultdict(set))
    for bar, voice, position, length, midi in notes:
        full[bar].add((voice, position, length, midi))
        voices[voice][bar].add((position, length, midi))
    exact = {bar: frozenset(items) for bar, items in full.items()}
    moved = {bar: _at_lowest(items, 3) for bar, items in full.items()}
    rhythm = {bar: frozenset(item[:3] for item in items) for bar, items in full.items()}
    counts: Counter[str] = Counter()
    for bar in exact:
        earlier = [number for number in range(bar - SPAN, bar) if number in exact]
        if exact.get(bar - 1) == exact[bar]:
            counts[REPETITION_MEASURES[0]] += 1
        if any(exact[bar] == exact[number] for number in earlier):
            counts[REPETITION_MEASURES[1]] += 1
        elif any(moved[bar] == moved[number] for number in earlier):
            counts[REPETITION_MEASURES[2]] += 1
        elif any(rhythm[bar] == rhythm[number] for number in earlier):
            counts[REPETITION_MEASURES[3]] += 1
    total = max(len(exact), 1)
    result = {name: counts[name] / total for name in REPETITION_MEASURES[:4]}

    same = moved_same = voice_bars = 0
    for bars in voices.values():
        for bar, items in bars.items():
            if len(items) < 2:
                continue
            voice_bars += 1
            earlier = [bars[number] for number in range(bar - SPAN, bar) if number in bars]
            if any(items == other for other in earlier):
                same += 1
            elif any(_at_lowest(items, 2) == _at_lowest(other, 2) for other in earlier):
                moved_same += 1
    result[REPETITION_MEASURES[4]] = same / max(voice_bars, 1)
    result[REPETITION_MEASURES[5]] = moved_same / max(voice_bars, 1)

    blocks: dict[tuple, list[int]] = defaultdict(list)
    for bar in sorted(exact):
        if all(number in exact for number in range(bar, bar + BLOCK)):
            blocks[tuple(exact[number] for number in range(bar, bar + BLOCK))].append(bar)
    again = {bar for starts in blocks.values() for bar in starts[1:]}
    covered = {number for bar in again for number in range(bar, bar + BLOCK)}
    result[REPETITION_MEASURES[6]] = len(covered) / total
    return result


def parts_of(work: Work) -> dict[str, tuple[int, int]]:
    """Return the first and the last bar of each part of the work, and of its two halves."""
    marks = {label: bar for bar, label in work.structure.marks.items()}
    last = len(work.structure.bars)
    return {
        "complete": (1, last),
        "before the turn": (1, marks["AA"] - 1),
        "after the turn": (marks["AA"], last),
        "part 1": (1, marks["D"] - 1),
        "part 2": (marks["D"], marks["S"] - 1),
        "part 3": (marks["S"], marks["AA"] - 1),
        "part 4": (marks["AA"], marks["GG"] - 1),
        "part 5": (marks["GG"], last),
    }


def bar_notes(work: Work) -> list[BarNote]:
    """Return all notes of the work for the repetition measurement."""
    structure = work.structure
    notes: list[BarNote] = []
    for player in work.orchestra.players:
        for note in perform(work, player.id):
            if note.grace:
                continue
            bar = structure.bar_at(note.start)
            notes.append(
                (bar.number, player.id, note.start - bar.start, note.duration, round(note.midi))
            )
    return notes


def work_repetition(work: Work) -> dict[str, dict[str, float]]:
    """Measure the repetition of the work and of each part."""
    notes = bar_notes(work)
    return {
        label: repetition(note for note in notes if first <= note[0] <= last)
        for label, (first, last) in parts_of(work).items()
    }


def work_harmony(work: Work) -> dict[str, dict[str, float]]:
    """Measure the harmony of the work and of each part, as the study measures a reference work."""
    structure = work.structure
    tones: list[Tone] = []
    for player in work.orchestra.players:
        for note in perform(work, player.id):
            if note.grace or note.instrument in UNPITCHED:
                continue
            tones.append(Tone(float(note.start), float(note.duration), round(note.midi), player.id))
    tones.sort(key=lambda tone: tone.start)
    result = {}
    for label, (first, last) in parts_of(work).items():
        low, high = float(structure.bar(first).start), float(structure.bar(last).end)
        chosen = [tone for tone in tones if low <= tone.start < high]
        line = metrics.skyline(chosen)
        values = metrics.fingerprint(chosen, line=line, max_gap=1.0, window=4.0)
        result[label] = {name: values[name] for name in HARMONY_MEASURES if name in values}
    return result


def work_instruments(work: Work) -> tuple[list[list[object]], list[str]]:
    """Measure the use of each player. Return the rows, and the instruments with no notes.

    A row has: the player, the share of the time in which the player
    plays, the part of the range of the instrument that the player uses,
    the shares of the notes in the low, the middle, and the high third of
    the range, and the techniques.
    """
    structure = work.structure
    total = structure.duration_seconds
    rows: list[list[object]] = []
    used: set[str] = set()
    for player in work.orchestra.players:
        notes = perform(work, player.id)
        if not notes:
            rows.append([player.id, 0.0, "", "", "", "", "no notes"])
            continue
        seconds = sum(
            structure.seconds(note.start + note.duration) - structure.seconds(note.start)
            for note in notes
            if not note.grace
        )
        techniques: set[str] = set()
        for note in notes:
            used.add(note.instrument)
            for key, value in note.state:
                if DEFAULT_STATE.get(key) != value and key != "ring":
                    techniques.add(value if key in ("attack", "place") else f"{key}: {value}")
            techniques.update(flag for flag in FLAGS if getattr(note, flag))
            if note.grace:
                techniques.add("grace notes")
        main = Counter(note.instrument for note in notes).most_common(1)[0][0]
        instrument = work.orchestra.instruments.get(main)
        share: object = ""
        thirds: list[object] = ["", "", ""]
        if instrument is not None and instrument.high > instrument.low and main not in UNPITCHED:
            pitches = [note.midi for note in notes if note.instrument == main and not note.harmonic]
            span = instrument.high - instrument.low
            share = (max(pitches) - min(pitches)) / span
            counts = [0, 0, 0]
            for midi in pitches:
                counts[min(2, int(3 * (midi - instrument.low) / span))] += 1
            thirds = [count / len(pitches) for count in counts]
        rows.append([player.id, seconds / total, share, *thirds, "; ".join(sorted(techniques))])
    listed: list[str] = []
    for player in work.orchestra.players:
        listed.extend(name for name in player.instruments if name not in listed)
    return rows, [name for name in listed if name not in used]


def _write(name: str, header: Sequence[str], rows: Iterable[Sequence[object]]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        for row in rows:
            writer.writerow([f"{v:.4g}" if isinstance(v, float) else v for v in row])
    return path


def write_reference_repetition(label: str, notes: Iterable[BarNote]) -> Path:
    """Write the repetition of a reference work (the study has its notes)."""
    values = repetition(notes)
    return _write("repetition.csv", ["measure", label], [[name, values[name]] for name in values])


def write_tables(work: Work) -> list[Path]:
    """Measure the work and write the three tables. Return the files."""
    repeats = work_repetition(work)
    harmony = work_harmony(work)
    rows, unused = work_instruments(work)
    labels = list(repeats)
    return [
        _write(
            "work_repetition.csv",
            ["measure", *labels],
            [[name, *[repeats[label][name] for label in labels]] for name in REPETITION_MEASURES],
        ),
        _write(
            "work_harmony.csv",
            ["measure", *labels],
            [
                [name, *[harmony[label].get(name, "") for label in labels]]
                for name in HARMONY_MEASURES
            ],
        ),
        _write(
            "work_instruments.csv",
            [
                "player",
                "share_of_time",
                "range_used",
                "low_third",
                "middle_third",
                "high_third",
                "techniques",
            ],
            rows,
        ),  # fmt: skip
        _write("work_unused.csv", ["instrument"], [[name] for name in unused]),
    ]
