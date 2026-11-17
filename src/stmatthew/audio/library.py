"""The sample libraries: where they come from, and an index of their samples.

The project uses free sample libraries only. The code downloads them with
`git` into the cache directory. Then it measures each sample: the real pitch,
the loudness, the start of the sound, and a loop for held tones. The engine
uses these measured values, not the file names alone.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from . import dsp

SAMPLES_DIR = Path(".cache/samples")
INDEX_VERSION = 4


@dataclass(frozen=True)
class Library:
    """One sample library in a git repository."""

    name: str
    url: str
    licence: str
    paths: tuple[str, ...]  # directories to download; empty = all


LIBRARIES = {
    library.name: library
    for library in [
        Library(
            "vsco2",
            "https://github.com/sgossner/VSCO-2-CE.git",
            "CC0 1.0",
            ("Strings", "Woodwinds", "Brass", "Percussion", "VSCO 1 Percussion"),
        ),
        Library(
            "sso",
            "https://github.com/peastman/sso.git",
            "CC Sampling Plus 1.0",
            ("Sonatina Symphonic Orchestra/Samples",),
        ),
        Library(
            "vcsl",
            "https://github.com/sgossner/VCSL.git",
            "CC0 1.0",
            (
                "Idiophones/Struck Idiophones",
                "Idiophones/Friction Idiophones",
                "Aerophones/Edge-blown Aerophones/Ocarina, Typical",
                "Aerophones/Edge-blown Aerophones/Ocarina, Small",
                "Aerophones/Free Aerophones/Harmonica-Hohner-Super64",
                "Chordophones/Zithers/Psaltery, Bowed and Plucked",
                "Chordophones/Composite Chordophones/Concert Harp",
                "Membranophones/Struck Membranophones",
                "Chordophones/Zithers/Grand Piano, Kawai",
            ),
        ),
        Library("mandolin", "https://github.com/sfzinstruments/Terkelsen.Mandolin.git", "free", ()),
        Library("zither", "https://github.com/sfzinstruments/hungarian_zither.git", "CC0 1.0", ()),
    ]
}


def fetch(name: str) -> Path:
    """Download one library into the cache (if it is not there) and return its directory."""
    library = LIBRARIES[name]
    target = SAMPLES_DIR / name
    if (target / ".git").exists():
        if library.paths:
            _add_missing_paths(target, library.paths)
        return target
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    command = ["git", "clone", "--quiet", "--depth", "1"]
    if library.paths:
        command += ["--filter=blob:none", "--sparse"]
    subprocess.run([*command, library.url, str(target)], check=True)
    if library.paths:
        subprocess.run(
            ["git", "-C", str(target), "sparse-checkout", "set", *library.paths], check=True
        )
    return target


def _add_missing_paths(target: Path, paths: tuple[str, ...]) -> None:
    """Get the directories of a library that came into the list after the first download."""
    present = subprocess.run(
        ["git", "-C", str(target), "sparse-checkout", "list"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()  # fmt: skip
    if any(path not in present for path in paths):
        subprocess.run(["git", "-C", str(target), "sparse-checkout", "set", *paths], check=True)


# ----------------------------------------------------------------------------
# Sample index
# ----------------------------------------------------------------------------

NOTE_RE = re.compile(r"(?<![A-Za-z])([A-Ga-g])(#|b)?(-?\d)(?![0-9A-Za-z#])")
PITCH_CLASS = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


@dataclass(frozen=True)
class Source:
    """A group of sample files of one instrument and one way to play.

    `pattern` is a regular expression for the file name. It can have the groups
    `layer` (loudness layer) and `rr` (alternative take of the same note).
    `layers` gives the loudness (0 to 1) of each layer name.
    """

    library: str
    folder: str
    pattern: str = r".*"
    layers: tuple[tuple[str, float], ...] = ()
    pitched: bool = True
    held: bool = True  # a held tone (with a loop) or a short sound
    low_hz: float = 25.0
    high_hz: float = 4500.0
    octave_shift: int | None = None  # octave correction of the file names; None = find it


@dataclass
class Sample:
    """One measured sample."""

    path: str
    midi: float  # the measured pitch (not rounded), or the pitch from the file name
    nominal: int  # the nearest semitone
    layer: float  # loudness of the layer, 0 to 1
    take: int
    onset: int  # index of the start of the sound, at the project rate
    length: int  # number of samples from the onset to the end
    peak: float
    level: float  # root mean square of the loud part
    loop_start: int = -1
    loop_end: int = -1
    loop_fade: int = 0


def _name_pitch_class(name: str) -> tuple[int, int] | None:
    """Return (pitch class, octave number in the name) from a file name."""
    matches = NOTE_RE.findall(name)
    if not matches:
        return None
    letter, accidental, octave = matches[-1]
    pitch_class = PITCH_CLASS[letter.lower()] + {"#": 1, "b": -1, "": 0}[accidental]
    return pitch_class % 12, int(octave)


def measure(path: Path, source: Source, layer: float, take: int) -> tuple[Sample, float | None]:
    """Measure one sample file. Return the sample and its detected pitch (or None)."""
    audio = dsp.load_mono(path)
    onset = dsp.onset_index(audio)
    body = audio[onset:]
    peak = float(np.max(np.abs(body))) if len(body) else 0.0
    loud = body[: int(1.5 * dsp.RATE)]
    level = dsp.rms(loud[np.abs(loud) > 0.05 * peak]) if peak > 0 else 0.0
    detected = None
    if source.pitched and peak > 0:
        if source.held:
            steady = body[int(0.15 * len(body)) : int(0.6 * len(body))]
        else:
            steady = body[int(0.04 * dsp.RATE) : int(0.45 * dsp.RATE)]
        frequency = dsp.detect_pitch(steady, dsp.RATE, source.low_hz, source.high_hz)
        detected = dsp.hz_to_midi(frequency) if frequency else None
    sample = Sample(
        path=str(path),
        midi=60.0,
        nominal=60,
        layer=layer,
        take=take,
        onset=onset,
        length=len(body),
        peak=peak,
        level=level,
    )
    if source.held and peak > 0:
        loop = dsp.find_loop(body)
        if loop:
            sample.loop_start, sample.loop_end, sample.loop_fade = loop
    return sample, detected


def _assign_pitches(entries: list[tuple[Sample, float | None]], source: Source) -> list[Sample]:
    """Give each sample its pitch from the file name and the detected pitch.

    Libraries do not agree on the octave numbers in file names. The code finds
    the octave difference that most detected pitches agree with.
    """
    named = [_name_pitch_class(Path(sample.path).stem) for sample, _ in entries]
    votes: dict[int, int] = {}
    for (_sample, detected), name in zip(entries, named, strict=True):
        if detected is None or name is None:
            continue
        pitch_class, octave = name
        written = pitch_class + 12 * (octave + 1)
        shift = round((detected - written) / 12)
        if abs(detected - (written + 12 * shift)) < 0.6:
            votes[shift] = votes.get(shift, 0) + 1
    shift = max(votes, key=lambda key: votes[key]) if votes else 0
    if source.octave_shift is not None:
        shift = source.octave_shift

    samples: list[Sample] = []
    for (sample, detected), name in zip(entries, named, strict=True):
        if sample.peak <= 0:
            continue
        if name is not None:
            nominal = name[0] + 12 * (name[1] + 1 + shift)
            fine = 0.0
            if detected is not None and abs(detected - nominal) < 0.6:
                fine = detected - nominal
                if not source.held:
                    fine = float(np.clip(fine, -0.3, 0.3))
            sample.midi = nominal + fine
        elif detected is not None:
            sample.midi = detected
        elif source.pitched:
            continue
        sample.nominal = int(round(sample.midi))
        samples.append(sample)
    return samples


def _layer_of(match: re.Match[str], source: Source) -> float:
    layers = dict(source.layers)
    if not layers:
        return 0.6
    name = match.groupdict().get("layer") or ""
    if name in layers:
        return layers[name]
    return sorted(layers.values())[len(layers) // 2]


def build_index(source: Source) -> list[Sample]:
    """Measure all samples of a source. The result is kept in the cache."""
    root = fetch(source.library) / source.folder
    files = sorted(
        path
        for path in root.iterdir()
        if path.suffix.lower() in (".wav", ".flac") and re.fullmatch(source.pattern, path.stem)
    )
    listing = [(path.name, path.stat().st_size) for path in files]
    key = hashlib.sha256(json.dumps([INDEX_VERSION, asdict(source), listing]).encode()).hexdigest()[
        :20
    ]
    cache = SAMPLES_DIR / "index" / f"{key}.json"
    if cache.exists():
        return [Sample(**entry) for entry in json.loads(cache.read_text())]

    entries: list[tuple[Sample, float | None]] = []
    for path in files:
        match = re.fullmatch(source.pattern, path.stem)
        assert match is not None
        take_text = match.groupdict().get("rr") or "1"
        entries.append(measure(path, source, _layer_of(match, source), int(take_text)))
    samples = _assign_pitches(entries, source) if source.pitched else [e[0] for e in entries]
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps([asdict(sample) for sample in samples]))
    return samples
