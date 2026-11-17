"""Tests of the cues and of the page turns in the parts."""

from fractions import Fraction

from stmatthew.notation import cues, lilypond, music, turns
from stmatthew.notation.work import Work, load_orchestra


def _work() -> Work:
    """Return a work of 12 bars at 60 quarter notes in a minute (one bar = 4 seconds).

    The trumpet has a rest of 10 bars. The flute plays a line in bars 9 and
    10, the violins hold one note, and the bass drum has strokes.
    """
    work = Work("Test", load_orchestra())
    section = work.section(12, 4, 4)
    work.structure.tempo(1, 1, 60, "Lento")
    section.write("tpt1", r"R1*10 | c''4\f d'' e'' f'' | g''1 |")
    section.write("fl1", r"R1*8 | c''4\mf d'' e'' f'' | g''2 a''4 b'' | c'''1 | R1 |")
    section.write("vn1", r"c'1\pp ~ | c'1 ~ | c'1 ~ | c'1 ~ | c'1 ~ | c'1 ~ | c'1 ~ | c'1 ~ "
                  r"| c'1 ~ | c'1 ~ | c'1 ~ | c'1 |")  # fmt: skip
    section.write(
        "perc3", r"""\switch "bass drum" R1*8 | c'4\ff c' c' c' | c'4 c' c' c' | R1*2 |"""
    )
    section.close()
    return work


def test_a_long_rest_is_a_rest_of_many_bars_or_of_much_time():
    work = _work()
    assert cues.long_rests(work, "tpt1") == [(1, 11)]
    assert cues.long_rests(work, "vn1") == []
    # The flute has 8 bars of rest: that is the smallest number for a cue.
    assert cues.long_rests(work, "fl1") == [(1, 9)]
    # One bar is 4 seconds: two bars before the entry are more than 5 seconds.
    assert cues.cue_bars(work, 1, 11) == 2


def test_a_cue_has_the_notes_of_the_player_that_is_best_to_hear():
    work = _work()
    found = cues.find_cues(work)["tpt1"]
    assert len(found) == 1
    cue = found[0]
    # The flute has more notes than the violins. The bass drum has no pitch: it is not a cue.
    assert (cue.source, cue.label) == ("fl1", "Fl. 1")
    assert (cue.start, cue.end) == (Fraction(32), Fraction(40))
    text = music.body_to_lilypond(music.Group("sequence", cue.elements))
    assert " ".join(text.split()) == "c''4 d''4 e''4 f''4 | g''2 a''4 b''4"


def test_a_part_shows_the_cue_in_small_notes_before_the_entry():
    work = _work()
    part = " ".join(lilypond.part_file(work, "tpt1").split())
    assert (
        r"R1*8 | << { \voiceTwo R1*2 | \oneVoice } "
        r"""\new CueVoice { \voiceOne c''4^\markup \cue "Fl. 1" d''4 e''4 f''4 | """
        r"g''2 a''4 b''4 } >>" in part
    )
    # The part of the horn is a fifth higher than the real sound: its cue also.
    work = _work()
    section = work.section(12, 4, 4)
    section.write("hn1", r"R1*10 | c'1\p | c'1 |")
    section.write("fl1", r"R1*8 | c''4\mf d'' e'' f'' | g''2 a''4 b'' | R1*2 |")
    section.close()
    horn = " ".join(lilypond.part_file(work, "hn1").split())
    assert r"""\new CueVoice { \voiceOne g'4^\markup \cue "Fl. 1" a'4 b'4 c''4 |""" in horn


def test_a_cue_is_in_the_best_octave_for_the_clef():
    notes = music.parse("c'''4 d''' e''' f'''").children
    fitted = cues.fitted(notes, "bass", 0)
    assert music.body_to_lilypond(music.Group("sequence", fitted)) == "c4 d e f"
    notes = music.parse("c,4 d, e, f,").children
    fitted = cues.fitted(notes, "treble", 0)
    assert music.body_to_lilypond(music.Group("sequence", fitted)) == "c''4 d'' e'' f''"


def test_a_cue_in_a_staff_with_no_pitch_has_its_own_clef():
    work = _work()
    section = work.section(12, 4, 4)
    section.write("perc3", r"R1*10 | c'4\ff c' c' c' | R1 |")
    section.write("fl1", r"R1*8 | c''4\mf d'' e'' f'' | g''2 a''4 b'' | R1*2 |")
    section.close()
    drum = " ".join(lilypond.part_file(work, "perc3").split())
    assert r'\new CueVoice { \voiceOne \cueClef "treble"' in drum
    assert r"\cueClefUnset } >>" in drum


def test_a_page_turn_is_possible_at_a_rest_of_four_seconds():
    work = _work()
    # The trumpet rests from bar 1 to bar 10. A turn is possible where the rest stops
    # (bar 11), and where the cue starts (bar 9).
    found = cues.find_cues(work)["tpt1"]
    starts = frozenset(cue.start for cue in found)
    assert turns.turn_bars(work, "tpt1", starts) == {9, 11}
    # The violins hold one note. Two string players read one part: one of them turns the
    # page while the other plays. Thus each bar line is possible.
    assert turns.turn_bars(work, "vn1") == set(range(2, 13))
    # A wind player who holds a note has no page turn.
    section = work.section(4, 4, 4)
    section.write("ob1", r"c''1\p ~ | c''1 ~ | c''1 ~ | c''1 |")
    section.close()
    assert not turns.turn_bars(work, "ob1") & {14, 15, 16}
    # The flute: where the rest at the start stops. No turn after its last note.
    assert turns.turn_bars(work, "fl1") == {9}
    part = lilypond.part_file(work, "tpt1")
    assert part.count("\\allowPageTurn") == 2


def test_a_keyboard_player_turns_a_page_with_a_free_hand():
    work = Work("Test", load_orchestra())
    section = work.section(4, 4, 4)
    work.structure.tempo(1, 1, 60, "Lento")
    section.write("pno.rh", r"c''4\f d'' e'' f'' | c''4 d'' e'' f'' | c''4 d'' e'' f'' | c''1 |")
    section.write("pno.lh", r"c4\f d e f | R1*2 | c1 |")
    section.close()
    # The left hand is free in bars 2 and 3 (8 seconds).
    assert turns.turn_bars(work, "pno") == {2, 3, 4}


def test_an_octave_sign_stops_at_a_long_rest():
    work = Work("Test", load_orchestra())
    section = work.section(4, 4, 4)
    section.write("pno.rh", r"R1*4 |")
    section.write("pno.lh", r"c,,1\f | R1*2 | c,,1 |")
    section.close()
    part = " ".join(lilypond.part_file(work, "pno").split())
    assert r"\ottava #-1 c,,1\f \ottava #0 | R1*2 | \ottava #-1 c,,1 |" in part


def test_a_percussion_staff_starts_with_the_clef_of_its_first_instrument():
    work = _work()
    drum = " ".join(lilypond.part_file(work, "perc3").split())
    assert "musicPercC = { \\clef percussion" in drum


def test_a_change_of_instrument_has_a_notice_and_a_name():
    work = Work("Test", load_orchestra())
    section = work.section(6, 4, 4)
    section.write("fl3", r"""c'''4\f r r2 | \switch "flute" R1*3 | c''1\p | R1 |""")
    section.write("perc1", r"R1*2 | c''4\mf r r2 | R1*3 |")
    section.close()
    part = " ".join(lilypond.part_file(work, "fl3").split())
    # After the last note on the piccolo, the first rest has the notice.
    assert r"""c''4\f r^\markup \tochange "to Flute" r2 |""" in part
    # The name of the new instrument is at its first note, not at the start of the rest.
    assert r"""R1*3 | \clef treble <>^\markup \instrumentchange "Flute" c''1\p""" in part
    # A percussion player has many instruments: the first note has the name of its instrument.
    drums = " ".join(lilypond.part_file(work, "perc1").split())
    assert r"""R1*2 | \clef treble <>^\markup \instrumentchange "Vibraphone" c''4\mf""" in drums


def test_a_long_rest_can_start_with_the_notice_of_a_change():
    work = Work("Test", load_orchestra())
    section = work.section(8, 4, 4)
    section.write("fl3", r"""c'''1\f | \switch "flute" R1*6 | c''1\p |""")
    section.close()
    part = " ".join(lilypond.part_file(work, "fl3").split())
    assert r"""R1*6^\markup \tochange "to Flute" |""" in part


def test_a_percussion_part_starts_with_a_key():
    from stmatthew.notation import frontmatter

    work = Work("Test", load_orchestra())
    section = work.section(4, 4, 4)
    section.write(
        "perc5",
        r"""\switch "tom-toms" a4\f c' e' c' | R1 | \switch "triangle" R1 | c'4\p r r2 |""",
    )
    section.close()
    sentences = frontmatter.percussion_key(work, "perc5")
    assert sentences[0] == "Instruments, in the sequence of their use: tom-toms, triangle."
    assert sentences[1] == (
        "Tom-toms: 3 sizes. From the largest to the smallest, their notes are on "
        "the second line, the middle line, the fourth line."
    )
    part = lilypond.part_file(work, "perc5")
    assert '"Instruments," "in" "the" "sequence"' in part
    # The timpani player has one instrument: no key.
    assert '"Instruments,"' not in lilypond.part_file(work, "timp")


def test_the_set_has_the_names_that_a_librarian_expects():
    work = Work("Night Test", load_orchestra(), composer="Ada Example")
    names = lilypond.set_names(work)
    assert names["score"] == "EXAMPLE Night Test 00 - Score in C"
    assert names["score-transposed"] == "EXAMPLE Night Test 00 - Transposed score"
    assert names["part-fl1"] == "EXAMPLE Night Test 01 - Flute 1"
    assert names["part-cb"] == "EXAMPLE Night Test 44 - Double Bass"


def test_a_part_has_a_cover_and_the_music_starts_on_page_two():
    work = Work("Night Test", load_orchestra(), composer="Ada Example")
    section = work.section(10, 4, 4)
    work.structure.tempo(1, 1, 60, "Lento")
    section.write("fl2", r"""c''1\p\flz | R1*8 | \switch "alto flute" c'1\p |""")
    section.write("fl1", r"c''4\mf d'' e'' f'' | " * 9 + "R1 |")
    section.close()
    part = lilypond.part_file(work, "fl2")
    # The cover: the composer, the instrument with its second instrument, and the notes.
    assert part.count("\\bookpart {") == 2
    assert '"A" \\hspace #0.35 "D" \\hspace #0.35 "A"' in part
    assert '\\bold "Flute 2"' in part
    assert '"also Alto Flute"' in part
    assert '"Notes for the player"' in part
    assert '"cues:"' in part  # this part has a cue
    assert '"take" "a" "different" "instrument."' in part
    assert '"Flutter-tongue."' in part  # the meaning of "flz."
    # A part with no cover starts with the music.
    plain = lilypond.part_file(work, "fl2", music_page=1)
    assert "\\bookpart {" not in plain
    # With the music on a right page, an empty page comes after the cover.
    right = lilypond.part_file(work, "fl2", music_page=3)
    assert "\\pageBreak" in right and "\\markup \\null" in right
    assert "\\pageBreak" not in part


def test_the_build_selects_the_page_on_which_the_music_starts():
    from stmatthew.notation import pages

    # A page with few staves costs much: the layout with full pages is better.
    assert pages.cost([12, 12, 11, 11, 11, 9]) < pages.cost([8, 11, 11, 10, 11, 11, 3])
    assert pages.better_start([12, 12, 11, 11, 11, 9], [8, 11, 11, 10, 11, 11, 3]) == 2
    assert pages.better_start([7, 7, 12, 10, 12, 4], [11, 12, 10, 12, 12]) == 3
    # The last page can have few staves. A page with more than 12 staves is too full.
    assert pages.cost([11, 11, 2]) == pages.cost([11, 11, 9])
    assert pages.cost([14, 11]) > pages.cost([12, 11])
    # A part with two staves in a system: 5 systems on a page are sufficient.
    assert pages.cost([10, 10, 10], 2) == pages.cost([12, 12, 10], 2)
