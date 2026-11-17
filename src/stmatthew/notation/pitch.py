"""Spelled pitches with quarter-tones, in the note names of LilyPond.

LilyPond uses Dutch note names: `c d e f g a b`. The suffix `is` is a sharp
and `es` is a flat. The suffix `ih` is a quarter-tone sharp and `eh` is a
quarter-tone flat. In the absolute octave system, `c'` is middle C.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

STEP_NAMES = "cdefgab"
STEP_SEMITONES = (0, 2, 4, 5, 7, 9, 11)

_SUFFIX_OF_ALTER = {
    Fraction(-2): "eses",
    Fraction(-3, 2): "eseh",
    Fraction(-1): "es",
    Fraction(-1, 2): "eh",
    Fraction(0): "",
    Fraction(1, 2): "ih",
    Fraction(1): "is",
    Fraction(3, 2): "isih",
    Fraction(2): "isis",
}


def _build_names() -> dict[str, tuple[int, Fraction]]:
    names: dict[str, tuple[int, Fraction]] = {}
    for step, letter in enumerate(STEP_NAMES):
        for alter, suffix in _SUFFIX_OF_ALTER.items():
            names[letter + suffix] = (step, alter)
            # The letters a and e have short forms: as, es, ases, eses, aseh, eseh.
            if letter in "ae" and suffix.startswith("es"):
                names[letter + suffix[1:]] = (step, alter)
    return names


NAMES = _build_names()
_NAMES_LONGEST_FIRST = sorted(NAMES, key=len, reverse=True)


@dataclass(frozen=True)
class Interval:
    """A transposition interval: a number of scale steps and a number of semitones."""

    steps: int
    semitones: int

    def __neg__(self) -> Interval:
        return Interval(-self.steps, -self.semitones)


UNISON = Interval(0, 0)


@dataclass(frozen=True, order=True)
class Pitch:
    """A spelled pitch. `octave` 4 is the octave that starts at middle C."""

    step: int
    alter: Fraction
    octave: int

    @property
    def midi(self) -> float:
        """Return the MIDI number. A quarter-tone gives a half number."""
        return 12 * (self.octave + 1) + STEP_SEMITONES[self.step] + float(self.alter)

    @property
    def name(self) -> str:
        """Return the LilyPond name with octave marks, for example `cis'`."""
        letter = STEP_NAMES[self.step]
        suffix = _SUFFIX_OF_ALTER[self.alter]
        # LilyPond has the short forms as, es, ases, and eses. The names of the
        # three-quarter flats have no short form (aeseh, eeseh).
        if letter in "ae" and suffix in ("es", "eses"):
            suffix = suffix[1:]
        marks = self.octave - 3
        return letter + suffix + ("'" * marks if marks > 0 else "," * -marks)

    @staticmethod
    def parse(text: str) -> Pitch:
        """Parse a LilyPond pitch name with octave marks."""
        pitch, rest = Pitch.parse_prefix(text)
        if rest:
            raise ValueError(f"not a pitch: {text!r}")
        return pitch

    @staticmethod
    def parse_prefix(text: str) -> tuple[Pitch, str]:
        """Parse a pitch at the start of `text`. Return the pitch and the remaining text."""
        for name in _NAMES_LONGEST_FIRST:
            if text.startswith(name):
                step, alter = NAMES[name]
                index = len(name)
                octave = 3
                while index < len(text) and text[index] in "',":
                    octave += 1 if text[index] == "'" else -1
                    index += 1
                return Pitch(step, alter, octave), text[index:]
        raise ValueError(f"not a pitch: {text!r}")

    def transposed(self, interval: Interval) -> Pitch:
        """Return this pitch moved by an interval. The spelling follows the interval."""
        index = self.step + 7 * self.octave + interval.steps
        octave, step = divmod(index, 7)
        natural = 12 * (octave + 1) + STEP_SEMITONES[step]
        target = self.midi + interval.semitones
        return Pitch(step, Fraction(target - natural).limit_denominator(2), octave)

    def simplified(self) -> Pitch:
        """Return a simpler spelling of the same sound, if this spelling is unusual.

        Unusual spellings are double accidentals and the notes E-sharp,
        B-sharp, C-flat, and F-flat. Quarter-tones stay as they are.
        """
        letter = STEP_NAMES[self.step]
        unusual = (
            abs(self.alter) >= 2
            or (self.alter == 1 and letter in "eb")
            or (self.alter == -1 and letter in "cf")
        )
        if not unusual:
            return self
        direction = 1 if self.alter > 0 else -1
        best = self
        for shift in (direction, 2 * direction):
            index = self.step + 7 * self.octave + shift
            octave, step = divmod(index, 7)
            natural = 12 * (octave + 1) + STEP_SEMITONES[step]
            alter = Fraction(self.midi - natural).limit_denominator(2)
            candidate = Pitch(step, alter, octave)
            if abs(candidate.alter) < abs(best.alter):
                best = candidate
        return best


def from_midi(midi: float, *, prefer_sharps: bool = False) -> Pitch:
    """Return a default spelling for a MIDI number (half numbers are quarter-tones)."""
    whole = int(midi // 1)
    quarter = Fraction(midi - whole).limit_denominator(2)
    sharp_table = {0: (0, 0), 1: (0, 1), 2: (1, 0), 3: (1, 1), 4: (2, 0), 5: (3, 0), 6: (3, 1)}
    sharp_table |= {7: (4, 0), 8: (4, 1), 9: (5, 0), 10: (5, 1), 11: (6, 0)}
    flat_table = {0: (0, 0), 1: (1, -1), 2: (1, 0), 3: (2, -1), 4: (2, 0), 5: (3, 0), 6: (4, -1)}
    flat_table |= {7: (4, 0), 8: (5, -1), 9: (5, 0), 10: (6, -1), 11: (6, 0)}
    step, alter = (sharp_table if prefer_sharps else flat_table)[whole % 12]
    return Pitch(step, Fraction(alter) + quarter, whole // 12 - 1)
