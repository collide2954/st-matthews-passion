"""Make the table of the movements of the St Matthew Passion from the Wikipedia article.

The article "St Matthew Passion structure" has one table row for each movement:
the number in the Neue Bach-Ausgabe (NBA), the number in the Bach-Werke-Verzeichnis
(BWV), the voices, the key, the time signature, the instruments, the first words,
and the source of the text.

Usage:

    uv run python tools/study/movements_table.py WIKITEXT_FILE

The wikitext comes from this address (the study team read the article on 2026-11-16):
https://en.wikipedia.org/w/api.php?action=parse&page=St_Matthew_Passion_structure&prop=wikitext
The script writes `research/tables/bach_movements.csv`.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

OUTPUT = Path("research/tables/bach_movements.csv")
SOURCE_KEY = "wp-smp-structure"

FORMS = [
    (r"Chorale fantasia", "chorale fantasia"),
    (r"Chorale", "chorale"),
    (r"Aria", "aria"),
    (r"Rec", "recitative with instruments"),
    (r"Ev", "Gospel recitative"),
    (r"Ch", "chorus"),
]


def clean(text: str) -> str:
    """Remove the wiki marks from a cell."""
    text = re.sub(r"\{\{music\|time\|(\d+)\|(\d+)\}\}", r"\1/\2", text)
    text = text.replace("{{music|common-time}}", "4/4")
    text = text.replace("{{music|b}}", "-flat").replace("{{music|#}}", "-sharp")
    text = re.sub(r"\{\{lang\|de\|(.*?)(\|italic=no)?\}\}", r"\1", text)
    text = re.sub(r"\{\{[Nn]owrap\|(.*?)\}\}", r"\1", text)
    text = re.sub(r"\{\{abbr\|(.*?)\|.*?\}\}", r"\1", text)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"<br\s*/?>", " ", text)
    text = text.replace("&nbsp;", " ").replace("→", "to")
    return " ".join(text.split())


def cells_of(block: str) -> list[str]:
    """Return the cells of one table row, with no attributes."""
    cells: list[str] = []
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith(("{|", "|}", "|+")):
            continue
        if line.startswith("!"):
            line = "|" + line[1:]
        if not line.startswith("|"):
            if cells:
                cells[-1] += " " + line
            continue
        for part in line[1:].split("||"):
            # A cell can start with attributes: `align="center" | 12`.
            attribute = re.match(r"\s*(?:(?:row|col)span|align|scope|style)=[^|]*\|(?!\|)", part)
            if attribute:
                part = part[attribute.end() :]
            cells.append(part.strip())
    return cells


def form_of(voices: str, text_from: str) -> str:
    """Return the form of a movement from its voices and from the source of its text."""
    if "Chorale S" in voices:
        return "chorus with a chorale"
    if "Rec" in voices and "Chorale" in voices:
        return "recitative with instruments"
    for pattern, name in FORMS:
        if re.search(pattern, voices):
            if name == "chorus":
                # The crowd of the Gospel text, or a chorus on a poem.
                return "chorus of the crowd" if text_from.startswith("Mt") else "chorus"
            return name
    return "chorus"


def main(path: str) -> None:
    wikitext = Path(path).read_text(encoding="utf-8")
    start = wikitext.index("==Movements==")
    end = wikitext.index("==References==")
    rows = []
    part = 0
    bwv = ""
    for table in wikitext[start:end].split("{|")[1:]:
        part += 1
        for block in re.split(r"\n\|-[^\n]*", table)[1:]:
            number = re.search(r'!\s*scope="row"\s*\|\s*(\d+[a-e]?)', block)
            if not number:
                continue
            cells = [clean(cell) for cell in cells_of(block)]
            cells = [cell for cell in cells if not cell.startswith("File:")]
            nba = cells[0]
            rest = cells[1:]
            if rest and re.fullmatch(r"\d+", rest[0]):
                bwv = rest[0]
                rest = rest[1:]
            key_at = next(i for i, cell in enumerate(rest) if re.search(r"\b(major|minor)\b", cell))
            voices = ", ".join(cell for cell in rest[:key_at] if cell)
            key = rest[key_at]
            metre, instruments, text, source = (rest[key_at + 1 : key_at + 5] + [""] * 4)[:4]
            rows.append(
                [nba, bwv, part, form_of(voices, source), voices, key, metre, instruments, text,
                 source, SOURCE_KEY, "R"]
            )  # fmt: skip
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            ["nba", "bwv", "part", "form", "voices", "key", "metre", "instruments", "first_words",
             "text_from", "source", "evidence"]
        )  # fmt: skip
        writer.writerows(rows)
    print(f"{OUTPUT}: {len(rows)} rows")


if __name__ == "__main__":
    main(sys.argv[1])
