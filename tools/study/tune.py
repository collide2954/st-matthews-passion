"""Print a line of a chorale of the corpus in the music language of the project.

Usage:

    uv run python tools/study/tune.py WORDS [VOICE]

WORDS is a part of the title or of the catalogue number, for example "O Lamm Gottes"
or "244/54". VOICE is 3 for the soprano (the default), 2 for the alto, 1 for the tenor,
and 0 for the bass. The corpus must be in the cache (`uv run stmatthew-study fetch`).
"""

from __future__ import annotations

import sys

from stmatthew.study import corpus, measure, readers


def main(words: str, voice: int = 3) -> None:
    for number in corpus.CHORALE_NUMBERS:
        chorale = readers.read_kern(corpus.CORPUS[f"chorale-{number:03d}"].path)
        if words.lower() not in f"{chorale.title} {chorale.catalogue}".lower():
            continue
        key = measure.key_name(chorale.tonic, chorale.minor)
        print(f"# {number}: {chorale.title} ({chorale.catalogue}), {key}, {chorale.metre}")
        phrase = []
        for note in chorale.voice(voice):
            phrase.append(note)
            if note.fermata:
                print(measure.to_lilypond(phrase))
                phrase = []
        if phrase:
            print(measure.to_lilypond(phrase))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 3)
