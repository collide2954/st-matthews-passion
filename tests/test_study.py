"""Tests for the style study: the readers, the measures, and the sourced tables."""

from fractions import Fraction
from pathlib import Path

import mido

from stmatthew.notation import music
from stmatthew.study import measure, readers, report
from stmatthew.study.metrics import Tone

KERN = """!!!COM: Bach, Johann Sebastian
!!!OTL@@DE: Ein Test
!!!SCT: BWV 0
**kern\t**kern\t**kern\t**kern
*k[f#]\t*k[f#]\t*k[f#]\t*k[f#]
*G:\t*G:\t*G:\t*G:
*M4/4\t*M4/4\t*M4/4\t*M4/4
=1\t=1\t=1\t=1
4GG\t4B\t4d\t4g
4G\t8cL\t4e\t2g
.\t8BJ\t.\t.
4F#\t[4A\t4d\t.
4D;\t4A];\t4d;\t4f#;
==\t==\t==\t==
*-\t*-\t*-\t*-
"""


def test_a_kern_file_gives_the_notes_of_four_voices():
    chorale = readers.parse_kern(KERN, "test")
    assert (chorale.title, chorale.catalogue) == ("Ein Test", "BWV 0")
    assert (chorale.tonic, chorale.minor, chorale.metre) == (7, False, "4/4")
    assert chorale.length == Fraction(4)
    bass = chorale.voice(0)
    assert [note.midi for note in bass] == [43, 55, 54, 50]
    assert [note.start for note in bass] == [0, 1, 2, 3]
    # The two tied notes of the tenor are one note of two quarter notes, with a fermata.
    tenor = chorale.voice(1)
    assert [note.duration for note in tenor] == [1, Fraction(1, 2), Fraction(1, 2), 2]
    assert tenor[-1].fermata
    soprano = chorale.voice(3)
    assert [(note.midi, note.duration, note.fermata) for note in soprano] == [
        (67, Fraction(1), False),
        (67, Fraction(2), False),
        (66, Fraction(1), True),
    ]


def test_a_chorale_line_becomes_text_of_the_music_language():
    chorale = readers.parse_kern(KERN, "test")
    assert measure.to_lilypond(chorale.voice(0)) == r"g,4 g4 fis4 d4\fermata"
    assert measure.cadences(chorale) == ["V"]
    assert measure.degree([60, 64, 67], 0) == "I"
    assert measure.degree([62, 65, 69], 0) == "ii"
    assert measure.degree([59, 62, 65, 68], 0) == "viio"


def test_a_midi_file_gives_one_line_for_each_track(tmp_path: Path):
    midi = mido.MidiFile(ticks_per_beat=384)
    control = mido.MidiTrack()
    control.append(mido.MetaMessage("time_signature", numerator=12, denominator=8, time=0))
    control.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(60), time=0))
    midi.tracks.append(control)
    track = mido.MidiTrack()
    for pitch in (59, 62):
        track.append(mido.Message("note_on", note=pitch, velocity=80, time=0))
        track.append(mido.Message("note_off", note=pitch, velocity=0, time=192))
    midi.tracks.append(track)
    path = tmp_path / "test.mid"
    midi.save(path)
    movement = readers.read_midi(path)
    assert (movement.numerator, movement.denominator) == (12, 8)
    assert movement.bar_quarters == 6.0
    assert [(tone.start, tone.duration, tone.midi) for tone in movement.tracks[0]] == [
        (0.0, 0.5, 59),
        (0.5, 0.5, 62),
    ]


def test_the_numbers_of_a_line():
    line = [Tone(0.0, 1.0, 66), Tone(1.0, 0.5, 74), Tone(1.5, 0.5, 73), Tone(3.0, 1.0, 71)]
    numbers = measure.line_numbers(line, 4.0, measure.MINOR_SCALE, 11)
    assert (numbers["lowest"], numbers["highest"]) == ("F#4", "D5")
    assert numbers["phrases"] == 2
    assert numbers["share_of_time"] == 0.75
    # The two moves inside the first phrase: a minor sixth up and a semitone down.
    assert numbers["sixth_or_larger"] == 0.5
    assert numbers["semitone"] == 0.5


def test_the_figures_of_a_text_source(tmp_path: Path):
    path = tmp_path / "test.ly"
    path.write_text(
        "cifrado=\\figuremode{\n  s8 <6>4. <6 5>4 <7 _+>8 % <9>\n  <_!>2\n}\n", encoding="utf-8"
    )
    assert readers.read_figures(path) == ["6", "6 5", "7 +", "!"]


def test_the_sourced_tables_have_no_problems():
    assert report.check() == []


def test_each_motif_is_correct_music_text():
    _, rows = report.read_table(report.TABLES_DIR / "motifs.csv")
    assert len(rows) >= 30
    for row in rows:
        parsed = music.parse(row["notes"])
        assert music.length(parsed) > 0, row["id"]


def test_the_report_is_up_to_date():
    assert report.build() == report.REPORT_PATH.read_text(encoding="utf-8")
