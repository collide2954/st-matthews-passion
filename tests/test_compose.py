"""Tests for the tools of the composer."""

from stmatthew.compose.tools import (
    Block,
    bars,
    double,
    dyn,
    fill,
    first,
    invert,
    lines,
    octave,
    scatter,
    times,
    tr,
)
from stmatthew.notation import music


def test_transposition_keeps_the_rhythm_and_the_marks():
    theme = r"d4.\pp( es8 f4. g8 | as2.) r4 |"
    assert tr(theme, 5) == "g4.\\pp( as8 bes4. c'8 |\ndes'2.) r4 |"
    assert octave(theme, -1).startswith("d,4.\\pp( es,8")
    assert music.length(music.parse(tr(theme, 3))) == 8


def test_inversion_is_the_mirror_form():
    # The walking theme goes up from D to A-flat. Its mirror goes down from D to G-sharp.
    up = r"d4. es8 f4. g8 | as2. r4 |"
    assert invert(up, "d") == "d4. cis8 b,4. a,8 |\ngis,2. r4 |"
    # The mirror of the mirror is the first form.
    assert invert(invert(up, "d"), "d") == "d4. es8 f4. g8 |\nas2. r4 |"


def test_times():
    assert times("c'4 d'", 3) == "c'4 d' c'4 d' c'4 d'"


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_first_puts_marks_on_the_first_rest_or_note():
    assert _flat(first(r"r8 d8( es4)", r"\senzasord")) == r"r8\senzasord d8( es4)"
    assert _flat(first(r"r8 d8( es4)", r"\pp", note=True)) == r"r8 d8\pp( es4)"


def test_dyn_replaces_the_dynamic_marks():
    assert _flat(dyn(r"d4\mf\< e4 f2\f", r"\pp")) == r"d4\pp e4 f2"


def test_lines_divides_chords_into_voices():
    low, high = lines(r"<d a>1\p( <c bes>1) | r1 |")
    assert _flat(low) == r"d1\p( c1) | r1 |"
    assert _flat(high) == r"a1\p( bes1) | r1 |"


def test_fill_makes_a_figure_from_each_chord():
    figure = fill(r"<c e g>1\p <d f a>1", r"A8 B C B A' X4. |")
    assert _flat(figure) == r"c8\p e g e c' <c e g>4. | d8 f a f d' <d f a>4. |"


def test_double_adds_the_octave():
    assert _flat(double(r"c4 d", -1)) == r"<c, c>4 <d, d>"
    assert _flat(double(r"c4", 1)) == r"<c c'>4"


def test_bars_puts_music_in_the_named_bars():
    assert bars(3, "R1 |", {2: "c1 |"}) == "R1 | c1 | R1 |"


def test_block_writes_phrases_and_rests():
    from stmatthew.notation.work import Work, load_orchestra

    work = Work("Test", load_orchestra())
    section = work.section(4, 4, 4)
    block = Block(section, "R1*2 |", "R1*2 |")
    block.add("fl1 ob1:-1", 2, r"c''1 | d''1 |", r"\p")
    block.spread("hn2 hn1", 1, r"<c' e'>1 | <d' f'>1 |")
    block.close()
    work.check_complete()
    assert _flat(music.body_to_lilypond(work.music_of("ob1"))) == r"R1*2 | c'1\p | d'1 |"
    assert _flat(music.body_to_lilypond(work.music_of("hn1"))) == r"e'1 | f'1 | R1*2 |"


def test_a_repeated_dynamic_mark_shows_one_time():
    from stmatthew.notation.work import Work, load_orchestra

    work = Work("Test", load_orchestra())
    section = work.section(2, 4, 4)
    section.write("fl1", times(r"c''4\p d''4 e''2 |", 2))
    section.close()
    assert _flat(music.body_to_lilypond(work.music_of("fl1"))).count(r"\p") == 1


def test_a_change_of_instrument_needs_time():
    from stmatthew.compose.check import check
    from stmatthew.notation.work import Work, load_orchestra

    work = Work("Test", load_orchestra())
    section = work.section(4, 4, 4)
    work.structure.tempo(section.bar(1), 1, 60, "Lento")
    # A roll occupies the player to its end. After a stroke, the player is free.
    section.write(
        "perc1",
        r"""\switch "snare drum" c'1:32\f | \switch "tam-tams" c'1\lv | R1 | """
        r"""\switch "triangle" c'1 |""",
    )
    section.close()
    assert [str(problem) for problem in check(work)] == [
        "perc1, bar 2: only 0.0 s for the change from the snare drum to the tam-tams"
    ]


def test_scatter_puts_figures_between_rests():
    text = scatter(3, 3, 2, {(1, 4): r"c'8 d'8 e'4", (3, 1.5): r"g'8"})
    assert text == "r2 r4 c'8 d'8 e'4 r4 | R1*3/2 | r8 g'8 r4 r2 r2 |"
    assert music.length(music.parse(text)) == 18


def test_passages_follow_the_dynamic_marks():
    from stmatthew.compose import stats
    from stmatthew.notation.work import Work, load_orchestra

    work = Work("Test", load_orchestra())
    section = work.section(12, 4, 4)
    work.structure.tempo(section.bar(1), 1, 60, "Lento")
    # 16 s soft, with one loud call of 2 s in it. Then 16 s loud, then 16 s soft.
    soft = r"c''1\pp ~ | c''1 ~ | c''1 ~ | c''1 | "
    section.write("vn1", soft + r"c''1\ff ~ | c''1 ~ | c''1 ~ | c''1 | " + soft)
    section.write("tpt1", r"R1 | r2 c''2\f | R1*10 |")
    section.close()
    assert stats.passages(work) == [0.0, 16.0, 32.0]


def test_a_change_of_tuning_of_the_timpani_needs_time():
    from stmatthew.compose.check import check
    from stmatthew.notation.work import Work, load_orchestra

    work = Work("Test", load_orchestra())
    section = work.section(4, 4, 4)
    work.structure.tempo(section.bar(1), 1, 60, "Lento")
    # Four drums have the notes D, F, G, and A. The note C comes 4 s after the stroke on D:
    # the player must tune that drum. The note F in bar 4 needs no change.
    section.write("timp", r"d,4\f f,4 g,4 a,4 | c4 r4 r2 | R1 | f,4 r4 r2 |")
    section.close()
    assert [str(problem) for problem in check(work)] == [
        "timp, bar 2: only 4.0 s to tune a drum from d, to c"
    ]


def test_a_short_passage_goes_to_the_adjacent_passage_with_the_nearer_mark():
    from stmatthew.compose import stats
    from stmatthew.notation.work import Work, load_orchestra

    work = Work("Test", load_orchestra())
    section = work.section(9, 4, 4)
    work.structure.tempo(section.bar(1), 1, 60, "Lento")
    # 16 s very soft, then 4 s at mf, then 16 s at ff: the 4 s are a part of the loud passage.
    section.write(
        "vn1",
        r"c''1\pp ~ | c''1 ~ | c''1 ~ | c''1 | c''1\mf | c''1\ff ~ | c''1 ~ | c''1 ~ | c''1 |",
    )
    section.close()
    assert stats.passages(work) == [0.0, 16.0]


def test_relay_makes_a_chain_of_colours():
    from stmatthew.compose.tools import relay

    first_group, second_group = relay(r"<c' e'>1 | <d' f'>2 <e' g'>2 | <c' e'>1 |", 2)
    # Group 1 starts, becomes softer in bar 2, and starts again in bar 3.
    assert _flat(first_group) == (
        r"<c' e'>1\ppp\< | <d' f'>2\p\> <e' g'>2\ppp | <c' e'>2\ppp\<~ <c' e'>2\p |"
    )
    # Group 2 has a rest, starts in bar 2, and becomes softer in bar 3.
    assert _flat(second_group) == r"R1 | <d' f'>2\ppp\< <e' g'>2 | <c' e'>2\p\>~ <c' e'>2\ppp |"


def test_figure_makes_a_bar_of_eighth_notes_with_joined_rests():
    from stmatthew.compose.tools import figure

    bar = figure([("c'", "->"), None, None, ("d'", ""), None, None, ("e'", "")])
    assert bar == "c'8-> r8 r8 d'8 r4 e'8 |"
    assert figure([None, None, ("c'", ""), None, None, None, None]) == "r4 c'8 r8 r4. |"
    assert figure([None] * 7) == "R1*7/8 |"


def test_stack_makes_chords_from_lines():
    from stmatthew.compose.tools import stack

    assert _flat(stack(r"c'2\p d'2 |", r"e'2 f'2 |")) == r"<c' e'>2\p <d' f'>2 |"


def test_sweep_makes_a_free_line_with_more_and_more_notes_in_each_eighth_note():
    from stmatthew.compose.tools import sweep

    groups = sweep("d e fis a b", "d,", (4, 5, 6))
    assert [text for text, _low, _high in groups] == [
        "d,32 e, fis, a,",
        r"\tuplet 5/4 { b,32 d e fis a }",
        r"\tuplet 6/4 { b32 d' e' fis' a' b' }",
    ]
    assert [(low, high) for _text, low, high in groups] == [(38, 45), (47, 57), (59, 71)]
    # Each group fills one eighth note.
    for text, _low, _high in groups:
        assert music.length(music.parse(text + " r8 r4 r2 |")) == 4
    down = sweep("d e fis a b", "b'", (4, 4), down=True)
    assert [text for text, _low, _high in down] == ["b'32 a' fis' e'", "d'32 b a fis"]


def test_one_hand_must_reach_each_chord():
    from stmatthew.compose.check import check
    from stmatthew.notation.work import Work, load_orchestra

    work = Work("Test", load_orchestra())
    section = work.section(4, 4, 4)
    work.structure.tempo(section.bar(1), 1, 60, "Lento")
    # The piano. Bar 1: a ninth (good). Bar 2: a tenth. Bar 3: the same chord, rolled
    # (good). Bar 4: six notes.
    section.write(
        "pno.rh",
        r"<c' d''>1\f | <c' e''>1 | <c' e''>1\arpeggio | <c' d' e' f' g' a'>1 |",
    )
    # The harp player can reach a tenth, has four fingers for each hand, and cannot roll
    # a chord that is wider than a tenth.
    section.write("harp.rh", r"<c' e' g' e''>1\f | <c' d' e' g' c''>1 | <c' f''>1\arpeggio | R1 |")
    section.close()
    assert [str(problem) for problem in check(work)] == [
        "harp.rh, bar 2: a chord of 5 notes for one hand of the harp",
        "harp.rh, bar 3: a chord from c' to f'' is too wide for one hand of the harp",
        "pno.rh, bar 2: a chord from c' to e'' is too wide for one hand of the piano",
        "pno.rh, bar 4: a chord of 6 notes for one hand of the piano",
    ]


def test_one_hand_of_a_keyboard_player_needs_time_for_a_move():
    from stmatthew.compose.check import check, hand_move, move_seconds
    from stmatthew.notation.work import Work, load_orchestra

    # The model of the hand: a window of one octave.
    assert hand_move([60, 64, 67], [62, 65, 69]) == 0  # the two chords are in one position
    assert hand_move([26, 38], [44]) == 6  # an octave, then a note a tritone above it
    assert hand_move([44], [26, 38]) == 6
    assert hand_move([60], [84]) == 12 and hand_move([84], [60]) == 12
    assert move_seconds(5) == 0.0 and 0.18 < move_seconds(12) < 0.20

    work = Work("Test", load_orchestra())
    section = work.section(4, 4, 4)
    work.structure.tempo(section.bar(1), 1, 120, "Allegro")  # an eighth note is 0.25 s
    # Bar 1: a scale (good). Bar 2: an octave and a note two octaves higher, in sixteenth
    # notes. Bar 3: the same leap in quarter notes (good). Bar 4: chords in thirty-second
    # notes in one hand.
    section.write(
        "pno.lh",
        r"c''16\f b' a' g' f' e' d' c' b a g f e d c b, | "
        r"<c, c>16 c''16 <c, c>16 c''16 r4 r2 | <c, c>4 c''4 <c, c>4 c''4 | "
        r"<c e>32 <d f> <c e> <d f> r8 r4 r2 |",
    )
    section.close()
    problems = [str(problem) for problem in check(work)]
    assert len(problems) == 2
    assert problems[0].startswith("pno.lh, bar 2: the hand must move 24 semitones in 0.12 s")
    assert problems[1].startswith("pno.lh, bar 4: chords come after 0.06 s in one hand")
