"""Tests for the notation of tones with free times, and for the ears of the composer."""

from fractions import Fraction as F

import pytest

from stmatthew.compose import ears, rhythm
from stmatthew.compose.rhythm import Tone, notate
from stmatthew.notation import music
from stmatthew.notation.work import Work, WorkError, load_orchestra


def test_a_tone_is_divided_at_the_strong_places_of_the_bar():
    # Dotted quarter notes in 4/4: the middle of the bar and the bar line divide them.
    line = [Tone(F(3 * n, 2), F(3, 2), name) for n, name in enumerate(["c'", "d'", "e'", "f'"])]
    assert notate(line, 4, 4, 2) == "c'4. d'8~ d'4 e'4~ | e'8 f'8~ f'4 r2 |"
    # The simple syncopations stay one note.
    assert notate([Tone(F(1, 2), F(1), "c'")], 4, 4, 1) == "r8 c'4 r8 r2 |"
    assert notate([Tone(F(1), F(2), "c'")], 4, 4, 1) == "r4 c'2 r4 |"
    # A quarter note across the middle of the bar is two eighth notes.
    assert notate([Tone(F(3, 2), F(1), "c'")], 4, 4, 1) == "r4 r8 c'8~ c'8 r8 r4 |"


def test_the_marks_go_to_the_start_and_to_the_end_of_a_divided_tone():
    line = [Tone(F(3), F(2), "c'", marks=r"\p", end=r"\fermata")]
    assert notate(line, 4, 4, 2) == r"r2 r4 c'4\p~ | c'4\fermata r4 r2 |"
    assert notate([Tone(F(8), F(4), "<c e g>")], 4, 4, 3) == "R1*4/4*2 | <c e g>1 |"


def test_a_compound_metre_shows_its_beats():
    assert notate([Tone(F(1), F(3, 2), "c'")], 12, 8, 1) == "r4 c'8~ c'4 r8 r2. |"
    # Two beats from a beat: one note. A full bar: one note.
    assert notate([Tone(F(3, 2), F(3), "c'")], 12, 8, 1) == "r4. c'4.~ c'4. r4. |"
    assert notate([Tone(F(0), F(6), "c'")], 12, 8, 1) == "c'1. |"
    assert notate([Tone(F(0), F(3, 2), "c'")], 3, 8, 2) == "c'4. | R1*3/8 |"


def test_each_result_has_the_length_of_its_bars():
    line = [Tone(F(n * 5, 8), F(5, 8), "c'") for n in range(12)]
    for numerator, denominator in ((4, 4), (3, 4), (12, 8), (6, 8)):
        bar = F(4 * numerator, denominator)
        count = int(F(60, 8) // bar) + 1
        text = notate(line, numerator, denominator, count)
        assert music.length(music.parse(text)) == count * bar
        # All parts of a tone but its last part have a tie.
        assert text.count("~") == text.count("c'") - 12


def test_music_text_becomes_tones_and_a_slower_line():
    line = rhythm.tones(r"c'4\p d'2~ | d'4 e'\fermata")
    assert line == [
        Tone(F(0), F(1), "c'", r"\p"),
        Tone(F(1), F(3), "d'"),
        Tone(F(4), F(1), "e'", end=r"\fermata"),
    ]
    slow = rhythm.stretch(line, F(3, 2))
    assert [(tone.start, tone.length) for tone in slow] == [
        (F(0), F(3, 2)), (F(3, 2), F(9, 2)), (F(6), F(3, 2)),
    ]  # fmt: skip
    assert rhythm.span(slow) == F(15, 2)
    assert notate(slow, 4, 4, 2) == r"c'4.\p d'8~ d'2~ | d'2 e'4.\fermata r8 |"


def test_a_note_must_not_go_across_a_bar_line():
    work = Work("Test", load_orchestra())
    section = work.section(2, 4, 4)
    with pytest.raises(WorkError, match="across a bar line"):
        section.write("vn1", "c'2. d'2 e'2.")
    section.write("vn1", "c'2. d'4~ d'4 e'2.")


def _chorale(viola: str = "c'4 b a d' | e1 |") -> Work:
    work = Work("Test", load_orchestra())
    section = work.section(2, 4, 4)
    section.write("vn1", "e''4 d'' c'' b' | c''1 |")
    section.write("vn2", "g'4 g' e' g' | g'1 |")
    section.write("va", viola)
    section.write("vc", "c4 g, a, g, | c1 |")
    section.close()
    return work


def test_the_ears_name_the_chords():
    work = _chorale()
    found = ears.moments(work, 1, 2)
    assert [moment.symbol for moment in found[:5]] == ["C", "G", "Am", "G", "C"]
    assert found[0].figures == "8 5 3"
    assert not found[0].clashes and not found[0].cluster
    assert ears.summary(found)["major and minor triads"] == 1.0
    assert ears.parallels(work, 1, 2) == []
    assert ears.chord_symbol([50, 57, 60, 66]) == "D7"
    assert ears.chord_symbol([64, 67, 72]) == "C/E"
    assert ears.chord_symbol([60, 61, 62]) == "{C C# D}"
    clash = ears.Moment(1, F(1), ((60, "va"), (64, "vn2"), (65, "vn1")))
    assert clash.clashes == ((64, 65),) and clash.cluster is False


def test_the_ears_find_parallel_fifths_and_not_a_doubling():
    # The viola is a fifth above the violoncello for three chords.
    work = _chorale("g4 d e d | g1 |")
    names = [str(item) for item in ears.parallels(work, 1, 2, ["va", "vc"])]
    assert names == [
        "bar 1, beat 2: parallel fifths, va and vc",
        "bar 1, beat 3: parallel fifths, va and vc",
        "bar 1, beat 4: parallel fifths, va and vc",
        "bar 2, beat 1: parallel fifths, va and vc",
    ]
    # The viola has the line of the violoncello one octave higher: this is a doubling.
    work = _chorale("c'4 g a g | c'1 |")
    assert ears.parallels(work, 1, 2, ["va", "vc"]) == []


def test_a_fermata_and_a_rest_are_breaths_of_the_voice():
    work = Work("Test", load_orchestra())
    section = work.section(3, 4, 4)
    work.structure.tempo(1, 1, 60, "")
    section.write("vn1", r"c''4 d'' e''2\fermata | f''4 g'' a''2 | r4 c''2. |")
    section.close()
    found = ears.phrases(work, "vn1")
    assert [(phrase.bar, phrase.notes, phrase.seconds) for phrase in found] == [
        (1, 3, 4.0), (2, 3, 4.0), (3, 1, 3.0),
    ]  # fmt: skip
