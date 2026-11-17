"""Keep the audio master of the MuseScore source in a GitHub release.

A build server cannot make this master: it cannot install Muse Sounds. The
computer of the owner makes the master and puts it in the release `audio`.
The build server gets the master from that release, if the master is for
the music of the present commit. If not, the build server makes the audio
with the open sample libraries.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from .notation import music
from .notation.work import Work

TAG = "audio"
FILES = ("st-matthews-passion.flac", "st-matthews-passion.mp3")
RECORD = "audio.json"
NOTES = (
    "The audio master of the work, made with MuseScore Studio and Muse Sounds. "
    "A build server cannot make this file. The builds of the repository use it."
)


def music_key(work: Work) -> str:
    """Return a checksum of all notes and of the tempo plan of the work."""
    digest = hashlib.sha256()
    for player in work.orchestra.players:
        digest.update(player.id.encode())
        digest.update(music.body_to_lilypond(work.music_of(player.id)).encode())
    for point in work.structure.tempo_points:
        digest.update(f"{point.position}|{point.bpm}|{point.glide}".encode())
    for bar in work.structure.bars:
        digest.update(f"{bar.numerator}/{bar.denominator}".encode())
    return digest.hexdigest()


def _gh(arguments: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *arguments], capture_output=True, text=True, check=check)


def publish(work: Work, directory: Path, source: str) -> None:
    """Put the audio master of `directory` in the release, with the checksum of the music."""
    record = directory / RECORD
    record.write_text(
        json.dumps({"music": music_key(work), "source": source}, indent=2) + "\n",
        encoding="utf-8",
    )
    if _gh(["release", "view", TAG], check=False).returncode != 0:
        _gh(["release", "create", TAG, "--title", "Audio master", "--notes", NOTES,
             "--latest=false"])  # fmt: skip
    files = [str(directory / name) for name in (*FILES, RECORD)]
    _gh(["release", "upload", TAG, *files, "--clobber"])


def fetch(work: Work, directory: Path) -> bool:
    """Get the audio master from the release. Return false if it is not for this music."""
    directory.mkdir(parents=True, exist_ok=True)
    result = _gh(
        ["release", "download", TAG, "--pattern", RECORD, "--dir", str(directory), "--clobber"],
        check=False,
    )
    record = directory / RECORD
    if result.returncode != 0 or not record.exists():
        print("fetch-audio: the release has no audio master")
        return False
    if json.loads(record.read_text(encoding="utf-8")).get("music") != music_key(work):
        print("fetch-audio: the audio master of the release is for different music")
        return False
    for name in FILES:
        _gh(["release", "download", TAG, "--pattern", name, "--dir", str(directory), "--clobber"])
    print(f"fetch-audio: got the audio master from the release '{TAG}'")
    return True
