"""Measure real orchestra recordings, and match the tone balance of the mix to them.

The references are public-domain recordings of full orchestras (Musopen).
The code measures their tone balance (level in third-octave bands), their
loudness range, and their stereo width. The master of the project must be
inside the range of these values.
"""

from __future__ import annotations

import csv
import hashlib
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile
import soxr
from scipy import signal

from . import dsp, loudness

REFERENCE_DIR = Path(".cache/reference")
BASE_URL = "https://archive.org/download/MusopenCollectionAsFlac/"
TARGET_FILE = Path("research/measured/reference_tone_balance.csv")
SUMMARY_FILE = Path("research/measured/reference_recordings.csv")


@dataclass(frozen=True)
class Reference:
    name: str
    work: str
    path: str
    sha1: str


_T6 = "Tchaikovsky_SymphonyPathetique/PyotrIlyichTchaikovsky-SymphonyNo.6InBMinorOp.74pathtique-"
REFERENCES = [
    Reference(
        "tchaikovsky6-1",
        "Tchaikovsky, Symphony No. 6, I",
        _T6 + "01-AdagioAllegroNonTroppo.flac",
        "dfae546cacdb682477861249fafe0d564b5c0f72",
    ),
    Reference(
        "tchaikovsky6-4",
        "Tchaikovsky, Symphony No. 6, IV",
        _T6 + "04-FinaleAdagioLamentoso.flac",
        "9d146de5bbca195b1a62d0b53a3175827859b2f4",
    ),
    Reference(
        "brahms4-1",
        "Brahms, Symphony No. 4, I",
        "Brahms_SymphonyNo.4inEMinor/"
        "JohannesBrahms-SymphonyNo.4InEMinorOp.98-01-AllegroNonTroppo.flac",
        "0d9699bad6fd6b13459a77468958506f49f8018d",
    ),
    Reference(
        "smetana-vltava",
        "Smetana, Vltava",
        "Smetana_Vltava/BedichSmetana-MVlast-Vltava.flac",
        "503422b5cdbde1266b1ffd92390a0aa4d7462e27",
    ),
    Reference(
        "borodin-steppes",
        "Borodin, In the Steppes of Central Asia",
        "Borodin_InTheSteppesOfCentralAsia/AlexanderBorodin-InTheSteppesOfCentralAsia.flac",
        "a25677d7b6435f8f18475f4f7e9d1ef75a895481",
    ),
]


def fetch(reference: Reference) -> Path:
    """Download one reference recording and verify its checksum."""
    path = REFERENCE_DIR / f"{reference.name}.flac"
    if not path.exists():
        REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(
            BASE_URL + reference.path, headers={"User-Agent": "stmatthew/0.1"}
        )
        with urllib.request.urlopen(request, timeout=600) as response:
            path.write_bytes(response.read())
    digest = hashlib.sha1(path.read_bytes()).hexdigest()  # noqa: S324 (the archive gives SHA-1)
    if digest != reference.sha1:
        raise RuntimeError(f"{path}: wrong checksum {digest}")
    return path


def load_stereo(path: Path) -> np.ndarray:
    """Read a two-channel file at the project sample rate."""
    data, rate = soundfile.read(str(path), dtype="float32", always_2d=True)
    if data.shape[1] == 1:
        data = np.repeat(data, 2, axis=1)
    if rate != dsp.RATE:
        data = soxr.resample(data, rate, dsp.RATE, quality="HQ")
    return data[:, :2].astype(np.float32)


@dataclass
class Measurement:
    """Numbers that describe one recording."""

    seconds: float
    loudness_lufs: float
    loudness_range: float
    short_term_p10: float  # short-term loudness relative to the integrated loudness
    short_term_p50: float
    short_term_p95: float
    peak_db: float
    crest_db: float
    correlation: float  # correlation of the left and the right channel
    side_db: float  # level of the side signal relative to the mid signal
    centres: np.ndarray
    balance: np.ndarray  # level of each third-octave band relative to the total, in dB


def _sums(audio: np.ndarray) -> tuple[float, float, float, float]:
    """Return the largest sample, and the sums of left*left, right*right, and left*right."""
    peak, left_left, right_right, left_right = 0.0, 0.0, 0.0, 0.0
    for start in range(0, len(audio), loudness.CHUNK):
        part = audio[start : start + loudness.CHUNK].astype(np.float64)
        peak = max(peak, float(np.max(np.abs(part)))) if len(part) else peak
        left_left += float(np.dot(part[:, 0], part[:, 0]))
        right_right += float(np.dot(part[:, 1], part[:, 1]))
        left_right += float(np.dot(part[:, 0], part[:, 1]))
    return peak, left_left, right_right, left_right


def tone_balance(audio: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return the centres of the third-octave bands and the level of each band (dB re total).

    The levels are those of the sum of the two channels, for the full time.
    """
    total = None
    for start in range(0, len(audio), 2 * loudness.CHUNK):
        part = audio[start : start + 2 * loudness.CHUNK]
        if len(part) < 16384:
            continue
        mid = 0.5 * (part[:, 0].astype(np.float64) + part[:, 1])
        frequencies, power = signal.welch(mid, fs=dsp.RATE, nperseg=16384)
        total = power * len(part) if total is None else total + power * len(part)
    if total is None:
        raise ValueError("the recording is too short")
    centres = 1000.0 * 2.0 ** (np.arange(-17, 13) / 3.0)  # 20 Hz to 16 kHz
    levels = []
    for centre in centres:
        low, high = centre / 2 ** (1 / 6), centre * 2 ** (1 / 6)
        band = total[(frequencies >= low) & (frequencies < high)]
        levels.append(10.0 * np.log10(band.sum() + 1e-20))
    levels = np.array(levels)
    return centres, levels - 10.0 * np.log10(np.sum(10.0 ** (levels / 10.0)))


def measure(audio: np.ndarray) -> Measurement:
    """Measure a two-channel recording."""
    power = loudness.block_power(audio)
    integrated = loudness.integrated(power)
    short_term = loudness.short_term(power)
    spread, gated = loudness.loudness_range(short_term)
    relative = gated - integrated if len(gated) else np.zeros(1)
    peak, left_left, right_right, left_right = _sums(audio)
    count = max(len(audio), 1)
    mid = (left_left + right_right + 2.0 * left_right) / 4.0
    side = (left_left + right_right - 2.0 * left_right) / 4.0
    rms = np.sqrt((left_left + right_right) / (2.0 * count))
    centres, balance = tone_balance(audio)
    return Measurement(
        seconds=len(audio) / dsp.RATE,
        loudness_lufs=integrated,
        loudness_range=spread,
        short_term_p10=float(np.percentile(relative, 10)),
        short_term_p50=float(np.percentile(relative, 50)),
        short_term_p95=float(np.percentile(relative, 95)),
        peak_db=dsp.to_db(peak),
        crest_db=dsp.to_db(peak / max(rms, 1e-12)),
        correlation=float(left_right / max(np.sqrt(left_left * right_right), 1e-20)),
        side_db=float(10.0 * np.log10(max(side, 1e-20) / max(mid, 1e-20))),
        centres=centres,
        balance=balance,
    )


def measure_references() -> None:
    """Measure all reference recordings and write the two tables."""
    results = [(reference, measure(load_stereo(fetch(reference)))) for reference in REFERENCES]
    SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "recording",
                "minutes",
                "integrated_loudness_lufs",
                "loudness_range_lu",
                "short_term_10th_percentile_lu",
                "short_term_median_lu",
                "short_term_95th_percentile_lu",
                "peak_db",
                "crest_factor_db",
                "left_right_correlation",
                "side_level_db",
            ]  # fmt: skip
        )
        for reference, m in results:
            writer.writerow(
                [
                    reference.work,
                    f"{m.seconds / 60:.2f}",
                    f"{m.loudness_lufs:.1f}",
                    f"{m.loudness_range:.1f}",
                    f"{m.short_term_p10:.1f}",
                    f"{m.short_term_p50:.1f}",
                    f"{m.short_term_p95:.1f}",
                    f"{m.peak_db:.1f}",
                    f"{m.crest_db:.1f}",
                    f"{m.correlation:.2f}",
                    f"{m.side_db:.1f}",
                ]  # fmt: skip
            )
    balances = np.array([m.balance for _, m in results])
    with TARGET_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["band_hz", "mean_db", "lowest_db", "highest_db"])
        for index, centre in enumerate(results[0][1].centres):
            column = balances[:, index]
            writer.writerow(
                [
                    f"{centre:.0f}",
                    f"{column.mean():.1f}",
                    f"{column.min():.1f}",
                    f"{column.max():.1f}",
                ]  # fmt: skip
            )


def target_balance() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Read the target tone balance: centres, mean, lowest, highest (dB re total)."""
    with TARGET_FILE.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    columns = ["band_hz", "mean_db", "lowest_db", "highest_db"]
    return tuple(np.array([float(row[c]) for row in rows]) for c in columns)  # type: ignore[return-value]


def matching_filter(
    audio: np.ndarray, strength: float = 0.9, limit_db: float = 6.0
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return a linear-phase filter that moves the tone balance of a mix to the target.

    The filter changes only the bands from 50 Hz to 8 kHz: the references are
    not reliable outside these bands. The change in one band is not more than
    `limit_db`. The function also returns the centres of the bands and the
    change of each band in dB.
    """
    centres, mean, _low, _high = target_balance()
    _centres, measured = tone_balance(audio)
    difference = np.clip((mean - measured) * strength, -limit_db, limit_db)
    # A smooth curve: each band with a part of its two adjacent bands.
    weights = np.array([0.25, 0.5, 0.25])
    smooth = np.convolve(np.pad(difference, 1, mode="edge"), weights, mode="valid")
    smooth[(centres < 48) | (centres > 8200)] = 0.0
    frequencies = np.concatenate(([0.0], centres, [dsp.RATE / 2]))
    gains = np.concatenate(([smooth[0]], smooth, [smooth[-1]]))
    grid = np.linspace(0.0, dsp.RATE / 2, 2049)
    log_grid = np.log10(np.maximum(grid, 1.0))
    log_frequencies = np.log10(np.maximum(frequencies, 1.0))
    response = 10.0 ** (np.interp(log_grid, log_frequencies, gains) / 20.0)
    return signal.firwin2(4097, grid, response, fs=dsp.RATE), centres, smooth


def match_tone_balance(audio: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Give the mix the tone balance of the reference recordings.

    The function changes `audio` in place. It returns the audio, the centres
    of the bands, and the change of each band in dB.
    """
    taps, centres, change = matching_filter(audio)
    for channel in range(audio.shape[1]):
        filtered = signal.oaconvolve(audio[:, channel], taps, mode="same")
        audio[:, channel] = filtered.astype(np.float32)
    return audio, centres, change
