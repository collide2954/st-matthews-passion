"""Measure how loud MuseScore with Muse Sounds plays each dynamic mark.

For each wind, brass, and string instrument of the orchestra, and for each
way to play (a long note, staccato, accent, marcato, and pizzicato for the
strings), the code renders a short test score: one bar for each dynamic mark
from ppp to fff. The level of a mark is the loudest 100 ms of its bar.

The harp, the celesta, and the percussion instruments with a pitch have one
test: one stroke for each dynamic mark.

The result is the table `muse_levels.csv`. The module
`notation/playback.py` uses it to select the marks of the audio file.

This command needs MuseScore Studio and the Muse Sounds libraries.
"""

from __future__ import annotations

import csv
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from ..notation import musicxml, playback
from ..notation.pitch import from_midi
from ..notation.work import Work, load_orchestra
from . import dsp, musescore

FAMILIES = ("woodwinds", "brass", "strings")
# Instruments that a player strikes or plucks. They have only the test "long": one
# stroke for each dynamic mark. A measurement showed why they are in the table: the
# soft marks of these instruments were much too soft (celesta: the mark p was 30 dB
# below the mark f; harp: 27 dB; xylophone: 37 dB).
STRUCK = (
    "harp", "celesta", "piano", "glockenspiel", "crotales", "vibraphone", "marimba",
    "xylophone", "tubular bells",
)  # fmt: skip
TEMPO = 120  # quarter notes in a minute: one bar of 4/4 is 2 s
BAR_SECONDS = 2.0
WINDOW_SECONDS = 0.1
PARALLEL = 4  # number of MuseScore programs that run at the same time


def _bar(note: str, way: str) -> str:
    """Return one bar of the test music, with no dynamic mark."""
    if way == "long":
        return f"{note}1"
    if way == "marcato":
        return f"{note}2-^ {note}2-^"
    mark = {"staccato": "-.", "accent": "->", "pizzicato": ""}[way]
    return " ".join([f"{note}8{mark}"] + [f"{note}{mark}"] * 7)


def tests(orchestra) -> list[tuple[str, str, str, bool]]:
    """Return the tests: the part name, the player, the instrument, and if it is a solo string."""
    found: dict[str, tuple[str, str, str, bool]] = {}
    for player in orchestra.players:
        if player.family not in FAMILIES:
            for instrument in player.instruments:
                sound = musicxml.SOUNDS.get(instrument)
                if instrument in STRUCK and sound and sound[0] not in found:
                    found[sound[0]] = (sound[0], player.id, instrument, False)
            continue
        for instrument in player.instruments:
            names = [(musicxml.SOUNDS.get(instrument), False)]
            if instrument in musicxml.SOLO_SOUNDS:
                names.append((musicxml.SOLO_SOUNDS[instrument], True))
            for sound, solo in names:
                if sound and sound[0] not in found:
                    found[sound[0]] = (sound[0], player.id, instrument, solo)
    return list(found.values())


def measure_one(
    part: str, player: str, instrument: str, solo: bool, way: str, directory: Path
) -> list[float]:
    """Render one test score and return the level of each dynamic mark in dB."""
    work = Work("Calibration", load_orchestra())
    section = work.section(2 * len(playback.MARKS), 4, 4)
    work.structure.tempo(section.bar(1), 1, TEMPO, "Moderato")
    data = work.orchestra.instruments[instrument]
    note = from_midi((data.low + data.high) // 2).name
    start = f'\\switch "{instrument}" '
    bars = []
    for index, mark in enumerate(playback.MARKS):
        head, _, tail = _bar(note, way).partition(" ")
        marks = f"\\{mark}"
        if index == 0:
            marks += (r"\solo" if solo else "") + (r"\pizz" if way == "pizzicato" else "")
        bars.append(f"{head}{marks} {tail} | R1 |")
    section.write(player, start + " ".join(bars))
    section.close()
    folder = directory / f"{part}-{way}".replace(" ", "-")
    # An empty table: the test score must have the marks as they are written.
    audio, names = musescore.render(work, folder, players={player}, levels={})
    if not any(name.startswith(part) for name in names):
        raise RuntimeError(f"the test for {part} made the parts {names}")
    mono = audio.mean(axis=1)
    size = int(WINDOW_SECONDS * dsp.RATE)
    levels = []
    for index in range(len(playback.MARKS)):
        begin = int(index * 2 * BAR_SECONDS * dsp.RATE)
        bar = mono[begin : begin + int(BAR_SECONDS * dsp.RATE)]
        windows = [bar[i : i + size] for i in range(0, max(len(bar) - size, 1), size // 2)]
        loudest = max(float(np.sqrt(np.mean(np.square(window)))) for window in windows)
        levels.append(round(20.0 * float(np.log10(loudest + 1e-9)), 1))
    return levels


def measure(directory: Path, table: Path = playback.TABLE, new_only: bool = False) -> Path:
    """Measure the instruments and write the table. Return the file.

    If `new_only` is true, the rows of the table stay, and the code measures
    only the tests that the table does not have.
    """
    orchestra = load_orchestra()
    families = {player.id: player.family for player in orchestra.players}
    known: list[tuple[str, str, list[float]]] = []
    if new_only:
        playback.load.cache_clear()
        for part, ways in playback.load(table).items():
            known += [(part, way, levels) for way, levels in ways.items()]
    done = {(part, way) for part, way, _levels in known}
    jobs = []
    for part, player, instrument, solo in tests(orchestra):
        for way in ("long",) if instrument in STRUCK else playback.WAYS:
            if way == "pizzicato" and families[player] != "strings":
                continue
            if (part, way) not in done:
                jobs.append((part, player, instrument, solo, way))

    def run(job: tuple[str, str, str, bool, str]) -> tuple[str, str, list[float]]:
        return job[0], job[4], measure_one(*job, directory)

    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        rows = list(pool.map(run, jobs))
    with table.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["part", "way", *playback.MARKS])
        for part, way, levels in sorted(known + rows):
            writer.writerow([part, way, *levels])
    playback.load.cache_clear()
    return table
