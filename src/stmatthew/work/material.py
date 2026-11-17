"""Material of J. S. Bach that the work uses: the chorale settings.

Each setting has the four voices of Bach, phrase by phrase. The notes come
from the edition of the chorales that the style study measured (table M3 of
the study); the tool `tools/study/tune.py` prints them in the music language
of the project, in the key of this work.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..compose.tools import first


@dataclass(frozen=True)
class Setting:
    """A chorale setting in four voices. Each voice is a list of phrases."""

    soprano: tuple[str, ...]
    alto: tuple[str, ...]
    tenor: tuple[str, ...]
    bass: tuple[str, ...]

    def line(self, voice: str, order: tuple[int, ...], marks: dict[int, str] | None = None) -> str:
        """Return one voice as one line of music.

        `order` gives the phrases in the sequence of the performance (the
        first phrase is 1): a chorale repeats its first phrases. `marks`
        gives marks for the first note of a phrase; its key is the place in
        `order` (the first place is 1).
        """
        phrases = getattr(self, voice)
        parts = []
        for place, number in enumerate(order, start=1):
            text = phrases[number - 1]
            if marks and place in marks:
                text = first(text, marks[place], note=True)
            parts.append(text)
        return " ".join(parts)


# "Herzlich tut mich verlangen" in the setting of BWV 244, movements 15 and 17, in E-flat
# major (the key of movement 17, "Ich will hier bei dir stehen").
HERZLICH_17 = Setting(
    soprano=(
        r"g'4 c'' bes' as' g' f'2 g'4\fermata",
        r"d''4 es'' es'' d''8 c'' d''4 c''2.\fermata",
        r"es''4 d''8 c'' bes'4 c'' d'' es''2 es''4\fermata",
        r"bes'4 c'' bes' as' as' g'2.\fermata",
        r"es''4 d''8 es'' f''4 es'' d'' c''2 d''4\fermata",
        r"g'4 as' g' f' bes' g'2.\fermata",
    ),
    alto=(
        "es'4 es' es' es'8 f' f' es' es'4 d' es'",
        "f'4 es'8 f' g'4 g' g'8 f' es'2.",
        "c''8 bes' as'4 g'8 f' es'4 as' as' g'8 f' g'4",
        "g'4 as' g' g' f' e'2.",
        "f'4 f' f' g' f' g' f' f'",
        "es'4 es'8 d' es'4 es' d' es'2.",
    ),
    tenor=(
        "bes4 as bes c'8 bes bes4 c' bes bes",
        "b4 g c' c' b c'2.",
        "g'4 f'8 es' d'4 c'8 bes as bes c'4 bes8 as bes4",
        "es'4 es' es'8 d' c'4 c' c'2.",
        "c'4 bes bes8 a bes c' d' bes g c' a4 bes",
        "bes4 as bes c' f8 bes bes2.",
    ),
    bass=(
        "es4 as g c8 d es4 as, bes, es",
        "d4 c8 d es f g4 g, c2.",
        "c'4 f g as8 g f4 es2 es4",
        "es4 as es f8 g as bes c'2.",
        "a4 bes d g8 a bes4 es f bes,",
        "es8 d c4 bes, as, bes, es,2.",
    ),
)

# The same tune in the setting of BWV 244, movement 62, in A minor ("Wenn ich einmal soll
# scheiden"). The last chord is E major: the dominant.
HERZLICH_62 = Setting(
    soprano=(
        r"e'4 a' g' f' e' d'2 e'4\fermata",
        r"b'4 c'' b'8 c''16 d'' c''4 b'8 a' a'2.\fermata",
        r"c''4 b'8 a' g'4 a' b' c''2 c''4\fermata",
        r"g'4 a' g' a'8 g' f'4 e'2.\fermata",
        r"c''4 b'8 c'' d''4 c'' b' a'2 b'4\fermata",
        r"e'4 f' e' d' g'8 f' e'2.\fermata",
    ),
    alto=(
        "c'4 c'8 d' e'4 a8 b c'4 c' b c'",
        "e'4 e' f' e' d'8 c' c'2.",
        "e'4 fis' e' f' f' g' f' e'",
        "e'4 e'8 d' cis' d' e'4. d'8 d'4 cis'2",
        "a'4 g' g' g'8 a' b' g' g'4 fis' g'",
        "c'4 d' c' d' e'8 d' d'4 c' b",
    ),
    tenor=(
        "a4 a8 b c'4 d' g a g g",
        "b4 a a a gis e2.",
        "a8 g fis4 b c' d' c'8 bes4 as8 g4",
        "c'8 bes a4 bes a a a2.",
        "d'4 d' d'8 e'16 f' e'4 d' e' d' d'",
        "g4 g g g8 a bes4 b a gis",
    ),
    bass=(
        "a8 g f4 e d c fis, g, c",
        "gis,4 a, d e e, a,2.",
        "a4 dis e es d e f c",
        "c4 f e8 d cis4 d a,2.",
        "fis4 g8 a b4 e8 fis g4 cis d g,",
        "c4 b, c bes,8 a, g,4 gis, a, e,",
    ),
)
