"""Measure the open data of the study and write the tables in `research/measured`.

The data are the four-part chorales of Bach (370 settings, 11 of them from
the St Matthew Passion) and 14 movements of the Passion and of related works.
"""

from __future__ import annotations

import csv
import statistics
from collections import Counter
from collections.abc import Iterable, Sequence
from fractions import Fraction
from pathlib import Path

from ..notation.pitch import STEP_SEMITONES, Pitch
from . import corpus, metrics, readers
from .metrics import Tone
from .readers import Chorale, ChoraleNote, Movement

OUTPUT_DIR = Path("research/measured")

NOTE_NAMES = ("C", "C#", "D", "E-flat", "E", "F", "F#", "G", "A-flat", "A", "B-flat", "B")
MAJOR_SCALE = frozenset({0, 2, 4, 5, 7, 9, 11})
# The minor scale with the two forms of its sixth note and of its seventh note.
MINOR_SCALE = frozenset({0, 2, 3, 5, 7, 8, 9, 10, 11})

# The chords that the study names by their root: the intervals above the root.
ROOT_CHORDS = {
    (0, 4, 7): "major",
    (0, 3, 7): "minor",
    (0, 3, 6): "diminished",
    (0, 4, 7, 10): "major",
    (0, 3, 7, 10): "minor",
    (0, 4, 7, 11): "major",
    (0, 3, 6, 10): "diminished",
    (0, 3, 6, 9): "diminished",
    (0, 4, 10): "major",
    (0, 3, 10): "minor",
    (0, 4): "major",
    (0, 3): "minor",
    (0, 7): "open",
    (0,): "open",
}
DEGREES = {0: "I", 1: "bII", 2: "II", 3: "bIII", 4: "III", 5: "IV", 6: "#IV", 7: "V", 8: "bVI",
           9: "VI", 10: "bVII", 11: "VII"}  # fmt: skip


def pitch_name(midi: float) -> str:
    """Return the name of a MIDI pitch, for example "B3" (60 = C4)."""
    number = round(midi)
    return f"{NOTE_NAMES[number % 12]}{number // 12 - 1}"


def key_name(tonic: int, minor: bool) -> str:
    return f"{NOTE_NAMES[tonic]} {'minor' if minor else 'major'}"


def degree(pitch_classes: Iterable[int], tonic: int) -> str:
    """Return the degree of a chord in a key, for example "V" or "vi" (minor in small letters)."""
    unique = sorted({pc % 12 for pc in pitch_classes})
    # A diminished seventh chord has four possible roots: the leading note of the key
    # (or of its fifth note) is the first choice.
    for root in sorted(unique, key=lambda pc: ((pc - tonic) % 12 not in (11, 6), pc)):
        above = tuple(sorted((pc - root) % 12 for pc in unique))
        quality = ROOT_CHORDS.get(above)
        if quality is None:
            continue
        name = DEGREES[(root - tonic) % 12]
        if quality == "minor":
            name = name.lower()
        elif quality == "diminished":
            name = name.lower() + "o"
        elif quality == "open":
            name += " (no third)"
        return name
    return "?"


def _write(name: str, header: Sequence[str], rows: Iterable[Sequence[object]]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        for row in rows:
            writer.writerow([_text(cell) for cell in row])
    return path


def _text(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".") if value % 1 else str(int(value))
    return str(value)


# ----------------------------------------------------------------------------
# Lines: one voice or one instrument
# ----------------------------------------------------------------------------


def phrases(line: Sequence[Tone], gap: float = 0.5) -> list[tuple[float, float]]:
    """Return the start and the end of each phrase: a group of tones with no rest of `gap`."""
    result: list[tuple[float, float]] = []
    for tone in sorted(line, key=lambda t: t.start):
        if result and tone.start - result[-1][1] < gap:
            result[-1] = (result[-1][0], max(result[-1][1], tone.end))
        else:
            result.append((tone.start, tone.end))
    return result


def line_numbers(line: Sequence[Tone], length: float, scale: frozenset[int], tonic: int) -> dict:
    """Return the style numbers of one line (a list of tones with one tone at a time)."""
    ordered = sorted(line, key=lambda t: t.start)
    weights = [(float(t.midi), float(t.duration)) for t in ordered]
    total = sum(t.duration for t in ordered)
    spans = phrases(ordered)
    lengths = sorted(end - start for start, end in spans)
    intervals = metrics.melodic_intervals(ordered, max_gap=0.5)
    profile = metrics.interval_profile(intervals)
    outside = sum(t.duration for t in ordered if (t.midi - tonic) % 12 not in scale)
    values = [t.duration for t in ordered]
    return {
        "notes": len(ordered),
        "lowest": pitch_name(min(t.midi for t in ordered)),
        "highest": pitch_name(max(t.midi for t in ordered)),
        "pitch_5": pitch_name(metrics.weighted_percentile(weights, 0.05)),
        "pitch_median": pitch_name(metrics.weighted_percentile(weights, 0.5)),
        "pitch_95": pitch_name(metrics.weighted_percentile(weights, 0.95)),
        "share_of_time": min(1.0, total / length),
        "notes_per_quarter": len(ordered) / length,
        "phrases": len(spans),
        "median_phrase_quarters": statistics.median(lengths),
        "longest_phrase_quarters": lengths[-1],
        "longest_note_quarters": max(values),
        "share_sixteenths_or_shorter": sum(1 for v in values if v <= 0.26) / len(values),
        "share_eighths": sum(1 for v in values if 0.26 < v <= 0.51) / len(values),
        "share_longer": sum(1 for v in values if v > 0.51) / len(values),
        "repeated_note": profile.get("repeated note", 0.0),
        "semitone": profile.get("semitone", 0.0),
        "whole_tone": profile.get("whole tone", 0.0),
        "third": profile.get("minor or major third", 0.0),
        "fourth_or_fifth": profile.get("fourth or fifth", 0.0),
        "sixth_or_larger": profile.get("sixth or seventh", 0.0)
        + profile.get("octave or larger", 0.0),
        "tritone": profile.get("tritone", 0.0),
        "descending_share": profile.get("descending share of moves", 0.0),
        "notes_outside_the_scale": outside / total if total else 0.0,
    }


LINE_COLUMNS = [
    "notes", "lowest", "highest", "pitch_5", "pitch_median", "pitch_95", "share_of_time",
    "notes_per_quarter", "phrases", "median_phrase_quarters", "longest_phrase_quarters",
    "longest_note_quarters", "share_sixteenths_or_shorter", "share_eighths", "share_longer",
    "repeated_note", "semitone", "whole_tone", "third", "fourth_or_fifth", "sixth_or_larger",
    "tritone", "descending_share", "notes_outside_the_scale",
]  # fmt: skip


# ----------------------------------------------------------------------------
# Chorales
# ----------------------------------------------------------------------------


def chorale_numbers(chorale: Chorale) -> dict[str, float]:
    """Return the style numbers of one chorale setting."""
    tones = chorale.tones()
    soprano = [Tone(float(n.start), float(n.duration), n.midi) for n in chorale.voice(3)]
    bass = [Tone(float(n.start), float(n.duration), n.midi) for n in chorale.voice(0)]
    scale = MINOR_SCALE if chorale.minor else MAJOR_SCALE
    length = float(chorale.length)
    print_ = metrics.fingerprint(tones, line=soprano, max_gap=0.5, window=4.0)
    total = sum(t.duration for t in tones)
    outside = sum(t.duration for t in tones if (t.midi - chorale.tonic) % 12 not in scale)
    off_beat = sum(1 for t in tones if t.start % 1)
    bass_profile = metrics.interval_profile(metrics.melodic_intervals(bass, max_gap=0.5))
    soprano_profile = metrics.interval_profile(metrics.melodic_intervals(soprano, max_gap=0.5))
    inner = [
        Tone(float(n.start), float(n.duration), n.midi)
        for voice in (1, 2)
        for n in chorale.voice(voice)
    ]
    return {
        "length (quarter notes)": length,
        "phrases (fermatas of the soprano)": sum(1 for n in chorale.voice(3) if n.fermata),
        "soprano: span (semitones)": max(t.midi for t in soprano) - min(t.midi for t in soprano),
        "soprano: steps (semitone or whole tone)": soprano_profile.get("semitone", 0.0)
        + soprano_profile.get("whole tone", 0.0),
        "soprano: repeated notes": soprano_profile.get("repeated note", 0.0),
        "bass: span (semitones)": max(t.midi for t in bass) - min(t.midi for t in bass),
        "bass: semitone moves": bass_profile.get("semitone", 0.0),
        "bass: steps (semitone or whole tone)": bass_profile.get("semitone", 0.0)
        + bass_profile.get("whole tone", 0.0),
        "bass: fourths and fifths": bass_profile.get("fourth or fifth", 0.0),
        "bass: octaves and larger": bass_profile.get("octave or larger", 0.0),
        "notes outside the scale (share of note time)": outside / total,
        "note starts off the beat for each quarter note": off_beat / length,
        "inner voices: mean note length (quarter notes)": statistics.fmean(
            t.duration for t in inner
        ),
        "chords: share built from thirds": print_.get("chords: share built from thirds", 0.0),
        "chords: share with a semitone clash": print_.get(
            "chords: share with a semitone clash", 0.0
        ),
        "share of sounding time: major and minor triads": print_.get(
            "share of sounding time: major and minor triads", 0.0
        ),
        "share of sounding time: dominant chords": print_.get(
            "share of sounding time: dominant chords", 0.0
        ),
        "share of sounding time: vagrant chords": print_.get(
            "share of sounding time: vagrant chords", 0.0
        ),
        "share of sounding time: other seventh and ninth chords": print_.get(
            "share of sounding time: other seventh and ninth chords", 0.0
        ),
        "mean distinct pitch classes in four quarter notes": print_.get(
            "mean distinct pitch classes in one window", 0.0
        ),
    }


def sounding_at(chorale: Chorale, position) -> list[ChoraleNote]:
    return [n for n in chorale.notes if n.start <= position < n.end]


def cadences(chorale: Chorale) -> list[str]:
    """Return the chord at each fermata of the soprano, as a degree of the key."""
    result = []
    for note in chorale.voice(3):
        if note.fermata:
            # The chord at the end of the note: the lower voices can move under a fermata.
            moment = note.end - note.duration / 8
            chord = [n.midi for n in sounding_at(chorale, moment)]
            result.append(degree(chord, chorale.tonic))
    return result


def to_lilypond(notes: Sequence[ChoraleNote]) -> str:
    """Return a line of a chorale in the music language of the project (absolute pitches)."""
    words = []
    for note in notes:
        octave = round((note.midi - STEP_SEMITONES[note.step]) / 12) - 1
        alter = note.midi - (12 * (octave + 1) + STEP_SEMITONES[note.step])
        pitch = Pitch(note.step, Fraction(alter), octave)
        value = _DURATION_NAMES.get(note.duration, f"4*{note.duration}")
        words.append(pitch.name + value + ("\\fermata" if note.fermata else ""))
    return " ".join(words)


_DURATION_NAMES = {
    Fraction(4): "1", Fraction(3): "2.", Fraction(2): "2", Fraction(3, 2): "4.",
    Fraction(1): "4", Fraction(3, 4): "8.", Fraction(1, 2): "8", Fraction(1, 4): "16",
}  # fmt: skip


def load_chorales() -> list[Chorale]:
    return [
        readers.read_kern(corpus.CORPUS[f"chorale-{number:03d}"].path)
        for number in corpus.CHORALE_NUMBERS
    ]


def measure_chorales(chorales: Sequence[Chorale]) -> list[Path]:
    """Write the tables of the chorales."""
    numbers = {chorale.name: chorale_numbers(chorale) for chorale in chorales}
    measures = list(next(iter(numbers.values())))
    passion = {f"chor{number:03d}": info for number, info in corpus.PASSION_CHORALES.items()}
    by_name = {chorale.name: chorale for chorale in chorales}

    # The style of all chorales: the middle value and the range of the middle 80 percent.
    rows = []
    for measure in measures:
        values = sorted(item[measure] for item in numbers.values())
        mine = sorted(numbers[name][measure] for name in passion)
        rows.append(
            [
                measure,
                statistics.median(values),
                values[round(0.1 * (len(values) - 1))],
                values[round(0.9 * (len(values) - 1))],
                statistics.median(mine),
                mine[0],
                mine[-1],
            ]
        )
    paths = [
        _write(
            "chorale_style.csv",
            ["measure", "all_median", "all_10_percent", "all_90_percent", "passion_median",
             "passion_lowest", "passion_highest"],
            rows,
        )
    ]  # fmt: skip

    # The settings of the Passion, one for each row.
    def movement_key(name: str) -> int:
        return int(passion[name][0].split()[0])

    rows = []
    for name in sorted(passion, key=movement_key):
        chorale, item = by_name[name], numbers[name]
        soprano, bass = chorale.voice(3), chorale.voice(0)
        last = [n.midi for n in sounding_at(chorale, chorale.length - chorale.length / 1000)]
        rows.append(
            [
                passion[name][0],
                passion[name][1],
                int(name[4:]),
                key_name(chorale.tonic, chorale.minor),
                chorale.metre,
                item["length (quarter notes)"],
                f"{pitch_name(min(n.midi for n in soprano))} to "
                f"{pitch_name(max(n.midi for n in soprano))}",
                f"{pitch_name(min(n.midi for n in bass))} to "
                f"{pitch_name(max(n.midi for n in bass))}",
                " ".join(cadences(chorale)),
                degree(last, chorale.tonic),
                item["notes outside the scale (share of note time)"],
                item["chords: share with a semitone clash"],
                item["share of sounding time: vagrant chords"],
                item["bass: semitone moves"],
                item["note starts off the beat for each quarter note"],
            ]
        )
    paths.append(
        _write(
            "passion_chorales.csv",
            ["movement", "tune", "edition_number", "key_of_the_edition", "metre",
             "quarter_notes", "soprano", "bass", "chords_at_the_fermatas", "last_chord",
             "notes_outside_the_scale", "chords_with_a_semitone_clash", "vagrant_chords",
             "bass_semitone_moves", "starts_off_the_beat_for_each_quarter"],
            rows,
        )
    )  # fmt: skip

    # The tunes: the soprano of one setting of each tune, phrase by phrase.
    rows = []
    seen: set[str] = set()
    for name in sorted(passion, key=movement_key):
        tune = passion[name][1]
        if tune in seen:
            continue
        seen.add(tune)
        chorale = by_name[name]
        phrase: list[ChoraleNote] = []
        number = 0
        for note in chorale.voice(3):
            phrase.append(note)
            if note.fermata:
                number += 1
                steps = " ".join(str((n.midi - chorale.tonic) % 12) for n in phrase)
                rows.append(
                    [tune, passion[name][0], key_name(chorale.tonic, chorale.minor), number,
                     to_lilypond(phrase), steps]
                )  # fmt: skip
                phrase = []
    paths.append(
        _write(
            "chorale_tunes.csv",
            ["tune", "movement", "key_of_the_edition", "phrase", "notes",
             "semitones_above_the_key_note"],
            rows,
        )
    )  # fmt: skip
    return paths


# ----------------------------------------------------------------------------
# Movements
# ----------------------------------------------------------------------------

# The key of each movement of the corpus: the pitch class of the key note, and minor or major.
MOVEMENT_KEYS = {
    "Bach-244-Erbarme_Dich": (11, True),
    "Bach-244-Konnen_Tranen": (7, True),
    "Bach-244-Aus_Liebe": (9, True),
    "Bach-244-Blute_Nur": (11, True),
    "Bach-244-Mache_Dich": (10, False),
    "Bach-244-O_Mensch": (4, False),
    "Bach-244-Wir_Setzen_Uns-orquesta": (0, True),
    "Bach-232-Crucifixus": (4, True),
    "Bach-232-Qui_Tollis": (11, True),
    "Bach-243-Et_Misericordia": (4, True),
    "Bach-245-Ach_Mein_Sinn": (6, True),
    "Bach-245-Herr_Unser_Herrscher": (7, True),
    "Bach-198-Lass_Furstin": (11, True),
    "Bach-198-Der_Ewigkeit": (4, True),
}


def load_movements() -> dict[str, Movement]:
    return {
        stem: readers.read_midi(corpus.CORPUS[f"movement-{stem}"].path) for stem in corpus.MOVEMENTS
    }


def _one_at_a_time(line: Sequence[Tone]) -> list[Tone]:
    """Return a line with one tone at a time: of tones that start together, the highest."""
    return metrics.skyline(list(line))


def measure_movements(movements: dict[str, Movement]) -> list[Path]:
    """Write the tables of the movements: the lines, the harmony, and the bass."""
    line_rows, harmony_rows, bass_rows = [], [], []
    for stem, movement in movements.items():
        info = corpus.MOVEMENTS[stem]
        tonic, minor = MOVEMENT_KEYS[stem]
        scale = MINOR_SCALE if minor else MAJOR_SCALE
        length = movement.length
        if len(info.roles) != len(movement.tracks):
            raise ValueError(f"{stem}: {len(info.roles)} roles for {len(movement.tracks)} tracks")
        first_of_role: dict[str, list[Tone]] = {}
        for role, track in zip(info.roles, movement.tracks, strict=True):
            first_of_role.setdefault(role, track)
        for role, track in first_of_role.items():
            if role.startswith("choir") or not track:
                continue
            item = line_numbers(_one_at_a_time(track), length, scale, tonic)
            line_rows.append([info.title, info.work, role, *[item[c] for c in LINE_COLUMNS]])

        tones = movement.all_tones()
        solo = next(
            (t for role, t in first_of_role.items() if role.startswith(("voice", "solo"))),
            metrics.skyline(tones),
        )
        print_ = metrics.fingerprint(
            tones, line=_one_at_a_time(solo), max_gap=0.5, window=movement.bar_quarters
        )
        cut = metrics.slices(tones)
        sounding = [(d, p) for d, p in cut if p]
        time = sum(d for d, _ in sounding)
        lines_now = _lines_sounding(movement)
        harmony_rows.append(
            [
                info.title,
                info.work,
                key_name(tonic, minor),
                f"{movement.numerator}/{movement.denominator}",
                round(length / movement.bar_quarters),
                round(movement.quarters_per_minute),
                round(movement.seconds),
                len(movement.tracks),
                lines_now,
                print_["mean pitch classes that sound together"],
                print_["mean distinct pitch classes in one window"],
                print_.get("chords: share built from thirds", 0.0),
                print_.get("chords: share with a semitone clash", 0.0),
                print_["share of sounding time: major and minor triads"],
                print_["share of sounding time: dominant chords"],
                print_["share of sounding time: vagrant chords"],
                print_["share of sounding time: other seventh and ninth chords"],
                sum(d for d, p in sounding if (p[0] - tonic) % 12 == 0) / time,
                sum(t.duration for t in tones if (t.midi - tonic) % 12 not in scale)
                / sum(t.duration for t in tones),
            ]
        )

        bass = first_of_role.get("continuo")
        if bass:
            line = _one_at_a_time(bass)
            profile = metrics.interval_profile(metrics.melodic_intervals(line, max_gap=0.5))
            values = [t.duration for t in line]
            pedal, pedal_pitch = _longest_pedal(line)
            bass_rows.append(
                [
                    info.title,
                    info.work,
                    pitch_name(min(t.midi for t in line)),
                    pitch_name(max(t.midi for t in line)),
                    len(line) / length,
                    sum(1 for v in values if v <= 0.26) / len(values),
                    sum(1 for v in values if 0.26 < v <= 0.51) / len(values),
                    sum(1 for v in values if v > 0.51) / len(values),
                    profile.get("repeated note", 0.0),
                    profile.get("semitone", 0.0),
                    profile.get("semitone", 0.0) + profile.get("whole tone", 0.0),
                    profile.get("minor or major third", 0.0),
                    profile.get("fourth or fifth", 0.0),
                    profile.get("sixth or seventh", 0.0) + profile.get("octave or larger", 0.0),
                    pedal,
                    pitch_name(pedal_pitch),
                    1 - min(1.0, sum(values) / length),
                ]
            )
    return [
        _write("lines.csv", ["movement", "work", "line", *LINE_COLUMNS], line_rows),
        _write(
            "movement_harmony.csv",
            ["movement", "work", "key", "metre", "bars", "quarter_notes_in_a_minute", "seconds",
             "lines", "mean_lines_that_sound", "pitch_classes_that_sound_together",
             "pitch_classes_in_one_bar", "chords_from_thirds", "chords_with_a_semitone_clash",
             "major_and_minor_triads", "dominant_chords", "vagrant_chords",
             "other_seventh_chords", "time_with_the_key_note_in_the_bass",
             "notes_outside_the_scale"],
            harmony_rows,
        ),
        _write(
            "bass_lines.csv",
            ["movement", "work", "lowest", "highest", "notes_per_quarter",
             "share_sixteenths_or_shorter", "share_eighths", "share_longer", "repeated_note",
             "semitone", "step", "third", "fourth_or_fifth", "sixth_or_larger",
             "longest_pedal_quarters", "pedal_note", "share_of_time_silent"],
            bass_rows,
        ),
    ]  # fmt: skip


def _lines_sounding(movement: Movement) -> float:
    """Return the mean number of lines that sound at the same time."""
    events: list[tuple[float, int]] = []
    for track in movement.tracks:
        for start, end in phrases(track, gap=0.01):
            events.append((start, 1))
            events.append((end, -1))
    events.sort()
    active, previous, weighted, sounding = 0, 0.0, 0.0, 0.0
    for moment, change in events:
        if active:
            weighted += active * (moment - previous)
            sounding += moment - previous
        active += change
        previous = moment
    return weighted / sounding if sounding else 0.0


def _longest_pedal(line: Sequence[Tone]) -> tuple[float, int]:
    """Return the longest time for which a line stays on one pitch, and that pitch."""
    best, best_pitch = 0.0, line[0].midi
    start, pitch, end = line[0].start, line[0].midi, line[0].end
    for tone in line[1:]:
        if tone.midi == pitch and tone.start - end < 1.0:
            end = tone.end
        else:
            if end - start > best:
                best, best_pitch = end - start, pitch
            start, pitch, end = tone.start, tone.midi, tone.end
    if end - start > best:
        best, best_pitch = end - start, pitch
    return best, best_pitch


def measure_figures() -> Path:
    """Write the table of the figures of the figured bass."""
    counts: Counter[str] = Counter()
    sources = 0
    for info in corpus.MOVEMENTS.values():
        if not info.figures:
            continue
        figures = readers.read_figures(corpus.CORPUS[f"figures-{info.stem}"].path)
        if figures:
            sources += 1
        counts.update(figures)
    total = sum(counts.values())
    rows = [
        [figure, count, count / total]
        for figure, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        if count >= 5
    ]
    rows.append(["(movements with figures)", sources, ""])
    rows.append(["(all figures)", total, ""])
    return _write("figures.csv", ["figure", "count", "share"], rows)


def measure_all() -> list[Path]:
    """Measure all data and write all tables."""
    paths = measure_chorales(load_chorales())
    paths += measure_movements(load_movements())
    paths.append(measure_figures())
    return paths
