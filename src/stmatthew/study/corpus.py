"""Registry of the open data files that the style study measures.

The study does not keep these files in the repository. The `fetch` function
downloads each file into the local cache directory. Each entry records the
source address and the licence of the file.

The files are data: Humdrum kern text, MIDI, and the text of LilyPond sources.
The study reads them. It does not run a program on them.
"""

from __future__ import annotations

import hashlib
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

CACHE_DIR = Path(".cache/corpus")
CHECKSUM_FILE = Path("research/corpus.sha256")
USER_AGENT = "stmatthew-study/0.1 (style study script)"


@dataclass(frozen=True)
class CorpusFile:
    """One downloadable data file."""

    key: str
    filename: str  # the path in the cache directory
    url: str
    licence: str
    description: str

    @property
    def path(self) -> Path:
        return CACHE_DIR / self.filename


# ----------------------------------------------------------------------------
# The four-part chorales of Bach (Humdrum kern)
# ----------------------------------------------------------------------------

# The address has a fixed commit, thus the data cannot change.
CHORALES_COMMIT = "a95574f9e93b4d72a96cd390a059df4f8471ddb6"
CHORALES_BASE = (
    f"https://raw.githubusercontent.com/craigsapp/bach-370-chorales/{CHORALES_COMMIT}/kern/"
)
# The edition has the numbers 1 to 371 of Breitkopf & Härtel. The number 150 is not in it.
CHORALE_NUMBERS = [number for number in range(1, 372) if number != 150]

# The chorale settings of the St Matthew Passion in this edition: the number of the
# edition, the number of the movement (Neue Bach-Ausgabe), and the tune.
PASSION_CHORALES: dict[int, tuple[str, str]] = {
    78: ("3", "Herzliebster Jesu"),
    117: ("10", "O Welt, ich muss dich lassen"),
    98: ("15 and 17", "Herzlich tut mich verlangen"),
    115: ("25", "Was mein Gott will, das g'scheh allzeit"),
    118: ("32", "In dich hab ich gehoffet, Herr"),
    50: ("37", "O Welt, ich muss dich lassen"),
    121: ("40", "Werde munter, mein Gemüte"),
    80: ("44", "Herzlich tut mich verlangen"),
    105: ("46", "Herzliebster Jesu"),
    74: ("54", "Herzlich tut mich verlangen"),
    89: ("62", "Herzlich tut mich verlangen"),
}


# ----------------------------------------------------------------------------
# Movements of the Passion and of related works (MIDI, and LilyPond text)
# ----------------------------------------------------------------------------

MOVEMENTS_BASE = "https://www.victoria.uma.es/varios/"


@dataclass(frozen=True)
class MovementInfo:
    """One movement of the corpus.

    `roles` gives the line of each track of the MIDI file. A role is
    "voice: alto", "solo: violin", "strings: viola", "winds: flute 1",
    "continuo", or "other" (a line that the study does not measure alone).
    """

    stem: str
    work: str
    title: str
    roles: tuple[str, ...]
    figures: bool = False  # the LilyPond source has a figured bass
    tags: tuple[str, ...] = field(default_factory=tuple)


SATB = ("choir: soprano", "choir: alto", "choir: tenor", "choir: bass")

MOVEMENTS: dict[str, MovementInfo] = {
    info.stem: info
    for info in [
        MovementInfo(
            "Bach-244-Erbarme_Dich",
            "St Matthew Passion",
            "39. Erbarme dich (aria, alto)",
            (
                "voice: alto",
                "solo: violin",
                "strings: violin 1",
                "strings: violin 2",
                "strings: viola",
                "continuo",
            ),
            figures=True,
            tags=("passion", "aria"),
        ),
        MovementInfo(
            "Bach-244-Konnen_Tranen",
            "St Matthew Passion",
            "52. Können Tränen meiner Wangen (aria, alto)",
            ("voice: alto", "strings: violins", "continuo"),
            figures=True,
            tags=("passion", "aria"),
        ),
        MovementInfo(
            "Bach-244-Aus_Liebe",
            "St Matthew Passion",
            "49. Aus Liebe will mein Heiland sterben (aria, soprano)",
            ("voice: soprano", "solo: flute", "winds: oboe da caccia 1", "winds: oboe da caccia 2"),
            tags=("passion", "aria"),
        ),
        MovementInfo(
            "Bach-244-Blute_Nur",
            "St Matthew Passion",
            "8. Blute nur, du liebes Herz (aria, soprano)",
            (
                "voice: soprano",
                "winds: flute 1",
                "winds: flute 2",
                "strings: violin 1",
                "strings: violin 2",
                "strings: viola",
                "continuo",
            ),
            figures=True,
            tags=("passion", "aria"),
        ),
        MovementInfo(
            "Bach-244-Mache_Dich",
            "St Matthew Passion",
            "65. Mache dich, mein Herze, rein (aria, bass)",
            ("voice: bass", "strings: violin 1", "strings: violin 2", "strings: viola", "continuo"),
            figures=True,
            tags=("passion", "aria"),
        ),
        MovementInfo(
            "Bach-244-O_Mensch",
            "St Matthew Passion",
            "29. O Mensch, bewein dein Sünde groß (chorale fantasia)",
            (
                *SATB,
                "winds: flute 1",
                "winds: flute 2",
                "strings: violin 1",
                "strings: violin 2",
                "strings: viola",
                "continuo",
            ),
            figures=True,
            tags=("passion", "chorus"),
        ),
        MovementInfo(
            "Bach-244-Wir_Setzen_Uns-orquesta",
            "St Matthew Passion",
            "68. Wir setzen uns mit Tränen nieder (chorus)",
            (
                "strings: violin 1",
                "strings: violin 2",
                "strings: viola",
                *SATB,
                "continuo",
                "strings: violin 1",
                "strings: violin 2",
                "strings: viola",
                *SATB,
                "continuo",
            ),
            figures=True,
            tags=("passion", "chorus"),
        ),
        MovementInfo(
            "Bach-232-Crucifixus",
            "Mass in B minor",
            "Crucifixus (chorus on a ground bass)",
            (
                *SATB,
                "winds: flute 1",
                "winds: flute 2",
                "strings: violin 1",
                "strings: violin 2",
                "strings: viola",
                "continuo",
            ),
            tags=("chorus",),
        ),
        MovementInfo(
            "Bach-232-Qui_Tollis",
            "Mass in B minor",
            "Qui tollis peccata mundi (chorus)",
            (
                *SATB,
                "winds: flute 1",
                "winds: flute 2",
                "strings: violin 1",
                "strings: violin 2",
                "strings: viola",
                "strings: violoncello",
                "continuo",
            ),
            figures=True,
            tags=("chorus",),
        ),
        MovementInfo(
            "Bach-243-Et_Misericordia",
            "Magnificat",
            "Et misericordia (duet, alto and tenor)",
            (
                "voice: alto",
                "voice: tenor",
                "strings: violin 1",
                "strings: violin 2",
                "strings: viola",
                "continuo",
            ),
            figures=True,
            tags=("aria",),
        ),
        MovementInfo(
            "Bach-245-Ach_Mein_Sinn",
            "St John Passion",
            "13. Ach, mein Sinn (aria, tenor)",
            (
                "voice: tenor",
                "strings: violin 1",
                "strings: violin 2",
                "strings: viola",
                "continuo",
            ),
            tags=("passion", "aria"),
        ),
        MovementInfo(
            "Bach-245-Herr_Unser_Herrscher",
            "St John Passion",
            "1. Herr, unser Herrscher (chorus)",
            (
                "winds: flute 1",
                "winds: flute 2",
                "strings: violin 1",
                "strings: violin 2",
                "strings: viola",
                *SATB,
                "continuo",
            ),
            tags=("passion", "chorus"),
        ),
        MovementInfo(
            "Bach-198-Lass_Furstin",
            "Trauerode, BWV 198",
            "1. Lass, Fürstin, lass noch einen Strahl (chorus)",
            (
                *SATB,
                "winds: flute 1",
                "winds: flute 2",
                "winds: oboe d'amore 1",
                "winds: oboe d'amore 2",
                "strings: violin 1",
                "strings: violin 2",
                "strings: viola",
                "strings: viola da gamba 1",
                "strings: viola da gamba 2",
                "continuo",
            ),
            figures=True,
            tags=("chorus",),
        ),
        MovementInfo(
            "Bach-198-Der_Ewigkeit",
            "Trauerode, BWV 198",
            "8. Der Ewigkeit saphirnes Haus (aria, tenor)",
            (
                "voice: tenor",
                "solo: flute",
                "solo: oboe d'amore",
                "strings: violin 1",
                "strings: violin 2",
                "strings: violas da gamba",
                "continuo",
            ),
            tags=("aria",),
        ),
    ]
}


def _entries() -> list[CorpusFile]:
    entries = [
        CorpusFile(
            key=f"chorale-{number:03d}",
            filename=f"chorales/chor{number:03d}.krn",
            url=f"{CHORALES_BASE}chor{number:03d}.krn",
            licence="CC BY-NC-SA 4.0",
            description=(
                f"J. S. Bach, four-part chorale no. {number} of the edition of Breitkopf & "
                "Härtel. Humdrum kern file, edited by Craig Stuart Sapp."
            ),
        )
        for number in CHORALE_NUMBERS
    ]
    for info in MOVEMENTS.values():
        entries.append(
            CorpusFile(
                key=f"movement-{info.stem}",
                filename=f"movements/{info.stem}.mid",
                url=f"{MOVEMENTS_BASE}mid/{info.stem}.mid",
                licence="No licence statement. Edition by Nancho Alvarez.",
                description=f"J. S. Bach, {info.work}: {info.title}. MIDI file of the edition.",
            )
        )
        if info.figures:
            source = info.stem.removesuffix("-orquesta")
            entries.append(
                CorpusFile(
                    key=f"figures-{info.stem}",
                    filename=f"sources/{source}.ly",
                    url=f"{MOVEMENTS_BASE}ly/{source}.ly",
                    licence="No licence statement. Edition by Nancho Alvarez.",
                    description=(
                        f"J. S. Bach, {info.work}: {info.title}. Text source of the edition; "
                        "the study reads the figures of the figured bass."
                    ),
                )
            )
    return entries


CORPUS: dict[str, CorpusFile] = {entry.key: entry for entry in _entries()}


def sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_checksums() -> dict[str, str]:
    """Read the recorded SHA-256 digest of each corpus file."""
    digests = {}
    if not CHECKSUM_FILE.exists():
        return digests
    for line in CHECKSUM_FILE.read_text(encoding="utf-8").splitlines():
        digest, _, filename = line.strip().partition("  ")
        if filename:
            digests[filename] = digest
    return digests


def write_checksums() -> Path:
    """Record the SHA-256 digest of each file of the cache. Use it after a first download."""
    lines = [f"{sha256(entry.path)}  {entry.filename}" for entry in CORPUS.values()]
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHECKSUM_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return CHECKSUM_FILE


def fetch(key: str, *, force: bool = False, expected: dict[str, str] | None = None) -> Path:
    """Download one corpus file into the cache, verify it, and return its path."""
    entry = CORPUS[key]
    if force or not entry.path.exists():
        entry.path.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(entry.url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
        entry.path.write_bytes(data)
        time.sleep(0.05)  # the servers are small: do not ask too fast
    if expected is None:
        expected = expected_checksums()
    wanted = expected.get(entry.filename)
    actual = sha256(entry.path)
    if wanted is not None and wanted != actual:
        raise RuntimeError(
            f"{entry.filename}: the file is different from the file that the study measured. "
            f"Expected SHA-256 {wanted}, found {actual}. "
            f"Examine the new file. Then update {CHECKSUM_FILE} if the new file is correct."
        )
    return entry.path


def fetch_all(*, force: bool = False) -> list[Path]:
    """Download all corpus files."""
    expected = expected_checksums()
    return [fetch(key, force=force, expected=expected) for key in CORPUS]
