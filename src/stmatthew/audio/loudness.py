"""The loudness of a recording, and the gain riding of the master.

The loudness values are those of the standards ITU-R BS.1770 (integrated
loudness), EBU R 128 (short-term loudness), and EBU Tech 3342 (loudness
range). The code reads the sound in parts, thus a long recording does not
need much memory.

Gain riding: an orchestra has a larger range of loudness than a listener
can use at home. The engineer of a classical recording moves the level
slowly: up in the soft passages, down in the loud passages. The function
`ride()` does this. It changes the level slowly (in some seconds), thus the
loudness of each note in relation to its adjacent notes does not change.

If `ride()` gets the passages of the music, each passage has one level
change. Thus the level does not follow the decay of a note: a bell or a
gong in a soft passage dies away as the instrument does it.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy import ndimage, signal

from . import dsp

BLOCK = dsp.RATE // 10  # the sound is measured in blocks of 100 ms
CHUNK = 30 * dsp.RATE  # the sound is read in parts of 30 s


def _k_weighting() -> np.ndarray:
    """Return the K-weighting filter: a high shelf and a high-pass filter."""
    frequency, gain_db, q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    k = np.tan(np.pi * frequency / dsp.RATE)
    vh = 10.0 ** (gain_db / 20.0)
    vb = vh**0.4996667741545416
    a0 = 1.0 + k / q + k * k
    shelf = [
        (vh + vb * k / q + k * k) / a0,
        2.0 * (k * k - vh) / a0,
        (vh - vb * k / q + k * k) / a0,
        1.0,
        2.0 * (k * k - 1.0) / a0,
        (1.0 - k / q + k * k) / a0,
    ]
    frequency, q = 38.13547087602444, 0.5003270373238773
    k = np.tan(np.pi * frequency / dsp.RATE)
    a0 = 1.0 + k / q + k * k
    highpass = [1.0, -2.0, 1.0, 1.0, 2.0 * (k * k - 1.0) / a0, (1.0 - k / q + k * k) / a0]
    return np.array([shelf, highpass])


def block_power(audio: np.ndarray) -> np.ndarray:
    """Return the K-weighted power of each block of 100 ms (the sum of the channels)."""
    sos = _k_weighting()
    count = len(audio) // BLOCK
    power = np.zeros(count)
    for channel in range(audio.shape[1]):
        state = np.zeros((sos.shape[0], 2))
        for start in range(0, count * BLOCK, CHUNK):
            part = audio[start : min(start + CHUNK, count * BLOCK), channel].astype(np.float64)
            weighted, state = signal.sosfilt(sos, part, zi=state)
            squares = np.square(weighted).reshape(-1, BLOCK).sum(axis=1) / BLOCK
            power[start // BLOCK : start // BLOCK + len(squares)] += squares
    return power


def _window_loudness(power: np.ndarray, blocks: int, step: int) -> np.ndarray:
    """Return the loudness of windows of `blocks` blocks, one window each `step` blocks."""
    if len(power) < blocks:
        return np.zeros(0)
    sums = np.concatenate(([0.0], np.cumsum(power)))
    starts = np.arange(0, len(power) - blocks + 1, step)
    mean = (sums[starts + blocks] - sums[starts]) / blocks
    return -0.691 + 10.0 * np.log10(np.maximum(mean, 1e-12))


def integrated(power: np.ndarray) -> float:
    """Return the integrated loudness in LUFS (windows of 400 ms, with the two gates)."""
    windows = _window_loudness(power, 4, 1)
    energy = 10.0 ** ((windows + 0.691) / 10.0)
    kept = energy[windows > -70.0]
    if len(kept) == 0:
        return float("-inf")
    relative_gate = -0.691 + 10.0 * np.log10(kept.mean()) - 10.0
    kept = energy[(windows > -70.0) & (windows > relative_gate)]
    if len(kept) == 0:
        return float("-inf")
    return float(-0.691 + 10.0 * np.log10(kept.mean()))


def short_term(power: np.ndarray, step_blocks: int = 10) -> np.ndarray:
    """Return the short-term loudness in LUFS (windows of 3 s; default: one each second)."""
    return _window_loudness(power, 30, step_blocks)


def loudness_range(values: np.ndarray) -> tuple[float, np.ndarray]:
    """Return the loudness range in LU, and the short-term values that are not gated."""
    gated = values[values > -70.0]
    if len(gated) == 0:
        return 0.0, gated
    mean = 10.0 * np.log10(np.mean(10.0 ** (gated / 10.0)))
    gated = gated[gated > mean - 20.0]
    if len(gated) == 0:
        return 0.0, gated
    return float(np.percentile(gated, 95) - np.percentile(gated, 10)), gated


# ----------------------------------------------------------------------------
# Gain riding
# ----------------------------------------------------------------------------

HOLD_SECONDS = 3.0  # the level follows the loudest sound in this time before and after
SMOOTH_SECONDS = 8.0  # the level changes in this time
KNEE_BELOW_LOUDEST = 8.0  # passages that are less than this below the loud level do not change
LARGEST_GAIN_DB = 18.0  # a soft passage does not get more gain than this
LARGEST_RATIO = 3.0


def program_level(power: np.ndarray) -> np.ndarray:
    """Return the slow loudness of the programme for each block of 100 ms, in LUFS."""
    blocks = 30
    sums = np.concatenate(([0.0], np.cumsum(power)))
    # A window of 3 s around each block.
    low = np.clip(np.arange(len(power)) - blocks // 2, 0, len(power))
    high = np.clip(low + blocks, 0, len(power))
    mean = (sums[high] - sums[low]) / np.maximum(high - low, 1)
    level = -0.691 + 10.0 * np.log10(np.maximum(mean, 1e-12))
    return _slow(level)


def _slow(level: np.ndarray) -> np.ndarray:
    """Hold the loudest level for some seconds before and after, then make the changes slow."""
    level = ndimage.maximum_filter1d(level, int(2 * HOLD_SECONDS * 10) + 1, mode="nearest")
    window = signal.windows.hann(int(SMOOTH_SECONDS * 10) | 1)
    padded = np.pad(level, len(window) // 2, mode="edge")
    return np.convolve(padded, window / window.sum(), mode="valid")


def passage_level(power: np.ndarray, starts: Sequence[float]) -> np.ndarray:
    """Return the slow loudness of the programme for each block, from the passages of the music.

    `starts` are the start times of the passages in seconds. All blocks of
    a passage get the loudness of that passage. Thus the level is constant
    in a passage, and it changes slowly between two passages.
    """
    count = len(power)
    edges = sorted({min(max(round(start * 10), 0), count) for start in starts} | {0, count})
    level = np.full(count, np.nan)
    for first, last in zip(edges, edges[1:], strict=False):
        value = integrated(power[first:last])
        if np.isfinite(value):
            level[first:last] = value
    # A passage with no sound gets the level of the passage before it (or after it).
    known = np.flatnonzero(np.isfinite(level))
    if len(known) == 0:
        return np.full(count, -70.0)
    level = level[
        known[np.clip(np.searchsorted(known, np.arange(count), side="right") - 1, 0, None)]
    ]
    return _slow(level)


def riding_gain(
    level: np.ndarray, ratio: float, largest_gain_db: float = LARGEST_GAIN_DB
) -> np.ndarray:
    """Return the gain in dB for each block: soft passages go up."""
    knee = float(np.percentile(level, 95)) - KNEE_BELOW_LOUDEST
    below = np.maximum(knee - level, 0.0)
    return np.minimum(below * (1.0 - 1.0 / ratio), largest_gain_db)


def ride(
    audio: np.ndarray,
    target_range: float,
    largest_gain_db: float = LARGEST_GAIN_DB,
    largest_ratio: float = LARGEST_RATIO,
    passages: Sequence[float] | None = None,
) -> tuple[np.ndarray, float, float]:
    """Move the level slowly until the loudness range is not more than `target_range`.

    The function changes `audio` in place. It returns the audio, the ratio
    that it used (1 = no change), and the largest gain in dB.

    `passages` are the start times of the passages of the music in seconds.
    If the function gets them, each passage has one level change. If not,
    the level follows the loudness of the sound.
    """
    power = block_power(audio)
    level = program_level(power) if passages is None else passage_level(power, passages)
    step = 10

    def range_with(ratio: float) -> float:
        gain = riding_gain(level, ratio, largest_gain_db)
        changed = power * 10.0 ** (gain / 10.0)
        return loudness_range(short_term(changed, step))[0]

    if range_with(1.0) <= target_range:
        return audio, 1.0, 0.0
    low, high = 1.0, largest_ratio
    for _ in range(18):
        middle = 0.5 * (low + high)
        if range_with(middle) > target_range:
            low = middle
        else:
            high = middle
    gain = riding_gain(level, high, largest_gain_db)
    # The gain of each sample: a straight line between the centres of the blocks.
    centres = (np.arange(len(gain)) + 0.5) * BLOCK
    for start in range(0, len(audio), CHUNK):
        stop = min(start + CHUNK, len(audio))
        curve = np.interp(np.arange(start, stop), centres, gain)
        audio[start:stop] *= (10.0 ** (curve / 20.0)).astype(np.float32)[:, None]
    return audio, high, float(gain.max())
