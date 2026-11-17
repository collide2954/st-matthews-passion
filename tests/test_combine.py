"""Tests of the staves that two players share in the conductor score."""

from fractions import Fraction

from stmatthew.notation import combine, music
from stmatthew.notation.work import Work, load_orchestra


def _work(
    first: str, second: str, bars: int = 0, players: tuple[str, str] = ("fl1", "fl2")
) -> Work:
    """Return a work in 4/4 with the music of two players."""
    work = Work("Test", load_orchestra())
    count = bars or first.count("|")
    section = work.section(count, 4, 4)
    section.write(players[0], first)
    section.write(players[1], second)
    section.close()
    return work


def _text(elements: list[music.Element]) -> str:
    return " ".join(music.body_to_lilypond(music.Group("sequence", elements)).split())


def test_a_duration_has_a_text():
    assert combine.duration_text(Fraction(1)) == "4"
    assert combine.duration_text(Fraction(3, 2)) == "4."
    assert combine.duration_text(Fraction(4)) == "1"
    assert combine.duration_text(Fraction(7, 2)) == "2.."
    assert combine.duration_text(Fraction(5)) == "1*5/4"
    assert combine.duration_text(Fraction(16)) == "1*4"


def test_each_bar_of_a_pair_has_a_mode():
    work = _work(
        r"R1 | c''4\p d'' e'' f'' | g''1 | e''2 f'' | c''4 d'' e''2 | R1 |",
        r"R1 | R1 | g''1\p | c''2 d'' | c''1 | a'1 |",
    )
    units, extras = combine.pair_units(work, "fl1", "fl2")
    assert [unit.mode for unit in units] == ["rest", "one", "unison", "chords", "voices", "two"]
    assert not extras


def test_the_staff_has_labels_chords_and_two_voices():
    work = _work(
        r"R1 | c''4\p d'' e'' f'' | g''1 | e''2 f'' | c''4 d'' e''2 | R1 |",
        r"R1 | R1 | g''1\p | c''2 d'' | c''1 | a'1 |",
    )
    staff = combine.shared_staff(work, "fl1", "fl2")
    one, two = (_text(voice) for voice in staff.chunks[0])
    assert one == (
        r"\oneVoice R1 | "
        r"""c''4\p^\markup \players "1." d''4 e''4 f''4 | """
        # Player 2 starts here: the staff gives the level again.
        r"""g''1\p^\markup \players "a 2" | """
        r"<c'' e''>2 <d'' f''>2 | "
        r"\voiceOne c''4 d''4 e''2 | "
        r"s1 |"
    )
    assert two == (
        r"s1 | s1 | s1 | s1 | "
        r"\voiceTwo c''1 | "
        r"""\oneVoice a'1^\markup \players "2." |"""
    )


def test_a_dynamic_mark_for_one_player_is_for_the_two_players_at_the_same_level():
    # Player 2 starts at the level that player 1 has: the staff shows one mark.
    work = _work(r"c''1\f | e''1 |", r"R1 | c''1\f |")
    units, _ = combine.pair_units(work, "fl1", "fl2")
    assert [unit.mode for unit in units] == ["one", "chords"]
    assert _text(units[1].merged) == r"<c'' e''>1\f"
    # Different levels: two voices.
    work = _work(r"c''1\f | e''1 |", r"R1 | c''1\p |")
    assert [unit.mode for unit in combine.pair_units(work, "fl1", "fl2")[0]] == ["one", "voices"]


def test_a_tie_of_player_two_does_not_go_from_one_voice_to_the_other_voice():
    # Bar 1 needs two voices. The tie of player 2 goes into bar 2: bar 2 has two voices also.
    work = _work(r"e''2\p f'' | e''1 | e''1 |", r"c''1\p ~ | c''1 | c''1 |")
    units, _ = combine.pair_units(work, "fl1", "fl2")
    assert [unit.mode for unit in units] == ["voices", "voices", "chords"]


def test_two_voices_show_a_dynamic_mark_one_time():
    work = _work(r"e''2\p\< f''2 | g''1\f |", r"c''1\p\< | d''2\f e''2 |")
    staff = combine.shared_staff(work, "fl1", "fl2")
    one, two = (_text(voice) for voice in staff.chunks[0])
    assert one == r"\voiceOne e''2\p\< f''2 | g''1\f |"
    assert two == r"\voiceTwo c''1 | d''2 e''2 |"


def test_different_dynamics_are_above_and_below_the_staff():
    work = _work(r"e''2\f\espr f''2 |", r"c''1\pp |")
    staff = combine.shared_staff(work, "fl1", "fl2")
    one, two = (_text(voice) for voice in staff.chunks[0])
    assert one == r"""\dynamicUp \voiceOne e''2\f^\markup { \italic "espr." } f''2 |"""
    assert two == r"\voiceTwo c''1\pp |"


def test_a_hairpin_stops_where_its_player_stops():
    # Player 1 stops after bar 1, and player 2 continues: the hairpin of voice one stops.
    work = _work(r"e''1\p\< | R1 |", r"c''1\p\< | c''1\f |")
    staff = combine.shared_staff(work, "fl1", "fl2")
    one, two = (_text(voice) for voice in staff.chunks[0])
    assert one == r"\oneVoice <c'' e''>1\p\< | s1\! |"
    assert two == r"""s1 | \oneVoice c''1\f^\markup \players "2." |"""


def test_the_label_is_given_again_at_a_new_system_and_after_a_long_silence():
    first = r"c''1\p | c''1 | c''1 | R1*2 | c''1 | R1 | c''1 |"
    work = _work(first, "R1*8 |", bars=8)
    staff = combine.shared_staff(work, "fl1", "fl2", frozenset({1, 3}))
    one = _text(staff.chunks[0][0])
    # Bar 1, bar 3 (a new system), and bar 6 (after two bars of silence): not bar 8.
    assert one.count(r'\players "1."') == 3
    assert one.endswith(r"R1 | c''1 |")


def test_a_rest_of_many_bars_and_a_repeat_are_divided_into_bars():
    work = _work(r"R1*2 | \repeat unfold 2 { c''4\p d'' e'' f'' | } |", r"R1*4 |", bars=4)
    units, _ = combine.pair_units(work, "fl1", "fl2")
    assert [unit.mode for unit in units] == ["rest", "rest", "one", "one"]
    assert [unit.length for unit in units] == [Fraction(4)] * 4


def test_a_mark_of_two_voices_shows_where_it_is_first():
    # Player 2 starts first, with the same marks as player 1: voice two shows them.
    work = _work(r"r2 e''2\p\< | g''1\f |", r"c''1\p\< | d''2\f e''2 |")
    staff = combine.shared_staff(work, "fl1", "fl2")
    one, two = (_text(voice) for voice in staff.chunks[0])
    assert one == r"\voiceOne r2 e''2 | g''1\f |"
    # The hairpin of voice two stops at the mark that voice one shows.
    assert two == r"\voiceTwo c''1\p\< | d''2\! e''2 |"
