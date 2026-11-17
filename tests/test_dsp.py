"""Tests for the signal tools."""

import numpy as np
import pytest

from stmatthew.audio import dsp


def tone(frequency: float, seconds: float = 1.0, harmonics: int = 6) -> np.ndarray:
    time = np.arange(int(seconds * dsp.RATE)) / dsp.RATE
    wave = sum(np.sin(2 * np.pi * frequency * k * time) / k for k in range(1, harmonics + 1))
    return (0.2 * wave).astype(np.float32)


@pytest.mark.parametrize("frequency", [41.2, 110.0, 261.63, 440.0, 1318.5, 3520.0])
def test_detect_pitch(frequency):
    found = dsp.detect_pitch(tone(frequency))
    assert found == pytest.approx(frequency, rel=0.003)


def test_detect_pitch_of_noise_is_none():
    noise = np.random.default_rng(1).normal(0, 0.1, dsp.RATE).astype(np.float32)
    assert dsp.detect_pitch(noise) is None


def test_shift_pitch():
    shifted = dsp.shift_pitch(tone(220.0), 3.0)
    assert dsp.detect_pitch(shifted) == pytest.approx(220.0 * 2 ** (3 / 12), rel=0.003)
    assert len(shifted) == pytest.approx(dsp.RATE / 2 ** (3 / 12), abs=4)
    quarter_tone = dsp.shift_pitch(tone(220.0), 0.5)
    assert dsp.hz_to_midi(dsp.detect_pitch(quarter_tone)) == pytest.approx(57.5, abs=0.02)


def test_bend_follows_the_curve():
    curve = np.full(dsp.RATE // 2, 2.0)
    bent = dsp.bend(tone(220.0), curve)
    assert dsp.detect_pitch(bent) == pytest.approx(220.0 * 2 ** (2 / 12), rel=0.005)


def test_loop_makes_a_long_tone_with_no_click():
    source = dsp.fade(tone(196.0, 3.0), fade_in=2000, fade_out=20000)
    loop = dsp.find_loop(source)
    assert loop is not None
    long_tone = dsp.sustain(source, 10 * dsp.RATE, loop)
    assert len(long_tone) == 10 * dsp.RATE
    assert dsp.detect_pitch(long_tone[4 * dsp.RATE : 5 * dsp.RATE]) == pytest.approx(
        196.0, rel=0.003
    )
    # No step between samples is larger than the largest step of the source.
    assert np.max(np.abs(np.diff(long_tone))) <= 1.05 * np.max(np.abs(np.diff(source)))
    level = dsp.envelope(long_tone[dsp.RATE : 9 * dsp.RATE])
    assert level.min() > 0.8 * level.max()


def test_filters():
    low, high = tone(60.0, harmonics=1), tone(6000.0, harmonics=1)
    cut = dsp.apply(low + high, dsp.highpass(1000.0, 4))
    assert dsp.rms(cut) == pytest.approx(dsp.rms(high), rel=0.05)
    boosted = dsp.apply(high, dsp.peaking(6000.0, 6.0, 1.0))
    assert dsp.to_db(dsp.rms(boosted) / dsp.rms(high)) == pytest.approx(6.0, abs=0.2)
    shelved = dsp.apply(high, dsp.shelf(1000.0, -4.0, high=True))
    assert dsp.to_db(dsp.rms(shelved) / dsp.rms(high)) == pytest.approx(-4.0, abs=0.3)
    same = dsp.apply(low, dsp.shelf(1000.0, -4.0, high=True))
    assert dsp.to_db(dsp.rms(same) / dsp.rms(low)) == pytest.approx(0.0, abs=0.3)


def test_third_octave_levels():
    centres, levels = dsp.third_octave_levels(tone(1000.0, 2.0, harmonics=1))
    assert centres[int(np.argmax(levels))] == pytest.approx(1000.0, rel=0.01)
