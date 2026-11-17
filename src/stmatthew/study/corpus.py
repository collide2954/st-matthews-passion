"""Registry of the open data files that the style study measures.

The study does not keep these files in the repository. The `fetch` function
downloads each file into the local cache directory. Each entry records the
source address and the licence of the file.
"""

from __future__ import annotations

import hashlib
import urllib.request
from dataclasses import dataclass
from pathlib import Path

CACHE_DIR = Path(".cache/corpus")
CHECKSUM_FILE = Path("research/corpus.sha256")
USER_AGENT = "stmatthew-study/0.1 (style study script)"


@dataclass(frozen=True)
class CorpusFile:
    """One downloadable data file."""

    key: str
    filename: str
    url: str
    licence: str
    description: str

    @property
    def path(self) -> Path:
        return CACHE_DIR / self.filename


# The open data files of the study. The study of this work adds its entries here.
CORPUS: dict[str, CorpusFile] = {}


def sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_checksums() -> dict[str, str]:
    """Read the recorded SHA-256 digest of each corpus file."""
    digests = {}
    for line in CHECKSUM_FILE.read_text(encoding="utf-8").splitlines():
        digest, _, filename = line.strip().partition("  ")
        if filename:
            digests[filename] = digest
    return digests


def fetch(key: str, *, force: bool = False) -> Path:
    """Download one corpus file into the cache, verify it, and return its path."""
    entry = CORPUS[key]
    if force or not entry.path.exists():
        entry.path.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(entry.url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
        entry.path.write_bytes(data)
    expected = expected_checksums().get(entry.filename)
    actual = sha256(entry.path)
    if expected != actual:
        raise RuntimeError(
            f"{entry.filename}: the file is different from the file that the study measured. "
            f"Expected SHA-256 {expected}, found {actual}. "
            f"Examine the new file. Then update {CHECKSUM_FILE} if the new file is correct."
        )
    return entry.path


def fetch_all(*, force: bool = False) -> list[Path]:
    """Download all corpus files."""
    return [fetch(key, force=force) for key in CORPUS]
