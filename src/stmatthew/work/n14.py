"""Number 14. Choral: "Wenn ich einmal soll scheiden" (after the death).

Words: the chorale verse of movement 62 of Bach.

Elements of Bach: the Passion chorale, the fourth and last of its times in
this work, with the four voices of the setting of movement 62, in its key
(A minor). The last chord is E major: the dominant.

The idea: "When I must go away, do not go away from me." The voice sings
the tune in plain notes. The strings (with mutes) have the four voices of
Bach, but not at one speed. In each line of the verse, some voices are
slower than the voice: their notes are 1.5, 2, or 3 times as long. Thus the
chords of Bach come apart: a slow voice holds the note of a chord that the
other voices left (the suspension of Bach, made longer). The voices that
are at the end of the line wait on their last note. When the slowest voice
comes to its last note, the chord of Bach is complete again.

The number of different speeds makes the form: 2, 2, 3, 2 in the first four
lines, four speeds in line 5 ("when my heart is most afraid"), then 3 and
2, and one speed for all in the last line: the plain setting of Bach.

The first violins have the tune one octave above the voice: the shadow of
the tune. In lines 1, 3, 5, and 6 the shadow is slower than the voice, and
it comes to the last note of the line after all other voices: its note
makes the chord complete. In the other lines it stays with the voice.

The violoncellos and the viola da gamba have the bass of Bach at the speed
of the voice. The violone comes for the last line.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F

from ..compose import rhythm
from ..compose.rhythm import Tone
from ..compose.tools import first, octave
from ..notation.work import Work
from .material import HERZLICH_62 as CHORALE

# The tune of each phrase with the slurs of the words (a slur is one syllable).
TUNE = {
    1: r"e'4 a' g' f' e' d'2 e'4",
    2: r"b'4 c'' b'8( c''16 d'') c''4 b'8( a') a'2.",
    3: r"c''4 b'8( a') g'4 a' b' c''2 c''4",
    4: r"g'4 a' g' a'8( g') f'4 e'2.",
    5: r"c''4 b'8( c'') d''4 c'' b' a'2 b'4",
    6: r"e'4 f' e' d' g'8( f') e'2.",
}

WORDS = """
    Wenn ich ein -- mal soll schei -- den,
    so schei -- de nicht von mir,
    wenn ich den Tod soll lei -- den,
    so tritt du dann her -- für!
    Wenn mir am al -- ler -- bäng -- sten
    wird um das Her -- ze sein,
    so reiß mich aus den Äng -- sten
    kraft dei -- ner Angst und Pein!
"""

# The players of the four voices of Bach. The first violins are one octave higher.
PLAYERS = {"soprano": ("vn1",), "alto": ("vn2",), "tenor": ("va",), "bass": ("vc", "gamba")}
MUTED = ("vn1", "vn2", "va", "vc")

# Each line of the verse: the phrase of the setting, the speed of each voice of the
# strings (the length of a note in relation to the note of Bach; 1 if not given), the
# dynamic mark of the strings, and the dynamic mark of the voice.
#
# The speeds come from a search: for each line, the code made all sets of speeds and
# counted the moments with a semitone clash (the tool `compose/ears.py`). The sets
# here make an arch: 0.19, 0.17, 0.22, 0.29, 0.29, 0.16, 0.00, 0.00 of the moments.
# The bass has always the speed of the voice: the tune and the bass of Bach stay
# together, as the frame of the harmony.
LINES = (
    # "When I must go away": the shadow of the tune goes away from the voice.
    (1, {"soprano": F(2)}, r"\pp", r"\p"),
    # "do not go away from me": the shadow stays with the voice; one middle voice is slow.
    (2, {"alto": F(3, 2)}, r"\pp", r"\p"),
    (1, {"soprano": F(2), "tenor": F(3, 2)}, r"\p", r"\mp"),
    (2, {"alto": F(3, 2), "tenor": F(3, 2)}, r"\p", r"\mp"),
    # "When my heart is most afraid": each voice has its own speed.
    (3, {"soprano": F(3), "alto": F(2), "tenor": F(3, 2)}, r"\mp", r"\mf"),
    (4, {"soprano": F(2), "alto": F(3, 2), "tenor": F(3, 2)}, r"\p", r"\mp"),
    # "take me out of the fears": only the tenor is slow, and it makes no clash.
    (5, {"tenor": F(3, 2)}, r"\pp", r"\mp"),
    # The last line: the plain setting of Bach.
    (6, {}, r"\pp", r"\p"),
)

UPBEAT = F(3)  # the first line starts on the fourth beat of the first bar
BREATH = F(1, 2)  # the strings stop this time before the subsequent line
LAST_HOLD = F(1)  # the last chord fills its bar: the last line has nine quarter notes


def line_length(speeds: dict[str, F]) -> F:
    """Return the length of a line in quarter notes: the time of its slowest voice."""
    return 8 * max([F(1), *speeds.values()])


def plan() -> tuple[dict[str, list[Tone]], int]:
    """Return the tones of each player and of the voice, and the number of bars."""
    parts: dict[str, list[Tone]] = {"alto": []}
    start = UPBEAT
    for number, (phrase, speeds, level, voice_level) in enumerate(LINES, start=1):
        last = number == len(LINES)
        length = line_length(speeds) + (LAST_HOLD if last else 0)
        stop = start + length
        # The voice: the tune at the speed of Bach. A short last note gets more time.
        tune = rhythm.shift(rhythm.tones(first(TUNE[phrase], voice_level)), start)
        if last:
            tune[-1] = replace(tune[-1], length=stop - tune[-1].start, end=r"\fermata")
        elif tune[-1].length < 2 and length > 8:
            tune[-1] = replace(tune[-1], length=F(2))
        parts["alto"].extend(tune)
        # The strings: each voice at its speed. Its last note stays to the end of the line.
        for voice, players in PLAYERS.items():
            text = first(getattr(CHORALE, voice)[phrase - 1].replace(r"\fermata", ""), level)
            if voice == "soprano":
                text = octave(text, 1)
            tones = rhythm.stretch(rhythm.tones(text), speeds.get(voice, F(1)))
            tones = rhythm.shift(tones, start)
            end = stop if last else stop - BREATH
            tones[-1] = replace(
                tones[-1], length=end - tones[-1].start, end=r"\fermata" if last else ""
            )
            for player in players:
                parts.setdefault(player, []).extend(tones)
            if voice == "bass" and last:
                # The violone comes for the last line only: the bass one octave lower.
                low = rhythm.shift(rhythm.tones(octave(text, -1)), start)
                low[-1] = replace(low[-1], length=end - low[-1].start, end=r"\fermata")
                parts.setdefault("vne", []).extend(low)
        start = stop
    bars, rest = divmod(start, 4)
    return parts, int(bars) + (1 if rest else 0)


def write(work: Work) -> None:
    structure = work.structure
    parts, bars = plan()
    s = work.section(bars, 4, 4)
    structure.mark(s.bar(1), "14")
    structure.key(s.bar(1), "a", "minor")
    structure.tempo(s.bar(1), 1, 54, "Choral. Molto adagio")
    # The last line goes slower, and the last chord (E major, the dominant) has a hold.
    structure.ritardando(s.bar(bars - 1), 1, 46, text="", resume="")
    structure.fermata(s.bar(bars), 2.5)

    s.sing("alto", rhythm.notate(parts.pop("alto"), 4, 4, bars), WORDS)
    for player, tones in parts.items():
        text = rhythm.notate(tones, 4, 4, bars)
        if player in MUTED:
            text = first(text, r"\consord", note=True)
        s.write(player, text)
    s.close()
    structure.double_bar(s.last_bar)
