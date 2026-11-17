"""The pages before the music: cover, imprint, instrumentation, stage plan, notes.

The guidelines of the orchestra librarians (see `research/tables/engraving.csv`)
give the contents of these pages:

- A cover with the title and the composer.
- The full instrumentation: the instruments of each player, the keys of the
  transposing instruments, each percussion instrument with its range, and the
  number of the string players.
- The duration, the notes for the performance, and a plan of the stage.
- A programme note.

Each function returns LilyPond markup for one page. All sizes are absolute
(points and millimetres): thus a page looks the same in the score and in a
part, which have different staff sizes.
"""

from __future__ import annotations

from dataclasses import dataclass

from .pitch import Pitch, from_midi
from .work import Work

POINT_MM = 0.3528  # one point in millimetres
LICENCE = "Creative Commons Attribution 4.0 International (CC BY 4.0)"
SOURCE = "github.com/collide2954/st-matthews-passion"
YEAR = 2026
# Percussion instruments with a pitch: the list of the instruments gives their range.
TUNED = (
    "timpani", "glockenspiel", "crotales", "xylophone", "vibraphone", "marimba",
    "tubular bells", "tuned gongs",
)  # fmt: skip
FAMILY_TITLES = {
    "woodwinds": "Woodwinds",
    "brass": "Brass",
    "percussion": "Timpani and percussion",
    "plucked": "Harp and plucked instruments",
    "keyboards": "Keyboards",
    "strings": "Strings",
}
TOP_SHARE = 0.025  # the empty space above the heading of a text page, as a share of the page
STRING_NAMES = {
    "vn1": "First violins", "vn2": "Second violins", "va": "Violas", "vc": "Cellos",
    "cb": "Double basses",
}  # fmt: skip


@dataclass(frozen=True)
class Page:
    """The size of a page and of its staff: the base of all lengths in the markup."""

    width_mm: float
    height_mm: float
    staff_size: float  # in points
    margin_mm: float = 24.0

    @property
    def space_mm(self) -> float:
        """Return one staff space: the unit of the lengths in LilyPond markup."""
        return self.staff_size * POINT_MM / 4.0

    def units(self, millimetres: float) -> float:
        return millimetres / self.space_mm

    def points(self, size: float) -> float:
        """Return a type size for this page. The sizes in the code are for an A4 page."""
        return round(size * (self.width_mm / 210.0) ** 0.8, 1)

    @property
    def text_width(self) -> float:
        """Return the width of the text area in staff spaces."""
        return self.units(self.width_mm - 2.0 * self.margin_mm)

    def skip(self, millimetres: float) -> str:
        """Return an empty vertical space (LilyPond multiplies the number by 3)."""
        return rf"\vspace #{self.units(millimetres) / 3.0:.2f}"


def copyright_line(work: Work) -> str:
    """Return the copyright notice for the first page of music."""
    return f"Copyright {YEAR} by {work.composer}. Licence: CC BY 4.0."


def quote(text: str) -> str:
    """Return a text as a LilyPond string."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def words(text: str) -> str:
    """Return a text as a sequence of LilyPond strings: LilyPond can then break the line."""
    return " ".join(quote(word) for word in text.split())


def spaced(text: str, gap: float = 0.35) -> str:
    """Return a text with more space between its letters (for a line of capital letters)."""
    letters = [quote(letter) if letter != " " else rf"\hspace #{4 * gap:.2f}" for letter in text]
    return r"\concat { " + rf" \hspace #{gap:.2f} ".join(letters) + " }"


def line(page: Page, text: str, size: float, style: str = "") -> str:
    """Return one line of text in the middle of the page."""
    return rf"\fill-line {{ \abs-fontsize #{page.points(size):g} {style} {text} }}"


def block(page: Page, text: str, size: float, width: float, kind: str = "wordwrap") -> str:
    """Return a text that LilyPond breaks into lines of a width (in staff spaces).

    The distance of the lines is 1.4 times the type size. LilyPond changes the
    line distance together with the size: thus the code sets it after the size.
    """
    points = page.points(size)
    skip = page.units(points * POINT_MM * 1.4)
    return (
        rf"\abs-fontsize #{points:g} \override #'(baseline-skip . {skip:.2f}) "
        rf"\override #'(line-width . {width:.1f}) \{kind} {{ {words(text)} }}"
    )


def paragraph(page: Page, text: str, size: float = 10.5) -> str:
    """Return a paragraph: the lines have the width of the text area."""
    return block(page, text, size, page.text_width, "justify")


def label(page: Page, text: str, size: float = 10.5, style: str = "") -> str:
    return rf"\line {{ \abs-fontsize #{page.points(size):g} {style} {quote(text)} }}"


def heading(page: Page, text: str, size: float = 20.0) -> str:
    return label(page, text, size, r"\bold")


def rule(page: Page, length_mm: float, thickness: float = 0.12) -> str:
    """Return a thin horizontal line in the middle of the page."""
    return (
        rf"\fill-line {{ \override #'(thickness . {thickness / 0.1:.1f}) "
        rf"\draw-line #'({page.units(length_mm):.1f} . 0) }}"
    )


def row(page: Page, cells: list[tuple[str, float, str]], size: float = 10.5) -> str:
    """Return one row of a table: each cell has a text, a width in millimetres, and a style.

    The last cell gets the rest of the width, and its text can have more than one line.
    """
    points = page.points(size)
    parts = []
    used = 0.0
    for text, width_mm, style in cells[:-1]:
        width = page.units(width_mm)
        used += width
        parts.append(
            rf"\override #'(line-width . {width:.1f}) \abs-fontsize #{points:g} {style} "
            rf"\fill-line {{ {quote(text)} \null }}"
        )
    last_text, _width, last_style = cells[-1]
    parts.append(
        block(page, last_text, size, page.text_width - used).replace(
            rf"\abs-fontsize #{points:g}", rf"\abs-fontsize #{points:g} {last_style}", 1
        )
    )
    return r"\line { " + " ".join(parts) + " }"


def _page(page: Page, lines: list[str]) -> str:
    """Return one page of markup. The text area has the margins of the page."""
    body = "\n  ".join(lines)
    return (
        rf"\markup \override #'(line-width . {page.text_width:.1f}) "
        rf"\column {{" + "\n  " + body + "\n}"
    )


# ----------------------------------------------------------------------------- cover


def cover(work: Work, page: Page, edition: str) -> str:
    """Return the cover: the composer, the title, and the type of the document."""
    title, _, rest = work.title.partition(" for ")
    lines = [
        page.skip(0.15 * page.height_mm),
        line(page, spaced(work.composer.upper()), 13.5),
        page.skip(0.050 * page.height_mm),
        line(page, quote(title), 46),
        page.skip(0.012 * page.height_mm),
        line(page, quote("for " + rest), 21.5, r"\italic") if rest else "",
        page.skip(0.050 * page.height_mm),
        rule(page, 46.0),
        page.skip(0.050 * page.height_mm),
        line(page, spaced(edition.upper(), 0.3), 10.5),
        page.skip(0.22 * page.height_mm),
        line(page, quote(str(YEAR)), 10.5),
    ]
    return _page(page, [text for text in lines if text])


def part_cover(
    work: Work,
    page: Page,
    instrument: str,
    remark: str,
    notes: list[str],
    marks: list[tuple[str, str]],
) -> str:
    """Return the cover of a part: the composer, the title, the instrument, and notes.

    The guidelines of the orchestra librarians ask for the title, the composer,
    and the instrument on the front of a part, with all instruments of the
    player and all instructions for the player.
    """
    title, _, rest = work.title.partition(" for ")
    lines = [
        page.skip(0.07 * page.height_mm),
        line(page, spaced(work.composer.upper()), 12.0),
        page.skip(0.032 * page.height_mm),
        line(page, quote(title), 34.0),
        page.skip(0.008 * page.height_mm),
        line(page, quote("for " + rest), 16.0, r"\italic") if rest else "",
        page.skip(0.036 * page.height_mm),
        rule(page, 40.0),
        page.skip(0.036 * page.height_mm),
        line(page, quote(instrument), 28.0, r"\bold"),
        page.skip(0.012 * page.height_mm) if remark else "",
        line(page, quote(remark), 13.0) if remark else "",
        page.skip(0.06 * page.height_mm),
    ]
    if notes:
        lines += [heading(page, "Notes for the player", 13.0), page.skip(3.5)]
        for note in notes:
            lines += [paragraph(page, note, 10.0), page.skip(3.6)]
    if marks:
        lines += [
            page.skip(4.0),
            heading(page, "Marks and words in this part", 13.0),
            page.skip(3.5),
        ]
        first_mm = 0.30 * (page.width_mm - 2.0 * page.margin_mm)
        for mark, meaning in marks:
            lines += [
                row(page, [(mark, first_mm, r"\italic"), (meaning, 0.0, "")], 10.0),
                page.skip(2.2),
            ]
    return _page(page, [text for text in lines if text])


def imprint(work: Work, page: Page) -> str:
    """Return the page behind the cover: the duration, the licence, and the source."""
    minutes = round(work.structure.duration_seconds / 60)
    bars = len(work.structure.bars)
    rows = [
        (work.title, r"\bold"),
        (f"Music by {work.composer}, {YEAR}", ""),
        ("", ""),
        (f"One movement in five linked parts. {bars} bars. Duration: about {minutes} minutes.", ""),
        ("", ""),
        (f"Copyright {YEAR} by {work.composer}.", ""),
        (f"Licence: {LICENCE}.", ""),
        ("You can copy and perform this music, if you give the name of the composer.", ""),
        ("", ""),
        (f"Score, parts, and a recording: {SOURCE}", ""),
        ("Music engraving by LilyPond (lilypond.org). The score and the parts are the output", ""),
        ("of a program: each note is in the source code at the address above.", ""),
    ]
    lines = [page.skip(0.66 * page.height_mm)]
    for text, style in rows:
        lines.append(label(page, text, 9.5, style) if text else page.skip(3.0))
        lines.append(page.skip(0.8))
    return _page(page, lines)


# ------------------------------------------------------------------ instrumentation


def _ranges(work: Work) -> dict[tuple[str, str], tuple[int, int]]:
    """Return the lowest and the highest note of each tuned percussion instrument of a player."""
    from ..perform.events import perform  # at call time: that module imports this package

    found: dict[tuple[str, str], tuple[int, int]] = {}
    for player in work.orchestra.players:
        if player.family != "percussion":
            continue
        for note in perform(work, player.id):
            if note.instrument in TUNED:
                key = (player.id, note.instrument)
                low, high = found.get(key, (200, 0))
                found[key] = (min(low, round(note.midi)), max(high, round(note.midi)))
    return found


def note_name(midi: int) -> str:
    """Return the name of a note with its octave number (C4 is middle C)."""
    name = from_midi(midi).name.rstrip("',")
    letter = name[0].upper()
    accidental = {"is": "-sharp", "es": "-flat", "s": "-flat"}.get(name[1:], "")
    return f"{letter}{accidental}{midi // 12 - 1}"


def _with_ranges(
    player_id: str, instruments: list[str], ranges: dict[tuple[str, str], tuple[int, int]]
) -> list[str]:
    """Return the instruments of a percussion player, each tuned instrument with its range."""
    items = []
    for instrument in instruments:
        low, high = ranges.get((player_id, instrument), (0, 0))
        if high and low != high:
            items.append(f"{instrument} ({note_name(low)} to {note_name(high)})")
        elif high:
            items.append(f"{instrument} ({note_name(low)})")
        else:
            items.append(instrument)
    return items


# The places on a staff with the percussion clef. The key is the number of steps
# from the middle line.
STAFF_PLACES = {
    -4: "the first line",
    -3: "the first space",
    -2: "the second line",
    -1: "the second space",
    0: "the middle line",
    1: "the third space",
    2: "the fourth line",
    3: "the fourth space",
    4: "the fifth line",
}


def percussion_key(work: Work, player_id: str) -> list[str]:
    """Return the sentences of the key at the start of the part of a percussion player.

    The key lists the instruments of the player in the sequence of their use.
    An instrument with no pitch that has more than one size gets the places of
    its sizes on the staff.
    """
    from ..perform.events import perform  # at call time: that module imports this package

    instruments = work.orchestra.instruments
    used: list[str] = []
    places: dict[str, set[int]] = {}
    for note in perform(work, player_id):
        if note.instrument not in used:
            used.append(note.instrument)
        if instruments.get(note.instrument) is None:
            pitch = from_midi(note.midi)
            places.setdefault(note.instrument, set()).add(pitch.step + 7 * pitch.octave)
    if not used:
        return []
    middle = Pitch.parse("c'")
    centre = middle.step + 7 * middle.octave
    items = _with_ranges(player_id, used, _ranges(work))
    sentences = ["Instruments, in the sequence of their use: " + ", ".join(items) + "."]
    for instrument, steps in places.items():
        if len(steps) > 1:
            names = [STAFF_PLACES.get(step - centre, "") for step in sorted(steps)]
            sentences.append(
                f"{instrument[0].upper()}{instrument[1:]}: {len(steps)} sizes. "
                f"From the largest to the smallest, their notes are on {', '.join(names)}."
            )
    sentences.append(
        "A box gives the name of an instrument at its first note. "
        'The words "to ..." after a note tell you to go to a different instrument.'
    )
    return sentences


def key_markup(page: Page, sentences: list[str], size: float = 8.5) -> str:
    """Return the key of a percussion part as a LilyPond markup below the title."""
    skip = page.units(page.points(size) * POINT_MM * 1.55)
    blocks = [block(page, sentence, size, page.text_width) for sentence in sentences]
    return (
        f"\\markup \\override #'(baseline-skip . {skip:.2f}) \\column {{\n  "
        + "\n  ".join(blocks)
        + "\n  \\vspace #0.3\n}"
    )


def instrument_lines(work: Work) -> dict[str, list[tuple[str, str]]]:
    """Return the list of the players in families: the name of each player, and a remark.

    The remark has the other instruments of a wind player, the instruments of
    a percussion player (with the ranges of those that have a pitch), or the
    number of the players of a string section.
    """
    from ..perform.events import perform

    ranges = _ranges(work)
    lines: dict[str, list[tuple[str, str]]] = {family: [] for family in FAMILY_TITLES}
    for player in work.orchestra.players:
        if player.id.endswith(".lh"):
            continue
        hands = [player.id]
        if player.id.endswith(".rh"):
            hands.append(player.id[: -len(".rh")] + ".lh")
        used: list[str] = []
        for hand in hands:
            for note in perform(work, hand):
                if note.instrument not in used:
                    used.append(note.instrument)
        if not used:
            continue
        first = player.instruments[0]
        if player.family == "strings":
            name = STRING_NAMES.get(player.id, player.name)
            lines["strings"].append((name, f"{player.count} players" if player.count > 1 else ""))
            continue
        if player.family == "percussion":
            items = _with_ranges(player.id, used, ranges)
            if len(player.instruments) > 1:
                lines["percussion"].append((player.name, ", ".join(items)))
            else:
                remark = items[0].split(" (", 1)[1].rstrip(")") if " (" in items[0] else ""
                lines["percussion"].append((player.name, remark))
            continue
        # A wind or keyboard player: the key of a transposing instrument, and the
        # other instruments of the player.
        name = player.name
        if " in " in first:
            name += " in " + first.split(" in ", 1)[1]
        others = [instrument for instrument in used if instrument != first]
        also = "also " if first in used else ""
        lines[player.family].append((name, f"{also}{', '.join(others)}" if others else ""))
    return lines


def instrumentation(work: Work, page: Page) -> str:
    """Return the page with the list of the players."""
    families = instrument_lines(work)
    column_mm = 0.47 * (page.width_mm - 2.0 * page.margin_mm)
    columns: list[list[str]] = [[], []]
    for family, title in FAMILY_TITLES.items():
        if not families[family]:
            continue
        target = columns[0] if family in ("woodwinds", "brass", "strings") else columns[1]
        target.append(page.skip(7.0))
        target.append(label(page, title, 12.5, r"\bold"))
        target.append(page.skip(2.2))
        for name, remark in families[family]:
            if family == "percussion" and remark and len(remark) > 24:
                # The instruments of a percussion player are below the name of the player.
                target.append(label(page, name, 10.5))
                target.append(page.skip(1.6))
                target.append(
                    rf"\line {{ \hspace #{page.units(5.0):.1f} "
                    + block(page, remark, 9.5, page.units(column_mm - 5.0)).replace(
                        r"\abs-fontsize", r"\italic \abs-fontsize", 1
                    )
                    + " }"
                )
                target.append(page.skip(2.6))
            else:
                text = f"{name} ({remark})" if remark else name
                target.append(block(page, text, 10.5, page.units(column_mm)))
                target.append(page.skip(2.3))
    players = sum(
        player.count for player in work.orchestra.players if not player.id.endswith(".lh")
    )
    left = "\n      ".join(columns[0])
    right = "\n      ".join(columns[1])
    lines = [
        page.skip(TOP_SHARE * page.height_mm),
        heading(page, "Instrumentation"),
        page.skip(5.0),
        paragraph(
            page,
            f"The work is for {players} players. A player who has more than one instrument "
            "changes between them: the part says when. The number of the string players can be "
            "smaller, but not smaller than 14, 12, 10, 8, and 6. Each percussion player has "
            "the instruments of one list. For an instrument with a pitch, the list gives the "
            "range that the music uses: the names of the notes are for the real sound, and C4 "
            "is the middle C.",
        ),
        page.skip(1.0),
        r"\line {",
        f"    \\column {{\n      {left}\n    }}",
        rf"    \hspace #{page.units(0.06 * (page.width_mm - 2.0 * page.margin_mm)):.1f}",
        f"    \\column {{\n      {right}\n    }}",
        "  }",
    ]
    return _page(page, lines)


# ------------------------------------------------------------------------ stage plan

# The plan of the stage, as seen from above: the label of each group, and its area in
# metres (left, right, front, back). The conductor is at 0, 0. The plan agrees with
# the seats of the hall model of the audio (`audio/space.py`).
STAGE = [
    ("First violins", -9.4, -1.5, 1.3, 3.8, True),
    ("Second violins", 1.5, 9.4, 1.3, 3.8, True),
    ("Cellos", -5.6, -0.4, 4.2, 6.2, True),
    ("Violas", 0.4, 5.6, 4.2, 6.2, True),
    ("Double basses", -9.8, -6.0, 4.2, 6.0, True),
    ("Flutes", -4.3, -0.3, 6.7, 7.9, False),
    ("Oboes", 0.3, 4.3, 6.7, 7.9, False),
    ("Clarinets", -5.3, -0.3, 8.2, 9.4, False),
    ("Bassoons", 0.3, 4.3, 8.2, 9.4, False),
    ("Horns", -6.6, -0.9, 9.8, 11.3, False),
    ("Trumpets", -0.5, 3.1, 9.8, 11.0, False),
    ("Trombones, tuba", 3.5, 8.4, 9.8, 11.0, False),
    ("Percussion", -8.4, -1.9, 11.7, 13.2, False),
    ("Timpani", -1.5, 1.5, 11.7, 13.2, False),
    ("Percussion", 1.9, 6.8, 11.7, 13.2, False),
    ("Harp", -10.6, -7.6, 6.4, 7.6, False),
    ("Piano", -10.6, -7.0, 7.9, 9.5, False),
    ("Celesta", -10.6, -7.6, 9.8, 11.0, False),
    ("Mandolin", 6.4, 9.2, 4.2, 5.4, False),
    ("Cimbalom", 6.4, 9.8, 5.7, 7.1, False),
    ("Accordion", 6.4, 9.8, 7.4, 8.6, False),
]
STAGE_WIDTH = 22.0  # metres: the width of the plan
STAGE_DEPTH = 13.4  # metres: from the conductor to the back of the plan


def stage_plan(page: Page) -> str:
    """Return the page with the plan of the stage, as seen from above."""
    scale = page.units((page.width_mm - 2.0 * page.margin_mm) / STAGE_WIDTH)  # units in a metre
    points = page.points(9.0)
    items = []
    for name, left, right, front, back, strings in STAGE:
        width, depth = (right - left) * scale, (back - front) * scale
        items.append(
            rf"\translate #'({left * scale:.2f} . {front * scale:.2f}) "
            rf"\override #'(line-join-style . round) \path #{0.22 if strings else 0.13} "
            rf"#'((moveto 0 0) (lineto {width:.2f} 0) (lineto {width:.2f} {depth:.2f}) "
            rf"(lineto 0 {depth:.2f}) (closepath))"
        )
        x = (left + right) / 2.0 * scale
        y = (front + back) / 2.0 * scale - page.units(points * POINT_MM * 0.35)
        style = r"\bold " if strings else ""
        items.append(
            rf"\translate #'({x:.2f} . {y:.2f}) \center-align \abs-fontsize #{points:g} "
            rf"{style}{quote(name)}"
        )
    # The conductor, the edge of the stage, and the audience.
    items.append(
        rf"\translate #'(0 . {-0.2 * scale:.2f}) \center-align \abs-fontsize #{points:g} "
        rf"\italic {quote('Conductor')}"
    )
    half = STAGE_WIDTH / 2.0 * scale
    items.append(
        rf"\translate #'({-half:.2f} . {-1.1 * scale:.2f}) \override #'(thickness . 2) "
        rf"\draw-line #'({2 * half:.2f} . 0)"
    )
    items.append(
        rf"\translate #'(0 . {-2.0 * scale:.2f}) \center-align \abs-fontsize #{points:g} "
        rf"\italic {quote('Audience')}"
    )
    drawing = r"\overlay { " + "\n    ".join(items) + " }"
    lines = [
        page.skip(TOP_SHARE * page.height_mm),
        heading(page, "Plan of the stage"),
        page.skip(5.0),
        paragraph(
            page,
            "The first violins are on the left of the conductor, and the second violins are "
            "on the right: many passages go from one group to the other. The cellos are "
            "behind the first violins, and the violas are behind the second violins. The "
            "double basses are on the left. For the interlude (rehearsal marks W to AA) the "
            "piano is a solo instrument: its lid is open. If the stage is small, the piano "
            "can be at the front, on the left of the conductor.",
        ),
        page.skip(10.0),
        rf"\fill-line {{ {drawing} }}",
    ]
    return _page(page, lines)


# ----------------------------------------------------------------------------- notes


def performance_notes(page: Page, notes: list[str], techniques: list[tuple[str, str]]) -> str:
    """Return the page with the notes for the performance, and the list of the marks."""
    lines = [
        page.skip(TOP_SHARE * page.height_mm),
        heading(page, "Notes for the performance"),
        page.skip(5.0),
    ]
    for note in notes:
        lines.append(paragraph(page, note))
        lines.append(page.skip(3.4))
    if techniques:
        lines += [
            page.skip(7.0),
            heading(page, "Marks and words in the music", 14.0),
            page.skip(4.0),
        ]
        first_mm = 0.30 * (page.width_mm - 2.0 * page.margin_mm)
        for mark, meaning in techniques:
            lines.append(row(page, [(mark, first_mm, r"\italic"), (meaning, 0.0, "")]))
            lines.append(page.skip(2.8))
    return _page(page, lines)


def programme_note(page: Page, paragraphs: list[str], form: list[tuple[str, str, str, str]]) -> str:
    """Return the page with the programme note and the plan of the form."""
    lines = [page.skip(TOP_SHARE * page.height_mm), heading(page, "About the work"), page.skip(5.0)]
    for text in paragraphs:
        lines.append(paragraph(page, text))
        lines.append(page.skip(4.0))
    if form:
        lines += [page.skip(7.0), heading(page, "The form", 14.0), page.skip(4.0)]
        width = page.width_mm - 2.0 * page.margin_mm
        for part, marks, time, contents in form:
            cells = [
                (part, 0.13 * width, r"\bold"),
                (marks, 0.16 * width, ""),
                (time, 0.10 * width, ""),
                (contents, 0.0, ""),
            ]
            lines.append(row(page, cells))
            lines.append(page.skip(2.6))
    return _page(page, lines)


# ------------------------------------------------------------- the texts of the pages

# The words of the playing techniques, and what the player does. The page of the notes
# shows the words that the work uses.
MEANINGS = {
    "pizz.": "Pluck the string. arco: with the bow again.",
    "col legno batt.": "Hit the string with the wood of the bow.",
    "spicc.": "Short strokes: the bow bounces on the string.",
    "sul pont.": "The bow is near the bridge: a thin, glassy sound.",
    "sul tasto": "The bow is above the fingerboard: a soft, veiled sound.",
    "ord.": "The usual way to play, after a special technique.",
    "con sord.": "With the mute. senza sord.: without the mute.",
    "practice mute": "A heavy mute: the sound is very soft and distant.",
    "non vib.": "No vibrato. poco vib., vib., molto vib.: a little, usual, and much vibrato.",
    "solo": "One player. tutti: all players of the section again.",
    "div.": "The section divides into groups. unis.: all players have one line again.",
    "flz.": "Flutter-tongue. nat.: the usual way to play again.",
    "air tone": "The sound of air, with little pitch.",
    "bells up": "Lift the bell of the instrument.",
    "cuivré": "A hard, brassy tone.",
    "l.v.": "Let the sound ring: do not stop it.",
    "damp": "Stop the sound at the end of the note.",
    "with a bow": "Bow the edge of the instrument (a double bass bow).",
    "soft mallets": "soft mallets, hard mallets: the type of the mallets.",
    "motor on": "The motor of the vibraphone. motor off: no motor.",
    "lontano": "As from far away.",
    "martellato": "Hammered: each note is short and hard.",
    "quasi arpa, liberamente": "As a harp plays: the time of the notes is free in the bar.",
}
SYMBOLS = [
    ("Three strokes on a stem", "A tremolo or a roll that is not measured: as fast as possible."),
    ("A small circle above a note", "Strings and harp: a harmonic. The note shows the real sound."),
    ("+ above a note", "Horn: a stopped note."),
    ("A line between two notes", "A slide (glissando) for the time of the first note."),
    ("A box with a name", "The player changes to this instrument."),
]
PROGRAMME = [
    "{title} is one movement in five linked parts. It goes from dark to light: from D minor "
    "with a tritone at the start to D major at the end. The music has no story, and its parts "
    "have no titles.",
    "One idea of three notes, the motto, is in all parts of the work. In its dark state it is "
    "D, E-flat, A-flat. At the turn of the work, two of its notes go up by a semitone, and the "
    "motto becomes D, E, A. The note A-flat is the pivot. In the dark half it goes down to G. "
    "After the turn the same pitch has the name G-sharp, and it goes up to A.",
    "The first part is a slow night scene. The second part is fast and agitated: a chase in "
    "the metre 7/8, a heavy section, and a first climax that breaks. The third part is night "
    "music with no pulse: a cluster, the calls of the night, a melody with quarter-tones. From "
    "this silence the piano starts an interlude, which is a small concerto: a toccata, a theme "
    "in hammered octaves, and a cadenza. At its end the full orchestra holds a chord of all "
    "twelve notes. After a silence, D major arrives, suddenly soft. This is the turn of the "
    "work.",
    "The fourth part has the themes of the dark half again, now in major keys, and it goes to "
    "the main climax. The fifth part starts with the harmonic series on D, as the first light. "
    "Then the themes sound together, the heavy rhythm comes back in D major, and a chorale "
    "with bells ends the work.",
    "The work has three models: Verklärte Nacht by Arnold Schoenberg for the form, the night "
    "music of Béla Bartók for the third part, and the orchestra of John Corigliano for the "
    "colours.",
]
# The plan of the form: the name, the first and the last rehearsal mark, and the contents.
FORM = [
    ("Part 1", "", "C", "Night: a low D, the walking theme, the long song, the chorale."),
    ("Part 2", "D", "R", "Unrest: the agitated theme, the chase, the heavy section, the first "
     "climax."),
    ("Part 3", "S", "V", "Night music: a cluster, gongs, the calls of the night, one cello "
     "above a drone."),
    ("Interlude", "W", "Z", "The piano is the soloist: a toccata, the theme in the forge, "
     "trades with the orchestra, a cadenza, a chord of twelve notes."),
    ("Part 4", "AA", "FF", "The turn to D major: the warm theme, the themes in major keys, the "
     "main climax, calm."),
    ("Part 5", "GG", "KK", "Light: the harmonic series, the themes together, the heavy rhythm "
     "in D major, the chorale with bells."),
]  # fmt: skip


def used_marks(work: Work, players: list[str] | None = None) -> list[tuple[str, str]]:
    """Return the technique words that have an explanation, with the symbols.

    With no `players`, the list is for the score: all words of the work and all
    symbols. With `players` (the staves of one part), the list has only the
    words and the symbols that the part uses.
    """
    from . import music
    from .techniques import TECHNIQUES

    found: set[str] = set()
    signs: set[str] = set()

    def walk(elements: list) -> None:
        for element in elements:
            if isinstance(element, music.Note | music.Rest):
                posts = list(element.posts)
                if isinstance(element, music.Note):
                    posts += [post for pitch in element.pitches for post in pitch.posts]
                for post in posts:
                    if post.kind == "command" and post.value in TECHNIQUES:
                        found.add(TECHNIQUES[post.value].text)
                    if post.kind == "tremolo":
                        signs.add("Three strokes on a stem")
                    elif post.value in ("flageolet", "harmonic"):
                        signs.add("A small circle above a note")
                    elif post.value == "stopped":
                        signs.add("+ above a note")
                    elif post.value == "glissando":
                        signs.add("A line between two notes")
            elif isinstance(element, music.Command) and element.name == "switch":
                signs.add("A box with a name")
            elif isinstance(element, music.Group):
                walk(element.children)

    for player in work.orchestra.players:
        if players is None or player.id in players:
            walk(work.music_of(player.id).children)
    rows = [(mark, meaning) for mark, meaning in MEANINGS.items() if mark in found]
    if players is None:
        return rows + SYMBOLS
    return rows + [(sign, meaning) for sign, meaning in SYMBOLS if sign in signs]


def part_notes(work: Work, players: list[str], has_cues: bool) -> list[str]:
    """Return the notes for the player on the cover of a part."""
    from ..perform.events import perform  # at call time: that module imports this package

    structure = work.structure
    first = work.orchestra.player(players[0])
    notes: list[str] = []
    changes = False
    if first.family == "percussion" and len(first.instruments) > 1:
        notes += percussion_key(work, first.id)
        changes = True
    quarter: set[int] = set()
    instruments: set[str] = set()
    for player_id in players:
        for note in perform(work, player_id):
            instruments.add(note.instrument)
            if note.midi != round(note.midi):
                quarter.add(structure.bar_at(note.start).number)
    if len(instruments) > 1 and not changes:
        notes.append(
            'The words "to ..." after a note tell you to take a different instrument. '
            "A box gives the name of the instrument at its first note."
        )
    if has_cues:
        notes.append(
            "Small notes with the name of an instrument are cues: they show the music of a "
            "different player before your entry. Do not play them."
        )
    if quarter:
        first_bar, last_bar = min(quarter), max(quarter)
        where = f"bar {first_bar}" if first_bar == last_bar else f"bars {first_bar} to {last_bar}"
        notes.append(
            f"This part has quarter-tones ({where}). A flat sign that is reversed makes the note "
            "a quarter-tone lower. A sharp sign with only one vertical line makes the note a "
            "quarter-tone higher."
        )
    notes.append("An accidental is for one bar and one octave only.")
    minutes = round(structure.duration_seconds / 60)
    notes.append(f"The work is one movement. Duration: about {minutes} minutes.")
    return notes


def form_rows(work: Work) -> list[tuple[str, str, str, str]]:
    """Return the plan of the form with the time of each part."""
    structure = work.structure
    bars = {label: bar for bar, label in structure.marks.items()}
    rows = []
    for name, first, last, contents in FORM:
        if first and first not in bars:
            continue
        seconds = structure.seconds(structure.bar(bars[first]).start) if first else 0.0
        marks = f"{first} to {last}" if first else f"start to {last}"
        clock = f"{int(seconds // 60)}:{int(seconds % 60):02d}"
        rows.append((name, marks, clock, contents))
    return rows


def pages(work: Work, page: Page, edition: str, notes: list[str]) -> list[str]:
    """Return all pages before the music, in their sequence. The number of pages is even."""
    programme = [text.format(title=work.title) for text in PROGRAMME]
    return [
        cover(work, page, edition),
        imprint(work, page),
        instrumentation(work, page),
        stage_plan(page),
        performance_notes(page, notes, used_marks(work)),
        programme_note(page, programme, form_rows(work)),
    ]
