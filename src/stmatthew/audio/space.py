"""The stage and the hall: where each player sits, and how the sound gets to the microphones.

The model has three parts:

1. A main pair of microphones above the conductor (two cardioid microphones,
   17 cm apart, at an angle of 110 degrees: the ORTF system). Each player has
   a seat on the stage. The sound of a player arrives at each microphone with
   the level and the delay of its real direction and distance. This gives the
   stereo image.
2. The first reflections from the floor, the side walls, the back wall, and
   the ceiling of the stage.
3. The late reverberation of the hall. The code makes it from noise with a
   decay time that depends on the frequency, as in a real concert hall.

The measured values of real orchestra recordings are the test for this model:
see `research/measured/reference_recordings.csv`.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from scipy import signal

from . import dsp

SPEED_OF_SOUND = 343.0  # metres in a second

# The stage, in metres. x: left (negative) to right, seen from the audience.
# y: from the front edge of the stage to the back. z: height.
SIDE_WALL = 11.5
BACK_WALL = 15.0
CEILING = 14.0
SOURCE_HEIGHT = 1.1
ARRAY = (0.0, -2.2, 3.4)  # centre of the microphone pair
CAPSULE_DISTANCE = 0.17  # metres between the two microphones
CAPSULE_ANGLE = np.radians(55.0)  # each microphone points this far to its side
REFERENCE_DISTANCE = 7.0  # a source at this distance has a gain of 1
NEAREST_PATH = 2.5  # metres; less than the distance of the nearest seat

# Decay time of the hall (seconds for a decrease of 60 dB) for each octave band.
# The values are those of a large concert hall with an audience.
DECAY_SECONDS = {
    63: 2.5,
    125: 2.35,
    250: 2.2,
    500: 2.1,
    1000: 2.0,
    2000: 1.8,
    4000: 1.45,
    8000: 1.0,
}


@dataclass(frozen=True)
class Seat:
    x: float
    y: float


# Seats of the players. The violins sit left and right of the conductor, as in
# the orchestras of Schoenberg's and Bartók's time.
SEATS: dict[str, Seat] = {
    "vn1": Seat(-5.5, 2.6), "vn2": Seat(5.2, 2.6), "va": Seat(2.4, 4.6), "vc": Seat(-2.2, 4.6),
    "cb": Seat(-6.8, 6.6),
    "fl1": Seat(-1.0, 7.0), "fl2": Seat(-2.0, 7.0), "fl3": Seat(-3.0, 7.0),
    "ob1": Seat(1.0, 7.0), "ob2": Seat(2.0, 7.0), "ob3": Seat(3.0, 7.0),
    "cl1": Seat(-1.0, 8.3), "cl2": Seat(-2.0, 8.3), "cl3": Seat(-3.0, 8.3), "cbcl": Seat(-4.0, 8.3),
    "bn1": Seat(1.0, 8.3), "bn2": Seat(2.0, 8.3), "bn3": Seat(3.0, 8.3),
    "hn1": Seat(-2.6, 9.7), "hn2": Seat(-3.6, 9.7), "hn3": Seat(-4.6, 9.7),
    "hn4": Seat(-5.6, 9.7), "hn5": Seat(-3.1, 10.8), "hn6": Seat(-4.1, 10.8),
    "tpt1": Seat(0.6, 9.8), "tpt2": Seat(1.6, 9.8), "tpt3": Seat(2.6, 9.8),
    "tbn1": Seat(3.8, 9.8), "tbn2": Seat(4.8, 9.8), "btbn": Seat(5.8, 9.8), "tuba": Seat(6.8, 9.8),
    "timp": Seat(0.0, 11.6),
    "perc1": Seat(-7.5, 11.4), "perc2": Seat(-5.5, 11.8), "perc3": Seat(-3.5, 12.0),
    "perc4": Seat(3.0, 12.0), "perc5": Seat(-1.5, 12.2), "perc6": Seat(5.0, 11.8),
    "harp": Seat(-8.2, 5.6), "pno": Seat(-8.8, 8.2), "cel": Seat(-7.6, 9.4),
    "cimb": Seat(7.8, 5.6), "mand": Seat(6.6, 4.2), "acc": Seat(7.8, 7.6),
}  # fmt: skip

# A string section is some metres wide. Each group of the section has its own seat.
SECTION_OFFSETS = [(0.0, 0.0), (-1.6, 0.9), (1.6, 1.0), (0.4, 1.9)]


def seat_of(player_id: str, group: int = 0) -> Seat:
    """Return the seat of a player, or of one group of a string section."""
    base = SEATS[player_id.split(".")[0]]
    dx, dy = SECTION_OFFSETS[group % len(SECTION_OFFSETS)]
    return Seat(base.x + dx, base.y + dy)


def _paths(seat: Seat) -> list[tuple[tuple[float, float, float], float, bool]]:
    """Return the image sources of a seat: (position, reflection gain, is a reflection)."""
    x, y, z = seat.x, seat.y, SOURCE_HEIGHT
    return [
        ((x, y, z), 1.0, False),  # direct sound
        ((x, y, -z), 0.75, True),  # floor
        ((-2 * SIDE_WALL - x, y, z), 0.6, True),  # left wall
        ((2 * SIDE_WALL - x, y, z), 0.6, True),  # right wall
        ((x, 2 * BACK_WALL - y, z), 0.65, True),  # back wall
        ((x, y, 2 * CEILING - z), 0.5, True),  # ceiling
    ]


def taps(seat: Seat) -> list[tuple[int, int, float, bool]]:
    """Return the sound paths from a seat to the microphones.

    Each path is (delay in samples, channel, gain, is a reflection).
    """
    result = []
    for position, gain, is_reflection in _paths(seat):
        offset = np.subtract(position, ARRAY)
        distance = float(np.linalg.norm(offset))
        # Angle of the source in the horizontal plane: 0 = straight ahead, positive = right.
        azimuth = float(np.arctan2(offset[0], offset[1]))
        elevation_loss = float(np.hypot(offset[0], offset[1])) / distance
        for channel, side in enumerate((-1.0, 1.0)):
            # Cardioid microphone that points to its side.
            pattern = 0.5 * (1.0 + np.cos(azimuth - side * CAPSULE_ANGLE) * elevation_loss)
            # The sound arrives earlier at the microphone on the side of the source.
            path = distance - side * 0.5 * CAPSULE_DISTANCE * np.sin(azimuth)
            delay = max(0, int(round((path - NEAREST_PATH) / SPEED_OF_SOUND * dsp.RATE)))
            result.append(
                (
                    delay,
                    channel,
                    float(gain * pattern * REFERENCE_DISTANCE / distance),
                    is_reflection,
                )
            )
    return result


class Stage:
    """Collect the sound of all players at the microphones."""

    def __init__(self, length: int = 0) -> None:
        self.length = length
        self.direct = np.zeros((length, 2), dtype=np.float32)
        self.reflected = np.zeros((length, 2), dtype=np.float32)
        self.send = np.zeros(length, dtype=np.float32)

    def _grow(self, length: int) -> None:
        """Make the stage longer, if a signal needs more time."""
        if length <= self.length:
            return
        extra = max(length - self.length, self.length // 4, 4 * dsp.RATE)
        self.direct = np.concatenate([self.direct, np.zeros((extra, 2), np.float32)])
        self.reflected = np.concatenate([self.reflected, np.zeros((extra, 2), np.float32)])
        self.send = np.concatenate([self.send, np.zeros(extra, np.float32)])
        self.length += extra

    def add(self, stem: np.ndarray, seat: Seat) -> None:
        """Add a one-channel signal that comes from a seat."""
        sounding = np.flatnonzero(stem)
        if len(sounding) == 0:
            return
        first, last = int(sounding[0]), int(sounding[-1]) + 1
        active = stem[first:last]
        paths = taps(seat)
        self._grow(last + max(delay for delay, _, _, _ in paths))
        for delay, channel, gain, is_reflection in paths:
            target = self.reflected if is_reflection else self.direct
            target[first + delay : last + delay, channel] += np.float32(gain) * active
        self.send[first:last] += np.float32(reverb_send(seat)) * active

    def mix(self, reverb_gain: float) -> np.ndarray:
        """Return the two-channel mix: direct sound, first reflections, and reverberation.

        The result is longer than the stage: it contains the end of the reverberation.
        """
        if self.length == 0:
            return np.zeros((0, 2), dtype=np.float32)  # no player has a note in this time
        # A reflection loses high frequencies at the wall and in the air.
        reflected = signal.sosfilt(dsp.lowpass(5500.0, 1), self.reflected, axis=0)
        result = np.float32(reverb_gain) * reverberate(self.send)
        result[: self.length] += self.direct + reflected.astype(np.float32)
        return result


def reverb_send(seat: Seat) -> float:
    """Return how much of a seat goes to the hall reverberation.

    The reverberant sound has almost the same level for all seats. The direct
    sound decreases with the distance. Thus a far seat sounds more distant.
    """
    distance = float(np.hypot(seat.x - ARRAY[0], seat.y - ARRAY[1]))
    return float(np.clip(0.75 + 0.03 * distance, 0.75, 1.15))


# How similar the reverberation is at the two microphones, for each octave band.
# In a real hall the low frequencies are almost the same in the two channels.
SHARED_PART = {63: 0.95, 125: 0.9, 250: 0.75, 500: 0.6, 1000: 0.5, 2000: 0.45, 4000: 0.4, 8000: 0.4}


def hall_response(seconds: float = 3.6, seed: int = 20261115) -> np.ndarray:
    """Return the two-channel impulse response of the late reverberation."""
    random = np.random.default_rng(seed)
    length = int(seconds * dsp.RATE)
    time = np.arange(length) / dsp.RATE
    response = np.zeros((length, 2), dtype=np.float64)
    centres = sorted(DECAY_SECONDS)
    for centre in centres:
        low, high = centre / np.sqrt(2.0), min(centre * np.sqrt(2.0), 0.45 * dsp.RATE)
        if centre == centres[0]:
            band = signal.butter(2, high, "lowpass", fs=dsp.RATE, output="sos")
        elif centre == centres[-1]:
            band = signal.butter(2, low, "highpass", fs=dsp.RATE, output="sos")
        else:
            band = signal.butter(2, [low, high], "bandpass", fs=dsp.RATE, output="sos")
        shared = SHARED_PART[centre]
        own = np.sqrt(1.0 - shared**2)
        noise = own * random.normal(0.0, 1.0, (length, 2)) + shared * random.normal(
            0.0, 1.0, (length, 1)
        )
        decay = np.exp(-6.908 * time / DECAY_SECONDS[centre])[:, None]
        response += signal.sosfiltfilt(band, noise, axis=0) * decay
    # The reverberation builds up after the first reflections.
    build = int(0.07 * dsp.RATE)
    response[:build] *= np.linspace(0.0, 1.0, build)[:, None] ** 2
    response[-2000:] *= np.linspace(1.0, 0.0, 2000)[:, None]
    response /= np.sqrt(np.sum(response**2, axis=0, keepdims=True))
    return response.astype(np.float32)


@lru_cache(maxsize=1)
def _default_response() -> np.ndarray:
    return hall_response()


def reverberate(send: np.ndarray, response: np.ndarray | None = None) -> np.ndarray:
    """Return the two-channel reverberation of a one-channel send signal.

    The result is longer than the send signal by the length of the hall response.
    """
    if response is None:
        response = _default_response()
    left = signal.oaconvolve(send, response[:, 0])
    right = signal.oaconvolve(send, response[:, 1])
    return np.stack([left, right], axis=1).astype(np.float32)
