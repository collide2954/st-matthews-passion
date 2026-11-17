"""Tests for the numbers of the work: each number keeps the facts of its plan."""

from fractions import Fraction as F

from stmatthew.compose import ears, rhythm
from stmatthew.perform.events import perform
from stmatthew.work import build, n14
from stmatthew.work.material import HERZLICH_62


def _bars_of(work, label: str) -> tuple[int, int]:
    """Return the first and the last bar of the number with this mark."""
    marks = sorted(work.structure.marks.items())
    starts = [bar for bar, _label in marks]
    first = next(bar for bar, name in marks if name == label)
    later = [bar for bar in starts if bar > first]
    return first, (later[0] - 1 if later else len(work.structure.bars))


def test_number_14_has_the_voices_of_bach_at_different_speeds():
    work = build([14])
    first, last = _bars_of(work, "14")
    assert (first, last) == (1, 30)
    # The voice has the tune of Bach: the notes of the soprano, phrase by phrase.
    tune = [
        tone.pitch
        for phrase, _speeds, _level, _voice in n14.LINES
        for tone in rhythm.tones(HERZLICH_62.soprano[phrase - 1])
    ]
    sung = [ears.note_name(note.midi) for note in perform(work, "alto")]
    wanted = [ears.note_name(_midi(pitch)) for pitch in tune]
    assert sung == wanted
    # The bass has the speed of the voice in all lines.
    assert all("bass" not in speeds for _phrase, speeds, _level, _voice in n14.LINES)
    # The last chord is E major, and all strings have it.
    end = ears.moments(work, last, last)[-1]
    assert end.symbol == "E"
    assert {player for _pitch, player in end.notes} == {
        "vn1", "vn2", "va", "gamba", "alto", "vc", "vne",
    }  # fmt: skip
    # Each line ends with the chord of Bach: the slow voices come to their last notes.
    parts, bars = n14.plan()
    assert bars == 30
    start = n14.UPBEAT
    for phrase, speeds, _level, _voice in n14.LINES[:-1]:
        stop = start + n14.line_length(speeds)
        bar, beat = divmod(stop - n14.BREATH - F(1, 2), 4)
        moment = ears.moments(work, int(bar) + 1, int(bar) + 1, F(1, 2))[int(beat * 2)]
        chord = {
            _midi(rhythm.tones(getattr(HERZLICH_62, voice)[phrase - 1])[-1].pitch) % 12
            for voice in ("soprano", "alto", "tenor", "bass")
        }
        assert moment.classes == chord
        start = stop


def _midi(pitch: str) -> int:
    from stmatthew.notation.pitch import Pitch

    return round(Pitch.parse(pitch).midi)


def test_the_last_lines_of_number_14_have_no_clash():
    work = build([14])
    found = ears.moments(work, 25, 30, F(1, 2))
    # From the upbeat of line 7 (bar 25, beat 4) to the end.
    late = [m for m in found if (m.bar, m.beat) >= (25, F(4))]
    assert not any(moment.clashes for moment in late)
