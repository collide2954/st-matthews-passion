"""The work: a new setting of the St Matthew Passion, written as code."""

from __future__ import annotations

from ..notation.work import Work, load_orchestra

TITLE = "St Matthew Passion"
SUBTITLE = "after J. S. Bach, BWV 244, for alto and baroque orchestra"
COMPOSER = "Brett Gilio"


def build() -> Work:
    """Build the full work from its parts.

    The music is not written yet. These four bars are a placeholder: with
    them, the build commands and the tests of the engine operate.
    """
    work = Work(TITLE, load_orchestra(), composer=COMPOSER, subtitle=SUBTITLE)
    section = work.section(4, 12, 8)
    work.structure.tempo(section.bar(1), 1, 54, "Largo", unit="4.")
    section.write("vc", r"e,8\p e, e, e, e, e, e, e, e, e, e, e, | e,1. ~ | e,1. ~ | e,1. |")
    section.write("vne", r"e,1.\p ~ | e,1. ~ | e,1. ~ | e,1. |")
    section.write("va", r"R1. | b4.\p( c'4 b8 a4. b4.) | g2. ~ g4. r4. | R1. |")
    section.close()
    work.check_complete()
    return work
