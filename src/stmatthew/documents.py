"""Keep the numbers in the documents the same as the numbers of the music.

The documents have tables with bar numbers, times, and measured values.
These values change when the music changes. This module calculates the
values from the work and writes them into the tables. A test makes sure
that the documents are up to date.

The text of the documents stays as the writer wrote it. The module changes
only these items:

- `docs/work.md`: the length, the columns "Bars", "Time", and "Share" of the
  form table, and the column "The work" of the tables of proportions and
  targets.
- `README.md`: the length, the columns "Bars" and "Start" of the table of
  the parts, the times of the climaxes, and the number of bars.
- The style study: the measured tables of the new work
  (`research/measured/work_*.csv`) and the report `docs/style-study.md`.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from .compose.stats import Stats, measure
from .notation.work import Work

ROOT = Path(__file__).resolve().parents[2]
FILES = (ROOT / "docs" / "work.md", ROOT / "README.md")

# The first rehearsal mark of each part. Part 1 starts before the first mark.
PART_MARKS = {"1": "", "2": "D", "3": "S", "4": "AA", "5": "GG"}
# The events of the form plan: the first bar and, for an event with a length, the bar
# after it. "KK+11" is bar 12 of the section at the mark KK.
EVENTS = {
    "First climax": ("Q", "R"),
    "Start of part 3": ("S", ""),
    "Point most distant from the tonic": ("U", "V"),
    "Turn to D major": ("AA", ""),
    "Main climax": ("EE", "FF"),
    "Start of part 5": ("GG", ""),
    "Last arrival on the tonic": ("KK+11", ""),
}
TARGETS: dict[str, Callable[[Stats], str]] = {
    "Share of the time: p or softer": lambda stats: f"{stats.share_p_or_softer:.2f}",
    "Share of the time: mp or mf": lambda stats: f"{stats.share_mp_or_mf:.2f}",
    "Share of the time: f or louder": lambda stats: f"{stats.share_f_or_louder:.2f}",
    "Bars for each tempo mark": lambda stats: f"{stats.bars_for_each_tempo_mark:.1f}",
}


def clock(seconds: float) -> str:
    """Return a time as minutes and seconds, for example "7:33"."""
    whole = int(seconds)
    return f"{whole // 60}:{whole % 60:02d}"


def sections(work: Work) -> dict[str, tuple[int, int]]:
    """Return the first and the last bar of the section at each rehearsal mark.

    The key "" is the section before the first mark.
    """
    marks = sorted(work.structure.marks.items())
    last_bar = len(work.structure.bars)
    result: dict[str, tuple[int, int]] = {}
    if marks and marks[0][0] > 1:
        result[""] = (1, marks[0][0] - 1)
    for index, (number, label) in enumerate(marks):
        end = marks[index + 1][0] - 1 if index + 1 < len(marks) else last_bar
        result[label] = (number, end)
    return result


def _bar(work: Work, place: str) -> int:
    """Return the bar number of a place such as "Q" or "KK+11"."""
    label, _, more = place.partition("+")
    return sections(work)[label][0] + int(more or 0)


def _seconds(work: Work, bar: int) -> float:
    structure = work.structure
    return structure.seconds(structure.bar(bar).start)


def _share(work: Work, bar: int) -> str:
    """Return the position of a bar as a part of the length of the work."""
    return f"{_seconds(work, bar) / work.structure.duration_seconds:.3f}"


def _change_table(text: str, header: str, change: Callable[[list[str]], None]) -> str:
    """Apply `change` to the cells of each row of the table that starts with `header`.

    `change` gets the cells of one row, with no spaces around them. The first
    cell is the text before the first bar character: it is empty.
    """
    lines = text.split("\n")
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith(header))
    except StopIteration:
        raise ValueError(f"no table with the header {header!r}") from None
    for index in range(start + 2, len(lines)):
        if not lines[index].startswith("|"):
            break
        cells = [cell.strip() for cell in lines[index].split("|")]
        change(cells)
        line = "| " + " | ".join(cells[1:-1]) + " |"
        lines[index] = re.sub(r"\|  (?=\|)", "| ", line)  # an empty cell is one space
    return "\n".join(lines)


def _replace(text: str, pattern: str, new: str) -> str:
    """Replace the one text that agrees with `pattern`."""
    result, count = re.subn(pattern, new, text)
    if count != 1:
        raise ValueError(f"{count} places agree with {pattern!r}")
    return result


def update_work_document(text: str, work: Work, stats: Stats) -> str:
    """Return the text of `docs/work.md` with the numbers of the work."""
    parts = sections(work)

    def form_row(cells: list[str]) -> None:
        first, last = parts[cells[2]]
        cells[3] = f"{first} to {last}"
        cells[4] = clock(_seconds(work, first))
        cells[5] = _share(work, first)

    def event_row(cells: list[str]) -> None:
        first, after = EVENTS[cells[1]]
        cells[3] = _share(work, _bar(work, first))
        if after:
            cells[3] += " to " + _share(work, _bar(work, after))

    def target_row(cells: list[str]) -> None:
        cells[3] = TARGETS[cells[1]](stats)

    text = _replace(
        text,
        r"\| Length \| \d+ bars, [\d.]+ minutes \|",
        f"| Length | {stats.bars} bars, {stats.minutes:.1f} minutes |",
    )
    text = _change_table(text, "| Part | Mark | Bars | Time | Share |", form_row)
    text = _change_table(text, "| Event | Plan (share of the time) | The work |", event_row)
    return _change_table(text, "| Value | Target | The work |", target_row)


def update_readme(text: str, work: Work, stats: Stats) -> str:
    """Return the text of `README.md` with the numbers of the work."""
    parts = sections(work)
    firsts = {part: parts[mark][0] for part, mark in PART_MARKS.items()}

    def part_row(cells: list[str]) -> None:
        first = firsts[cells[1]]
        later = [bar for bar in firsts.values() if bar > first]
        cells[2] = f"{first} to {min(later) - 1 if later else stats.bars}"
        cells[3] = clock(_seconds(work, first))

    def minute(place: str) -> int:
        return round(_seconds(work, _bar(work, place)) / 60)

    text = _replace(
        text,
        r"five linked parts, \d+ minutes",
        f"five linked parts, {round(stats.minutes)} minutes",
    )
    text = _replace(
        text,
        r"The two climaxes are at \d+ minutes and at \d+ minutes\.\n?"
        r" ?The last statement starts at \d+ minutes\.",
        f"The two climaxes are at {minute('Q')} minutes and at {minute('EE')} minutes. "
        f"The last statement starts at {minute('KK')} minutes.",
    )
    text = _replace(text, r"complete \(\d+ bars\)", f"complete ({stats.bars} bars)")
    return _change_table(text, "| Part | Bars | Start | Contents |", part_row)


def update(path: Path, text: str, work: Work, stats: Stats) -> str:
    """Return the text of one document with the numbers of the work."""
    if path.name == "README.md":
        return update_readme(text, work, stats)
    return update_work_document(text, work, stats)


def update_study(work: Work) -> list[Path]:
    """Measure the work for the style study and write the report. Return the files that changed.

    The study code uses paths from the root of the repository: start the
    command there.
    """
    from .study import report, workcheck

    names = ["work_repetition.csv", "work_harmony.csv", "work_instruments.csv", "work_unused.csv"]
    paths = [workcheck.OUTPUT_DIR / name for name in names] + [report.REPORT_PATH]
    before = {path: path.read_bytes() if path.exists() else b"" for path in paths}
    workcheck.write_tables(work)
    report.write()
    return [path for path in paths if path.read_bytes() != before[path]]


def update_files(work: Work) -> list[Path]:
    """Write the numbers of the work into the documents. Return the files that changed."""
    stats = measure(work)
    changed = []
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        new = update(path, text, work, stats)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(path)
    return changed + update_study(work)
