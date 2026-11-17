"""Signal tools for the audio engine: loading, pitch, loops, fades, and filters."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile
import soxr
from scipy import signal

RATE = 48000  # sample rate of the project, in hertz


def load_mono(path: Path, rate: int = RATE) -> np.ndarray:
    """Read an audio file as one channel at the project sample rate."""
    data, file_rate = soundfile.read(str(path), dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    if file_rate != rate:
        mono = soxr.resample(mono, file_rate, rate, quality="HQ")
    return np.ascontiguousarray(mono, dtype=np.float32)


def db(value: float) -> float:
    """Change a level in decibels into a gain factor."""
    return float(10.0 ** (value / 20.0))


def to_db(gain: float) -> float:
    """Change a gain factor into a level in decibels."""
    return float(20.0 * np.log10(max(gain, 1e-12)))


def rms(samples: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(samples, dtype=np.float64)))) if len(samples) else 0.0


def onset_index(samples: np.ndarray, threshold_db: float = -42.0) -> int:
    """Return the index where the sound starts: the first sample above a threshold."""
    peak = float(np.max(np.abs(samples))) if len(samples) else 0.0
    if peak <= 0:
        return 0
    above = np.nonzero(np.abs(samples) > peak * db(threshold_db))[0]
    return int(above[0]) if len(above) else 0


def envelope(samples: np.ndarray, rate: int = RATE, window_seconds: float = 0.02) -> np.ndarray:
    """Return the loudness envelope: the root mean square in a moving window."""
    window = max(1, int(window_seconds * rate))
    squared = np.square(samples.astype(np.float64))
    sums = np.concatenate(([0.0], np.cumsum(squared)))
    indexes = np.arange(len(samples))
    low = np.maximum(indexes - window // 2, 0)
    high = np.minimum(indexes + window - window // 2, len(samples))
    return np.sqrt(np.maximum(sums[high] - sums[low], 0.0) / (high - low))


def detect_pitch(
    samples: np.ndarray, rate: int = RATE, low_hz: float = 25.0, high_hz: float = 4500.0
) -> float | None:
    """Return the fundamental frequency of a steady tone in hertz (YIN method).

    Return None if the sound has no clear pitch.
    """
    size = min(len(samples), int(rate * 0.25))
    if size < int(3 * rate / low_hz):
        return None
    start = (len(samples) - size) // 2
    frame = samples[start : start + size].astype(np.float64)
    frame = frame - frame.mean()
    max_lag = min(int(rate / low_hz), size // 2)
    min_lag = max(2, int(rate / high_hz))
    window = size - max_lag
    # Difference function d(lag) for a window of fixed length.
    spectrum = np.fft.rfft(frame, 2 * size)
    correlation = np.fft.irfft(spectrum * np.conj(spectrum))[: max_lag + 1]
    squares = np.concatenate(([0.0], np.cumsum(frame * frame)))
    energy_start = squares[window] - squares[0]
    lags = np.arange(max_lag + 1)
    energy_lag = squares[lags + window] - squares[lags]
    # The correlation above uses the full frame. For a steady tone the error is small.
    difference = energy_start + energy_lag - 2.0 * correlation * (window / size)
    difference[0] = 0.0
    cumulative = np.cumsum(difference[1:])
    normalized = np.ones(max_lag + 1)
    normalized[1:] = difference[1:] * np.arange(1, max_lag + 1) / np.maximum(cumulative, 1e-12)
    candidates = np.nonzero(normalized[min_lag:max_lag] < 0.15)[0]
    if len(candidates):
        lag = int(candidates[0]) + min_lag
        while lag + 1 < max_lag and normalized[lag + 1] < normalized[lag]:
            lag += 1
    else:
        lag = int(np.argmin(normalized[min_lag:max_lag])) + min_lag
        if normalized[lag] > 0.45:
            return None
    # Parabolic interpolation for a lag between two samples.
    if 1 <= lag < max_lag:
        left, centre, right = normalized[lag - 1], normalized[lag], normalized[lag + 1]
        denominator = left - 2 * centre + right
        if denominator != 0:
            lag = lag + 0.5 * (left - right) / denominator
    return float(rate / lag)


def hz_to_midi(frequency: float) -> float:
    return float(69.0 + 12.0 * np.log2(frequency / 440.0))


def shift_pitch(samples: np.ndarray, semitones: float, rate: int = RATE) -> np.ndarray:
    """Play a sample faster or slower to change its pitch (as a sampler does)."""
    if abs(semitones) < 1e-4:
        return samples
    ratio = 2.0 ** (semitones / 12.0)
    return soxr.resample(samples, rate * ratio, rate, quality="HQ").astype(np.float32)


def bend(samples: np.ndarray, semitone_curve: np.ndarray) -> np.ndarray:
    """Play a sample with a pitch that changes in time.

    `semitone_curve` gives the pitch offset for each OUTPUT sample. The function
    reads the input at a speed that follows the curve (linear interpolation).
    """
    speed = 2.0 ** (semitone_curve / 12.0)
    positions = np.concatenate(([0.0], np.cumsum(speed[:-1])))
    positions = positions[positions < len(samples) - 1]
    return np.interp(positions, np.arange(len(samples)), samples).astype(np.float32)


def find_loop(samples: np.ndarray, rate: int = RATE) -> tuple[int, int, int] | None:
    """Find a loop in the steady part of a held tone.

    Return (loop start, loop end, crossfade length) in samples, or None if the
    sample is too short for a loop.
    """
    level = envelope(samples, rate, 0.05)
    peak = float(level.max()) if len(level) else 0.0
    if peak <= 0:
        return None
    steady = np.nonzero(level > 0.5 * peak)[0]
    if len(steady) == 0:
        return None
    first, last = int(steady[0]), int(steady[-1])
    region_start = first + int(0.35 * (last - first))
    region_end = first + int(0.9 * (last - first))
    crossfade = int(0.25 * rate)
    length = min(int(2.0 * rate), region_end - region_start - crossfade)
    if length < int(0.4 * rate):
        return None
    loop_end = region_end
    target = loop_end - length
    tail = samples[loop_end - crossfade : loop_end].astype(np.float64)
    # Try loop starts near the target. Keep the start whose sound before it is
    # most similar to the sound before the loop end: the crossfade joins these two.
    search = int(0.03 * rate)
    starts = np.arange(max(target - search, crossfade), target + search, 8)
    windows = np.lib.stride_tricks.sliding_window_view(samples, crossfade)
    heads = windows[starts - crossfade].astype(np.float64)
    norms = np.sqrt(np.einsum("ij,ij->i", heads, heads)) * np.sqrt(float(np.sum(tail * tail)))
    scores = np.einsum("ij,j->i", heads, tail) / np.maximum(norms, 1e-12)
    best_start = int(starts[int(np.argmax(scores))])
    return best_start, loop_end, crossfade


def sustain(samples: np.ndarray, length: int, loop: tuple[int, int, int] | None) -> np.ndarray:
    """Return the first `length` samples of a held tone. Use the loop if the tone is too short."""
    if length <= len(samples) or loop is None:
        return samples[:length]
    start, end, crossfade = loop
    fade_in = np.linspace(0.0, 1.0, crossfade, dtype=np.float32)
    fade_out = 1.0 - fade_in
    pieces = [samples[: end - crossfade]]
    total = end - crossfade
    while total < length:
        joint = (
            samples[end - crossfade : end] * fade_out + samples[start - crossfade : start] * fade_in
        )
        body = samples[start : end - crossfade]
        pieces += [joint, body]
        total += len(joint) + len(body)
    return np.concatenate(pieces)[:length]


def fade(samples: np.ndarray, fade_in: int = 0, fade_out: int = 0) -> np.ndarray:
    """Return a copy with a raised-cosine fade at the start and at the end."""
    result = samples.copy()
    fade_in = min(fade_in, len(result))
    fade_out = min(fade_out, len(result))
    if fade_in > 1:
        result[:fade_in] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_in, dtype=np.float32))
    if fade_out > 1:
        result[-fade_out:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, fade_out, dtype=np.float32))
    return result


# ----------------------------------------------------------------------------
# Filters
# ----------------------------------------------------------------------------


def highpass(frequency: float, order: int = 2, rate: int = RATE) -> np.ndarray:
    return signal.butter(order, frequency, "highpass", fs=rate, output="sos")


def lowpass(frequency: float, order: int = 2, rate: int = RATE) -> np.ndarray:
    return signal.butter(order, frequency, "lowpass", fs=rate, output="sos")


def _biquad(b: list[float], a: list[float]) -> np.ndarray:
    return np.array([[b[0] / a[0], b[1] / a[0], b[2] / a[0], 1.0, a[1] / a[0], a[2] / a[0]]])


def peaking(frequency: float, gain_db: float, q: float = 1.0, rate: int = RATE) -> np.ndarray:
    """A bell filter (Audio EQ Cookbook)."""
    amplitude = 10.0 ** (gain_db / 40.0)
    omega = 2.0 * np.pi * frequency / rate
    alpha = np.sin(omega) / (2.0 * q)
    cosine = np.cos(omega)
    return _biquad(
        [1 + alpha * amplitude, -2 * cosine, 1 - alpha * amplitude],
        [1 + alpha / amplitude, -2 * cosine, 1 - alpha / amplitude],
    )


def shelf(frequency: float, gain_db: float, *, high: bool, rate: int = RATE) -> np.ndarray:
    """A low shelf or a high shelf filter (Audio EQ Cookbook, slope 1)."""
    amplitude = 10.0 ** (gain_db / 40.0)
    omega = 2.0 * np.pi * frequency / rate
    cosine = np.cos(omega)
    alpha = np.sin(omega) / 2.0 * np.sqrt(2.0)
    root = 2.0 * np.sqrt(amplitude) * alpha
    sign = 1.0 if high else -1.0
    b = [
        amplitude * ((amplitude + 1) + sign * (amplitude - 1) * cosine + root),
        -sign * 2 * amplitude * ((amplitude - 1) + sign * (amplitude + 1) * cosine),
        amplitude * ((amplitude + 1) + sign * (amplitude - 1) * cosine - root),
    ]
    a = [
        (amplitude + 1) - sign * (amplitude - 1) * cosine + root,
        sign * 2 * ((amplitude - 1) - sign * (amplitude + 1) * cosine),
        (amplitude + 1) - sign * (amplitude - 1) * cosine - root,
    ]
    return _biquad(b, a)


def apply(samples: np.ndarray, *filters: np.ndarray) -> np.ndarray:
    """Apply filters (second-order sections) one after the other."""
    if not filters:
        return samples
    sections = np.vstack(filters)
    return signal.sosfilt(sections, samples, axis=0).astype(np.float32)


def third_octave_levels(samples: np.ndarray, rate: int = RATE) -> tuple[np.ndarray, np.ndarray]:
    """Return the centre frequencies and the levels (dB) of the third-octave bands.

    The levels come from the long-term average power spectrum.
    """
    frequencies, power = signal.welch(samples, fs=rate, nperseg=16384, axis=0)
    if power.ndim > 1:
        power = power.mean(axis=1)
    centres = 1000.0 * 2.0 ** (np.arange(-17, 13) / 3.0)  # 20 Hz to 16 kHz
    levels = []
    for centre in centres:
        low, high = centre / 2 ** (1 / 6), centre * 2 ** (1 / 6)
        band = power[(frequencies >= low) & (frequencies < high)]
        levels.append(10.0 * np.log10(band.sum() + 1e-20))
    return centres, np.array(levels)
