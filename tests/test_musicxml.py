"""Tests for the MusicXML file and for the MuseScore steps that need no program."""

import xml.etree.ElementTree as ElementTree
from fractions import Fraction

import pytest

from stmatthew.audio import musescore
from stmatthew.notation import musicxml
from stmatthew.notation.work import Work, load_orchestra


def _small_work() -> Work:
    work = Work("Test", load_orchestra())
    section = work.section(2, 4, 4)
    work.structure.tempo(1, 1, 60, "Lento")
    work.structure.change(2, 1, "rit.")
    section.write("fl1", r"c''4\p\<( d''8 e''8) \tuplet 3/2 { f''8 g'' a'' } r4 | c'''1\f ~ |")
    section.write("vn1", r"<d' a'>2\pp\pizz r2 | d''1:32\arco |")
    section.write("perc1", r"""\switch "tam-tams" c'1\p | R1 |""")
    section.close()
    section = work.section(1, 3, 4)
    work.structure.tempo(3, 1, 40, "Largo")
    section.write("fl1", r"c'''2. |")
    section.close()
    return work


def test_the_file_is_xml_and_has_one_part_for_each_instrument():
    text, names = musicxml.score(_small_work())
    root = ElementTree.fromstring(text.split("\n", 2)[2])
    assert names == ["Flute (fl1)", "Tam-tam (perc1)", "Violins (vn1)"]
    assert [len(part.findall("measure")) for part in root.findall("part")] == [3, 3, 3]
    # The tam-tam is unpitched percussion: its note has a drum, not a pitch.
    assert "<unpitched>" in text and "<midi-unpitched>53</midi-unpitched>" in text


def test_each_bar_of_each_voice_has_the_length_of_the_bar():
    text, _names = musicxml.score(_small_work())
    root = ElementTree.fromstring(text.split("\n", 2)[2])
    for part in root.findall("part"):
        for measure, quarters in zip(part.findall("measure"), [4, 4, 3], strict=True):
            position, longest = 0, 0
            for element in measure:
                if element.tag == "backup":
                    position -= int(element.findtext("duration"))
                elif element.tag == "forward" or (
                    element.tag == "note"
                    and element.find("chord") is None
                    and element.find("grace") is None
                ):
                    position += int(element.findtext("duration"))
                longest = max(longest, position)
            assert longest == quarters * musicxml.DIVISIONS


def test_the_tempo_points_keep_the_time_of_the_tempo_plan():
    work = _small_work()
    structure = work.structure
    points = musicxml._tempo_points(work, Fraction(0), structure.length)
    places = sorted(points) + [structure.length]
    seconds = sum(
        60.0 * float(end - start) / points[start]
        for start, end in zip(places[:-1], places[1:], strict=True)
    )
    assert abs(seconds - structure.duration_seconds) < 1e-6
    assert len(points) > 3  # the gradual change has a point at each quarter note


def test_marks_of_the_notes():
    text, _names = musicxml.score(_small_work())
    assert '<wedge type="crescendo"/>' in text and '<wedge type="stop"/>' in text
    assert "<dynamics><p/></dynamics>" in text and "<dynamics><f/></dynamics>" in text
    assert '<tremolo type="single">3</tremolo>' in text
    assert 'pizzicato="yes"' in text and 'pizzicato="no"' in text
    assert "<actual-notes>3</actual-notes><normal-notes>2</normal-notes>" in text
    assert '<tie type="start"/>' in text and '<tie type="stop"/>' in text


def test_staff_texts_of_techniques_become_playing_techniques():
    before = (
        "<StaffText>\n  <eid>x</eid>\n  <text>sul pont.</text>\n  </StaffText>"
        "<StaffText>\n  <text>dolce</text>\n  </StaffText>"
    )
    after, count = musescore.play_techniques(before)
    assert count == 1
    assert "<playTechType>sul_ponticello</playTechType>" in after
    assert "<StaffText>\n  <text>dolce</text>" in after


def test_a_stem_that_is_too_wide_gets_a_smaller_difference_signal():
    import numpy as np

    random = np.random.default_rng(1)
    wide = random.normal(0.0, 0.1, (48000, 2)).astype(np.float32)  # independent channels
    narrowed, gain_db = musescore.narrow(wide.copy())
    correlation = float(np.corrcoef(narrowed[:, 0], narrowed[:, 1])[0, 1])
    assert gain_db < 0.0
    assert abs(correlation - musescore.SMALLEST_CORRELATION) < 0.03
    # A stem that is not too wide does not change.
    shared = random.normal(0.0, 0.1, 48000).astype(np.float32)
    normal = np.stack([shared + 0.3 * wide[:, 0], shared + 0.3 * wide[:, 1]], axis=1)
    same, gain_db = musescore.narrow(normal.copy())
    assert gain_db == 0.0 and np.array_equal(same, normal)


@pytest.fixture(autouse=True)
def _no_measured_levels(monkeypatch):
    """The tests use the marks of the score, if a test does not give a table of levels."""
    monkeypatch.setattr(musicxml.playback, "load", dict)


def _work_with(player: str, text: str, bars: int = 2) -> Work:
    work = Work("Test", load_orchestra())
    section = work.section(bars, 4, 4)
    work.structure.tempo(1, 1, 60, "Lento")
    section.write(player, text)
    section.close()
    return work


def test_a_note_of_an_instrument_that_rings_is_longer_in_the_file():
    text, _names = musicxml.score(_work_with("harp.rh", r"c''4\p r4 r2 | R1 |"))
    root = ElementTree.fromstring(text.split("\n", 2)[2])
    durations = [int(note.findtext("duration")) for note in root.iter("note")]
    # The harp rings for 6 seconds: 6 quarter notes at this tempo, across the bar line.
    assert sum(durations) == 6 * musicxml.DIVISIONS
    assert text.count('<tie type="start"/>') == text.count('<tie type="stop"/>') >= 1


def test_the_last_note_of_a_soft_phrase_gets_softer_and_the_dynamic_comes_again():
    text, _names = musicxml.score(_work_with("fl1", r"c''1\p | r2 d''2 |"))
    first, second = text.split('<measure number="2">')
    assert '<wedge type="diminuendo"/>' in first and '<wedge type="stop"/>' in first
    assert "<dynamics><p/></dynamics>" in second
    # The tempo is 60: the last quarter note of the whole note gets softer.
    held, soft = first.split('<wedge type="diminuendo"/>')
    assert (
        f"<duration>{3 * musicxml.DIVISIONS}</duration>" in held and '<tie type="start"/>' in held
    )
    assert f"<duration>{musicxml.DIVISIONS}</duration>" in soft and '<tie type="stop"/>' in soft
    loud, _names = musicxml.score(_work_with("fl1", r"c''1\ff | r2 d''2 |"))
    assert "wedge" not in loud  # a loud phrase stops with its full sound


def test_spiccato_makes_short_notes():
    text, _names = musicxml.score(
        _work_with("vn1", r"c''8\spicc d'' e'' f'' g''2 | a''8\arco b'' r4 r2 |")
    )
    assert text.count("<staccato/>") == 4  # the four eighth notes, not the half note


def test_the_mixer_gets_the_levels_of_some_instruments(monkeypatch):
    from stmatthew.audio import musescore

    monkeypatch.setattr(musescore, "TRIM_DB", {"Taiko": -9.0})
    score = (
        '<Part id="1"><Staff id="1"/><trackName>Timpani</trackName>'
        '<Instrument id="timpani"><longName>Timpani</longName></Instrument></Part>'
        '<Part id="2"><Staff id="2"/><trackName>Taiko</trackName>'
        '<Instrument id="taiko"><longName>Taiko</longName></Instrument></Part>'
    )
    tracks = musescore.mixer_tracks(score, ["Timpani (timp)", "Taiko (perc6)"])
    assert tracks == [
        {
            "partId": "2",
            "instrumentId": "taiko",
            "out": {"volumeDb": musescore.TRIM_DB["Taiko"], "balance": 0, "fxChain": {}},
        }
    ]


def test_a_rolled_chord_and_a_slide_are_in_the_file():
    text, _names = musicxml.score(_work_with("harp.rh", r"<c' e' g'>1\p\arpeggio | c'1 |"))
    assert text.count("<arpeggiate/>") == 3  # one mark for each note of the chord
    text, _names = musicxml.score(_work_with("vc", r"g2\p\glissando e2 | c1 |"))
    first, second, third = text.split("<note>")[1:4]
    assert '<slide type="start"' in first and '<slide type="stop"' not in first
    assert '<slide type="stop"' in second
    assert "slide" not in third


def test_a_long_note_of_some_instruments_has_no_accent_in_the_file():
    # The tempo is 60: a whole note is 4 s. The limit of the trombone is 3.9 s.
    text, _names = musicxml.score(_work_with("tbn1", r"c'1\f-^ | c'2-^ r2 |"))
    assert text.count("<strong-accent/>") == 1  # only the half note
    text, _names = musicxml.score(_work_with("tbn1", r"c'2\f-> ~ c'2 ~ | c'2 r2 |"))
    assert "<accent/>" not in text  # three tied notes of 6 s
    text, _names = musicxml.score(_work_with("hn1", r"c'1\f-^ ~ | c'1 |"))
    assert text.count("<strong-accent/>") == 1  # the horn has no limit


VIOLINS = {
    "long": [-59.3, -53.8, -48.5, -41.7, -28.5, -24.1, -19.2, -17.6],
    "staccato": [-61.2, -54.1, -49.1, -43.0, -31.0, -24.7, -19.6, -18.0],
}
CLARINET = {"long": [-45.2, -42.3, -39.2, -49.9, -36.5, -32.7, -30.2, -29.1]}
FLUTE = {
    "long": [-47.0, -44.9, -43.1, -43.2, -33.6, -33.0, -29.2, -29.6],
    "staccato": [-70.7, -64.3, -59.1, -52.7, -41.9, -31.4, -29.5, -27.9],
}
TRUMPET = {
    "long": [-49.2, -46.5, -43.7, -40.9, -36.8, -30.2, -27.0, -26.1],
    "accent": [-42.2, -40.4, -38.3, -34.1, -30.5, -27.0, -27.1, -25.8],
    "marcato": [-40.2, -38.0, -36.9, -27.9, -23.4, -23.5, -23.8, -25.7],
}


def test_the_playback_marks_come_from_the_measured_levels():
    from stmatthew.notation.playback import played

    # The soft marks of the violins are very soft: they play one mark louder.
    assert played(VIOLINS, "pp") == ("p", "long")
    assert played(VIOLINS, "p") == ("mp", "long")
    assert played(VIOLINS, "mp") == ("mp", "long")
    assert played(VIOLINS, "pp", "staccato") == ("p", "staccato")
    assert played(VIOLINS, "pppp") == ("ppp", "long")
    # The mark mp of the clarinet is softer than its mark p: no note gets it.
    assert played(CLARINET, "mp") == ("ppp", "long")
    assert played(CLARINET, "mf") == ("p", "long")
    # A soft staccato note of the flute is almost silent: it gets a louder mark.
    assert played(FLUTE, "p") == ("ppp", "long")
    assert played(FLUTE, "p", "staccato") == ("mp", "staccato")
    # The marcato of the trumpet is very loud: a softer mark gives the correct level,
    # or the note gets an accent.
    assert played(TRUMPET, "f", "marcato", brass=True) == ("mp", "marcato")
    assert played(TRUMPET, "mf", "marcato", brass=True) == ("mp", "accent")
    assert played(TRUMPET, "f", "accent", brass=True) == ("f", "accent")
    # A brass instrument plays no mark louder than ff.
    assert played(TRUMPET, "fff", brass=True) == ("ff", "long")
    # Marks that are not levels, and instruments with no measurement, do not change.
    assert played(TRUMPET, "sffz", brass=True) == ("sffz", "long")
    assert played(None, "pp", "staccato") == ("pp", "staccato")


def test_the_audio_file_gets_the_playback_marks():
    work = _work_with("fl1", r"c''8-.\p d''-. e''-. f''-. g''2 | c''1\ff |")
    plain, _names = musicxml.score(work, levels={})
    assert plain.count("<staccato/>") == 4 and "<dynamics><p/></dynamics>" in plain
    tuned, _names = musicxml.score(work, levels={"Flute": FLUTE})
    # The staccato notes get the mark mp. The long note after them gets the mark ppp.
    short, long_note = tuned.split("<type>half</type>")[0].split("<dynamics><ppp/></dynamics>")
    assert "<dynamics><mp/></dynamics>" in short and short.count("<staccato/>") == 4
    assert "<dynamics><ff/></dynamics>" in tuned
    work = _work_with("vn1", r"c''1\pp ~ | c''1 |")
    violins, _names = musicxml.score(work, levels={"Violins": VIOLINS})
    assert "<dynamics><p/></dynamics>" in violins and "<pp/>" not in violins


def test_the_pedal_marks_of_a_piano_are_in_the_audio_file_of_its_two_hands():
    work = Work("Test", load_orchestra())
    section = work.section(3, 4, 4)
    work.structure.tempo(1, 1, 60, "Lento")
    section.write("pno.lh", r"c,1\p\sustainOn | c,1\sustainOff\sustainOn | r2\sustainOff r2 |")
    section.write("pno.rh", r"e'1\p | g'1 | R1 |")
    section.close()
    text, names = musicxml.score(work)
    assert names == ["Piano (pno.rh)", "Piano (pno.lh)"] or sorted(names) == sorted(
        ["Piano (pno.rh)", "Piano (pno.lh)"]
    )
    # Each hand has: push, release and push (the change), release.
    assert text.count('<pedal type="start" line="yes"/>') == 4
    assert text.count('<pedal type="stop" line="yes"/>') == 4


def test_an_excerpt_that_starts_with_the_pedal_down_has_a_push_at_its_start():
    marks = musicxml._pedal_marks(
        [(Fraction(0), "start"), (Fraction(4), "stop"), (Fraction(4), "start"),
         (Fraction(10), "stop"), (Fraction(12), "stop")],
        Fraction(6), Fraction(16),
    )  # fmt: skip
    # The pedal is down at the start. The second release has no push before it.
    assert marks == [(Fraction(6), "start"), (Fraction(10), "stop")]
