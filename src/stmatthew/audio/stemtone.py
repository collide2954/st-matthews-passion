"""Give the loud dynamic marks of a group of players their difference again.

The marks f, ff, and fff of the brass of Muse Sounds are almost the same
sound. The table `muse_levels.csv` and a measurement of the tone show this:

- The level of the three marks is the same in a range of 3 dB.
- The tone of the three marks is the same: very bright, with a hard edge.
  For the trombone, the share of the sound above 2 kHz is 26 dB larger at
  the mark f than at the mark mf.
- The mark mf is 4 to 11 dB softer, and its tone is mellow.

Thus a written f of the brass sounds as loud and as hard as a written fff.
In a real orchestra, the brass at f has a full and round tone, and only the
brass at fff has the hard edge. The owner of the project heard the fault as
a "splat" of the loud brass that "cuts against the texture".

The mix repairs this in two steps.

1. The tone. The mix knows the written dynamic marks of the group at each
   moment. It makes the group less bright in relation to the written mark:
   a large change at f, a smaller change at fff. Between the marks, the
   change moves smoothly (for example in a crescendo). The loudest written
   mark of the group at a moment controls the change.
2. The level. In most loud passages, the brass is not louder than the
   strings. But where all brass players hold loud chords (the main climax,
   the last chords), the brass was 5 to 6 dB louder than the strings. There
   the mix moves the level of the brass down slowly, as an engineer moves a
   fader: only the part of the level above a threshold becomes smaller.

The two steps apply to one stem (all players of the group together).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np

from ..notation.work import Work
from ..perform.events import DYNAMIC_LEVEL, perform
from . import dsp

# One row: the written loudness (the scale of `DYNAMIC_LEVEL`), the gain in dB,
# and the gain above 2 kHz in dB (this second gain adds to the first).
Row = tuple[float, float, float]

# The brass. Below mf there is no change: Muse Sounds play these marks with a
# mellow tone.
BRASS: tuple[Row, ...] = (
    (DYNAMIC_LEVEL["mf"], 0.0, 0.0),
    (DYNAMIC_LEVEL["f"], 0.0, -8.0),
    (DYNAMIC_LEVEL["ff"], 0.0, -6.0),
    (DYNAMIC_LEVEL["fff"], 0.0, -4.0),
)
TABLES: dict[str, tuple[Row, ...]] = {"brass": BRASS}

# The slow change of the level of a stem: the threshold in dB (the level of the stem
# in the mix, as a mean of 2 s), and the ratio. Above the threshold, a level that is
# `ratio` dB higher gives a sound that is 1 dB louder. A measurement of the brass stem
# gave these levels (the loudest 3 s): the main climax and the last chords -8.5 dB,
# the broad motto of part 2 -12 dB, the heavy section -13 dB, all other passages
# -14 dB or lower. Thus only the two loudest places change much (3 dB).
RIDES: dict[str, tuple[float, float]] = {"brass": (-13.5, 2.5)}
RIDE_WINDOW_SECONDS = 2.0  # the level is the mean of this time
RIDE_SMOOTH_SECONDS = 1.0  # the gain changes in this time
RIDE_BLOCK = dsp.RATE // 10  # the level is measured in blocks of 100 ms

CONTROL_RATE = 100  # values of a control curve in one second
SHELF_HZ = 2000.0
SHELF_DB = -12.0  # the filtered signal; the output is a mix of it and of the input
LEAD_SECONDS = 0.05  # the change starts this time before a note
HOLD_SECONDS = 1.0  # the change stays for this time after a note (the sound in the hall)
SMOOTH_SECONDS = 0.4  # the change moves in this time
CHUNK = 30 * dsp.RATE


def written_level(work: Work, players: Iterable[str], begin: float, seconds: float) -> np.ndarray:
    """Return the loudest written loudness of the players at each moment.

    `begin` is the time of the first value, in seconds from the start of the
    work. `seconds` is the length of the result. The result has
    `CONTROL_RATE` values for each second. A moment with no notes has 0.
    """
    count = int(np.ceil(seconds * CONTROL_RATE)) + 1
    curve = np.zeros(count)
    structure = work.structure
    for player in players:
        for note in perform(work, player):
            if note.grace:
                continue
            start = structure.seconds(note.start) - begin
            end = structure.seconds(note.start + note.duration) - begin
            first = max(int((start - LEAD_SECONDS) * CONTROL_RATE), 0)
            last = min(int(np.ceil((end + HOLD_SECONDS) * CONTROL_RATE)), count - 1)
            if last < first:
                continue
            times = np.arange(first, last + 1) / CONTROL_RATE
            share = np.clip((times - start) / max(end - start, 1e-6), 0.0, 1.0)
            level = note.level + (note.level_end - note.level) * share
            np.maximum(curve[first : last + 1], level, out=curve[first : last + 1])
    return curve


def curves(level: np.ndarray, table: Sequence[Row]) -> tuple[np.ndarray, np.ndarray]:
    """Return the gain in dB and the gain above 2 kHz in dB for each value of the loudness."""
    marks = [row[0] for row in table]
    size = int(SMOOTH_SECONDS * CONTROL_RATE)
    gain, shelf = (
        _smooth(np.interp(level, marks, [row[column] for row in table]), size) for column in (1, 2)
    )
    return gain, shelf


def _smooth(values: np.ndarray, size: int) -> np.ndarray:
    """Return the values as a moving mean of `size` values (the ends keep their values)."""
    size = max(size, 1)
    window = np.hanning(size + 2)[1:-1]
    window /= window.sum()
    padded = np.pad(values, (size // 2, size - 1 - size // 2), mode="edge")
    return np.convolve(padded, window, mode="valid")


def ride_gain(audio: np.ndarray, threshold_db: float, ratio: float) -> np.ndarray:
    """Return the gain in dB for each block of 100 ms (0 below the threshold)."""
    count = len(audio) // RIDE_BLOCK
    if count == 0:
        return np.zeros(1)
    mono = audio[: count * RIDE_BLOCK].mean(axis=1, dtype=np.float64)
    power = np.square(mono).reshape(count, RIDE_BLOCK).mean(axis=1)
    blocks_in_second = dsp.RATE // RIDE_BLOCK
    mean = _smooth(power, int(RIDE_WINDOW_SECONDS * blocks_in_second))
    level = 10.0 * np.log10(mean + 1e-20)
    gain = -np.maximum(level - threshold_db, 0.0) * (1.0 - 1.0 / ratio)
    return _smooth(gain, int(RIDE_SMOOTH_SECONDS * blocks_in_second))


def ride(audio: np.ndarray, threshold_db: float, ratio: float) -> tuple[np.ndarray, float]:
    """Move the level of a stem down slowly where it is above the threshold.

    The function changes `audio` in place. It returns the audio and the
    largest change in dB (0 or a negative number).
    """
    gain_db = ride_gain(audio, threshold_db, ratio)
    centres = (np.arange(len(gain_db)) + 0.5) * RIDE_BLOCK
    for start in range(0, len(audio), CHUNK):
        stop = min(start + CHUNK, len(audio))
        gain = 10.0 ** (np.interp(np.arange(start, stop), centres, gain_db) / 20.0)
        audio[start:stop] *= gain.astype(np.float32)[:, None]
    return audio, float(gain_db.min())


def shape(audio: np.ndarray, level: np.ndarray, table: Sequence[Row]) -> np.ndarray:
    """Change the level and the tone of a stem in relation to its written loudness.

    The function changes `audio` in place and returns it. `level` comes
    from `written_level`.
    """
    gain_db, shelf_db = curves(level, table)
    # A mix of the input and of a filtered signal gives each gain above 2 kHz
    # between 0 dB and the gain of the filter.
    deepest = 10.0 ** (SHELF_DB / 20.0)
    weight = np.clip((1.0 - 10.0 ** (shelf_db / 20.0)) / (1.0 - deepest), 0.0, 1.0)
    gain = 10.0 ** (gain_db / 20.0)
    control = np.arange(len(level)) / CONTROL_RATE
    filter_ = dsp.shelf(SHELF_HZ, SHELF_DB, high=True)
    for channel in range(audio.shape[1]):
        filtered = dsp.apply(audio[:, channel], filter_)
        for start in range(0, len(audio), CHUNK):
            stop = min(start + CHUNK, len(audio))
            times = np.arange(start, stop) / dsp.RATE
            mix = np.interp(times, control, weight).astype(np.float32)
            loud = np.interp(times, control, gain).astype(np.float32)
            part = audio[start:stop, channel]
            audio[start:stop, channel] = loud * (part + mix * (filtered[start:stop] - part))
    return audio
