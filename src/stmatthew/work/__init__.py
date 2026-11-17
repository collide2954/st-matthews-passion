"""The work: a new setting of the St Matthew Passion, written as code.

Each number of the work is one module. The numbers that are written are in the
list `NUMBERS`, in the sequence of the performance. The plan of all 16 numbers
is in `design/form.toml`.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..notation.work import Work, load_orchestra
from . import n06, n14

TITLE = "St Matthew Passion"
SUBTITLE = "after J. S. Bach, BWV 244, for alto and baroque orchestra"
COMPOSER = "Brett Gilio"

# The numbers that are written: the number, and the module that writes it.
NUMBERS = {6: n06, 14: n14}


def build(only: Iterable[int] | None = None) -> Work:
    """Build the work from the numbers that are written.

    `only` selects some numbers (for a preview of one number).
    """
    work = Work(TITLE, load_orchestra(), composer=COMPOSER, subtitle=SUBTITLE)
    chosen = set(only) if only is not None else set(NUMBERS)
    for number, module in sorted(NUMBERS.items()):
        if number in chosen:
            module.write(work)
    work.check_complete()
    return work
