"""Write notes with free start times and lengths into bars.

Some methods of the work make a line from numbers: a line at a slower speed,
a line that starts later, a rhythm cycle that turns against the bar. The
result is a list of tones: each has a start time and a length. This module
writes such a list as music text: it divides each tone at the bar lines and
at the strong beats, and it ties the parts. It writes the rests between the
tones.

The rules of the division are those of usual notation:

- A note does not go across a bar line.
- In a simple metre (4/4, 3/4, 2/4), a note that starts on a weak place
  does not go across a stronger place. The exception is the simple
  syncopation: a note of two units that starts on the second unit (for
  example a quarter note after an eighth note, or a half note on beat 2).
- In a compound metre (12/8, 6/8, 9/8, 3/8), a note that goes across a beat
  starts on a beat and has the length of whole beats.
- A rest does not go across a stronger place, and it has no dot in a simple
  metre.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from fractions import Fraction

from ..notation import music

# Note values in quarter notes, and their text. The first group has no dot.
_PLAIN = {
    Fraction(4): "1", Fraction(2): "2", Fraction(1): "4", Fraction(1, 2): "8",
    Fraction(1, 4): "16", Fraction(1, 8): "32", Fraction(1, 16): "64",
}  # fmt: skip
_DOTTED = {value * 3 / 2: text + "." for value, text in _PLAIN.items()}
VALUES = {**_PLAIN, **_DOTTED}


@dataclass(frozen=True)
class Tone:
    """A note or a chord with a start time and a length, in quarter notes."""

    start: Fraction
    length: Fraction
    pitch: str  # the note or the chord with no duration: "c'" or "<c e g>"
    marks: str = ""  # marks for the start of the note (a dynamic mark, a slur, an articulation)
    end: str = ""  # marks for the last part of the note (a fermata)

    @property
    def stop(self) -> Fraction:
        return self.start + self.length


@dataclass(frozen=True)
class Metre:
    """The strong places of a bar, from the strongest level to the weakest."""

    numerator: int
    denominator: int

    @property
    def bar(self) -> Fraction:
        return Fraction(4 * self.numerator, self.denominator)

    @property
    def compound(self) -> bool:
        return self.denominator == 8 and self.numerator % 3 == 0

    @property
    def beat(self) -> Fraction:
        return Fraction(3, 2) if self.compound else Fraction(4, self.denominator)

    @property
    def spacings(self) -> list[Fraction]:
        """Return the distance between the places of each level."""
        levels = [self.bar]
        if self.compound:
            if self.numerator == 12:
                levels.append(Fraction(3))
            if self.numerator > 3:
                levels.append(self.beat)
            unit = Fraction(1, 2)
        else:
            if self.numerator == 4:
                levels.append(self.bar / 2)
            if self.beat != levels[-1]:
                levels.append(self.beat)
            unit = self.beat / 2
        while unit >= Fraction(1, 16):
            levels.append(unit)
            unit /= 2
        return levels

    def level(self, position: Fraction) -> int:
        """Return the level of a place in the bar (0 = the start of the bar)."""
        spacings = self.spacings
        for number, spacing in enumerate(spacings):
            if position % spacing == 0:
                return number
        raise ValueError(f"the place {position} is not on a sixty-fourth note")

    def crossed(self, start: Fraction, stop: Fraction, level: int) -> list[Fraction]:
        """Return the places of one level between `start` and `stop` (not the two ends)."""
        spacing = self.spacings[level]
        first = (start // spacing + 1) * spacing
        places = []
        while first < stop:
            places.append(first)
            first += spacing
        return places

    def single(self, start: Fraction, length: Fraction, rest: bool = False) -> bool:
        """Return true if one note (or one rest) can have this place and this length."""
        if length not in VALUES:
            return False
        stop = start + length
        level = self.level(start)
        if self.compound:
            inside = (
                self.crossed(start, stop, self.spacings.index(self.beat))
                if (self.beat in self.spacings)
                else []
            )
            if inside and (start % self.beat or length % self.beat):
                return False
            if not inside and length not in _PLAIN and length % Fraction(3, 4):
                return False
        elif rest and length not in _PLAIN:
            return False
        for stronger in range(level):
            if not self.crossed(start, stop, stronger):
                continue
            syncopation = (
                not rest
                and not self.compound
                and stronger == level - 1
                and length == 2 * self.spacings[level]
                and not any(self.crossed(start, stop, other) for other in range(stronger))
            )
            if not syncopation:
                return False
        return True

    def divide(self, start: Fraction, stop: Fraction, rest: bool = False) -> list[Fraction]:
        """Divide the time from `start` to `stop` in one bar. Return the lengths of the parts."""
        if self.single(start, stop - start, rest):
            return [stop - start]
        for level in range(len(self.spacings)):
            places = self.crossed(start, stop, level)
            if not places:
                continue
            # The latest place that gives one note before it; if there is none, the first place.
            good = [place for place in places if self.single(start, place - start, rest)]
            place = good[-1] if good else places[0]
            return self.divide(start, place, rest) + self.divide(place, stop, rest)
        raise ValueError(f"no note value for the time from {start} to {stop}")


def notate(
    tones: Sequence[Tone], numerator: int, denominator: int, bars: int, first_bar: int = 1
) -> str:
    """Return the music text of some bars with the tones in them, and rests between them.

    The time of a tone is in quarter notes from the start of bar 1. The
    result has the bars from `first_bar`, `bars` in number. A tone that
    starts before the first bar, or stops after the last bar, is an error.
    """
    metre = Metre(numerator, denominator)
    begin = (first_bar - 1) * metre.bar
    end = begin + bars * metre.bar
    ordered = sorted(tones, key=lambda tone: tone.start)
    for tone, following in zip(ordered[:-1], ordered[1:], strict=True):
        if tone.stop > following.start:
            raise ValueError(f"two tones at the same time ({tone.pitch} and {following.pitch})")
    if ordered and (ordered[0].start < begin or ordered[-1].stop > end):
        raise ValueError("a tone is not in the bars")
    # The time of the bars as a sequence of tones and silences.
    segments: list[tuple[Fraction, Fraction, Tone | None]] = []
    position = begin
    for tone in ordered:
        if tone.start > position:
            segments.append((position, tone.start, None))
        segments.append((tone.start, tone.stop, tone))
        position = tone.stop
    if position < end:
        segments.append((position, end, None))

    parts: list[str] = []
    empty = 0  # the number of full bars of rest before the place

    def flush() -> None:
        nonlocal empty
        if empty:
            count = "" if empty == 1 else f"*{empty}"
            parts.append(f"R1*{numerator}/{denominator}{count} |")
            empty = 0

    for number in range(bars):
        bar_start = begin + number * metre.bar
        bar_end = bar_start + metre.bar
        tokens: list[str] = []
        for start, stop, tone in segments:
            if stop <= bar_start or start >= bar_end:
                continue
            low, high = max(start, bar_start), min(stop, bar_end)
            if tone is None:
                if low == bar_start and high == bar_end:
                    continue  # a full bar of rest
                for length in metre.divide(low - bar_start, high - bar_start, rest=True):
                    tokens.append("r" + VALUES[length])
                continue
            lengths = metre.divide(low - bar_start, high - bar_start)
            for place, length in enumerate(lengths):
                text = tone.pitch + VALUES[length]
                if low == start and place == 0:
                    text += tone.marks
                text += tone.end if high == stop and place == len(lengths) - 1 else "~"
                tokens.append(text)
        if tokens:
            flush()
            parts.append(" ".join(tokens) + " |")
        else:
            empty += 1
    flush()
    return " ".join(parts)


def tones(text: str, start: Fraction | int = 0) -> list[Tone]:
    """Read music text as tones. The text can have notes, chords, rests, and bar checks.

    A tie makes one tone from two notes. The marks of a note stay with its
    tone; a fermata goes to the end of the tone.
    """
    position = Fraction(start)
    result: list[Tone] = []
    tied = False
    for element in music.parse(text).children:
        if isinstance(element, music.BarCheck):
            continue
        if isinstance(element, music.Rest):
            position += element.duration
            tied = False
            continue
        if not isinstance(element, music.Note):
            raise ValueError("tones() reads only notes, chords, rests, and bar checks")
        names = [p.pitch.name + p.marks for p in element.pitches]
        pitch = "<" + " ".join(names) + ">" if element.chord else names[0]
        posts = [post for post in element.posts if post.kind != "tie"]
        ends = [post for post in posts if post.kind == "command" and "fermata" in post.value]
        marks = "".join(post.text for post in posts if post not in ends)
        end = "".join(post.text for post in ends)
        if tied and result and result[-1].pitch == pitch:
            last = result[-1]
            result[-1] = replace(last, length=last.length + element.duration, end=last.end + end)
        else:
            result.append(Tone(position, element.duration, pitch, marks, end))
        tied = any(post.kind == "tie" for post in element.posts)
        position += element.duration
    return result


def stretch(
    found: Sequence[Tone], factor: Fraction | int, origin: Fraction | int = 0
) -> list[Tone]:
    """Return the tones at a different speed: each time from `origin` is `factor` times longer."""
    factor, origin = Fraction(factor), Fraction(origin)
    return [
        replace(tone, start=origin + (tone.start - origin) * factor, length=tone.length * factor)
        for tone in found
    ]


def shift(found: Sequence[Tone], offset: Fraction | int) -> list[Tone]:
    """Return the tones `offset` quarter notes later."""
    return [replace(tone, start=tone.start + Fraction(offset)) for tone in found]


def span(found: Sequence[Tone]) -> Fraction:
    """Return the time from the first start to the last stop."""
    return max(tone.stop for tone in found) - min(tone.start for tone in found)
