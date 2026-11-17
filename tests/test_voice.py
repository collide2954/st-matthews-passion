"""Tests for the words of the voice, the key signatures, and the groups of the score."""

import pytest

from stmatthew.notation import lilypond, lyrics, music
from stmatthew.notation.pitch import Interval
from stmatthew.notation.work import Work, WorkError, load_orchestra
from stmatthew.work import build


def _work() -> Work:
    return Work("Test", load_orchestra())


def test_a_slur_and_a_tie_make_one_syllable_from_more_than_one_note():
    state = lyrics.State()
    parsed = music.parse(r"g'4 c''8( bes') as'4~ as'8 g' \grace { f'8 } g'2")
    # g', the slur, the tied note, g', and the last g' (the grace note has no syllable).
    assert lyrics.slots(parsed.children, state) == 5
    assert lyrics.syllables("Ich will hier bei dir ste -- hen; __ _") == [
        "Ich", "will", "hier", "bei", "dir", "ste", "hen;", "_",
    ]  # fmt: skip
    assert lyrics.words("Töch -- ter, helft mir kla -- gen, __") == "Töchter, helft mir klagen,"


def test_the_words_of_a_section_must_fit_its_notes():
    work = _work()
    section = work.section(1, 4, 4)
    with pytest.raises(WorkError, match="4 notes for syllables, and the words have 3"):
        section.sing("alto", "g'4 a' b' c''", "Kommt, ihr Töch")
    section = work.section(1, 4, 4)
    section.sing("alto", "g'4 a'8( b') c''4 d''", "Kommt, ihr Töch -- ter")
    section.close()
    # A voice with notes and with no words is an error: all later words would move.
    section = work.section(1, 4, 4)
    section.write("alto", "g'1")
    with pytest.raises(WorkError, match="notes but no words"):
        section.close()


def test_the_score_has_the_words_below_the_staff_of_the_voice():
    work = _work()
    section = work.section(1, 4, 4)
    work.structure.key(section.bar(1), "e", "minor")
    section.sing("alto", "g'4 a'8( b') c''4 d''", "Kommt, ihr Töch -- ter")
    section.write("ob1", "\\switch \"oboe d'amore\" g'1")
    section.close()
    text = lilypond.score_file(work)
    assert "wordsAlto = \\lyricmode {\nKommt, ihr Töch -- ter\n}" in text
    assert '\\new Voice = "alto" { \\musicAlto }' in text
    assert '\\new Lyrics \\lyricsto "alto" { \\wordsAlto }' in text
    # The voice is immediately above the continuo group.
    assert text.index('\\new StaffGroup = "voice"') < text.index('\\new StaffGroup = "continuo"')
    assert text.index('\\new StaffGroup = "strings"') < text.index('\\new StaffGroup = "voice"')
    # Each staff has the key signature. The part of the oboe d'amore is a minor third higher.
    assert "\\key e \\minor" in text
    part = lilypond.part_file(work, "ob1", music_page=1)
    assert "\\key g \\minor" in part


def test_a_key_signature_moves_with_a_transposing_instrument():
    assert lilypond.key_command(("bes", "major")).arguments == ["bes", "\\major"]
    # The oboe da caccia is in F: its part is a fifth higher.
    command = lilypond.key_command(("as", "major"), Interval(4, 7))
    assert command.arguments == ["es", "\\major"]


def test_the_work_has_no_problems():
    from stmatthew.compose.check import check

    assert [str(problem) for problem in check(build())] == []
