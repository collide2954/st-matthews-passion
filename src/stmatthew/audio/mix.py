"""The mixer: put all players on the stage, add the hall, and make the master file."""

from __future__ import annotations

import multiprocessing
import os
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile

from ..compose import stats
from ..notation.work import Work
from ..perform.events import perform
from . import dsp, loudness, reference, sampler, space

TAIL_SECONDS = 6.0  # time after the last bar for the reverberation
SEGMENT_SECONDS = 40.0  # the render divides the work into segments of this length
SHORTEST_SEGMENT_SECONDS = 6.0
SEGMENT_LEAD = 1.0  # time before a segment, for notes that start early (grace notes)
MAX_WORKERS = 8  # largest number of parallel processes
CACHE_BYTES = 2_400_000_000  # memory for samples, for all processes together
REVERB_GAIN_DB = -9.0  # level of the hall reverberation relative to the direct sound
TARGET_LUFS = -20.0  # integrated loudness of the master
PEAK_LIMIT_DB = -1.0  # largest permitted sample peak
TARGET_RANGE = 20.0  # loudness range of the master in LU (the references: 14 to 24)


@dataclass
class MixReport:
    """Numbers that describe the master."""

    seconds: float
    loudness_lufs: float
    loudness_range: float
    peak_db: float
    gain_db: float
    players: int
    tone_change_db: tuple[float, float]  # smallest and largest change of the equalization
    riding_ratio: float  # 1 = no gain riding
    riding_gain_db: float  # largest gain of the gain riding


# The data of the present render. The worker processes get it when they start.
_JOB: dict = {}


def _render_segment(window: tuple[float, float]) -> tuple[int, np.ndarray]:
    """Render the notes that start in one time window. Return the first sample and the sound."""
    first = max(0, int(round((window[0] - SEGMENT_LEAD) * dsp.RATE)))
    stage = space.Stage()
    for player_id, prepared in _JOB["players"]:
        for group, stem in enumerate(sampler.render_player(prepared, window, first)):
            stage.add(stem, space.seat_of(player_id, group))
    return first, stage.mix(dsp.db(REVERB_GAIN_DB))


def render(
    work: Work,
    *,
    players: list[str] | None = None,
    bars: tuple[int, int] | None = None,
    workers: int | None = None,
) -> tuple[np.ndarray, MixReport]:
    """Render the work. Return the two-channel master and its report."""
    mix, count = render_mix(work, players=players, bars=bars, workers=workers)
    return master(mix, count, full=bars is None, passages=stats.passages(work))


def render_mix(
    work: Work,
    *,
    players: list[str] | None = None,
    bars: tuple[int, int] | None = None,
    workers: int | None = None,
    instruments: set[str] | None = None,
) -> tuple[np.ndarray, int]:
    """Render the work. Return the two-channel mix (not the master) and the number of players.

    `players` gives the players that play (default: all). `bars` gives the
    first and the last bar of an excerpt (default: the full work).
    `instruments` gives the instruments that play (default: all). The mix
    of an excerpt starts `SEGMENT_LEAD` seconds before its first bar.

    The function divides the time into segments and renders the segments in
    parallel processes. The sum of the segments is the same as one render of
    the full time, because each note is independent of the other notes.
    """
    structure = work.structure
    begin, end = 0.0, structure.duration_seconds
    if bars is not None:
        begin = structure.seconds(structure.bar(bars[0]).start)
        end = structure.seconds(structure.bar(bars[1]).end)
    prepared = []
    for player in work.orchestra.players:
        if players is not None and player.id not in players:
            continue
        notes = perform(work, player.id)
        if instruments is not None:
            notes = [note for note in notes if note.instrument in instruments]
        entry = sampler.prepare(notes, structure)
        if entry is not None and np.any((entry.starts >= begin) & (entry.starts < end)):
            prepared.append((player.id, entry))

    workers = max(1, min(workers or os.cpu_count() or 1, MAX_WORKERS))
    # A short excerpt gets shorter segments: thus all processes have work.
    count = max(
        int(np.ceil((end - begin) / SEGMENT_SECONDS)),
        min(workers, int(np.ceil((end - begin) / SHORTEST_SEGMENT_SECONDS))),
        1,
    )
    edges = np.linspace(begin, end, count + 1)
    edges[-1] = end + 1.0  # a note at the last moment is in the last segment
    windows = [(float(a), float(b)) for a, b in zip(edges[:-1], edges[1:], strict=True)]
    workers = min(workers, len(windows))

    first_sample = max(0, int(round((begin - SEGMENT_LEAD) * dsp.RATE))) if bars else 0
    length = int(np.ceil((end + TAIL_SECONDS) * dsp.RATE)) - first_sample
    mix = np.zeros((length, 2), dtype=np.float32)

    def add(first: int, sound: np.ndarray) -> None:
        start = first - first_sample
        stop = min(length, start + len(sound))
        if stop > start:
            mix[start:stop] += sound[: stop - start]

    _JOB["players"] = prepared
    sampler.CACHE.limit = CACHE_BYTES // workers
    try:
        if workers == 1:
            for window in windows:
                add(*_render_segment(window))
        else:
            # The worker processes are copies of this process: they have the job data.
            with multiprocessing.get_context("fork").Pool(workers) as pool:
                for first, sound in pool.imap_unordered(_render_segment, windows):
                    add(first, sound)
    finally:
        _JOB.clear()
    return mix, len(prepared)


def master(
    mix: np.ndarray,
    players: int = 0,
    *,
    full: bool = True,
    tone: bool = True,
    largest_gain_db: float = loudness.LARGEST_GAIN_DB,
    largest_ratio: float = loudness.LARGEST_RATIO,
    passages: Sequence[float] | None = None,
) -> tuple[np.ndarray, MixReport]:
    """Make the master from the mix. The function changes `mix` in place.

    The steps are:

    1. Equalization: the tone balance of the mix goes to the tone balance of
       the reference recordings (see `reference.py`).
    2. Gain riding: the soft passages go up slowly, until the loudness range
       is in the range of the reference recordings (see `loudness.py`).
       `passages` are the start times of the passages of the music: each
       passage has one level change.
    3. Level: the integrated loudness goes to the target, and the largest
       sample stays below the limit.

    An excerpt (`full` is false) does not get step 2. If `tone` is false,
    the mix does not get step 1: this is for a mix that is a recording of
    real instruments in a real room.
    """
    change = np.zeros(1)
    if tone and len(mix) >= 16384:
        mix, _centres, change = reference.match_tone_balance(mix)
    ratio, largest = 1.0, 0.0
    if full:
        mix, ratio, largest = loudness.ride(
            mix, TARGET_RANGE, largest_gain_db, largest_ratio, passages
        )
    power = loudness.block_power(mix)
    measured = loudness.integrated(power)
    gain_db = TARGET_LUFS - measured if np.isfinite(measured) else 0.0
    peak = max(
        float(np.max(np.abs(mix[start : start + loudness.CHUNK])))
        for start in range(0, max(len(mix), 1), loudness.CHUNK)
    )
    peak_db = dsp.to_db(peak) + gain_db
    if peak_db > PEAK_LIMIT_DB:
        gain_db -= peak_db - PEAK_LIMIT_DB
    mix *= np.float32(dsp.db(gain_db))
    spread, _gated = loudness.loudness_range(loudness.short_term(power))
    report = MixReport(
        seconds=len(mix) / dsp.RATE,
        loudness_lufs=measured + gain_db,
        loudness_range=spread,
        peak_db=dsp.to_db(peak) + gain_db,
        gain_db=gain_db,
        players=players,
        tone_change_db=(float(change.min()), float(change.max())),
        riding_ratio=ratio,
        riding_gain_db=largest,
    )
    return mix, report


def write(audio: np.ndarray, directory: Path, name: str = "st-matthews-passion") -> list[Path]:
    """Write the master as FLAC and as MP3. Return the paths."""
    directory.mkdir(parents=True, exist_ok=True)
    flac = directory / f"{name}.flac"
    soundfile.write(str(flac), audio, dsp.RATE, subtype="PCM_24")
    mp3 = directory / f"{name}.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(flac), "-codec:a", "libmp3lame",
         "-q:a", "1", str(mp3)],
        check=True,
    )  # fmt: skip
    return [flac, mp3]
