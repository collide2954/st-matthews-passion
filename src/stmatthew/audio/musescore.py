"""Render the audio with MuseScore Studio and its Muse Sounds libraries.

Muse Sounds are free sample libraries of an orchestra. They are much more
realistic than the open sample libraries of this project. They are not open:
only MuseScore Studio can play them, and a build server cannot install them.
Thus this render is for the computer of the owner of the project.

Muse Sounds are the instruments of a modern orchestra. The work is for a
baroque orchestra. Thus each baroque instrument gets the modern instrument
that is nearest to it (the table `SOUNDS` of `notation/musicxml.py`).

The steps are:

1. Write the work as a MusicXML file (`notation/musicxml.py`).
2. MuseScore changes the MusicXML file into its own format.
3. The playing techniques in that file get the form that MuseScore plays
   (for example pizzicato, sul ponticello, mute).
4. MuseScore renders the file to audio with the sound profile "Muse Sounds".
5. The sampler of this project renders the instruments that Muse Sounds do
   not have: the organ (samples of a pipe organ), and the voice if its
   stand-in is a sound of the sampler (see `voice.py`). The mixer adds them.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from ..compose import stats
from ..notation import musicxml, playback
from ..notation.work import Work
from . import dsp, reference, stemtone

PROFILE = "Muse Sounds"
MASTER_VOLUME_DB = -18.0  # level of the master control of MuseScore for the render
SAMPLER_HOME = Path.home() / ".local/share/MuseSampler"
# The Muse Sounds libraries play only in the official build of MuseScore Studio.
OFFICIAL_PROGRAM = Path.home() / ".local/opt/musescore-studio/squashfs-root/AppRun"
PROGRAM_VARIABLE = "STMATTHEW_MUSESCORE"


def program() -> str:
    """Return the MuseScore program: the official build if it is there."""
    if os.environ.get(PROGRAM_VARIABLE):
        return os.environ[PROGRAM_VARIABLE]
    return str(OFFICIAL_PROGRAM) if OFFICIAL_PROGRAM.exists() else "mscore"


# Words of a playing technique in the score -> the technique of MuseScore.
PLAY_TECHNIQUES = {
    "pizz.": "pizzicato",
    "arco": "natural",
    "ord.": "natural",
    "col legno": "col_legno",
    "sul pont.": "sul_ponticello",
    "sul tasto": "sul_tasto",
    "con sord.": "mute",
    "senza sord.": "open",
}

STAFF_TEXT = re.compile(r"<StaffText>(.*?)</StaffText>", re.DOTALL)
PART = re.compile(r'<Part id="(\d+)">.*?<Instrument id="([^"]+)"', re.DOTALL)

# The level of some parts of Muse Sounds in relation to the other parts, in dB. The
# mixer of MuseScore gets these values.
# - The violone is one player. Its sound is that of a group of double basses: there
#   is no single double bass in the libraries. A group of eight players is 9 dB
#   louder than one player (10 x log10 of the number of players). The groups of the
#   other strings are also larger than those of this work, by 6 dB (see
#   `STEM_GAIN_DB`). The difference of the two values is the value for the violone.
TRIM_DB = {
    "Contrabasses": -3.0,
}
TEXT = re.compile(r"<text>(.*?)</text>", re.DOTALL)


def available() -> bool:
    """Return true if MuseScore and the Muse Sounds libraries are on this computer."""
    return shutil.which(program()) is not None and any(SAMPLER_HOME.rglob("*.so"))


def _run(arguments: list[str], log: Path) -> None:
    environment = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    with log.open("a", encoding="utf-8") as handle:
        result = subprocess.run(
            [program(), *arguments], env=environment, stdout=handle, stderr=handle, check=False
        )
    if result.returncode != 0:
        raise RuntimeError(f"MuseScore failed ({' '.join(arguments)}). See {log}.")


def play_techniques(text: str) -> tuple[str, int]:
    """Change the staff texts of playing techniques into playing technique marks.

    MuseScore reads the words of a MusicXML file as plain text. A plain text
    has no effect on the sound. Return the new text and the number of changes.
    """
    count = 0

    def change(match: re.Match[str]) -> str:
        nonlocal count
        words = TEXT.search(match.group(1))
        technique = PLAY_TECHNIQUES.get(words.group(1).strip()) if words else None
        if technique is None:
            return match.group(0)
        count += 1
        body = match.group(1).rstrip()
        return (
            f"<PlayTechAnnotation>{body}\n            <playTechType>{technique}</playTechType>"
            f"\n            </PlayTechAnnotation>"
        )

    return STAFF_TEXT.sub(change, text), count


def render(
    work: Work,
    directory: Path,
    bars: tuple[int, int] | None = None,
    profile: str = PROFILE,
    instruments: set[str] | None = None,
    players: set[str] | None = None,
    levels: dict[str, playback.Levels] | None = None,
) -> tuple[np.ndarray, list[str]]:
    """Render the work (or some bars) with MuseScore.

    Return the two-channel sound at the sample rate of the project, and the
    names of the parts that MuseScore played. The sound starts at the start
    of the first bar.
    """
    directory.mkdir(parents=True, exist_ok=True)
    log = directory / "musescore.log"
    log.write_text("", encoding="utf-8")
    text, names = musicxml.score(work, bars, instruments, players, levels)
    source = directory / "score.musicxml"
    source.write_text(text, encoding="utf-8")
    packed = directory / "score.mscz"
    packed.unlink(missing_ok=True)
    _run(["-o", str(packed), str(source)], log)
    count = prepare_file(packed, profile, names)
    sound = directory / "score.wav"
    sound.unlink(missing_ok=True)
    _run(["-o", str(sound), str(packed)], log)
    print(f"musescore: {len(names)} parts, {count} playing technique marks, profile {profile}")
    return _load(sound), names


# The highest note (MIDI number) that Muse Sounds play, for the instruments whose
# range in the orchestra file goes higher. A higher note has no sound. A test score
# with all notes of each range gave the values of the modern instruments. Each
# baroque instrument has the value of the modern instrument that plays it.
HIGHEST_NOTE = {
    "flute": 97, "recorder": 97, "bassoon": 75, "theorbo": 102, "violin": 101, "viola": 86,
    "violone": 61,
}  # fmt: skip
# The lowest note that Muse Sounds play. The viola da gamba has the sound of a
# violoncello: the notes below its lowest string (C) have no sound.
LOWEST_NOTE = {"viola da gamba": 36}


def silent_notes(work: Work) -> list[tuple[str, int, float]]:
    """Return the notes of the work that Muse Sounds do not play: player, bar, MIDI number."""
    from ..perform.events import perform

    found = []
    for player in work.orchestra.players:
        for note in perform(work, player.id):
            too_high = note.midi > HIGHEST_NOTE.get(note.instrument, 1000)
            too_low = note.midi < LOWEST_NOTE.get(note.instrument, 0)
            if too_high or too_low:
                found.append((player.id, work.structure.bar_at(note.start).number, note.midi))
    return found


def continuous_slides(score: str, keyboard: bool = False) -> str:
    """Make each slide between two notes a continuous change of pitch.

    MuseScore plays a slide from a MusicXML file as a sequence of semitones.
    The play style "portamento" gives the slide of a string player. A keyboard
    instrument cannot do this: its slide is on the white keys.
    """
    style = "whitekeys" if keyboard else "portamento"
    return score.replace("<Glissando>", f"<Glissando><glissandoStyle>{style}</glissandoStyle>")


def mixer_tracks(score: str, names: list[str]) -> list[dict]:
    """Return the mixer settings for the parts that have a level in `TRIM_DB`.

    `score` is the text of the MuseScore file. `names` are the names of its
    parts, in the sequence of the file, for example "Contrabasses (vne)".
    """
    tracks = []
    for (part, instrument), name in zip(PART.findall(score), names, strict=True):
        trim = TRIM_DB.get(name.rsplit(" (", 1)[0], 0.0)
        if trim:
            out = {"volumeDb": trim, "balance": 0, "fxChain": {}}
            tracks.append({"partId": part, "instrumentId": instrument, "out": out})
    return tracks


def prepare_file(packed: Path, profile: str, names: list[str] | None = None) -> int:
    """Change the MuseScore file for the render. Return the number of technique marks.

    The file is a ZIP archive. The function changes two files in it:

    - The score: the words of the playing techniques become technique marks,
      and a slide between two notes becomes a continuous change of pitch.
    - The audio settings: the sound profile, a lower level of the master
      control, and the levels of `TRIM_DB`. With the master control at 0 dB,
      a loud passage of the full orchestra is too loud for the output of
      MuseScore and has distortion.
    """
    count = 0
    tracks: list[dict] = []
    contents: dict[str, bytes] = {}
    with zipfile.ZipFile(packed) as archive:
        for name in archive.namelist():
            contents[name] = archive.read(name)
    for name, data in contents.items():
        if name.endswith(".mscx"):
            changed, count = play_techniques(data.decode("utf-8"))
            keyboard = bool(names) and all(part.startswith(KEYBOARD_PARTS) for part in names)
            changed = continuous_slides(changed, keyboard)
            contents[name] = changed.encode("utf-8")
            if names is not None:
                tracks = mixer_tracks(changed, names)
    for name, data in contents.items():
        if name == "audiosettings.json":
            settings = json.loads(data.decode("utf-8"))
            settings["activeSoundProfile"] = profile
            settings.setdefault("master", {})["volumeDb"] = MASTER_VOLUME_DB
            if tracks:
                settings["tracks"] = tracks
            contents[name] = json.dumps(settings, indent=4).encode("utf-8")
    with zipfile.ZipFile(packed, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in contents.items():
            archive.writestr(name, data)
    return count


def other_instruments(work: Work) -> set[str]:
    """Return the instruments of the work that MuseScore does not play."""
    names = {name for player in work.orchestra.players for name in player.instruments}
    return {name for name in names if not musicxml.can_play(name)}


# The two sound sources (MuseScore, and the sampler of this project) must agree on
# the level. The two sources play the same short passage of one instrument that the
# two have. The difference of the two levels is the gain for the sampler.
CALIBRATION_PLAYER = "vc"
CALIBRATION_INSTRUMENT = "violoncello"
CALIBRATION_MUSIC = r"c1\mf | g1 | c'1 | g1 |"
CALIBRATION_VERSION = 2


def calibration_work(work: Work) -> Work:
    """Return a work of four bars for the orchestra of `work`: long notes of one group."""
    passage = Work("Calibration", work.orchestra)
    section = passage.section(4, 4, 4)
    passage.structure.tempo(1, 1, 60, "")
    section.write(CALIBRATION_PLAYER, CALIBRATION_MUSIC)
    section.close()
    return passage


def calibration_gain(work: Work, directory: Path, profile: str) -> float:
    """Return the gain in dB for the sampler of this project, to agree with MuseScore.

    The result is kept in a file: the measurement is necessary only one time.
    """
    from . import mix

    record = directory / "calibration.json"
    key = {"profile": profile, "version": CALIBRATION_VERSION, "music": CALIBRATION_MUSIC}
    if record.exists():
        known = json.loads(record.read_text(encoding="utf-8"))
        if all(known.get(name) == value for name, value in key.items()):
            return float(known["gain_db"])
    passage = calibration_work(work)
    instruments = {CALIBRATION_INSTRUMENT}
    theirs, _names = render(passage, directory / "calibration", None, profile, instruments)
    ours, _count = mix.render_mix(passage, instruments=instruments)
    # The same time of the two sounds: from the first note to the end of the last bar.
    last = int(passage.structure.duration_seconds * dsp.RATE)
    first = dsp.RATE // 2
    gain_db = dsp.to_db(dsp.rms(theirs[first:last]) / max(dsp.rms(ours[first:last]), 1e-12))
    directory.mkdir(parents=True, exist_ok=True)
    record.write_text(json.dumps({**key, "gain_db": gain_db}), encoding="utf-8")
    return gain_db


# The groups of the orchestra. MuseScore renders each group as one file (a
# stem). The sum of the stems is the same as one render of all groups. The
# stems make three things possible: parallel renders, a new render of one
# group only, and a change of the balance between the groups. Each group is
# the players of some families (the entry `family` of the orchestra file).
STEMS = {
    "woodwinds": ("woodwinds",),
    "strings": ("strings",),
    "continuo": ("plucked", "keyboards"),
    "voice": ("voice",),
}

KEYBOARD_PARTS = ("Harpsichord", "Piano", "Celesta")  # parts whose slides are on the white keys

# Level of each stem in the mix, in dB.
# - The string groups of Muse Sounds are those of a symphony orchestra: about four
#   times the players of this work (4, 4, 3, and 2 players). A group with four times
#   the players is 6 dB louder (10 x log10 of 4). Thus the strings get -6 dB: the
#   woodwinds and the voice then have the weight that they have in a small orchestra.
# - The voice is the soloist: she stands at the front of the stage. A measurement of
#   the first chorale (number 6) gave the stand-in for the voice a level 12 dB below
#   the strings and 7 dB below the woodwinds. With +9 dB the voice is 3 dB below all
#   strings together in a chorale, and it is above the continuo in a recitative.
STEM_GAIN_DB = {"woodwinds": 0.0, "strings": -6.0, "continuo": 0.0, "voice": 9.0}

# Level of each instrument of the sampler (the organ, and a voice of the sampler) in
# the mix, in dB. The calibration makes the two sound sources agree on the level of
# one instrument. These values are corrections after that.
# - The voice of the sampler (a group of women) was 6 dB louder in the first chorale
#   than the voice of MuseScore (a clarinet with the gain of `STEM_GAIN_DB`). With
#   -6 dB the two stand-ins have the same level.
SAMPLER_GAIN_DB = {"organ": 0.0, musicxml.VOICE: -6.0}

# The equalization of the mix. The loud passages of the mix (the loudest tenth of its
# seconds) were compared with those of five reference recordings of real
# orchestras, in bands of one octave, in relation to the band 250 Hz to 1 kHz:
# - 125 to 250 Hz: the mix was 2 to 3 dB above the middle of the recordings.
# - 1 to 4 kHz: the mix was 1.5 to 2 dB below the middle of the recordings.
# - 8 to 16 kHz: the mix was 5 dB above the middle, and above four of the five.
# The soft and the medium passages gave almost the same differences.
# The microphones of Muse Sounds are near the instruments. In a hall, the air and the
# distance take away much of the sound above 8 kHz. Each row is: the type, the
# frequency in Hz, the gain in dB, and (for a bell filter) the quality factor.
# These values come from the project "Night Music for Orchestra", which has the same
# sound source. A measurement for this work is not done.
MASTER_EQ: tuple[tuple, ...] = (
    ("bell", 170.0, -2.0, 0.8),
    ("bell", 2000.0, 2.0, 0.7),
    ("high shelf", 6000.0, -4.0),
)

PARALLEL_RENDERS = 3  # number of MuseScore programs that run at the same time

# The sound of MuseScore is much wider than a recording of a real orchestra:
# the left and the right channel are almost independent. The measured
# recordings have a correlation of 0.39 to 0.69. A stem with a smaller
# correlation than this value gets a smaller difference signal.
SMALLEST_CORRELATION = 0.35

# Limits of the gain riding of the master for this source of sound.
RIDING_GAIN_DB = 26.0
RIDING_RATIO = 4.0
RENDER_VERSION = 4  # a change of this number makes all kept stems invalid


def stem_players(work: Work, name: str) -> set[str]:
    """Return the players of one stem."""
    return {player.id for player in work.orchestra.players if player.family in STEMS[name]}


def render_stems(
    work: Work, directory: Path, bars: tuple[int, int] | None = None, profile: str = PROFILE
) -> dict[str, np.ndarray]:
    """Render each group of the orchestra with MuseScore. Return the sound of each group.

    A stem that is in the directory from an earlier render stays, if its
    music did not change.
    """

    def one(name: str) -> tuple[str, np.ndarray | None]:
        players = stem_players(work, name)
        text, names = musicxml.score(work, bars, players=players)
        if not names:
            return name, None
        # An excerpt has its own folder: thus the stems of the full work stay.
        folder = directory / (name if bars is None else f"{name}-{bars[0]}-{bars[1]}")
        record = folder / "stem.json"
        sound = folder / "score.wav"
        # Only the mixer levels of the parts of this stem are in the key. Thus a new
        # level for one instrument does not make the other stems stale.
        parts = {name.rsplit(" (", 1)[0] for name in names}
        trims = sorted((part, TRIM_DB[part]) for part in parts if part in TRIM_DB)
        key = hashlib.sha256(
            f"{RENDER_VERSION}|{profile}|{MASTER_VOLUME_DB}|{trims}|{text}".encode()
        ).hexdigest()
        kept = json.loads(record.read_text(encoding="utf-8")) if record.exists() else {}
        if sound.exists() and kept.get("key") == key:
            print(f"musescore: stem {name}: kept from the last render")
            return name, _load(sound)
        audio, _names = render(work, folder, bars, profile, players=players)
        record.write_text(json.dumps({"key": key, "parts": names}), encoding="utf-8")
        return name, audio

    with ThreadPoolExecutor(max_workers=PARALLEL_RENDERS) as pool:
        results = list(pool.map(one, list(STEMS)))
    return {name: audio for name, audio in results if audio is not None}


def _load(sound: Path) -> np.ndarray:
    """Read the sound of MuseScore, at the level of a master control at 0 dB."""
    audio = reference.load_stereo(sound)
    audio *= np.float32(dsp.db(-MASTER_VOLUME_DB))
    return audio


def narrow(audio: np.ndarray, smallest: float = SMALLEST_CORRELATION) -> tuple[np.ndarray, float]:
    """Make a stem less wide, if its channels are too independent.

    The function changes `audio` in place. It returns the audio and the gain
    of the difference signal in dB (0 = no change).
    """
    sum_power, difference_power = 0.0, 0.0
    step = 60 * dsp.RATE
    for start in range(0, len(audio), step):
        part = audio[start : start + step].astype(np.float64)
        sum_power += float(np.sum(np.square(part[:, 0] + part[:, 1])))
        difference_power += float(np.sum(np.square(part[:, 0] - part[:, 1])))
    if sum_power <= 0.0 or difference_power <= 0.0:
        return audio, 0.0
    correlation = (sum_power - difference_power) / (sum_power + difference_power)
    if correlation >= smallest:
        return audio, 0.0
    wanted = (1.0 - smallest) / (1.0 + smallest)  # difference power / sum power
    gain = float(np.sqrt(wanted * sum_power / difference_power))
    for start in range(0, len(audio), step):
        part = audio[start : start + step]
        middle = 0.5 * (part[:, 0] + part[:, 1])
        side = 0.5 * (part[:, 0] - part[:, 1]) * np.float32(gain)
        part[:, 0] = middle + side
        part[:, 1] = middle - side
    return audio, dsp.to_db(gain)


def equalize(audio: np.ndarray, rows: tuple[tuple, ...] | None = None) -> np.ndarray:
    """Apply the equalization of the mix (`MASTER_EQ`). The function changes `audio`."""
    filters = []
    for kind, frequency, gain_db, *more in MASTER_EQ if rows is None else rows:
        if kind == "bell":
            filters.append(dsp.peaking(frequency, gain_db, *more))
        else:
            filters.append(dsp.shelf(frequency, gain_db, high=kind == "high shelf"))
    for channel in range(audio.shape[1]):
        audio[:, channel] = dsp.apply(audio[:, channel], *filters)
    return audio


def render_parts(
    work: Work, directory: Path, bars: tuple[int, int] | None = None, profile: str = PROFILE
) -> dict[str, np.ndarray]:
    """Return the sound of each group of the mix, at its level in the mix.

    The groups are the stems of MuseScore and the instruments that the
    sampler of this project plays (each is one group, with the name of the
    instrument). All sounds start at the start of the first bar.
    """
    from . import mix

    stems = render_stems(work, directory, bars, profile)
    begin = work.structure.seconds(work.structure.bar(bars[0]).start) if bars else 0.0
    parts: dict[str, np.ndarray] = {}
    for name, audio in stems.items():
        audio, side_db = narrow(audio)
        print(f"musescore: stem {name}: difference signal {side_db:+.1f} dB")
        if name in stemtone.TABLES:
            # The loud marks of this group get their difference again (see `stemtone`).
            level = stemtone.written_level(
                work, stem_players(work, name), begin, len(audio) / dsp.RATE
            )
            stemtone.shape(audio, level, stemtone.TABLES[name])
        if name in stemtone.RIDES:
            audio, largest = stemtone.ride(audio, *stemtone.RIDES[name])
            print(f"musescore: stem {name}: largest slow level change {largest:+.1f} dB")
        parts[name] = np.float32(dsp.db(STEM_GAIN_DB[name])) * audio
    for instrument in sorted(other_instruments(work)):
        sound, count = mix.render_mix(work, bars=bars, instruments={instrument})
        if not count:
            continue
        # The mix of an excerpt starts some time before its first bar.
        lead = int(round(min(begin, mix.SEGMENT_LEAD) * dsp.RATE)) if bars else 0
        gain_db = calibration_gain(work, directory, profile) + SAMPLER_GAIN_DB.get(instrument, 0.0)
        print(f"musescore: sampler: {instrument}, {gain_db:+.1f} dB")
        parts[instrument] = np.float32(dsp.db(gain_db)) * sound[lead:]
    return parts


def render_master(
    work: Work, directory: Path, bars: tuple[int, int] | None = None, profile: str = PROFILE
):
    """Render the master: MuseScore plays, the sampler adds the other instruments."""
    from . import mix

    parts = render_parts(work, directory, bars, profile)
    length = max(len(audio) for audio in parts.values())
    total = np.zeros((length, 2), dtype=np.float32)
    for audio in parts.values():
        total[: len(audio)] += audio
    equalize(total)
    # The soft passages of Muse Sounds are much softer than those of the open
    # samples: the gain riding of the master can do more.
    return mix.master(
        total,
        len(parts),
        full=bars is None,
        tone=False,
        largest_gain_db=RIDING_GAIN_DB,
        largest_ratio=RIDING_RATIO,
        passages=stats.passages(work),
    )
