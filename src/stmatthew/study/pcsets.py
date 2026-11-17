"""Pitch-class set tools: normal order, set types, interval vectors, and chord names."""

from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache

PITCH_CLASS_NAMES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")


def _packing_key(rotation: tuple[int, ...]) -> tuple[int, ...]:
    """Return a sort key. A smaller key is a set that is more packed to the left."""
    first = rotation[0]
    spans = [(pc - first) % 12 for pc in rotation]
    return tuple(reversed(spans))


@lru_cache(maxsize=8192)
def _normal_order(pcs: frozenset[int]) -> tuple[int, ...]:
    ordered = sorted(pcs)
    if not ordered:
        return ()
    rotations = [tuple(ordered[i:] + ordered[:i]) for i in range(len(ordered))]
    return min(rotations, key=lambda r: (_packing_key(r), r[0]))


def normal_order(pcs: Iterable[int]) -> tuple[int, ...]:
    """Return the normal order of a pitch-class set (Rahn method)."""
    return _normal_order(frozenset(pc % 12 for pc in pcs))


def tn_type(pcs: Iterable[int]) -> tuple[int, ...]:
    """Return the transposition type: the normal order moved to start on 0."""
    order = normal_order(pcs)
    return tuple((pc - order[0]) % 12 for pc in order) if order else ()


def prime_form(pcs: Iterable[int]) -> tuple[int, ...]:
    """Return the prime form: the more packed of the set type and its inversion."""
    pcs = [pc % 12 for pc in pcs]
    direct = tn_type(pcs)
    inverted = tn_type([-pc % 12 for pc in pcs])
    return min(direct, inverted, key=lambda t: tuple(reversed(t)))


def interval_vector(pcs: Iterable[int]) -> tuple[int, int, int, int, int, int]:
    """Return the interval-class vector of a pitch-class set."""
    unique = sorted({pc % 12 for pc in pcs})
    vector = [0] * 6
    for i, low in enumerate(unique):
        for high in unique[i + 1 :]:
            distance = (high - low) % 12
            vector[min(distance, 12 - distance) - 1] += 1
    return tuple(vector)  # type: ignore[return-value]


def has_semitone(pcs: Iterable[int]) -> bool:
    """Return True if two members of the set are a semitone apart."""
    return interval_vector(pcs)[0] > 0


def has_chromatic_cluster(pcs: Iterable[int]) -> bool:
    """Return True if the set contains three adjacent semitones."""
    unique = {pc % 12 for pc in pcs}
    return any({(pc + 1) % 12, (pc + 2) % 12} <= unique for pc in unique)


# Chord vocabulary. Each chord is given by the semitones above its root.
_CHORDS_BY_ROOT_INTERVALS: dict[str, tuple[int, ...]] = {
    # three notes
    "major triad": (0, 4, 7),
    "minor triad": (0, 3, 7),
    "diminished triad": (0, 3, 6),
    "augmented triad": (0, 4, 8),
    "fourths or fifths trichord (sus)": (0, 5, 7),
    "incomplete dominant seventh": (0, 4, 10),
    "incomplete minor seventh": (0, 3, 10),
    "incomplete major seventh": (0, 4, 11),
    "whole-tone trichord (0 2 4)": (0, 2, 4),
    "semitone cluster (0 1 2)": (0, 1, 2),
    "tritone-fourth trichord (0 1 6)": (0, 1, 6),
    "tritone-fifth trichord (0 5 6)": (0, 5, 6),
    # four notes
    "dominant seventh": (0, 4, 7, 10),
    "half-diminished seventh": (0, 3, 6, 10),
    "diminished seventh": (0, 3, 6, 9),
    "minor seventh": (0, 3, 7, 10),
    "major seventh": (0, 4, 7, 11),
    "minor-major seventh": (0, 3, 7, 11),
    "augmented major seventh": (0, 4, 8, 11),
    "dominant seventh, raised fifth": (0, 4, 8, 10),
    "French sixth (dominant seventh, lowered fifth)": (0, 4, 6, 10),
    "whole-tone tetrachord (0 2 4 6)": (0, 2, 4, 6),
    "major triad, added second": (0, 2, 4, 7),
    "minor triad, added second": (0, 2, 3, 7),
    "fourths tetrachord": (0, 5, 10, 15),
    "semitone cluster (0 1 2 3)": (0, 1, 2, 3),
    # five notes
    "dominant ninth": (0, 4, 7, 10, 14),
    "dominant minor ninth": (0, 4, 7, 10, 13),
    "minor ninth": (0, 3, 7, 10, 14),
    "major ninth": (0, 4, 7, 11, 14),
    "half-diminished ninth": (0, 3, 6, 10, 14),
    "dominant seventh, raised ninth": (0, 4, 7, 10, 15),
    "whole-tone pentachord": (0, 2, 4, 6, 8),
    "pentatonic set": (0, 2, 4, 7, 9),
    # six notes
    "whole-tone scale": (0, 2, 4, 6, 8, 10),
}

CHORD_NAMES: dict[tuple[int, ...], str] = {}
for _name, _intervals in _CHORDS_BY_ROOT_INTERVALS.items():
    CHORD_NAMES.setdefault(tn_type(_intervals), _name)

INTERVAL_NAMES = {
    0: "unison or octave",
    1: "semitone or major seventh",
    2: "whole tone or minor seventh",
    3: "minor third or major sixth",
    4: "major third or minor sixth",
    5: "fourth or fifth",
    6: "tritone",
}

TERTIAN = {
    "major triad",
    "minor triad",
    "diminished triad",
    "augmented triad",
    "incomplete dominant seventh",
    "incomplete minor seventh",
    "incomplete major seventh",
    "dominant seventh",
    "half-diminished seventh",
    "diminished seventh",
    "minor seventh",
    "major seventh",
    "minor-major seventh",
    "augmented major seventh",
    "dominant seventh, raised fifth",
    "French sixth (dominant seventh, lowered fifth)",
    "dominant ninth",
    "dominant minor ninth",
    "minor ninth",
    "major ninth",
    "half-diminished ninth",
    "dominant seventh, raised ninth",
}


# Chord families for the style comparison. "Vagrant" is Schoenberg's word for
# chords that do not belong to one key.
CHORD_FAMILIES: dict[str, set[str]] = {
    "major and minor triads": {"major triad", "minor triad"},
    "vagrant chords": {
        "diminished triad",
        "augmented triad",
        "diminished seventh",
        "half-diminished seventh",
        "half-diminished ninth",
        "French sixth (dominant seventh, lowered fifth)",
        "dominant seventh, raised fifth",
        "whole-tone trichord (0 2 4)",
        "whole-tone tetrachord (0 2 4 6)",
        "whole-tone pentachord",
        "whole-tone scale",
    },
    "dominant chords": {
        "dominant seventh",
        "incomplete dominant seventh",
        "dominant ninth",
        "dominant minor ninth",
        "dominant seventh, raised ninth",
    },
    "other seventh and ninth chords": {
        "minor seventh",
        "major seventh",
        "minor-major seventh",
        "augmented major seventh",
        "incomplete minor seventh",
        "incomplete major seventh",
        "minor ninth",
        "major ninth",
    },
}


def chord_family(name: str) -> str | None:
    """Return the chord family of a chord name, or None."""
    for family, members in CHORD_FAMILIES.items():
        if name in members:
            return family
    return None


def chord_name(pcs: Iterable[int]) -> str:
    """Return a name for a pitch-class set.

    A set with one member is a "single pitch class". A set with two members has
    the name of its interval class. A larger set has a chord name if the
    vocabulary contains it. If not, the name shows the set type.
    """
    unique = {pc % 12 for pc in pcs}
    if not unique:
        return "silence"
    if len(unique) == 1:
        return "single pitch class"
    kind = tn_type(unique)
    if len(unique) == 2:
        distance = kind[1]
        return f"interval: {INTERVAL_NAMES[min(distance, 12 - distance)]}"
    if kind in CHORD_NAMES:
        return CHORD_NAMES[kind]
    return "set type (" + " ".join(str(pc) for pc in kind) + ")"


def is_tertian(name: str) -> bool:
    """Return True if a chord name is a chord built from thirds."""
    return name in TERTIAN
