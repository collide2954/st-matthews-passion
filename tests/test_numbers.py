"""Tests for the numbers of the work: each number keeps the facts of its plan."""

from fractions import Fraction as F

from stmatthew.compose import ears, rhythm
from stmatthew.perform.events import perform
from stmatthew.work import build, n14
from stmatthew.work.material import HERZLICH_62


def _bars_of(work, label: str) -> tuple[int, int]:
    """Return the first and the last bar of the number with this mark."""
    marks = sorted(work.structure.marks.items())
    starts = [bar for bar, _label in marks]
    first = next(bar for bar, name in marks if name == label)
    later = [bar for bar in starts if bar > first]
    return first, (later[0] - 1 if later else len(work.structure.bars))


def test_number_14_has_the_voices_of_bach_at_different_speeds():
    work = build([14])
    first, last = _bars_of(work, "14")
    assert (first, last) == (1, 30)
    # The voice has the tune of Bach: the notes of the soprano, phrase by phrase.
    tune = [
        tone.pitch
        for phrase, _speeds, _level, _voice in n14.LINES
        for tone in rhythm.tones(HERZLICH_62.soprano[phrase - 1])
    ]
    sung = [ears.note_name(note.midi) for note in perform(work, "alto")]
    wanted = [ears.note_name(_midi(pitch)) for pitch in tune]
    assert sung == wanted
    # The bass has the speed of the voice in all lines.
    assert all("bass" not in speeds for _phrase, speeds, _level, _voice in n14.LINES)
    # The last chord is E major, and all strings have it. The voice stops before the hold.
    end = ears.moments(work, last, last)[-1]
    assert end.symbol == "E"
    assert {player for _pitch, player in end.notes} == {
        "vn1", "vn2", "va", "gamba", "vc", "vne",
    }  # fmt: skip
    # Each line ends with the chord of Bach: the slow voices come to their last notes.
    parts, bars = n14.plan()
    assert bars == 30
    start = n14.UPBEAT
    for phrase, speeds, _level, _voice in n14.LINES[:-1]:
        stop = start + n14.line_length(speeds)
        bar, beat = divmod(stop - n14.BREATH - F(1, 2), 4)
        moment = ears.moments(work, int(bar) + 1, int(bar) + 1, F(1, 2))[int(beat * 2)]
        chord = {
            _midi(rhythm.tones(getattr(HERZLICH_62, voice)[phrase - 1])[-1].pitch) % 12
            for voice in ("soprano", "alto", "tenor", "bass")
        }
        assert moment.classes == chord
        start = stop


def _midi(pitch: str) -> int:
    from stmatthew.notation.pitch import Pitch

    return round(Pitch.parse(pitch).midi)


def _motif(name: str) -> str:
    """Return the notes of a motif of the style study (the table of the motifs)."""
    import csv
    from pathlib import Path

    with Path("research/tables/motifs.csv").open(encoding="utf-8", newline="") as handle:
        return next(row["notes"] for row in csv.DictReader(handle) if row["id"] == name)


def test_number_1_has_the_themes_of_bach_and_a_pulse_that_loses_its_notes():
    work = build([1])
    structure = work.structure
    assert len(structure.bars) == 41
    assert {(bar.numerator, bar.denominator) for bar in structure.bars} == {(12, 8)}
    # The first notes of the voice are the theme of the sopranos of Bach (bar 17). The
    # last note of Bach is F-sharp 5: it is too high for the alto, and it is different.
    theme = [_midi(tone.pitch) for tone in rhythm.tones(_strip(_motif("kommt-soprano")))]
    sung = [round(note.midi) for note in perform(work, "alto")]
    assert len(theme) == 19 and sung[:18] == theme[:18]
    # The theme of the instruments: the oboe at the start, the bass in bar 5, the voice
    # at the end (one octave above the bass of Bach).
    steps = [_midi(tone.pitch) for tone in rhythm.tones(_strip(_motif("kommt-bass")))]
    oboe = [round(note.midi) for note in perform(work, "ob1")]
    assert oboe[: len(steps)] == [pitch + 24 for pitch in steps]
    bass = [n for n in perform(work, "vc") if structure.bar_at(n.start).number in (5, 6)]
    assert [round(note.midi) for note in bass] == steps
    last = [n for n in perform(work, "alto") if structure.bar_at(n.start).number in (33, 34)]
    assert [round(note.midi) for note in last] == [pitch + 12 for pitch in steps]
    # The recorders have the tune of the chorale, one octave above the tune of the study.
    lines = _strip(_motif("lamm-tune")).split("|")
    order = [0, 1, 0, 1, 2, 3, 4]  # the first two lines come two times
    tune = [_midi(tone.pitch) + 12 for line in order for tone in rhythm.tones(lines[line])]
    recorder = [round(n.midi) for n in perform(work, "fl1") if n.instrument == "recorder"]
    assert recorder == tune
    # The theorbo has all twelve eighth notes of a bar; at the end it loses them.
    starts: dict[int, set] = {}
    for note in perform(work, "lute"):
        starts.setdefault(structure.bar_at(note.start).number, set()).add(note.start)
    counts = [len(starts.get(number, ())) for number in range(1, 42)]
    assert counts[:35] == [12] * 35
    assert counts[35:] == [10, 8, 6, 4, 2, 1]
    # The last chord is E major.
    assert ears.moments(work, 41, 41)[0].symbol == "E"
    assert ears.parallels(work, 1, 41) == []


def _strip(notes: str) -> str:
    """Return the notes of a motif with a mark at the end of each line, and no beams."""
    return notes.replace("[", "").replace("]", "").replace("\\fermata", " |")


def test_the_last_lines_of_number_14_have_no_clash():
    work = build([14])
    found = ears.moments(work, 25, 30, F(1, 2))
    # From the upbeat of line 7 (bar 25, beat 4) to the end.
    late = [m for m in found if (m.bar, m.beat) >= (25, F(4))]
    assert not any(moment.clashes for moment in late)
