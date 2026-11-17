"""Print the lines of a chorale of the corpus in the music language of the project.

Usage:

    uv run python tools/study/tune.py WORDS [SEMITONES STEPS]

WORDS is a part of the title or of the catalogue number, for example "O Lamm Gottes"
or "244/54". The script prints the four voices (soprano, alto, tenor, bass), one
phrase of the soprano for each line. SEMITONES and STEPS move the music to a
different key: "1 1" is one minor second up, "-7 -4" is one fifth down.
The corpus must be in the cache (`uv run stmatthew-study fetch`).
"""

from __future__ import annotations

import sys

from stmatthew.compose.tools import tr
from stmatthew.study import corpus, measure, readers

VOICES = {3: "soprano", 2: "alto", 1: "tenor", 0: "bass"}


def main(words: str, semitones: int = 0, steps: int = 0) -> None:
    for number in corpus.CHORALE_NUMBERS:
        chorale = readers.read_kern(corpus.CORPUS[f"chorale-{number:03d}"].path)
        if words.lower() not in f"{chorale.title} {chorale.catalogue}".lower():
            continue
        key = measure.key_name(chorale.tonic, chorale.minor)
        print(f"# {number}: {chorale.title} ({chorale.catalogue}), {key}, {chorale.metre}")
        # The ends of the phrases: the ends of the soprano notes with a fermata.
        ends = [note.end for note in chorale.voice(3) if note.fermata]
        for voice, name in VOICES.items():
            print(f"## {name}")
            notes = chorale.voice(voice)
            start = 0
            for end in ends:
                phrase = [note for note in notes if start <= note.start < end]
                start = end
                text = measure.to_lilypond(phrase)
                print(tr(text, semitones, steps) if semitones else text)


if __name__ == "__main__":
    shift = [int(value) for value in sys.argv[2:4]] if len(sys.argv) > 3 else []
    main(sys.argv[1], *shift)
