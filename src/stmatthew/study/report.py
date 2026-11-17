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
        return f"{100 * float(value):.1f} %"
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


FINGERPRINT_LABELS = {
    "Schoenberg: Verklärte Nacht, complete": "VN",
    "Schoenberg: Verklärte Nacht, part 1 (bars 1-228)": "VN part 1",
    "Schoenberg: Verklärte Nacht, part 2 (bars 229-418)": "VN part 2",
    "Bartók: Out of Doors, 1. With Drums and Pipes": "OoD 1",
    "Bartók: Out of Doors, 2. Barcarolla": "OoD 2",
    "Bartók: Out of Doors, 3. Musettes": "OoD 3",
    "Bartók: Out of Doors, 4. The Night's Music": "OoD 4 (Night)",
    "Bartók: Out of Doors, 5. The Chase": "OoD 5",
    "Bartók: Bagatelle op. 6 no. 12 (early night music)": "Bag. 12",
    "Bartók: Fourteen Bagatelles op. 6, complete": "Bag. 1-14",
}
SHARE_WORDS = ("share", "top line: ")
NOT_SHARES = ("mean size", "entropy")


def render_fingerprints() -> str:
    """Render the comparison table of all measured works."""
    path = MEASURED_DIR / "fingerprints.csv"
    header, rows = read_table(path)
    works = header[1:]
    body = []
    for row in rows:
        name = row["measure"]
        is_share = any(word in name for word in SHARE_WORDS) and not any(
            word in name for word in NOT_SHARES
        )
        convert = percent if is_share else number(2)
        cells = [convert(row[work]) if row[work] else "-" for work in works]
        body.append([_label(name), *cells])
    return markdown_table(["Measure", *[FINGERPRINT_LABELS.get(w, w) for w in works]], body)


def render_sonorities(works: Sequence[str], count: int = 12) -> str:
    """Render the most frequent sonorities of the given works."""
    _, rows = read_table(MEASURED_DIR / "sonorities.csv")
    parts = []
    for work in works:
        chosen = [row for row in rows if row["work"] == work][:count]
        parts.append(f"**{work}**")
        parts.append(
            markdown_table(
                ["Rank", "Sonority", "Share of the sounding time"],
                [
                    [row["rank"], row["sonority"], percent(row["share_of_sounding_time"])]
                    for row in chosen
                ],
            )
        )
    return "\n\n".join(parts)


# The rows of the harmony table of the new work: the measure, and the parameter of
# the profile "Transfigured" that gives its target range.
WORK_HARMONY_TARGETS = {
    "chords: share built from thirds": "Chords built from thirds",
    "chords: share with a semitone clash": "Chords with a semitone clash",
    "chords: share with a 3-semitone cluster": "Chords with a cluster of 3 semitones",
    "chords: share in one whole-tone scale": "Chords in one whole-tone scale",
    "share of sounding time: dominant chords": "Dominant chords",
    "mean distinct pitch classes in one window": "Different pitch classes in one bar of 4/4",
}
WORK_COLUMNS = ["complete", "before the turn", "after the turn"]
WORK_PARTS = ["part 1", "part 2", "part 3", "part 4", "part 5"]


def _value(name: str, text: str) -> str:
    if not text:
        return "-"
    is_share = any(word in name for word in (*SHARE_WORDS, "bar", "bars")) and not any(
        word in name for word in NOT_SHARES
    )
    return percent(text) if is_share else number(2)(text)


def render_work_repetition() -> str:
    """Render the repetition of the reference work and of the new work in one table."""
    reference_header, reference = read_table(MEASURED_DIR / "repetition.csv")
    _, rows = read_table(MEASURED_DIR / "work_repetition.csv")
    label = reference_header[1]
    values = {row["measure"]: row[label] for row in reference}
    columns = [*WORK_COLUMNS[:1], *WORK_PARTS]
    body = [
        [
            _label(row["measure"]),
            percent(values[row["measure"]]),
            *[percent(row[column]) for column in columns],
        ]
        for row in rows
    ]
    header = ["Measure", "Verklärte Nacht", *[f"New work, {column}" for column in columns]]
    return markdown_table(header, body)


def render_work_harmony() -> str:
    """Render the harmony of the new work with the reference work and the profile."""
    _, rows = read_table(MEASURED_DIR / "work_harmony.csv")
    _, prints = read_table(MEASURED_DIR / "fingerprints.csv")
    _, profiles = read_table(TABLES_DIR / "profiles.csv")
    reference = {row["measure"]: row["Schoenberg: Verklärte Nacht, complete"] for row in prints}
    ranges = {
        row["parameter"]: f"{row['low']} to {row['high']}"
        for row in profiles
        if row["profile"] == "Transfigured"
    }
    columns = [*WORK_COLUMNS, *WORK_PARTS]
    body = []
    for row in rows:
        name = row["measure"]
        target = ranges.get(WORK_HARMONY_TARGETS.get(name, ""), "-")
        body.append(
            [
                _label(name),
                target,
                _value(name, reference.get(name, "")),
                *[_value(name, row[column]) for column in columns],
            ]
        )
    header = [
        "Measure",
        'Range of the profile "Transfigured"',
        "Verklärte Nacht",
        *[f"New work, {column}" for column in columns],
    ]
    return markdown_table(header, body)


def render_work_instruments() -> str:
    """Render the use of the players of the new work."""
    _, rows = read_table(MEASURED_DIR / "work_instruments.csv")
    body = [
        [
            row["player"],
            percent(row["share_of_time"]),
            percent(row["range_used"]) if row["range_used"] else "-",
            percent(row["low_third"]) if row["low_third"] else "-",
            percent(row["middle_third"]) if row["middle_third"] else "-",
            percent(row["high_third"]) if row["high_third"] else "-",
            row["techniques"] or "-",
        ]
        for row in rows
    ]
    header = [
        "Player",
        "Share of the time",
        "Range in use",
        "Notes in the low third",
        "Notes in the middle third",
        "Notes in the high third",
        "Techniques",
    ]
    _, unused = read_table(MEASURED_DIR / "work_unused.csv")
    names = ", ".join(row["instrument"] for row in unused) or "none"
    return (
        markdown_table(header, body)
        + f"\n\nInstruments in the list of the orchestra that have no notes: {names}."
    )


def _measured_specs() -> list[TableSpec]:
    section_columns = [
        "section",
        "content",
        "first_bar",
        "last_bar",
        "minutes",
        "share_of_time",
        "start_position",
        "mean_quarter_bpm",
        "slowest_bar_bpm",
        "fastest_bar_bpm",
        "note_starts_per_second",
        "mean_midi_volume",
    ]
    section_formats = {
        "minutes": number(2),
        "share_of_time": percent,
        "start_position": percent,
        "mean_quarter_bpm": number(0),
        "slowest_bar_bpm": number(0),
        "fastest_bar_bpm": number(0),
        "note_starts_per_second": number(1),
        "mean_midi_volume": number(0),
    }
    section_labels = {
        "mean_quarter_bpm": "Mean tempo (quarter notes in a minute)",
        "slowest_bar_bpm": "Slowest bar",
        "fastest_bar_bpm": "Fastest bar",
        "start_position": "Start (share of the time)",
        "mean_midi_volume": "Mean loudness (MIDI volume, 0 to 127)",
    }
    return [
        TableSpec(
            "M1. Verklärte Nacht: general numbers",
            MEASURED_DIR / "vn_overview.csv",
            [
                "This table gives the size, the tempo range, and the positions of the "
                "main events. A position is a share of the full duration.",
            ],
            formats={"value": number(2)},
        ),
        TableSpec(
            "M2. Verklärte Nacht: the five sections",
            MEASURED_DIR / "vn_parts.csv",
            [
                "The bar numbers of the sections are from Frisch (1993). "
                "The tempo values use the timing of the arrangement. "
                "Real recordings are slower by the factor 1.12.",
            ],
            columns=section_columns,
            formats=section_formats,
            labels=section_labels,
        ),
        TableSpec(
            "M3. Verklärte Nacht: the ten segments",
            MEASURED_DIR / "vn_segments.csv",
            [
                "This table divides section 2 and section 4 into smaller segments. "
                "The loudness and the density are highest in the development (segment 2d).",
            ],
            columns=section_columns,
            formats=section_formats,
            labels=section_labels,
        ),
        TableSpec(
            "M4. Verklärte Nacht: tempo marks",
            MEASURED_DIR / "vn_marks.csv",
            [
                "The table shows each tempo mark with its bar number. "
                "The work has 33 tempo marks in 418 bars: one mark for each 12.7 bars.",
            ],
            columns=["bar", "text"],
            labels={"text": "Tempo mark"},
            keep=lambda row: row["kind"] == "tempo",
        ),
        TableSpec(
            "M5. Verklärte Nacht: words for tempo change and expression",
            MEASURED_DIR / "vn_mark_counts.csv",
            [
                "The table shows the words that occur two times or more. "
                "The spelling is the spelling of the source.",
            ],
            keep=lambda row: int(row["count"]) >= 2,
        ),
        TableSpec(
            "M6. Verklärte Nacht: dynamic marks",
            MEASURED_DIR / "vn_dynamics.csv",
            [
                "A level mark stays in effect until the subsequent level mark. "
                "The soft levels (p and softer) are in effect for 64 percent of the time. "
                "The middle levels (mp and mf) are in effect for only 11 percent.",
            ],
            formats={"share_of_time_in_effect": percent},
        ),
        TableSpec(
            "M7. Verklärte Nacht: metres",
            MEASURED_DIR / "vn_metres.csv",
            ["The metres are the metres of the arrangement."],
            formats={"share_of_bars": percent},
        ),
        TableSpec(
            "M8. Verklärte Nacht: motion of the bass",
            MEASURED_DIR / "vn_bass_motion.csv",
            [
                "The study took the lowest note at each quarter-note beat. "
                "The table counts the interval between two different bass notes. "
                "The most frequent move of the bass is the semitone.",
            ],
            formats={"share": percent},
        ),
        TableSpec(
            "M9. Bartók, Out of Doors: the five pieces in one performance",
            MEASURED_DIR / "ood_pieces.csv",
            [
                "The data come from a MIDI capture of one piano performance. "
                "The key velocity is the force of each key stroke, from 0 to 127.",
            ],
            formats={
                "minutes": number(2),
                "note_starts_per_second": number(1),
                "mean_key_velocity": number(0),
            },
        ),
        TableSpec(
            "M10. Bartók, Fourteen Bagatelles: metres and chords",
            MEASURED_DIR / "bagatelles.csv",
            [
                "Bagatelle no. 12 is an early form of the night music style. "
                "It has five different metres in 44 bars.",
            ],
            formats={
                "chords_share_built_from_thirds": percent,
                "chords_share_with_semitone_clash": percent,
                "pitch_class_entropy_bits": number(2),
            },
        ),
        TableSpec(
            "M13. Real orchestra recordings: loudness and stereo width",
            MEASURED_DIR / "reference_recordings.csv",
            [
                "The recordings are public-domain recordings of full orchestras (Musopen). "
                "They are the reference for the sound of the audio master.",
                "The loudness unit is the LUFS (ITU-R BS.1770). "
                "The loudness range is the difference between the loud and the soft "
                "passages (EBU Tech 3342). "
                "The short-term values are relative to the integrated loudness. "
                "The side level is the level of the difference of the two channels, "
                "relative to their sum.",
            ],
        ),
        TableSpec(
            "M14. Real orchestra recordings: tone balance",
            MEASURED_DIR / "reference_tone_balance.csv",
            [
                "The table gives the level of each third-octave band, relative to the "
                "total level, for the five recordings of table M13. "
                "The master of the project must agree with the mean values from 50 Hz to 8 kHz. "
                "Above 8 kHz, some of the recordings have no content, thus the values are not "
                "a reliable target.",
            ],
        ),
    ]


def _sourced_specs() -> list[TableSpec]:
    return [
        TableSpec(
            "S1. Reference works",
            TABLES_DIR / "works.csv",
            ["The table lists the works that the study uses, and the reason for each work."],
            columns=[
                "composer",
                "work",
                "year",
                "forces",
                "minutes",
                "use_in_this_study",
                "source",
            ],
        ),
        TableSpec(
            "S2. Orchestra sizes",
            TABLES_DIR / "forces.csv",
            [
                "Each number is the number of players. "
                "A note in parentheses shows the auxiliary instruments.",
            ],
            columns=[
                "work",
                "flutes",
                "oboes",
                "clarinets",
                "bassoons",
                "horns",
                "trumpets",
                "trombones",
                "tubas",
                "timpani_and_percussion",
                "keyboards_and_harp",
                "strings",
                "special",
                "source",
            ],
        ),
        TableSpec(
            "S3. Form and proportion",
            TABLES_DIR / "form.csv",
            ["The table gives the plan of each reference work and the positions of its events."],
        ),
        TableSpec(
            "S4. Tempo",
            TABLES_DIR / "tempo.csv",
            ["The table gives metronome marks and durations from the scores and the recordings."],
        ),
        TableSpec(
            "S5. Harmony",
            TABLES_DIR / "harmony.csv",
            [
                'The column "Set type" gives the prime form of the pitch-class set. '
                "The numbers are semitones above the lowest note of the most compact form.",
            ],
        ),
        TableSpec(
            "S6. Scales and modes",
            TABLES_DIR / "scales.csv",
            [
                "The steps are distances from the tonic. "
                "The unit is the semitone, or the cent for tunings that are not equal-tempered. "
                "One semitone is 100 cents.",
            ],
        ),
        TableSpec(
            "S7. Themes and motives",
            TABLES_DIR / "motifs.csv",
            ["The table gives the shapes of themes and the methods that change them."],
        ),
        TableSpec(
            "S8. Rhythm and metre",
            TABLES_DIR / "rhythm.csv",
            [
                "The table gives metres, rhythm patterns, "
                "and methods for layers in different tempos."
            ],
        ),
        TableSpec(
            "S9. Texture and orchestration",
            TABLES_DIR / "texture.csv",
            ["The table gives the orchestration devices of the three composers."],
        ),
        TableSpec(
            "S10. Bartók's night music: list of works",
            TABLES_DIR / "night_list.csv",
            [
                'The list is from the Wikipedia article "Night music (Bartók)" '
                "(source key `wiki-stmatthew`). The article uses the list of Danchenka (1987).",
            ],
        ),
        TableSpec(
            "S12. Variation: how an idea comes again",
            TABLES_DIR / "variation.csv",
            [
                "The table gives the methods of the reference composers for the return of an "
                "idea. No row permits a return with no change.",
            ],
        ),
        TableSpec(
            "S13. Instrument techniques",
            TABLES_DIR / "techniques.csv",
            [
                "The table lists ways to play that give an instrument more colours. "
                "Table S9 gives the orchestration devices of the three composers.",
            ],
        ),
        TableSpec(
            "S14. Notes that are not in the chord",
            TABLES_DIR / "colour.csv",
            [
                "The table gives the types of notes outside the chord, and the chords that "
                "keep such notes.",
            ],
        ),
        TableSpec(
            "S15. More devices of modern orchestral writing",
            TABLES_DIR / "devices.csv",
            [
                "The table gives devices of composers after 1900. "
                "The first edition of the study did not have them."
            ],
        ),
        TableSpec(
            "S16. The piano as a soloist with the orchestra",
            TABLES_DIR / "concertante.csv",
            [
                "The owner of the project asked for a piano interlude that is virtuosic, "
                '"almost like a small piano concerto". The table gives how the reference '
                "composers and two other composers write for a solo piano with an orchestra.",
            ],
        ),
        TableSpec(
            "S11. Night music and melody from different regions of the world",
            TABLES_DIR / "world.csv",
            [
                "The table lists possible material from different regions. "
                "Most rows have the code K: the study did not read a source for them. "
                "The design stage must check the selected rows with primary sources.",
                "Each tradition has its own meaning and context. "
                "The new work must use this material with respect and with exact knowledge.",
            ],
        ),
    ]


def render_profiles() -> str:
    """Render the style profiles, one table for each profile."""
    _, rows = read_table(TABLES_DIR / "profiles.csv")
    parts = []
    titles = {
        "All": 'P1. Profile "All": the full work',
        "Transfigured": 'P2. Profile "Transfigured": the Schoenberg zone',
        "Night": 'P3. Profile "Night": the Bartók zone',
        "Theatre": 'P4. Profile "Theatre": the Corigliano zone',
    }
    for profile, title in titles.items():
        chosen = [row for row in rows if row["profile"] == profile]
        parts.append(f"### {title}")
        parts.append(
            markdown_table(
                ["Group", "Parameter", "Low", "High", "Unit", "Basis", "Code"],
                [
                    [
                        row["group"],
                        row["parameter"],
                        row["low"],
                        row["high"],
                        row["unit"],
                        row["basis"],
                        row["evidence"],
                    ]
                    for row in chosen
                ],
            )
        )
    path = (TABLES_DIR / "profiles.csv").as_posix()
    parts.append(f"Data file: [`{path}`](../{path})")
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
        "The study code made all tables of this part. "
        "The directory [`research/measured`](../research/measured) has the full data, "
        "which includes one row for each bar of *Verklärte Nacht* "
        "([`vn_bars.csv`](../research/measured/vn_bars.csv))."
    )
    parts += [spec.render() for spec in _measured_specs()]
    parts.append("### M11. Comparison of all measured works")
    parts.append(
        '"Chord time" is the time in which three or more pitch classes sound together. '
        'A "semitone clash" is two notes that are a semitone apart (in all octaves). '
        'A "cluster" is three or more adjacent semitones. '
        'A "window" is four quarter notes (score data) or four seconds (performance data). '
        'The "top line" is the highest note at each note start.'
    )
    parts.append("Abbreviations: VN = *Verklärte Nacht*. OoD = *Out of Doors*. Bag. = Bagatelle.")
    parts.append(render_fingerprints())
    parts.append(
        "Data file: [`research/measured/fingerprints.csv`](../research/measured/fingerprints.csv)"
    )
    parts.append("### M12. The most frequent sonorities")
    parts.append(
        "A sonority is the set of pitch classes that sound at one moment. "
        'A name of the form "set type (0 1 2 3 4)" gives the semitone steps of a set '
        "that has no chord name."
    )
    parts.append(
        render_sonorities(
            [
                "Schoenberg: Verklärte Nacht, complete",
                "Bartók: Out of Doors, 4. The Night's Music",
                "Bartók: Fourteen Bagatelles op. 6, complete",
            ]
        )
    )
    parts.append(
        "Data file: [`research/measured/sonorities.csv`](../research/measured/sonorities.csv)"
    )

    parts.append("### M15. Literal repetition: Verklärte Nacht and the new work")
    parts.append(
        "The table shows how frequently a bar comes again with no change. "
        "Each value is a share of the bars that have notes. "
        '"The same" means the same notes at the same positions with the same lengths. '
        "A voice is one player of the new work, or one voice of the piano arrangement of "
        "*Verklärte Nacht*. An orchestra has more voices with accompaniment figures than a "
        "piano arrangement: thus the values for one voice are not fully comparable."
    )
    parts.append(render_work_repetition())
    parts.append(
        "Data files: [`research/measured/repetition.csv`](../research/measured/repetition.csv), "
        "[`research/measured/work_repetition.csv`](../research/measured/work_repetition.csv)"
    )
    parts.append("### M16. The new work: harmony")
    parts.append(
        "The table measures the new work with the method of table M11. "
        '"The turn" is the change from the dark half to the light half of the work '
        '(the start of part 4). Part 3 is the zone of the profile "Night": '
        'the ranges of the profile "Transfigured" do not apply to it.'
    )
    parts.append(render_work_harmony())
    parts.append(
        "Data file: [`research/measured/work_harmony.csv`](../research/measured/work_harmony.csv)"
    )
    parts.append("### M17. The new work: use of the instruments")
    parts.append(
        '"Range in use" is the distance from the lowest note to the highest note of the player, '
        "as a part of the range of the instrument. "
        "The three subsequent columns divide the range of the instrument into three equal parts. "
        'The column "Techniques" lists each way to play that is not the usual way.'
    )
    parts.append(render_work_instruments())
    parts.append(
        "Data file: "
        "[`research/measured/work_instruments.csv`](../research/measured/work_instruments.csv)"
    )

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
    parts.append(
        'The profile "All" applies to the full work. '
        "The other three profiles apply to zones of the work. "
        "The design stage will decide the sequence and the mix of the zones."
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
