"""Tests for the music language, the structure, and the LilyPond writer."""

import shutil
import subprocess
from fractions import Fraction

import pytest

from stmatthew.notation import lilypond, music
from stmatthew.notation.pitch import Interval, Pitch, from_midi
from stmatthew.notation.structure import Structure, global_to_lilypond
from stmatthew.notation.work import Work, WorkError, load_orchestra


def test_pitch_names_and_midi():
    assert Pitch.parse("c'").midi == 60
    assert Pitch.parse("bes,").midi == 46
    assert Pitch.parse("fis''").midi == 78
    assert Pitch.parse("es'").midi == 63
    assert Pitch.parse("as").midi == 56
    assert Pitch.parse("deh'").midi == 61.5
    assert Pitch.parse("cih'").midi == 60.5
    for name in ["c'", "bes,", "fis''", "es'", "as", "deh'", "eeseh", "aisis,,", "eeh'"]:
        assert Pitch.parse(name).name == name
    assert from_midi(61).name == "des'"
    assert from_midi(61, prefer_sharps=True).name == "cis'"
    assert from_midi(60.5).midi == 60.5


def test_transposition_gives_a_good_spelling():
    major_second = Interval(1, 2)
    fifth = Interval(4, 7)
    assert Pitch.parse("bes").transposed(major_second).name == "c'"
    assert Pitch.parse("cis'").transposed(major_second).name == "dis'"
    assert Pitch.parse("a").transposed(fifth).name == "e'"
    # A-sharp up a major second is B-sharp. The simple spelling is C.
    assert Pitch.parse("ais").transposed(major_second).simplified().name == "c'"
    assert Pitch.parse("deh'").transposed(major_second).name == "eeh'"


def test_parser_reads_durations_and_events():
    parsed = music.parse(r"""d'4\pp( e'8. f'16) <g' b'>2-> ~ | <g' b'>1\fermata |""")
    notes = [e for e in parsed.children if isinstance(e, music.Note)]
    assert [n.duration for n in notes] == [1, Fraction(3, 4), Fraction(1, 4), 2, 4]
    assert notes[0].posts[0].kind == "dynamic" and notes[0].posts[0].value == "pp"
    assert notes[3].chord and [p.pitch.midi for p in notes[3].pitches] == [67, 71]
    assert [p.kind for p in notes[3].posts] == ["articulation", "tie"]
    assert music.length(parsed) == 8


def test_parser_handles_groups():
    parsed = music.parse(
        r"""\tuplet 3/2 { c'8 d' e' } \grace { f'16 g' } a'4 << { c''2 } \\ { e'4 f' } >>"""
    )
    assert music.length(parsed) == 4
    assert music.length(music.parse(r"\repeat tremolo 8 { c'16 e' }")) == 4
    assert music.length(music.parse(r"R1*3/4 R1*4")) == 19
    # A duration with a multiplier does not change the duration of the subsequent notes.
    assert music.length(music.parse(r"s4*5 c'")) == 6


def test_parser_reports_errors():
    with pytest.raises(music.MusicSyntaxError):
        music.parse(r"c'4 \unknowncommand d'4")
    with pytest.raises(music.MusicSyntaxError):
        music.length(music.parse(r"<< { c'2 } \\ { c'4 } >>"))


def test_output_is_the_same_music():
    text = r"""d'4\pp( e'8. f'16) <g' b'>2->~ |
\tuplet 3/2 { c'8 d' e' } r4 r2\fermata |"""
    parsed = music.parse(text)
    again = music.parse(music.body_to_lilypond(parsed))
    assert music.body_to_lilypond(again) == music.body_to_lilypond(parsed)
    transposed = music.body_to_lilypond(parsed, Interval(1, 2))
    assert transposed.startswith("e'4\\pp( fis'8. g'16) <a' cis''>2->~")


def test_structure_times():
    structure = Structure()
    structure.add_bars(4, 4, 4)
    structure.add_bars(2, 7, 8, (2, 2, 3))
    structure.tempo(1, 1, 60, "Lento")
    assert structure.length == 23
    assert structure.position(2, 3) == 6
    assert structure.position(5, 3) == 17
    assert structure.seconds(Fraction(16)) == pytest.approx(16.0)
    # A gradual change from 60 to 120 in bars 3 and 4.
    structure.change(3, 1, "accel.")
    structure.tempo(5, 1, 120, "Allegro")
    assert structure.bpm_at(Fraction(12)) == pytest.approx(90.0)
    assert structure.seconds(Fraction(16)) == pytest.approx(8.0 + 8 * 0.6931, rel=1e-3)
    text = global_to_lilypond(structure)
    assert "\\time 2,2,3 7/8" in text
    assert '\\tempo "Lento" 4 = 60' in text
    assert "s1*2 " in text  # bars 1 and 2 are one spacer rest


def _small_work() -> Work:
    work = Work("Test", load_orchestra())
    section = work.section(2, 4, 4)
    work.structure.tempo(1, 1, 60, "Lento")
    section.write("cl1", r"""R1 | d'2\p( e'2) |""")
    section.write("vc", r"""d1\pp ~ | d1 |""")
    section.close()
    return work


def test_section_checks_the_length_and_the_bar_lines():
    work = _small_work()
    work.check_complete()
    section = work.section(1, 3, 4)
    with pytest.raises(WorkError, match="quarter notes"):
        section.write("vc", r"d1 |")
    with pytest.raises(WorkError, match="bar check"):
        work.section(2, 4, 4).write("vc", r"d2. | d4 d1 |")


@pytest.mark.skipif(shutil.which("lilypond") is None, reason="LilyPond is not installed")
def test_lilypond_compiles_the_files(tmp_path):
    work = _small_work()
    paths = lilypond.write_all(work, tmp_path)
    for name in ["score.ly", "score-transposed.ly", "part-cl1.ly", "part-harp.ly"]:
        result = subprocess.run(
            ["lilypond", "-dno-point-and-click", "--loglevel=ERROR", name],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    # The score in C, the transposed score, and two layouts of each of the 44 parts.
    assert len(paths) == 90
    assert (tmp_path / "score.pdf").exists()


def test_three_quarter_flat_names_are_valid_in_lilypond():
    from fractions import Fraction

    from stmatthew.notation.pitch import Interval, Pitch

    low = Pitch.parse("beseh'").transposed(Interval(3, 5))  # a fourth higher
    assert low.alter == Fraction(-3, 2)
    assert low.name == "eeseh''"
    assert Pitch.parse("es'").name == "es'"
    assert Pitch.parse("aeseh").name == "aeseh"


def test_a_fermata_adds_time_to_the_end_of_a_bar():
    from stmatthew.notation.structure import Structure

    structure = Structure()
    structure.add_bars(3, 4, 4)
    structure.tempo(1, 1, 60, "Lento")
    structure.fermata(2, 3.0)
    assert structure.seconds(structure.bar(2).start) == pytest.approx(4.0)
    assert structure.seconds(structure.bar(3).start) == pytest.approx(11.0)  # 4 s and 3 s more
    assert structure.seconds(structure.length) == pytest.approx(15.0)  # the tempo comes back
    # A gradual change of tempo before the fermata keeps its own speed.
    slower = Structure()
    slower.add_bars(3, 4, 4)
    slower.tempo(1, 1, 60, "Lento")
    slower.change(1, 1, "rit.")
    slower.tempo(3, 1, 30, "Largo")
    plain = slower.seconds(slower.bar(2).start)
    slower.fermata(2, 3.0)
    assert slower.seconds(slower.bar(2).start) == pytest.approx(plain)


def test_a_hand_of_the_piano_changes_its_clef_in_a_bar_that_is_wide():
    work = Work("Test", load_orchestra())
    section = work.section(3, 4, 4)
    work.structure.tempo(1, 1, 60, "Lento")
    # Bar 1: a line from the low register to the high register. Bar 2: only low notes.
    # Bar 3: a narrow bar near middle C keeps the clef of the bar before it.
    section.write("pno.lh", r"c,4\f g, e'' c''' | c,4 g, c g, | b4 c' d' c' |")
    section.close()
    text = " ".join(lilypond.part_file(work, "pno").split())
    expected = (
        r"musicPnolh = { \clef bass c,4\f g, \clef treble e'' c''' | "
        r"\clef bass c,4 g, c g, | b4 c' d' c' | }"
    )
    assert expected in text
    # The division of a bar at its beats: a tuplet stays in one piece.
    bar = music.parse(r"c8 d \tuplet 3/2 { e8 f g } a2 |").children
    pieces = lilypond._beat_pieces(bar, [Fraction(1)] * 4)
    assert [len(piece) for piece in pieces] == [2, 1, 1, 1]
    # The beat groups of a bar: the groups of an uneven metre, or quarter notes.
    structure = Structure()
    structure.add_bars(1, 8, 8, (3, 3, 2))
    structure.add_bars(1, 4, 4)
    structure.add_bars(1, 6, 8)
    lengths = [lilypond._beat_groups(bar) for bar in structure.bars]
    assert lengths[0] == [Fraction(3, 2), Fraction(3, 2), Fraction(1)]
    assert lengths[1] == [Fraction(1)] * 4
    assert lengths[2] == [Fraction(3, 2)] * 2


def test_the_systems_of_the_score_are_equally_full():
    # A short bar between two long bars does not stay alone: a system can be a little
    # more than full.
    assert lilypond.system_breaks([20.0, 40.0, 20.0, 40.0, 20.0, 40.0], 56.0, 10) == {2, 4}
    # Bars that go into one system have no break. The last system can be empty in part.
    assert lilypond.system_breaks([10.0] * 5, 56.0, 10) == set()
    assert lilypond.system_breaks([10.0] * 7, 56.0, 10) == {5}
    # A system has not more than the largest number of bars.
    assert lilypond.system_breaks([1.0] * 9, 56.0, 4) == {4, 8}
    # A bar that is wider than a system is alone.
    assert lilypond.system_breaks([30.0, 90.0, 30.0], 56.0, 10) == {1, 2}


def _one_player(text: str, bars: int, player: str = "vc", other: str = "") -> str:
    """Return the music of one player after the section is complete."""
    work = Work("Test", load_orchestra())
    section = work.section(bars, 4, 4)
    work.structure.tempo(1, 1, 60, "Lento")
    section.write(player, text)
    if other:
        section.write(player.replace(".lh", ".rh"), other)
    section.close()
    written = music.body_to_lilypond(work.music_of(player))
    return " ".join(written.split())


def test_a_hairpin_stops_at_a_silence():
    # A hairpin with no end: it stops at the start of the rest.
    assert _one_player(r"c1\p\< | R1 | R1 | d1 |", 4) == r"c1\p\< | R1\! | R1 | d1 |"
    assert _one_player(r"c2\p\> r2 | R1 |", 2) == r"c2\p\> r2\! | R1 |"
    # Short rests in a figure do not stop a hairpin.
    figure = r"c4\p\< r4 d4 r4 | e4 r4 f4 r4 | g1\f |"
    assert _one_player(figure, 3) == figure
    # A hairpin that has its end mark before the rest does not change.
    assert _one_player(r"c1\p\< | d1\f | R1 |", 3) == r"c1\p\< | d1\f | R1 |"
    # A hairpin cannot start on a rest.
    assert _one_player(r"r1\< | c1\f |", 2) == r"r1 | c1\f |"


def test_a_crescendo_through_entries_with_rests_gets_a_mark_at_each_entry():
    # The old hairpin went from p (bar 1) to ff (bar 7), through two entries.
    text = r"c1\p\< | R1 | d4 r2. | R1 | e4 f4 r2 | R1 | g1\ff |"
    expected = r"c1\p\< | R1\! | d4\mp r2. | R1 | e4\f\< f4 r2\! | R1 | g1\ff |"
    assert _one_player(text, 7) == expected
    # A diminuendo: the marks go down, and the mark of the end stays new.
    text = r"c1\f\> | R1 | d4 e4 r2 | R1 | g1\p |"
    assert _one_player(text, 5) == r"c1\f\> | R1\! | d4\mf\> e4 r2\! | R1 | g1\p |"


def test_a_rest_of_one_hand_is_not_a_silence_while_the_other_hand_plays():
    left = r"c4\p\< r2. | r2. d4 | e1\f |"
    assert _one_player(left, 3, "pno.lh", r"r4 c'2. | d'2. r4 | e'1\f |") == left
    # The two hands have a rest: the hairpin stops, and the entry after it gets a mark.
    stopped = _one_player(left, 3, "pno.lh", r"R1 | R1 | e'1\f |")
    assert stopped == r"c4\p\< r2.\! | r2. d4\mf | e1\f |"


def test_a_long_rest_of_a_part_stops_at_a_change_of_tempo():
    work = Work("Test", load_orchestra())
    section = work.section(8, 4, 4)
    work.structure.tempo(1, 1, 60, "Lento")
    work.structure.change(5, 1, "poco rit.")
    section.write("vc", r"R1*8 |")
    section.write("va", r"R1*4 | R1 | R1 | R1 | c'1\p |")
    section.close()
    cello = " ".join(lilypond.part_file(work, "vc").split())
    # Bar 5 has the words "poco rit.": the rest of 8 bars stops there and starts again.
    assert "musicVc = { \\clef bass R1*4 | R1*4 | }" in cello
    assert "extra-spacing-width" in cello  # the words take their own width
    viola = " ".join(lilypond.part_file(work, "va").split())
    assert "R1*4 | R1*3 | c'1\\p |" in viola
    # The parts have the staff height of the guidelines: 7 mm or more.
    assert lilypond.part_staff_size("woodwinds") * 0.3528 >= 7.0
    assert lilypond.part_staff_size("strings") > lilypond.part_staff_size("brass")
