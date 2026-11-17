"""Check the study tables and write the style study report."""

from __future__ import annotations

import csv
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

RESEARCH_DIR = Path("research")
TABLES_DIR = RESEARCH_DIR / "tables"
MEASURED_DIR = RESEARCH_DIR / "measured"
TEXT_DIR = RESEARCH_DIR / "text"
REPORT_PATH = Path("docs/style-study.md")

EVIDENCE_CODES = {"R", "K", "M", "R, K"}

Row = dict[str, str]


def read_table(path: Path) -> tuple[list[str], list[Row]]:
    """Read a CSV table. Return its header and its rows."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


# ----------------------------------------------------------------------------
# Checks
# ----------------------------------------------------------------------------


def check() -> list[str]:
    """Check the sourced tables. Return a list of problems."""
    problems: list[str] = []
    _, sources = read_table(RESEARCH_DIR / "sources.csv")
    keys = {row["key"] for row in sources}
    if len(keys) != len(sources):
        problems.append("sources.csv: a key occurs more than one time")

    cited_keys: set[str] = set()
    for path in sorted(TABLES_DIR.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            raw = list(csv.reader(handle))
        header = raw[0]
        for number, cells in enumerate(raw[1:], 2):
            if len(cells) != len(header):
                problems.append(
                    f"{path.name} line {number}: {len(cells)} cells, header has {len(header)}"
                )
        _, rows = read_table(path)
        for number, row in enumerate(rows, 2):
            if not (row[header[0]] or "").strip():
                problems.append(f"{path.name} line {number}: first cell is empty")
            if "evidence" in row and row["evidence"] not in EVIDENCE_CODES:
                problems.append(f"{path.name} line {number}: evidence code {row['evidence']!r}")
            if "source" in row:
                cited = [key.strip() for key in row["source"].split(";") if key.strip()]
                cited_keys.update(cited)
                if not cited:
                    problems.append(f"{path.name} line {number}: no source")
                for key in cited:
                    if key not in keys:
                        problems.append(f"{path.name} line {number}: unknown source {key!r}")
                evidence = row.get("evidence", "")
                if evidence == "K" and cited != ["reference"]:
                    problems.append(f"{path.name} line {number}: code K must cite 'reference'")
                if evidence == "R" and "reference" in cited:
                    problems.append(f"{path.name} line {number}: code R cannot cite 'reference'")
    for key in sorted(keys - cited_keys):
        problems.append(f"sources.csv: no table cites the source {key!r}")
    return problems


# ----------------------------------------------------------------------------
# Markdown output
# ----------------------------------------------------------------------------


def _cell(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def markdown_table(header: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    """Return a Markdown table."""
    lines = [
        "| " + " | ".join(_cell(h) for h in header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    lines += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _label(column: str) -> str:
    text = column.replace("_", " ")
    return text[0].upper() + text[1:]


def percent(value: str) -> str:
    """Show a share (0 to 1) as a percentage."""
    try:
        return f"{100 * float(value):.0f} %"
    except ValueError:
        return value


def number(digits: int) -> Callable[[str], str]:
    """Return a function that rounds a number to the given number of decimal places."""

    def convert(value: str) -> str:
        try:
            amount = float(value)
        except ValueError:
            return value
        if amount == int(amount) and "." not in value:
            return str(int(amount))
        return f"{amount:.{digits}f}"

    return convert


def code(value: str) -> str:
    """Show music text in a fixed-width font."""
    return f"`{value}`" if value else ""


@dataclass
class TableSpec:
    """How the report shows one table."""

    title: str
    path: Path
    intro: list[str]
    columns: list[str] | None = None  # columns to show; None = all
    formats: dict[str, Callable[[str], str]] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    keep: Callable[[Row], bool] | None = None

    def render(self) -> str:
        header, rows = read_table(self.path)
        columns = self.columns or header
        if self.keep:
            rows = [row for row in rows if self.keep(row)]
        body = [
            [self.formats.get(column, str)(row[column] or "") for column in columns] for row in rows
        ]
        shown = [self.labels.get(column, _label(column)) for column in columns]
        parts = [f"### {self.title}", *self.intro, markdown_table(shown, body)]
        parts.append(f"Data file: [`{self.path.as_posix()}`](../{self.path.as_posix()})")
        return "\n\n".join(parts)


SHARE_MEASURES = ("steps", "repeated", "semitone", "fourths", "octaves", "share", "outside")


def render_chorale_style() -> str:
    """Render the style numbers of the chorales: all settings, and those of the Passion."""
    _, rows = read_table(MEASURED_DIR / "chorale_style.csv")
    body = []
    for row in rows:
        name = row["measure"]
        show = percent if any(word in name for word in SHARE_MEASURES) else number(1)
        body.append(
            [
                _label(name),
                show(row["all_median"]),
                f"{show(row['all_10_percent'])} to {show(row['all_90_percent'])}",
                show(row["passion_median"]),
                f"{show(row['passion_lowest'])} to {show(row['passion_highest'])}",
            ]
        )
    return markdown_table(
        ["Measure", "All 370: middle value", "All 370: middle 80 percent",
         "Passion (11): middle value", "Passion (11): lowest to highest"],
        body,
    )  # fmt: skip


LINE_SHARES = [
    "share_of_time", "share_sixteenths_or_shorter", "share_eighths", "share_longer",
    "repeated_note", "semitone", "whole_tone", "third", "fourth_or_fifth", "sixth_or_larger",
    "tritone", "descending_share", "notes_outside_the_scale",
]  # fmt: skip


def _line_spec(title: str, intro: list[str], keep: Callable[[Row], bool]) -> TableSpec:
    return TableSpec(
        title,
        MEASURED_DIR / "lines.csv",
        intro,
        columns=["movement", "line", "notes", "lowest", "pitch_5", "pitch_median", "pitch_95",
                 "highest", "share_of_time", "notes_per_quarter", "share_sixteenths_or_shorter",
                 "repeated_note", "semitone", "whole_tone", "third", "fourth_or_fifth",
                 "sixth_or_larger", "notes_outside_the_scale"],
        formats={**dict.fromkeys(LINE_SHARES, percent), "notes_per_quarter": number(2)},
        labels={
            "pitch_5": "5 % point", "pitch_median": "Middle", "pitch_95": "95 % point",
            "share_of_time": "Time with notes", "notes_per_quarter": "Notes in a quarter note",
            "share_sixteenths_or_shorter": "Sixteenths or shorter",
            "repeated_note": "Repeated", "third": "Thirds", "fourth_or_fifth": "Fourths, fifths",
            "sixth_or_larger": "Sixths or larger", "notes_outside_the_scale": "Outside the scale",
        },
        keep=keep,
    )  # fmt: skip


def _measured_specs() -> list[TableSpec]:
    shares = {
        "chords_from_thirds", "chords_with_a_semitone_clash", "major_and_minor_triads",
        "dominant_chords", "vagrant_chords", "other_seventh_chords",
        "time_with_the_key_note_in_the_bass", "notes_outside_the_scale",
    }  # fmt: skip
    bass_shares = {
        "share_sixteenths_or_shorter", "share_eighths", "share_longer", "repeated_note",
        "semitone", "step", "third", "fourth_or_fifth", "sixth_or_larger", "share_of_time_silent",
    }  # fmt: skip
    return [
        TableSpec(
            "M2. The chorale settings of the St Matthew Passion",
            MEASURED_DIR / "passion_chorales.csv",
            [
                "The edition of the chorales has 11 settings from the Passion "
                "(the settings of movements 15 and 17 are one setting in two keys). "
                "The edition gives some settings in a key that is not the key of the Passion: "
                "table S2 gives the keys of the Passion.",
                'The column "Chords at the fermatas" gives the chord at the end of each phrase '
                "as a degree of the key: small letters are minor chords. "
                "The last setting (movement 62) ends on the dominant.",
            ],
            columns=["movement", "tune", "key_of_the_edition", "quarter_notes", "soprano", "bass",
                     "chords_at_the_fermatas", "notes_outside_the_scale",
                     "chords_with_a_semitone_clash", "bass_semitone_moves"],
            formats={
                "notes_outside_the_scale": percent,
                "chords_with_a_semitone_clash": percent,
                "bass_semitone_moves": percent,
            },
        ),
        TableSpec(
            "M3. The chorale tunes of the Passion",
            MEASURED_DIR / "chorale_tunes.csv",
            [
                "The table gives the soprano of one setting of each tune, phrase by phrase, "
                "in the music language of the project (a `'` is one octave up; `is` is a sharp, "
                "`es` is a flat). The last column gives each note as semitones above the key note.",
            ],
            columns=["tune", "movement", "key_of_the_edition", "phrase", "notes"],
            formats={"notes": code},
        ),
        _line_spec(
            "M4. The voice lines",
            [
                "Each row is one solo voice of one movement. "
                '"Middle" is the pitch below which the voice is for one half of its time. '
                "The voice is between the 5 % point and the 95 % point for 90 percent of its "
                'time. The columns from "Repeated" to "Sixths or larger" give the moves from '
                "note to note as shares of all moves.",
            ],
            lambda row: row["line"].startswith("voice"),
        ),
        _line_spec(
            "M5. The lines of the instruments",
            [
                "Each row is one instrument line of one movement. "
                "A line with more than one note at a time counts with its highest note.",
            ],
            lambda row: not row["line"].startswith("voice"),
        ),
        TableSpec(
            "M6. The harmony and the texture of the movements",
            MEASURED_DIR / "movement_harmony.csv",
            [
                "The tempo and the duration are those of the MIDI file of the edition: "
                "they are a decision of the editor, not of Bach. "
                '"Vagrant chords" are diminished and augmented chords and other chords that do '
                "not belong to one key. "
                'A "semitone clash" is a chord that has two notes one semitone apart: '
                "passing notes and suspensions make most of them.",
            ],
            columns=["movement", "key", "metre", "bars", "seconds", "lines",
                     "mean_lines_that_sound", "pitch_classes_in_one_bar", "chords_from_thirds",
                     "chords_with_a_semitone_clash", "major_and_minor_triads", "dominant_chords",
                     "vagrant_chords", "notes_outside_the_scale"],
            formats={
                **dict.fromkeys(shares, percent),
                "mean_lines_that_sound": number(1),
                "pitch_classes_in_one_bar": number(1),
            },
        ),
        TableSpec(
            "M7. The bass lines",
            MEASURED_DIR / "bass_lines.csv",
            [
                "Each row is the continuo line of one movement. "
                '"Longest pedal" is the longest time for which the bass stays on one note.',
            ],
            columns=["movement", "lowest", "highest", "notes_per_quarter",
                     "share_sixteenths_or_shorter", "share_eighths", "repeated_note", "semitone",
                     "step", "fourth_or_fifth", "sixth_or_larger", "longest_pedal_quarters",
                     "pedal_note"],
            formats={**dict.fromkeys(bass_shares, percent), "notes_per_quarter": number(2)},
            labels={"notes_per_quarter": "Notes in a quarter note",
                    "share_sixteenths_or_shorter": "Sixteenths or shorter",
                    "share_eighths": "Eighths", "step": "Steps",
                    "longest_pedal_quarters": "Longest pedal (quarter notes)"},
        ),
        TableSpec(
            "M8. The figures of the figured bass",
            MEASURED_DIR / "figures.csv",
            [
                "The table counts the figures in the text sources of the movements that have a "
                "figured bass. The numbers of a figure are from the top to the bottom. "
                "A `+` is a raised note, a `-` is a lowered note, a `!` is a natural sign; "
                "a figure with only a sign changes the third. "
                "The table shows the figures that come five times or more.",
            ],
            formats={"share": percent, "figure": code},
        ),
    ]  # fmt: skip


def _sourced_specs() -> list[TableSpec]:
    return [
        TableSpec(
            "S1. The works of the study",
            TABLES_DIR / "works.csv",
            [
                "The table lists the works that the study team examined: works of Bach, "
                "music for one voice of his time, and works of later composers that use the "
                "music of Bach or the form of the Passion. "
                'The column "Lesson for this work" gives what the new work takes from each.',
            ],
            columns=[
                "composer",
                "work",
                "year",
                "forces",
                "minutes",
                "lesson_for_this_work",
                "source",
                "evidence",
            ],
        ),
        TableSpec(
            "S2. The movements of the St Matthew Passion",
            TABLES_DIR / "bach_movements.csv",
            [
                "One row for each section. NBA is the number of the Neue Bach-Ausgabe; the "
                "letters divide a movement into its sections. "
                "Voices: Ev = Evangelist, Ch I and Ch II = the two choirs, S A T B = the four "
                "voice types. Instruments: Ft = flute, Ob = oboe, Oa = oboe d'amore, "
                "Oc = oboe da caccia, Vn = violin, Vs = solo violin, Va = viola, "
                "Vg = viola da gamba, Bc = continuo.",
            ],
            columns=[
                "nba",
                "form",
                "voices",
                "key",
                "metre",
                "instruments",
                "first_words",
                "text_from",
            ],
        ),
        TableSpec(
            "S3. Elements of the St Matthew Passion",
            TABLES_DIR / "bach_elements.csv",
            ["The table lists the elements of the work of Bach that the new work can use."],
        ),
        TableSpec(
            "S4. Motifs of the St Matthew Passion",
            TABLES_DIR / "motifs.csv",
            [
                "The notes are in the music language of the project: `c'` is middle C, a `'` "
                "is one octave up, a `,` is one octave down, `is` is a sharp, `es` is a flat, "
                "and a number is a note value (`8` = eighth note). "
                "A test makes sure that each line of notes is correct text of this language.",
            ],
            columns=[
                "name",
                "movement",
                "key",
                "metre",
                "line",
                "notes",
                "words",
                "character",
                "source",
                "evidence",
            ],
            formats={"notes": code},
        ),
        TableSpec(
            "S5. The chorales of the St Matthew Passion",
            TABLES_DIR / "chorales.csv",
            ["Eight tunes come in 17 movements."],
        ),
        TableSpec(
            "S6. The voice and the instruments",
            TABLES_DIR / "instruments.csv",
            [
                "The measured ranges come from tables M4 and M5. "
                "The ranges of this work are in the file `design/orchestra.toml`.",
            ],
        ),
        TableSpec(
            "S7. Devices of counterpoint and form",
            TABLES_DIR / "devices.csv",
            [
                "The first part of the table has the devices of the time of Bach. "
                "The second part has devices of later music that the study team examined "
                "for the new work.",
            ],
        ),
        TableSpec(
            "S8. Figures of musical speech",
            TABLES_DIR / "rhetoric.csv",
            ["The names are those of the German theory of the 17th and 18th centuries."],
        ),
        TableSpec(
            "S9. Performance practice",
            TABLES_DIR / "practice.csv",
            [],
        ),
    ]


PROFILE_TITLES = {
    "All": 'P1. Profile "All": the full work',
    "Voice": 'P2. Profile "Voice": the alto',
    "Solo instrument": 'P3. Profile "Solo instrument": the partner of the voice in an aria',
    "Bass": 'P4. Profile "Bass": the continuo line',
    "Aria": 'P5. Profile "Aria": a number for the voice with instruments',
    "Chorus": 'P6. Profile "Chorus": a number for the full orchestra',
    "Chorale": 'P7. Profile "Chorale": a chorale setting',
}


def render_profiles() -> str:
    """Render the style profiles, one table for each profile."""
    _, rows = read_table(TABLES_DIR / "profiles.csv")
    parts = []
    for profile, title in PROFILE_TITLES.items():
        chosen = [row for row in rows if row["profile"] == profile]
        parts.append(f"### {title}")
        parts.append(
            markdown_table(
                ["Group", "Parameter", "Low", "High", "Unit", "Basis", "Code"],
                [
                    [row["group"], row["parameter"], row["low"], row["high"], row["unit"],
                     row["basis"], row["evidence"]]
                    for row in chosen
                ],
            )
        )  # fmt: skip
    parts.append("Data file: [`research/tables/profiles.csv`](../research/tables/profiles.csv)")
    return "\n\n".join(parts)


def render_sources() -> str:
    """Render the list of sources."""
    _, rows = read_table(RESEARCH_DIR / "sources.csv")
    body = []
    for row in rows:
        citation = row["citation"]
        if row["url"]:
            citation += f" <{row['url']}>"
        body.append([f"`{row['key']}`", citation, row["access"]])
    return markdown_table(["Key", "Source", "Access"], body)


def build() -> str:
    """Return the full text of the report."""
    parts = [(TEXT_DIR / "introduction.md").read_text(encoding="utf-8").rstrip()]

    parts.append("## Part 1: Measured tables")
    parts.append(
        "The study code made all tables of this part from the open data. "
        "The directory [`research/measured`](../research/measured) has the data files."
    )
    parts.append("### M1. The style of the four-part chorales")
    parts.append(
        "The table compares all 370 chorale settings of the edition with the 11 settings "
        "of the St Matthew Passion. A share is a part of the moves of a voice, of the note "
        "time, or of the sounding time."
    )
    parts.append(render_chorale_style())
    parts.append(
        "Data file: [`research/measured/chorale_style.csv`](../research/measured/chorale_style.csv)"
    )
    parts += [spec.render() for spec in _measured_specs()]

    parts.append("## Part 2: Sourced tables")
    parts.append(
        "The study team wrote the tables of this part from the sources. "
        "The directory [`research/tables`](../research/tables) has the data files."
    )
    parts += [spec.render() for spec in _sourced_specs()]

    parts.append("## Part 3: Style profiles")
    parts.append(
        "A style profile is a set of target ranges for the new work. "
        "Each range has a low value and a high value. "
        "The study team set each range around a measured value or a sourced value. "
        'The column "Basis" gives that value.'
    )
    parts.append(render_profiles())

    parts.append((TEXT_DIR / "limits.md").read_text(encoding="utf-8").rstrip())
    parts.append("## Sources")
    parts.append(render_sources())
    return "\n\n".join(parts) + "\n"


def write() -> Path:
    """Write the report file and return its path."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build(), encoding="utf-8")
    return REPORT_PATH
