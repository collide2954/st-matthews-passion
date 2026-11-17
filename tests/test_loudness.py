"""Tests for the loudness measurement and the gain riding."""

import numpy as np

from stmatthew.audio import dsp, loudness


def _tone(seconds: float, amplitude: float) -> np.ndarray:
    time = np.arange(int(seconds * dsp.RATE)) / dsp.RATE
    wave = (amplitude * np.sin(2 * np.pi * 997.0 * time)).astype(np.float32)
    return np.stack([wave, wave], axis=1)


def test_integrated_loudness_of_a_sine_tone():
    # A sine tone at -20 dBFS in two channels has a loudness of about -20 LUFS.
    power = loudness.block_power(_tone(8.0, 0.1))
    assert abs(loudness.integrated(power) - (-20.0)) < 0.3


def test_loudness_range_of_two_levels():
    audio = np.concatenate([_tone(30.0, 0.01), _tone(30.0, 0.1)])
    spread, _ = loudness.loudness_range(loudness.short_term(loudness.block_power(audio)))
    assert 17.0 < spread < 20.5


def test_gain_riding_makes_the_range_smaller_and_keeps_the_loud_part():
    audio = np.concatenate([_tone(40.0, 0.012), _tone(40.0, 0.1), _tone(40.0, 0.012)])
    before, _ = loudness.loudness_range(loudness.short_term(loudness.block_power(audio)))
    ridden, ratio, gain = loudness.ride(audio.copy(), 12.0)
    after, _ = loudness.loudness_range(loudness.short_term(loudness.block_power(ridden)))
    assert before > 17.0
    assert after <= 12.5
    assert ratio > 1.0 and 0.0 < gain <= loudness.LARGEST_GAIN_DB
    # The middle of the loud part does not change.
    start = 55 * dsp.RATE
    assert np.allclose(ridden[start : start + 1000], audio[start : start + 1000], atol=1e-4)


def _strokes(seconds: float, amplitude: float, period: float, decay_db: float) -> np.ndarray:
    """Return strokes of a tone: each stroke becomes softer by `decay_db` in one period."""
    audio = _tone(seconds, amplitude)
    time = np.arange(len(audio)) / dsp.RATE
    envelope = 10.0 ** (-decay_db * ((time % period) / period) / 20.0)
    return audio * envelope[:, None].astype(np.float32)


def _decay_db(audio: np.ndarray, start: float, length: float) -> float:
    """Return the fall of the level in dB from `start` to `start + length` (in seconds)."""

    def level(moment: float) -> float:
        first = int(moment * dsp.RATE)
        return dsp.to_db(float(np.sqrt(np.mean(np.square(audio[first : first + 4800])))))

    return level(start) - level(start + length)


def test_gain_riding_by_passage_keeps_the_decay_of_a_note():
    # A loud passage, then a soft passage: two strokes that die away slowly, as a tam-tam does.
    audio = np.concatenate([_tone(40.0, 0.2), _strokes(60.0, 0.05, 30.0, 45.0)])
    natural = _decay_db(audio, 72.0, 20.0)
    followed, _, _ = loudness.ride(audio.copy(), 12.0)
    by_passage, ratio, gain = loudness.ride(audio.copy(), 12.0, passages=[0.0, 40.0])
    assert ratio > 1.0 and gain > 3.0
    # With the passages, the stroke dies away as before. Without them, the level follows it.
    assert abs(_decay_db(by_passage, 72.0, 20.0) - natural) < 0.5
    assert _decay_db(followed, 72.0, 20.0) < natural - 3.0
    # The soft passage is louder than before, in relation to the loud passage.
    assert _decay_db(by_passage, 20.0, 52.0) < _decay_db(audio, 20.0, 52.0) - 3.0
