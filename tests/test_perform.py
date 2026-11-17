"""Tests for the performance notes."""

from fractions import Fraction

from stmatthew.notation.work import Work, load_orchestra
from stmatthew.perform.events import DYNAMIC_LEVEL, perform


def _work(player: str, text: str, bars: int = 2) -> Work:
    work = Work("Test", load_orchestra())
    section = work.section(bars, 4, 4)
    section.write(player, text)
    section.close()
    return work


def test_ties_slurs_and_dynamics():
    work = _work("vc", r"""d2\pp ~ d8 r bes,4\<( | a,4\mf g,8. f,16 e,4-. d,8.) r16 |""")
    notes = perform(work, "vc")
    assert [float(n.midi) for n in notes] == [50, 46, 45, 43, 41, 40, 38]
    assert notes[0].duration == Fraction(5, 2)  # the tie makes one note
    assert notes[0].level == DYNAMIC_LEVEL["pp"]
    # The hairpin goes from pp at the B-flat to mf at the subsequent note.
    assert notes[1].level == DYNAMIC_LEVEL["pp"]
    assert abs(notes[1].level_end - DYNAMIC_LEVEL["mf"]) < 1e-9
    assert notes[2].level == DYNAMIC_LEVEL["mf"]
    assert [n.legato for n in notes] == [False, False, True, True, True, True, True]
    assert "staccato" in notes[5].articulations


def test_techniques_change_the_state():
    work = _work("vn1", r"""a'4\pizz a' a'\arco\consord a'\sulpont | a'1:32\senzasord |""")
    notes = perform(work, "vn1")
    assert [n.get("attack") for n in notes] == ["pizzicato", "pizzicato", "arco", "arco", "arco"]
    assert [n.get("mute") for n in notes] == ["off", "off", "on", "on", "off"]
    assert notes[3].get("place") == "sul ponticello"
    assert notes[4].tremolo


def test_chords_tuplets_grace_notes_and_voices():
    work = _work(
        "va",
        r"""<d a>2 \tuplet 3/2 { d'8 e' f' } \grace { g'16 a' } b'4 |
        << { d''2 e'' } \\ { f'1 } >> |""",
    )
    notes = perform(work, "va")
    chord = [n for n in notes if n.start == 0]
    assert len(chord) == 2 and all(n.chord_size == 2 for n in chord)
    triplet = [n for n in notes if n.duration == Fraction(1, 3)]
    assert [n.start for n in triplet] == [2, Fraction(7, 3), Fraction(8, 3)]
    grace = [n for n in notes if n.grace]
    assert [(n.grace, float(n.midi)) for n in grace] == [(2, 67.0), (1, 69.0)]
    assert all(n.start == 3 for n in grace)
    voices = {(n.voice, float(n.midi)) for n in notes if n.start >= 4}
    assert voices == {(0, 74.0), (0, 76.0), (1, 65.0)}


def test_instrument_switch_and_quarter_tones():
    work = _work("fl2", r"""c''1 | \switch "alto flute" geh'1 |""")
    notes = perform(work, "fl2")
    assert [n.instrument for n in notes] == ["flute", "alto flute"]
    assert notes[1].midi == 66.5


def test_grace_notes_take_the_dynamic_of_the_main_note():
    from stmatthew.notation.work import Work, load_orchestra
    from stmatthew.perform.events import DYNAMIC_LEVEL, perform

    work = Work("Test", load_orchestra())
    section = work.section(2, 4, 4)
    section.write("fl1", r"c''1\fff | \grace { d''16 e'' } f''1\ppp |")
    section.close()
    notes = perform(work, "fl1")
    assert [note.level for note in notes if note.grace] == [DYNAMIC_LEVEL["ppp"]] * 2
