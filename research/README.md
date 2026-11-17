# Style study

This directory contains the style study for the new setting of the *St Matthew Passion*.
The study gives the style of the work of Bach, and the methods of related works, as numbers and tables.
The design of the new work and the composition code use these tables.

The full report is [`docs/style-study.md`](../docs/style-study.md).

## Contents

| Path | Contents | How it is made |
| --- | --- | --- |
| [`tables/`](tables) | Sourced tables: works, the movements of the Passion, its elements, its motifs, its chorales, instruments, devices of counterpoint and form, figures of musical speech, performance practice | Written by the study team from the sources |
| [`tables/bach_movements.csv`](tables/bach_movements.csv) | One row for each section of the Passion | Made from the Wikipedia article by `tools/study/movements_table.py` |
| [`tables/profiles.csv`](tables/profiles.csv) | Style profiles: target ranges for the new work | Written by the study team from the measured and sourced values |
| [`measured/`](measured) | Measured tables | Made by the study code |
| [`sources.csv`](sources.csv) | List of all sources | Written by the study team |
| [`corpus.sha256`](corpus.sha256) | Checksums of the open data files | Made by `uv run stmatthew-study fetch --record` |
| [`text/`](text) | Text sections of the report | Written by the study team |

## Evidence codes

Each row of a sourced table has an evidence code.

| Code | Meaning |
| --- | --- |
| M | The study code measured the value. |
| R | The study team read the source. The row gives the key of the source. |
| K | The row is standard reference knowledge. The study team did not read a source for the row. |
| R, K | A part of the row comes from a source, and a part is reference knowledge. |

## Open data

The study measures two sets of open data.
The repository does not contain these files.
The study code downloads them into the directory `.cache/corpus`.

| Data | Author | Licence |
| --- | --- | --- |
| 370 four-part chorales of J. S. Bach, Humdrum kern files | Craig Stuart Sapp | CC BY-NC-SA 4.0 |
| 14 movements of J. S. Bach, MIDI files, and the text sources of 9 of them | Nancho Alvarez (editor) | No licence statement on the site |

The study code reads these files as data. It does not run a program on them.
The study code verifies the checksum of each file after the download.
If a file changed at its source, the code stops and shows a message.

## How to build the study

1. Install the Python environment:

   ```bash
   uv sync
   ```

2. Build the study:

   ```bash
   make study
   ```

The command does these steps:

1. It downloads the open data files (`make fetch`).
2. It measures the data and writes the files in `measured/` (`make measure`).
3. It checks the sourced tables for errors (`make check`).
4. It writes the report `docs/style-study.md` (`make report`).

## How to add a row to a sourced table

1. Read the source.
2. If the source is new, add it to `sources.csv` with a new key.
3. Add the row to the applicable file in `tables/`.
4. Put the key of the source in the column `source`.
5. Put the evidence code in the column `evidence`.
6. Run `make check`.
7. Run `make report`.

## Rules for the tables

- Each value must have a source or a measurement.
- A row with the code K must cite the key `reference`.
- A row with the code R must not cite the key `reference`.
- Each source of the list must be in one row or more.
- Do not copy music notation or audio from sources that have a copyright.
  Facts, numbers, and short descriptions are permitted.
  The music of Bach is in the public domain: the table of motifs gives its notes.
