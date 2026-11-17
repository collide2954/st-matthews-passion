"""Number 1. Eingang: "Kommt, ihr Töchter, helft mir klagen".

Words: the poem of movement 1 of Bach. The words of the second choir (the
questions "Wen?", "Wie?", "Was?", "Wohin?") and the chorale "O Lamm Gottes,
unschuldig" have no singer: the instruments have them.

Elements of Bach:

- The key (E minor), the metre (12/8), and the pedal note E at the start.
- The theme that goes up by step from the key note in the rhythm long, short.
  In the work of Bach the instruments have it first, and then the bass of
  the choir (bar 17). Here the oboes have it first, and then the bass.
- The theme of the sopranos of bar 17, with the words as Bach put them: the
  first word is a long call that goes up through the chord.
- The calls "Kommt!" of the other voices, and the questions of the second choir.
- The chorale "O Lamm Gottes, unschuldig" in G major, above all other lines.

What is new:

- One voice sings the words of the first choir.
- The pulse: the theorbo has all twelve eighth notes of each bar. At the
  end of the number the pulse loses its notes one by one.
- The questions of the second choir are three notes of three instruments,
  one after the other: the call "Kommt" of the theme, divided between colours.
- The chorale is a canon of two colours, one beat apart: the recorders,
  then the organ.
"""

from __future__ import annotations

from ..notation.work import Work

TEMPO = 48  # dotted quarter notes in a minute
REST = "R1*12/8"  # one bar with no notes


def bars(*parts: str) -> str:
    """Return the bars of one player as one line of music."""
    return " | ".join(parts) + " |"


def rests(count: int) -> str:
    """Return a number of bars with no notes."""
    return REST if count == 1 else f"{REST}*{count}"


def says(words: str) -> str:
    """Return the mark for words that the instruments have and no person sings."""
    return rf'^\markup {{ \italic "{words}" }}'


def write(work: Work) -> None:
    structure = work.structure
    opening(work)
    dialogue(work)
    lamb(work)
    turn(work)
    patience(work)
    burden(work)
    cross(work)
    close(work)
    structure.double_bar(len(structure.bars))


def opening(work: Work) -> None:
    """Bars 1 to 8: the instruments, then the first words of the voice."""
    structure = work.structure
    s = work.section(8, 12, 8)
    structure.mark(s.bar(1), "1")
    structure.key(s.bar(1), "e", "minor")
    structure.tempo(s.bar(1), 1, TEMPO, "Largo", unit="4.")

    # The theme of the instruments of Bach (bars 1 and 2), in sixths, on the pedal note E.
    # Then a sequence of fifths in the bass (bars 3 and 4), for all winds.
    theme = bars(
        r"e''4.\mp~ e''8 fis'' g'' fis''4 fis''8 fis'' gis'' a''",
        r"gis''8 fis'' e'' a''4.~ a''8 g'' fis'' g''4 fis''8",
    )
    under = bars(
        r"g'4.\mp~ g'8 a' b' a'4 a'8 a' b' c''",
        r"b'8 a' gis' c''4.~ c''8 b' a' b'4 a'8",
    )
    top = bars(
        r"g''4.\mf~ g''8 a'' g'' fis''4.~ fis''8 g'' fis''",
        r"e''4.~ e''8 fis'' e'' e''4. dis''4.",
    )
    second = bars(
        r"e''4.\mf~ e''8 fis'' e'' d''4.~ d''8 e'' d''",
        r"c''4.~ c''8 d'' c'' b'4. b'4 a'8",
    )
    # Bar 7: the oboes answer the voice with the call of the theme.
    s.write("ob1", " ".join([theme, top, bars(rests(2), r"b'8\mf( e'' g'') b''4. r2.", REST)]))
    s.write("ob2", " ".join([under, second, bars(rests(2), r"g'8\mf( b' e'') g''4. r2.", REST)]))
    s.write("fl1", " ".join([bars(rests(2)), top, bars(rests(4))]))
    s.write("fl2", " ".join([bars(rests(2)), second, bars(rests(4))]))

    # The strings: long notes on the pedal, then the pulse (long, short) of the sequence.
    # In bars 5 and 6 the violins have the calls "Kommt!" of the alto and the tenor of Bach.
    s.write(
        "vn1",
        bars(
            r"b'2.\p c''4. b'4.~",
            r"b'4. c''4. c''4. b'4 b'8",
            r"b'4\mf b'8 c''4 c''8 a'4 a'8 b'4 b'8",
            r"g'4 g'8 a'4 a'8 g'4 g'8 fis'4 fis'8",
            r"r4. g'4\mf" + says("Kommt!") + r" r8 r4. a'4 r8",
            r"r2. b8( dis' fis') b'4.",
            r"g'4\p g'8 g'4 g'8 a'4 a'8 a'4 a'8",
            r"g'4 g'8 a'4 a'8 a'4 a'8 a'4 a'8",
        ),
    )
    s.write(
        "vn2",
        bars(
            r"g'2.\p a'4. gis'4.~",
            r"gis'4. a'4. a'4. g'4 a'8",
            r"g'4\mf g'8 e'4 e'8 fis'4 fis'8 d'4 d'8",
            r"e'4 e'8 e'4 e'8 e'4 e'8 dis'4 dis'8",
            r"r4. b4\mf r8 r4. fis'4 r8",
            REST,
            r"e'4\p e'8 e'4 e'8 e'4 e'8 fis'4 fis'8",
            r"d'4 d'8 e'4 e'8 e'4 e'8 dis'4 dis'8",
        ),
    )
    s.write(
        "va",
        bars(
            r"e'2.\p e'4. d'4.~",
            r"d'4. c'4. e'4. e'4 dis'8",
            r"e'4\mf e'8 c'4 c'8 d'4 d'8 b4 b8",
            r"c'4 c'8 c'4 c'8 g4 g8 b4 b8",
            rests(2),
            r"b4\p b8 b4 b8 c'4 c'8 c'4 c'8",
            r"b4 b8 c'4 c'8 c'4 c'8 b4 b8",
        ),
    )

    # The voice: the theme of the sopranos of Bach, with his words (bars 5 and 6). Then
    # the same words go down through one octave (bars 7 and 8).
    s.sing(
        "alto",
        bars(
            rests(4),
            r"e'8\mf( g' b' e''4.~ e''8 dis'') cis'' dis''( b') c'' \breathe",
            r"d''4 d''8 c''( b' a' dis'' b' dis'' e''4 dis''8)",
            r"b'4. r4. e''4 d''8 c''4.",
            r"b'4. a'4 g'8 fis'4.~ fis'8( e' dis')",
        ),
        "Kommt, ihr Töch -- ter, helft mir kla -- gen, helft mir kla -- gen, helft mir kla --",
    )

    # The bass. Bars 1 and 2: the pedal note in the rhythm long, short. Bars 5 and 6: the
    # theme of the bass of Bach (bar 17). The violone has one note on each beat.
    bass = [
        r"e4\p e8 e4 e8 e4 e8 e4 e8",
        r"e4 e8 e4 e8 e4 e8 e4 e8",
        r"e4\mf e8 a4 a8 d4 d8 g4 g8",
        r"c4 c8 a,4 a,8 b,4 b,8 b,4 b,8",
        r"e4.\mf~ e8 fis g fis4 fis8 fis gis a",
        r"gis8 fis e a4.~ a8 g fis g4 fis8",
        r"e4\p e8 e4 e8 a4 a8 d4 d8",
        r"g4 g8 c4 c8 a,4 a,8 b,4 b,8",
    ]
    s.write("vc", bars(*bass))
    s.write("bn", bars(rests(2), *bass[2:]))
    s.write(
        "vne",
        bars(
            r"e,4.\p r4. e,4. r4.",
            r"e,4. r4. e,4. r4.",
            r"e,4.\mf a,,4. d,4. g,4.",
            r"c,4. a,,4. b,,2.",
            r"e,4.\mf~ e,8 fis, g, fis,4 fis,8 fis, gis, a,",
            r"gis,8 fis, e, a,4.~ a,8 g, fis, g,4 fis,8",
            r"e,4.\p e,4. a,,4. d,4.",
            r"g,4. c,4. a,,4. b,,4.",
        ),
    )

    # The theorbo: all twelve eighth notes of each bar. The first note of each beat is the
    # bass note.
    s.write(
        "lute",
        bars(
            r"e,8\p b, g e, b, g e, c fis e, d gis",
            r"e,8 d gis e, c a e, c fis e, b, a",
            r"e,8\mf b, g a, e c' d a fis' g, d b",
            r"c8 g e' a, e c' b, e g b, dis a",
            r"e,8\p b, g e, b, e fis, dis a fis, b, e",
            r"gis,8 d b a, e c' a, e b g, e b",
            r"e,8 b, g e, b, g a, e c' d a c'",
            r"g,8 d b c e a a, e c' b, dis a",
        ),
    )

    # The organ: the chords of the strings, and the bass in long notes.
    s.write(
        "org.rh",
        bars(
            r"<e' g' b'>2.\p <e' a' c''>4. <d' gis' b'>4.~",
            r"<d' gis' b'>4. <c' a' c''>4. <e' a' c''>4. <e' g' b'>4 <dis' a' b'>8",
            r"<e' g' b'>4.\mf <c' e' c''>4. <d' fis' a'>4. <b d' b'>4.",
            r"<c' e' g'>4. <c' e' a'>4. <g e' g'>4. <b dis' fis'>4.",
            r"<g b e'>2.\p <a b dis'>4. <a b dis'>4 <a c' e'>8",
            r"<b d' e'>4. <a c' e'>4. <fis b dis'>4. <g b e'>4 <fis b dis'>8",
            r"<g b e'>2. <a c' e'>4. <a c' fis'>4.",
            r"<g b d'>4. <a c' e'>4. <a c' e'>4. <a b dis'>4.",
        ),
    )
    s.write(
        "org.lh",
        bars(
            r"e,1.\p~",
            r"e,1.",
            r"e4.\mf a4. d4. g4.",
            r"c4. a,4. b,2.",
            r"e2.\p fis2.",
            r"gis4. a4.~ a4. g4 fis8",
            r"e2. a4. d4.",
            r"g4. c4. a,4. b,4.",
        ),
    )
    s.close()


def dialogue(work: Work) -> None:
    """Bars 9 to 12: "Sehet! - Wen? - den Bräutigam. Seht ihn! - Wie? - als wie ein Lamm."

    Each question of the second choir is three notes that go up through one
    chord, each note from a different instrument. The last note is a note
    that must go on: the answer of the voice brings its chord.
    """
    s = work.section(4, 12, 8)
    s.sing(
        "alto",
        bars(
            r"e'4. r4. e''4\mf b'8 r4.",
            r"r4 b'8 d''4 c''8 b'4. r4.",
            r"e''4. c''4. r4. r4 d''8",
            r"e''4 d''8 c''4.( b'4.) r4.",
        ),
        "gen, Se -- het! den Bräu -- ti -- gam. Seht ihn! als wie ein Lamm.",
    )

    # "Wen?": the bassoon, the violas, the first oboe. The last note is the seventh of
    # the chord of D: it goes down to the note B when the voice answers in G major.
    # "Wie?": the violas, the second violins, the first violins.
    s.write("bn", bars(r"r2. r4. a4.\mf", r"g4. r4. r2.", rests(2)))
    s.write(
        "va",
        bars(r"r2. r4. r8 d'4\mf", r"d'4. r4. r2.", r"r2. fis4.\mf g4.", REST),
    )
    s.write(
        "ob1",
        bars(r"r2. r4. r4 c''8\mf" + says("Wen?"), r"b'4. r4. r2.", rests(2)),
    )
    s.write("vn2", bars(rests(2), r"r2. r8 a4\mf d'4.", REST))
    s.write("vn1", bars(rests(2), r"r2. r4 c''8\mf" + says("Wie?") + r" b'4.", REST))

    # The flute players take the recorders. The chorale starts on the last beat of bar 12.
    chorale = r"g''4.\mf" + says("O Lamm Gottes, unschuldig")
    for player in ("fl1", "fl2"):
        s.write(player, r'\switch "recorder" ' + bars(rests(3), "r2. r4. " + chorale))

    s.write(
        "vc",
        bars(
            r"e4\p e8 e4 e8 g4 g8 fis4 fis8",
            r"g4 g8 d4 d8 g4 g8 e4 e8",
            r"c4 c8 a,4 a,8 d4 d8 b,4 b,8",
            r"c4 c8 d4 d8 g,4 g,8 g,4 g,8",
        ),
    )
    s.write(
        "vne",
        bars(
            r"e,4.\p e,4. g,4. fis,4.",
            r"g,4. d,4. g,4. e,4.",
            r"c,4. a,,4. d,4. b,,4.",
            r"c,4. d,4. g,,2.",
        ),
    )
    s.write(
        "lute",
        bars(
            r"e,8\p b, g e, b, g g, e b fis, d c'",
            r"g,8 d b d a c' g, d b e, b, g",
            r"c8 g e' a, e c' d a c' b, d g",
            r"c8 g e' d a c' g, d b g, d b",
        ),
    )
    s.write(
        "org.rh",
        bars(
            r"<g b e'>2.\p <g b e'>4. <a c' d'>4.",
            r"<g b d'>4. <a c' fis'>4. <g b g'>4. <g b e'>4.",
            r"<g c' e'>4. <a c' e'>4. <a c' d'>4. <g b d'>4.",
            r"<g c' e'>4. <a c' fis'>4. <g b g'>2.",
        ),
    )
    s.write(
        "org.lh",
        bars(r"e2.\p g4. fis4.", r"g4. d4. g4. e4.", r"c4. a,4. d4. b,4.", r"c4. d4. g,2."),
    )
    s.close()


def lamb(work: Work) -> None:
    """Bars 13 to 16: the first two lines of the chorale "O Lamm Gottes, unschuldig".

    The recorders have the tune, one octave above the voices of Bach. The
    organ has the same tune one beat later: a canon of two colours.
    """
    s = work.section(4, 12, 8)
    tune = bars(
        r"g''4. g''4. d'''4. d'''4.",
        r"e'''2. d'''4. d'''4." + says("am Stamm des Kreuzes geschlachtet"),
        r"g''4. a''4. b''4. c'''4.",
        r"b''4. a''4 g''8 g''2.",
    )
    s.write("fl1", tune)
    s.write("fl2", tune)
    s.write(
        "org.rh",
        bars(
            r"g'4.\mf g'4. g'4. d''4.",
            r"d''4. e''2. d''4.",
            r"d''4. g'4. a'4. b'4.",
            r"c''4. b'4. a'4 g'8 g'4.",
        ),
    )
    s.write(
        "org.lh",
        bars(r"g4.\mf c4. b,4. d4.", r"g4. c4. d4. fis4.", r"g4. c4. b,4. a,4.", r"d2. g,2."),
    )
    # The strings: soft chords. The first violins have no notes.
    s.write(
        "vn2",
        bars(
            r"d'4.\pp e'4. d'4. d'4.",
            r"d'4. e'4. d'4. d'4.",
            r"d'4. e'4. d'4. c'4.",
            r"d'4. fis'4. g'2.",
        ),
    )
    s.write(
        "va",
        bars(
            r"b4.\pp c'4. g4. a4.",
            r"b4. c'4. a4. c'4.",
            r"b4. c'4. g4. a4.",
            r"b4. c'4. b2.",
        ),
    )
    # The bass goes down (B, A) while the tune goes up (B, C): bar 15.
    s.write(
        "vc",
        bars(
            r"g4\p g8 c4 c8 b,4 b,8 d4 d8",
            r"g4 g8 c4 c8 d4 d8 fis4 fis8",
            r"g4 g8 c4 c8 b,4 b,8 a,4 a,8",
            r"d4 d8 d4 d8 g,4 g,8 g,4 g,8",
        ),
    )
    s.write(
        "vne",
        bars(
            r"g,4.\p c,4. b,,4. d,4.",
            r"g,4. c,4. d,4. fis,4.",
            r"g,4. c,4. b,,4. a,,4.",
            r"d,2. g,,2.",
        ),
    )
    s.write(
        "lute",
        bars(
            r"g,8\p d b c g e' b, d g d a fis'",
            r"g,8 d b c g e' d a fis' fis, d c'",
            r"g,8 d b c g a b, d g a, e c'",
            r"d8 g b d a c' g, d b g, d b",
        ),
    )
    s.close()


def turn(work: Work) -> None:
    """Bars 17 and 18: the instruments go from G major to the dominant of B minor.

    The oboes have the theme of the start, in thirds. The call "Kommt" of
    the theme goes from the first violins to the second violins and to the
    violas. The chord of F-sharp does not go to B minor: it goes to G major,
    and the chorale starts again there.
    """
    s = work.section(2, 12, 8)
    s.write(
        "ob1",
        bars(
            r"b'4.\mp~ b'8 cis'' d'' e''4 e''8 e'' fis'' g''",
            r"fis''8 e'' d'' g''4.~ g''8 fis'' e'' d''4.",
        ),
    )
    s.write(
        "ob2",
        bars(
            r"g'4.\mp~ g'8 a' b' cis''4 cis''8 cis'' d'' e''",
            r"d''8 cis'' b' e''4.~ e''8 d'' cis'' b'4.",
        ),
    )
    s.write("vn1", bars(r"r4. b8\mp( e' g') b'4. r4.", REST))
    s.write("vn2", bars(r"r2. r4. fis'8\mp( ais' cis'')", r"d''4. r4. r2."))
    s.write("va", bars(REST, r"r4. e8\mp( g b) e'4. d'4."))
    chorale = r"g''4.\mf" + says("allzeit erfunden geduldig")
    for player in ("fl1", "fl2"):
        s.write(player, bars(REST, "r2. r4. " + chorale))
    s.write(
        "vc",
        bars(r"g4\p g8 e4 e8 e4 e8 fis4 fis8", r"b,4 b,8 g4 g8 fis4 fis8 g4 g8"),
    )
    s.write("vne", bars(r"g,4.\p e,4. e,4. fis,4.", r"b,,4. g,4. fis,4. g,4."))
    s.write(
        "lute",
        bars(
            r"g,8\p d b e, b, g e, cis g fis, e ais",
            r"b,8 fis d' g, e b fis, cis ais g, d b",
        ),
    )
    s.write(
        "org.rh",
        bars(
            r"<g b d'>4.\p <g b e'>4. <g cis' e'>4. <fis ais e'>4.",
            r"<fis b d'>4. <g b e'>4. <fis ais e'>4. <d b d'>4.",
        ),
    )
    s.write("org.lh", bars(r"g4.\p e2. fis4.", r"b,4. g4. fis4. g4."))
    s.close()


def patience(work: Work) -> None:
    """Bars 19 to 22: "Sehet! - Was? - seht die Geduld. Seht! - Wohin? - auf unsre Schuld."

    The chorale (lines 3 and 4) is above the voice now. Its last note G is
    the third of the chord of E minor: the chorale in G major ends in the
    key of the number. The word "Schuld" has the two notes of the word
    "Lamm" (C, then B), on a chord of the dominant with a minor ninth.
    """
    s = work.section(4, 12, 8)
    tune = bars(
        r"g''4. g''4. d'''4. d'''4.",
        r"e'''2. d'''4. d'''4." + says("wiewohl du warest verachtet"),
        r"g''4. a''4. b''4. c'''4.",
        r"b''4. a''4 g''8 g''4. b''4." + says("All Sünd hast du getragen"),
    )
    s.write("fl1", tune)
    s.write("fl2", tune)
    s.write(
        "org.rh",
        bars(
            r"g'4.\mf g'4. g'4. d''4.",
            r"d''4. e''2. d''4.",
            r"d''4. g'4. a'4. b'4.",
            r"c''4. b'4. a'4 g'8 g'4.",
        ),
    )
    s.write(
        "org.lh",
        bars(r"e2.\mf b,2.", r"e4. a,4. d4. b,4.", r"e4. a,4. d4. dis4.", r"e4. b,4. e2."),
    )
    s.sing(
        "alto",
        bars(
            r"b'4\mf e'8 r4. r2.",
            r"b'4. a'4 g'8 fis'2.",
            r"b'4. r4. r4. r4 fis'8",
            r"g'4 a'8 c''4.( b'4.) r4.",
        ),
        "Se -- het! seht die Ge -- duld. Seht! auf uns -- re Schuld.",
    )
    # "Was?": the bassoon, the second oboe, the first oboe.
    s.write("bn", bars(r"r2. b2.\mf", rests(3)))
    s.write("ob2", bars(r"r2. r8 d'4\mf~ d'4.", rests(3)))
    s.write("ob1", bars(r"r2. r4 g'8\mf" + says("Was?") + r" fis'4.", rests(3)))
    # "Wohin?": the violas, the second violins, the first violins.
    s.write("va", bars(rests(2), r"r4. a2.\mf r4.", REST))
    s.write("vn2", bars(rests(2), r"r4. r8 cis'4\mf d'4. r4.", REST))
    s.write("vn1", bars(rests(2), r"r4. r4 e'8\mf" + says("Wohin?") + r" fis'4. r4.", REST))
    s.write(
        "vc",
        bars(
            r"e4\p e8 e4 e8 b,4 b,8 b,4 b,8",
            r"e4 e8 a,4 a,8 d4 d8 b,4 b,8",
            r"e4 e8 a,4 a,8 d4 d8 dis4 dis8",
            r"e4 e8 b,4 b,8 e4 e8 e4 e8",
        ),
    )
    s.write(
        "vne",
        bars(
            r"e,4.\p e,4. b,,4. b,,4.",
            r"e,4. a,,4. d,4. b,,4.",
            r"e,4. a,,4. d,4. dis,4.",
            r"e,4. b,,4. e,2.",
        ),
    )
    s.write(
        "lute",
        bars(
            r"e,8\p b, g e, b, g b, d g b, d fis",
            r"e,8 b, d a, e cis' d a fis' b, fis d'",
            r"e,8 b, d a, e cis' d fis a dis a c'",
            r"e,8 b, g b, dis a e, b, g e, b, g",
        ),
    )
    s.close()


def burden(work: Work) -> None:
    """Bars 23 to 26: lines 5 and 6 of the chorale. The voice has no notes.

    The oboes have the theme of the start below the chorale, and the strings
    have the pulse (long, short). The music becomes louder.
    """
    s = work.section(4, 12, 8)
    tune = bars(
        r"b''4. b''4. a''4. b''4.",
        r"g''4 fis''8 e''4. d''4. d'''4." + says("sonst müßten wir verzagen"),
        r"e'''4. d'''4. d'''4. b''4 c'''8",
        r"d'''4. c'''4. b''2.",
    )
    s.write("fl1", tune)
    s.write("fl2", tune)
    s.write(
        "org.rh",
        bars(
            r"b'4. b'4. b'4. a'4.",
            r"b'4. g'4 fis'8 e'4. d'4.",
            r"d''4. e''4. d''4. d''4.",
            r"b'4 c''8 d''4. c''4. b'4.",
        ),
    )
    s.write(
        "org.lh",
        bars(r"e4. b,4. fis4. g4.", r"e4. c4. d2.", r"c4. b,4. g,4. e4.", r"g4. a,4. g,2."),
    )
    s.write(
        "ob1",
        bars(
            r"g'4.\mp~ g'8 a' b' a'4 a'8 a' b' c''",
            r"b'8 a' g' e''4.~ e''8 d'' c'' d''4 b'8",
            r"g'4.\<~ g'8 a' b' b'4 b'8 b' c'' d''",
            r"d''8 c'' b' e''4.~ e''8 d'' c'' d''4\mf c''8",
        ),
    )
    s.write(
        "ob2",
        bars(
            r"e'4.\mp~ e'8 fis' g' fis'4 fis'8 fis' g' a'",
            r"g'8 fis' e' c''4.~ c''8 b' a' a'4 fis'8",
            r"e'4.\<~ e'8 fis' g' g'4 g'8 g' a' b'",
            r"b'8 a' g' c''4.~ c''8 b' a' b'4\mf a'8",
        ),
    )
    s.write(
        "vn1",
        bars(
            r"g'4\p g'8 g'4 g'8 a'4 a'8 g'4 g'8",
            r"g'4 g'8 g'4 g'8 fis'4 fis'8 fis'4 fis'8",
            r"g'4\< g'8 g'4 g'8 g'4 g'8 g'4 g'8",
            r"g'4 g'8 fis'4 fis'8 g'4 g'8 g'4\mf g'8",
        ),
    )
    s.write(
        "vn2",
        bars(
            r"e'4\p e'8 d'4 d'8 d'4 d'8 d'4 d'8",
            r"e'4 e'8 e'4 e'8 d'4 d'8 d'4 d'8",
            r"e'4\< e'8 d'4 d'8 d'4 d'8 e'4 e'8",
            r"d'4 d'8 d'4 d'8 d'4 d'8 d'4\mf d'8",
        ),
    )
    s.write(
        "va",
        bars(
            r"b4\p b8 b4 b8 d'4 d'8 b4 b8",
            r"b4 b8 c'4 c'8 a4 a8 a4 a8",
            r"e4\< e8 g4 g8 b4 b8 b4 b8",
            r"b4 b8 c'4 c'8 b4 b8 b4\mf b8",
        ),
    )
    bass = [
        r"e4\p e8 b,4 b,8 fis4 fis8 g4 g8",
        r"e4 e8 c4 c8 d4 d8 d4 d8",
        r"c4\< c8 b,4 b,8 g,4 g,8 e4 e8",
        r"g4 g8 a,4 a,8 g,4 g,8 g,4\mf g,8",
    ]
    s.write("vc", bars(*bass))
    s.write("bn", bars(*bass))
    s.write(
        "vne",
        bars(
            r"e,4.\p b,,4. fis,4. g,4.",
            r"e,4. c,4. d,2.",
            r"c,4.\< b,,4. g,,4. e,4.",
            r"g,4. a,,4. g,,2.\mf",
        ),
    )
    s.write(
        "lute",
        bars(
            r"e,8\p b, g b, d g fis, d a g, d b",
            r"e,8 b, g c g e' d a fis' d a fis'",
            r"c8\< g e' b, d g g, d b e, b, d",
            r"g,8 d b a, fis c' g, d b g,\mf d b",
        ),
    )
    s.close()


def cross(work: Work) -> None:
    """Bars 27 to 31: "Sehet ihn aus Lieb und Huld Holz zum Kreuze selber tragen."

    The bass goes up by semitones from E to B, and the voice goes up with it
    in thirds. The chord of B does not go to E minor: it goes to C major, and
    there the last line of the chorale starts ("Erbarm dich unser, o Jesu!").
    The voice has the notes of this line also, with more notes between them:
    the witness sings with the congregation. The end is in E minor, and the
    last note G of the chorale is its third.
    """
    s = work.section(5, 12, 8)
    s.sing(
        "alto",
        bars(
            r"g'4\mf g'8 a'4 a'8 b'4 b'8 b'4. \breathe",
            r"c''4\< c''8 cis''4 cis''8 \breathe d''4 d''8 dis''4.(",
            r"e''4.\f~ e''8 d'' c'' b'4 c''8 a'4 b'8)",
            r"b'4 r8 d''4 c''8 b'4.( a'4.~",
            r"a'4.) g'4. r2.",
        ),
        "Se -- het ihn aus Lieb und Huld Holz zum Kreu -- ze sel -- ber tra -- gen, "
        "sel -- ber tra -- gen.",
    )
    tune = bars(
        rests(2),
        r"e'''4.\f" + says("Erbarm dich unser, o Jesu!") + r" d'''4 c'''8 b''4. a''4.",
        r"b''4. d'''4. b''4. a''4.~",
        r"a''4. g''2.~ g''4.",
    )
    s.write("fl1", tune)
    s.write("fl2", tune)
    # The oboes: with the voice in bars 27 and 28, then the tune of the chorale.
    s.write(
        "ob1",
        bars(
            r"b'4\mf b'8 c''4 c''8 d''4 d''8 d''4.",
            r"e''4\< e''8 e''4 e''8 fis''4 fis''8 fis''4.",
            r"e''4.\f d''4 c''8 b'4. a'4.",
            r"b'4. d''4. b'4. a'4.~",
            r"a'4. g'2.\>~ g'4.\p",
        ),
    )
    s.write(
        "ob2",
        bars(
            r"e'4.\mf dis'4. e'4. e'4.",
            r"e'4.\< e'4. fis'4. fis'4.",
            r"g'4.\f g'4. g'4. e'4.",
            r"fis'4. g'4. g'4. fis'4.",
            r"fis'4. e'2.\>~ e'4.\p",
        ),
    )
    s.write(
        "vn1",
        bars(
            r"g'4\mf g'8 a'4 a'8 b'4 b'8 b'4 b'8",
            r"c''4\< c''8 cis''4 cis''8 d''4 d''8 dis''4 dis''8",
            r"e''4\f e''8 e''4 e''8 d''4 d''8 e''4 e''8",
            r"dis''4 dis''8 e''4 e''8 e''4 e''8 c''4 c''8",
            r"b'4 b'8 b'4. r2.",
        ),
    )
    s.write(
        "vn2",
        bars(
            r"e'4\mf e'8 c'4 c'8 b4 b8 b4 b8",
            r"c'4\< c'8 e'4 e'8 d'4 d'8 fis'4 fis'8",
            r"e'4\f e'8 e'4 e'8 g'4 g'8 e'4 e'8",
            r"fis'4 fis'8 g'4 g'8 e'4 e'8 e'4 e'8",
            r"dis'4 dis'8 e'4. r2.",
        ),
    )
    s.write(
        "va",
        bars(
            r"e'4\mf e'8 dis'4 dis'8 e'4 e'8 d'4 d'8",
            r"c'4\< c'8 g4 g8 fis4 fis8 b4 a8",
            r"g4\f g8 g4 g8 b4 b8 a4 a8",
            r"a4 a8 g4 g8 b4 b8 fis4 fis8",
            r"fis4 fis8 e4. r2.",
        ),
    )
    # The bass: up by semitones from E to B, then one more semitone to C.
    bass = [
        r"e,4\mf e,8 fis,4 fis,8 g,4 g,8 gis,4 gis,8",
        r"a,4\< a,8 ais,4 ais,8 b,4 b,8 b,4 b,8",
        r"c4\f c8 c4 c8 g,4 g,8 c4 c8",
        r"b,4 b,8 e4 e8 g4 g8 a4 a8",
    ]
    s.write("vc", bars(*bass, r"b4 b8 e4\> e8 e4 e8 e4\p e8"))
    s.write("bn", bars(*bass, r"b4 b8 e4. r2."))
    s.write("gamba", bars(*bass, r"b4 b8 e4. r2."))
    s.write(
        "vne",
        bars(
            r"e,,4.\mf fis,,4. g,,4. gis,,4.",
            r"a,,4.\< ais,,4. b,,2.",
            r"c,4.\f c,4. g,,4. c,4.",
            r"b,,4. e,4. g,4. a,4.",
            r"b,4. e,4. r2.",
        ),
    )
    s.write(
        "lute",
        bars(
            r"e,8\mf b, g fis, dis c' g, e b gis, e d'",
            r"a,8\< e c' ais, e cis' b, fis d' b, fis dis'",
            r"c8\f g e' c g e' g, d b c e a",
            r"b,8 fis a e, b, d g, e b a, fis c'",
            r"b,8 fis a e, b,\> g e, b, g e,\p b, g",
        ),
    )
    # The organ: chords, then the tune of the chorale one beat after the recorders.
    s.write(
        "org.rh",
        bars(
            r"<g b e'>4.\mf <a c' dis'>4. <g b e'>4. <b d' e'>4.",
            r"<a c' e'>4. <cis' e' g'>4. <b d' fis'>4. <a b dis'>4.",
            r"<g c' e'>4.\f e''4. d''4 c''8 b'4.",
            r"a'4. b'4. d''4. b'4.",
            r"a'2. g'2.~",
        ),
    )
    s.write(
        "org.lh",
        bars(
            r"e,4.\mf fis,4. g,4. gis,4.",
            r"a,4. ais,4. b,2.",
            r"c4.\f c4. g,4. c4.",
            r"b,4. e4. g4. a4.",
            r"b4. e4.~ e2.",
        ),
    )
    s.close()


def close(work: Work) -> None:
    """Bars 32 to 41: the first words again, and the end.

    The pedal note E comes back. The voice has the theme of the start, with
    the words as the bass of the choir of Bach has them (bar 17). Then the
    pulse of the theorbo loses its notes: 12 in a bar, then 10, 8, 6, 4, 2,
    and one last chord. The last chord is E major, as in the work of Bach.
    """
    structure = work.structure
    s = work.section(10, 12, 8)
    # Slower in the last bars: from 48 to 40 dotted quarter notes in a minute.
    structure.ritardando(s.bar(9), 1, 60, text="", resume="")
    structure.fermata(s.bar(10), 3.0)
    s.sing(
        "alto",
        bars(
            REST,
            r"e'4.\p~( e'8 fis') g' fis'4 fis'8 \breathe fis'( gis') a'",
            r"gis'8( fis' e' a'4.~ a'8 g' fis' g'4 fis'8)",
            r"e'2. r2.",
            rests(6),
        ),
        "Kommt, ihr Töch -- ter, helft mir kla -- gen.",
    )
    # The oboes: the end of the theme one last time (bar 36).
    s.write(
        "ob1",
        bars(rests(4), r"a''4.\p~ a''8 g'' fis'' g''4 fis''8 r4.", r"e''4. r4. r2.", rests(4)),
    )
    s.write(
        "ob2",
        bars(rests(4), r"c''4.\p~ c''8 b' a' b'4 a'8 r4.", r"g'4. r4. r2.", rests(4)),
    )
    s.write(
        "vn1",
        bars(
            REST,
            r"b'2.\pp c''4. b'4.~",
            r"b'4. c''4. c''4. b'4 b'8",
            r"b'2. c''2.~",
            r"c''2. b'2.~",
            r"b'2. c''2.~",
            r"c''2.~ c''4. b'4.~",
            r"b'2. c''2.",
            r"b'1.~",
            r"b'1.\fermata",
        ),
    )
    s.write(
        "vn2",
        bars(
            REST,
            r"g'2.\pp a'4. gis'4.~",
            r"gis'4. a'4. a'4. g'4 a'8",
            r"g'2. a'2.~",
            r"a'1.",
            r"g'1.",
            r"a'1.",
            r"g'2. a'2.",
            r"gis'1.~",
            r"gis'1.\fermata",
        ),
    )
    s.write(
        "va",
        bars(
            REST,
            r"e'2.\pp e'4. d'4.~",
            r"d'4. c'4. e'4. e'4 dis'8",
            r"e'1.~",
            r"e'2. dis'2.",
            r"e'1.~",
            r"e'2.~ e'4. dis'4.",
            r"e'1.~",
            r"e'1.~",
            r"e'1.\fermata",
        ),
    )
    s.write(
        "vc",
        bars(
            r"e4\p e8 e4 e8 e4 e8 e4 e8",
            r"e4 e8 e4 e8 e4 e8 e4 e8",
            r"e4 e8 e4 e8 e4 e8 e4 e8",
            r"e4 e8 e4 e8 e4 e8 e4 e8",
            r"e4 e8 e4. e4 e8 e4.",
            r"e4. e4. e4. e4.",
            r"e4. r4. e4. r4.",
            r"e4.\pp r4. r2.",
            r"e4. r4. r2.",
            r"e1.\fermata",
        ),
    )
    s.write(
        "vne",
        bars(
            r"e,4.\p r4. e,4. r4.",
            r"e,4. r4. e,4. r4.",
            r"e,4. r4. e,4. r4.",
            r"e,4. r4. e,4. r4.",
            r"e,4. r4. e,4. r4.",
            r"e,4. r4. r2.",
            r"e,4. r4. r2.",
            r"e,4.\pp r4. r2.",
            REST,
            r"e,1.\fermata",
        ),
    )
    # The theorbo: 12 notes in a bar, then 10, 8, 6, 4, 2, and one chord.
    s.write(
        "lute",
        bars(
            r"e,8\p b, g e, b, g e, b, g e, b, g",
            r"e,8 b, g e, b, g e, c fis e, d gis",
            r"e,8 d gis e, c a e, c fis e, b, a",
            r"e,8 b, g e, b, g e, c a e, c a",
            r"e,8 c fis e, c r e, dis a e, dis r",
            r"e,8 b, r e, b, r e, c r e, c r",
            r"e,8 c r e, r4 e,8 c r dis r4",
            r"e,8\pp r4 b,8 r4 e,8 r4 c8 r4",
            r"e,8 r4 r4. gis8 r4 r4.",
            r"<e, b, e gis b e'>1.\arpeggio\fermata",
        ),
    )
    s.write(
        "org.rh",
        bars(
            r"g'4. r4. r2.",
            r"<e' g' b'>2.\pp <e' a' c''>4. <d' gis' b'>4.~",
            r"<d' gis' b'>4. <c' a' c''>4. <e' a' c''>4. <e' g' b'>4 <dis' a' b'>8",
            r"<e' g' b'>2. <e' a' c''>2.~",
            r"<e' a' c''>2. <dis' a' b'>2.",
            r"<e' g' b'>2. <e' g' c''>2.",
            r"<e' a' c''>2.~ <e' a' c''>4. <dis' a' b'>4.",
            r"<e' g' b'>2. <e' a' c''>2.",
            r"<e' gis' b'>1.~",
            r"<e' gis' b'>1.\fermata",
        ),
    )
    s.write(
        "org.lh",
        bars(
            r"e,1.\p~",
            r"e,1.~",
            r"e,1.~",
            r"e,1.~",
            r"e,1.~",
            r"e,1.~",
            r"e,1.~",
            r"e,1.~",
            r"e,1.~",
            r"e,1.\fermata",
        ),
    )
    s.close()
