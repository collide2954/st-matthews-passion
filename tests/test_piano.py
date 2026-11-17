"""Tests for the piano that the project renders with the Salamander samples."""

import numpy as np
import pytest

from stmatthew.audio import dsp, piano
from stmatthew.notation.work import Work, load_orchestra


def _piano_work() -> Work:
    """Three bars at 60 quarter notes in a minute: one bar is 4 s."""
    work = Work("Test", load_orchestra())
    section = work.section(3, 4, 4)
    work.structure.tempo(1, 1, 60, "Lento")
    section.write("pno.rh", r"c''8-.\mf r8 r4 r2 | c''8-.\ff r8 r4 r2 | R1 |")
    section.write("pno.lh", r"R1 | c2\ff\sustainOn r2 | r2\sustainOff r2 |")
    section.close()
    return work


def test_each_dynamic_mark_has_its_own_velocity_and_level_of_the_samples():
    marks = {"ppp": 0.18, "pp": 0.27, "p": 0.38, "mp": 0.49, "mf": 0.59, "f": 0.71, "ff": 0.83}
    values = [piano.velocity(level) for level in marks.values()]
    assert values == sorted(set(values))  # each mark is louder than the mark before it
    assert piano.velocity(0.0) == 1 and piano.velocity(1.5) == 127
    assert piano.velocity(0.59, accent=0.2) > piano.velocity(0.59)
    layers = [piano._layer(value) for value in values]
    assert layers == sorted(layers) and layers[0] == 1 and layers[-1] >= 13
    assert [piano._layer(value) for value in (1, 26, 27, 127)] == [1, 1, 2, 16]
    # A soft note is much softer than a loud note: more than the samples give.
    assert piano._gain(48) < 0.35 * piano._gain(94)


def test_the_names_of_the_sampled_keys_are_those_of_the_library():
    names = [piano._Library.name(centre) for centre in piano.CENTRES]
    assert names[:5] == ["A0", "C1", "D#1", "F#1", "A1"]
    assert names[-1] == "C8" and len(names) == 30


def test_the_pedal_and_the_short_notes_of_the_score_control_the_dampers():
    work = _piano_work()
    assert piano.pedal_spans(work) == [(4.0, 8.0)]
    notes = piano.notes_of(work)
    # A staccato note: the key goes up after a short time.
    start, key_up, midi, _value = notes[0]
    largest = piano.LARGEST_SHIFT_MS / 1000.0
    assert 0.0 <= start <= largest and midi == 72
    assert key_up - start <= piano.STACCATO_SECONDS
    # The low strings need more time to stop than the high strings.
    assert piano._damp_seconds(30) > piano._damp_seconds(60) > piano._damp_seconds(85)


@pytest.mark.skipif(not piano.available(), reason="the samples are not on this computer")
def test_a_note_with_the_pedal_sounds_longer_than_a_note_with_no_pedal():
    audio = piano.render(_piano_work(), 0.0, 12.0).mean(axis=1)

    def level(second: float) -> float:
        part = audio[int(second * dsp.RATE) : int((second + 0.5) * dsp.RATE)]
        return float(20 * np.log10(np.sqrt(np.mean(np.square(part))) + 1e-9))

    assert level(0.0) > -40.0  # the first note sounds
    assert level(1.0) < -80.0  # no pedal: the damper stopped it
    assert level(6.0) > -45.0  # the pedal holds the second bar
    assert level(11.0) < level(6.0) - 30.0  # after the pedal goes up, the sound stops
    assert level(4.0) > level(0.0) + 3.0  # ff is louder than mf


def test_the_notes_of_a_rolled_chord_start_one_after_the_other():
    work = Work("Test", load_orchestra())
    section = work.section(2, 4, 4)
    work.structure.tempo(1, 1, 60, "Lento")
    section.write("pno.rh", r"<e' g' c''>1\f\arpeggio | <e' g' c''>1 |")
    section.write("pno.lh", r"<c, c>1\f\arpeggio | <c, c>1 |")
    section.close()
    notes = piano.notes_of(work)
    rolled = sorted(note for note in notes if note[0] < 3.0)
    block = sorted(note for note in notes if note[0] > 3.0)
    assert [midi for _start, _key_up, midi, _value in rolled] == [36, 48, 64, 67, 72]
    steps = np.diff([start for start, *_rest in rolled])
    largest = 2 * piano.LARGEST_SHIFT_MS / 1000.0
    assert np.all(steps > piano.ROLL_STEP_SECONDS - largest)  # from the lowest note up
    assert rolled[-1][0] - rolled[0][0] <= piano.ROLL_SECONDS + largest
    # A chord with no mark: all its notes start together (with the small differences).
    assert block[-1][0] - block[0][0] <= largest


def test_each_stroke_has_small_differences_of_time_and_loudness():
    notes = [piano._human(float(second), second + 0.5, 60, 80) for second in range(1, 201)]
    shifts = np.array([start - second for second, (start, *_rest) in enumerate(notes, 1)])
    assert np.all(np.abs(shifts) <= piano.LARGEST_SHIFT_MS / 1000.0 + 1e-9)
    assert 0.003 < float(np.std(shifts)) < 0.010  # some milliseconds, not more
    values = np.array([value for *_rest, value in notes])
    assert 1.5 < float(np.std(values)) < 5.0 and abs(float(np.mean(values)) - 80.0) < 1.0
    # The key is down for the same time as before the change.
    assert all(key_up - start == pytest.approx(0.5) for start, key_up, *_rest in notes)
    # The same note gets the same differences each time: a render is repeatable.
    assert piano._human(3.0, 3.5, 60, 80) == piano._human(3.0, 3.5, 60, 80)
    # The notes of one chord stay together: their common difference is the larger part.
    chord = [piano._human(7.0, 7.5, midi, 80)[0] for midi in (48, 55, 60, 64, 67)]
    assert max(chord) - min(chord) < 0.012
    # A note at the start of the work does not start before the work.
    assert all(piano._human(0.0, 0.5, midi, 80)[0] >= 0.0 for midi in range(40, 80))


def test_the_piano_is_the_soloist_only_between_the_two_marks():
    from stmatthew.audio import musescore

    work = Work("Test", load_orchestra())
    section = work.section(40, 4, 4)
    work.structure.tempo(1, 1, 60, "Lento")  # one bar is 4 s
    first, last = musescore.PIANO_SOLO_MARKS
    work.structure.mark(11, first)  # at 40 s
    work.structure.mark(21, last)  # at 80 s
    section.close()
    step = dsp.RATE  # the test examines one sample for each second
    role = musescore.piano_role(work, 0.0, 120 * dsp.RATE)[::step]
    assert role[0] == 0.0 and role[110] == 0.0
    assert role[37] == 0.0  # the change starts 2 s before the first mark
    assert 0.0 < role[39] < 1.0
    assert role[40] == 1.0 and role[80] == 1.0
    assert 0.0 < role[81] < 1.0 and role[83] == 0.0  # the change is after the second mark
    # An excerpt that starts in the interlude has the soloist immediately.
    assert musescore.piano_role(work, 50.0, 100)[0] == 1.0
    # A work that does not have the marks: the piano is an instrument of the orchestra.
    assert not musescore.piano_role(_piano_work(), 0.0, 100).any()


@pytest.mark.skipif(not piano.available(), reason="the samples are not on this computer")
def test_the_piano_in_the_orchestra_is_on_the_left_and_has_more_hall_than_the_soloist():
    dry = piano.render(_piano_work(), 0.0, 4.0)
    front, seat = piano.place(dry), piano.place_in_orchestra(dry)

    def level(audio: np.ndarray) -> float:
        return float(np.sqrt(np.mean(np.square(audio))))

    # After the note stops (at 0.2 s), only the hall sounds.
    note, hall = slice(0, dsp.RATE // 10), slice(dsp.RATE, 2 * dsp.RATE)
    # The seat of the piano is on the left of the stage: the note is louder on the left.
    assert level(seat[note, 0]) > 1.2 * level(seat[note, 1])
    # The seat in the orchestra has more hall in relation to the note than the place
    # of the soloist has.
    assert level(seat[hall]) / level(seat[note]) > 1.5 * level(front[hall]) / level(front[note])
