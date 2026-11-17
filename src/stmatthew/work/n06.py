"""Number 6. Choral: "Ich will hier bei dir stehen" (the end of part 1).

Words: one sentence of the story (Matthew 26:56, movement 28 of Bach), then the
chorale verse of movement 17.

Elements of Bach: the Passion chorale ("Herzlich tut mich verlangen"), the first
of its four times in this work, in the setting of movement 17, note for note, in
its key (E-flat major). This is the one plain setting of the work.

The idea: all disciples flee, and the witness stays. The voice sings the tune of
the congregation alone. The instruments come in group by group: the strings and
the organ, then the oboes and the bassoon, then the flutes.

The recitative goes from the E minor of number 5 to E-flat major by a bass that
goes down by semitones: E, E-flat, D. The chord of C major becomes C minor on the
words "alle Jünger".
"""

from __future__ import annotations

from ..compose.tools import octave, plain
from ..notation.work import Work
from .material import HERZLICH_17 as CHORALE

# The chorale: its two first phrases come two times.
ORDER = (1, 2, 1, 2, 3, 4, 5, 6)

VOICE = r"""
    r8 g'16\mf g' c''8 c''16 g' c''8 c'' g' es' |
    r8 f' as'4 f'8 r
    g'4 |
    c''4 bes' as' g' | f'2 g'4\fermata d'' | es''4 es'' d''8( c'') d''4 | c''2.\fermata
    g'4 |
    c''4 bes' as' g' | f'2 g'4\fermata d'' | es''4 es'' d''8( c'') d''4 | c''2.\fermata
    es''4 |
    d''8( c'') bes'4 c'' d'' | es''2 es''4\fermata bes'\p | c''4 bes' as' as' | g'2.\fermata
    es''4\mf |
    d''8( es'') f''4 es'' d'' | c''2 d''4\fermata g'\p | as'4 g' f' bes' | g'2.\fermata r4 |
"""

WORDS = """
    Da ver -- lie -- ßen ihn al -- le Jün -- ger und flo -- hen.
    Ich will hier bei dir ste -- hen; ver -- ach -- te mich doch nicht!
    Von dir will ich nicht ge -- hen, wenn dir dein Her -- ze bricht.
    Wenn dein Herz wird er -- blas -- sen im letz -- ten To -- des -- stoß,
    als -- denn will ich dich fas -- sen in mei -- nen Arm und Schoß.
"""


def write(work: Work) -> None:
    structure = work.structure
    s = work.section(18, 4, 4)
    structure.mark(s.bar(1), "6")
    structure.key(s.bar(1), "es", "major")
    structure.tempo(s.bar(1), 1, 60, "Recitativo")
    structure.tempo(s.bar(3), 1, 56, "Choral")
    # The last chord has more time.
    structure.ritardando(s.bar(18), 1, 32, text="", resume="")

    s.sing("alto", VOICE, WORDS)

    # The recitative: harpsichord and violoncello.
    s.write("hpd.rh", r"<g c' e'>2\mf\arpeggio <g c' es'> | <f as bes>2. r4 | R1*16 |")
    s.write("hpd.lh", r"e2\mf es | d2. r4 | R1*16 |")

    # The chorale. All instruments: mf; softer for "im letzten Todesstoß" and for the last phrase.
    full = {1: r"\mf", 6: r"\p", 7: r"\mf", 8: r"\p"}
    wait = "R1 | r2. "  # the recitative: 7 quarter notes before the first note of the chorale
    end = " r4 |"
    lines = {voice: CHORALE.line(voice, ORDER, full) for voice in ("soprano", "alto", "tenor")}
    bass = CHORALE.line("bass", ORDER, full)
    s.write("vn1", wait + lines["soprano"] + end)
    s.write("vn2", wait + lines["alto"] + end)
    s.write("va", wait + lines["tenor"] + end)
    s.write("gamba", wait + lines["tenor"] + end)
    s.write("vc", r"e2\mf es | d2. " + bass + end)
    s.write("vne", wait + octave(bass, -1) + end)
    # The right hand of the organ: the tune and the alto voice of Bach (one set of marks).
    inner = plain(lines["alto"])
    s.write("org.rh", wait + "<< { " + lines["soprano"] + r" } \\ { " + inner + " } >>" + end)
    s.write("org.lh", wait + bass + end)

    # From the second time of the first two phrases: the oboes and the bassoon.
    later = {1: r"\mf", 4: r"\p", 5: r"\mf", 6: r"\p"}
    wait = "R1*5 | r2. "
    s.write("ob1", wait + CHORALE.line("soprano", ORDER[2:], later) + end)
    s.write("ob2", wait + CHORALE.line("alto", ORDER[2:], later) + end)
    s.write("bn", wait + CHORALE.line("bass", ORDER[2:], later) + end)

    # From the third phrase: the flutes.
    last = {1: r"\mf", 2: r"\p", 3: r"\mf", 4: r"\p"}
    wait = "R1*9 | r2. "
    s.write("fl1", wait + CHORALE.line("soprano", ORDER[4:], last) + end)
    s.write("fl2", wait + CHORALE.line("alto", ORDER[4:], last) + end)

    s.close()
    structure.double_bar(s.last_bar)
