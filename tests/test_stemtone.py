"""Tests for the rule that gives the loud marks of the brass their difference again."""

import numpy as np

from stmatthew.audio import dsp, stemtone
from stmatthew.notation.work import Work, load_orchestra
from stmatthew.perform.events import DYNAMIC_LEVEL


def _brass_work() -> Work:
    """Four bars at 60 quarter notes in a minute: one bar is 4 s."""
    work = Work("Test", load_orchestra())
    section = work.section(4, 4, 4)
    work.structure.tempo(1, 1, 60, "Lento")
    section.write("tpt1", r"R1 | c''1\f | R1 | c''1\mp\< |")
    section.write("tbn1", r"R1 | c'2\fff r2 | R1*2 |")
    section.close()
    work.section(1, 4, 4).close()
    return work


def _level_at(curve: np.ndarray, second: float) -> float:
    return float(curve[int(round(second * stemtone.CONTROL_RATE))])


def test_the_written_loudness_is_that_of_the_loudest_player():
    curve = stemtone.written_level(_brass_work(), ["tpt1", "tbn1"], 0.0, 20.0)
    assert _level_at(curve, 2.0) == 0.0  # the empty bar
    assert _level_at(curve, 5.0) == DYNAMIC_LEVEL["fff"]  # the trombone is louder
    # The trombone stops after 2 s. Its level stays for the hold time, then the trumpet rules.
    assert _level_at(curve, 6.0 + stemtone.HOLD_SECONDS / 2) == DYNAMIC_LEVEL["fff"]
    assert _level_at(curve, 7.5) == DYNAMIC_LEVEL["f"]
    # The crescendo of the last bar: the loudness goes up during the note.
    assert _level_at(curve, 12.5) < _level_at(curve, 15.5)
    assert _level_at(curve, 12.1) >= DYNAMIC_LEVEL["mp"]


def test_an_excerpt_has_the_time_of_its_first_bar_as_zero():
    work = _brass_work()
    begin = work.structure.seconds(work.structure.bar(2).start)
    curve = stemtone.written_level(work, ["tpt1"], begin, 4.0)
    assert _level_at(curve, 1.0) == DYNAMIC_LEVEL["f"]


def test_the_change_is_large_at_f_and_small_at_fff_and_zero_below_mf():
    table = stemtone.BRASS
    for mark, (gain, shelf) in {"mp": (0.0, 0.0), "f": table[1][1:], "fff": table[3][1:]}.items():
        level = np.full(500, DYNAMIC_LEVEL[mark])
        gain_db, shelf_db = stemtone.curves(level, table)
        assert np.allclose(gain_db, gain) and np.allclose(shelf_db, shelf)
    # A written f is softer and less bright than a written fff.
    assert table[1][1] <= table[3][1] and table[1][2] < table[3][2]


def test_the_change_moves_smoothly_between_two_marks():
    level = np.concatenate([np.full(300, DYNAMIC_LEVEL["mp"]), np.full(300, DYNAMIC_LEVEL["f"])])
    _gain_db, shelf_db = stemtone.curves(level, stemtone.BRASS)
    steps = np.abs(np.diff(shelf_db))
    assert len(shelf_db) == len(level)
    assert steps.max() < 0.5  # no jump
    assert shelf_db[0] == 0.0 and np.isclose(shelf_db[-1], stemtone.BRASS[1][2])


def _band_db(samples: np.ndarray, low: float, high: float) -> float:
    spectrum = np.abs(np.fft.rfft(samples)) ** 2
    frequencies = np.fft.rfftfreq(len(samples), 1.0 / dsp.RATE)
    return 10.0 * np.log10(spectrum[(frequencies >= low) & (frequencies < high)].sum())


def test_the_stem_gets_the_gain_and_the_gain_above_2_khz_of_its_written_mark():
    generator = np.random.default_rng(1)
    noise = generator.standard_normal((4 * dsp.RATE, 2)).astype(np.float32) * 0.1
    seconds = len(noise) / dsp.RATE
    count = int(seconds * stemtone.CONTROL_RATE) + 1
    for mark, row in (("f", stemtone.BRASS[1]), ("fff", stemtone.BRASS[3])):
        audio = noise.copy()
        stemtone.shape(audio, np.full(count, DYNAMIC_LEVEL[mark]), stemtone.BRASS)
        low = _band_db(audio[:, 0], 100, 400) - _band_db(noise[:, 0], 100, 400)
        high = _band_db(audio[:, 0], 8000, 16000) - _band_db(noise[:, 0], 8000, 16000)
        assert abs(low - row[1]) < 0.4
        assert abs(high - (row[1] + row[2])) < 0.6
    # A soft passage does not change.
    audio = noise.copy()
    stemtone.shape(audio, np.full(count, DYNAMIC_LEVEL["p"]), stemtone.BRASS)
    assert np.allclose(audio, noise, atol=1e-6)


def test_the_equalization_of_the_mix_changes_the_bands_that_its_table_gives():
    from stmatthew.audio import musescore

    generator = np.random.default_rng(2)
    noise = generator.standard_normal((4 * dsp.RATE, 2)).astype(np.float32) * 0.1
    audio = musescore.equalize(
        noise.copy(), (("bell", 1800.0, 2.0, 0.7), ("high shelf", 7000.0, -3.0))
    )
    low = _band_db(audio[:, 1], 100, 300) - _band_db(noise[:, 1], 100, 300)
    bell = _band_db(audio[:, 1], 1600, 2000) - _band_db(noise[:, 1], 1600, 2000)
    high = _band_db(audio[:, 1], 14000, 18000) - _band_db(noise[:, 1], 14000, 18000)
    assert abs(low) < 0.3
    assert 1.4 < bell < 2.1
    assert -3.2 < high < -2.5
    # The table of the project has only small changes: a mix must not get a new character.
    assert all(abs(row[2]) <= 4.0 for row in musescore.MASTER_EQ)


def test_a_stem_above_the_threshold_becomes_softer_slowly():
    generator = np.random.default_rng(3)
    seconds = 12
    noise = generator.standard_normal((seconds * dsp.RATE, 2)).astype(np.float32)
    # The first half is 10 dB above the threshold, the second half is 6 dB below it.
    threshold, ratio = -20.0, 2.5
    loud, soft = 10.0 ** (-10.0 / 20.0), 10.0 ** (-26.0 / 20.0)
    half = len(noise) // 2
    noise[:half] *= loud / np.sqrt(np.mean(np.square(noise[:half].mean(axis=1))))
    noise[half:] *= soft / np.sqrt(np.mean(np.square(noise[half:].mean(axis=1))))
    audio, largest = stemtone.ride(noise.copy(), threshold, ratio)
    change = 20.0 * np.log10(np.abs(audio[dsp.RATE]).max() / np.abs(noise[dsp.RATE]).max())
    assert abs(change - (-10.0 * (1.0 - 1.0 / ratio))) < 0.3  # 6 dB softer
    assert abs(largest - change) < 0.3
    assert np.allclose(audio[-dsp.RATE :], noise[-dsp.RATE :], atol=1e-6)  # no change
    # The gain moves slowly: no step between two blocks of 100 ms is large.
    gain = stemtone.ride_gain(noise, threshold, ratio)
    assert np.abs(np.diff(gain)).max() < 1.5
