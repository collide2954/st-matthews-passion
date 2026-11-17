# St Matthew Passion

*St Matthew Passion* is a new setting of the St Matthew Passion of J. S. Bach (BWV 244) for one alto voice and one baroque orchestra.
Code makes all parts of the work: the style study, the music, the score, the parts, the audio, and the video.

The work is primarily in the baroque style. Its structure and its counterpoint are modern.
It uses motifs and elements of the work of Bach.

## The idea

The work of Bach has two choirs, two orchestras, and a group of soloists.
The new work has one voice: the witness.
She tells the story, she says the words of the persons, and she answers with the poems and the chorales.
The orchestra has the music of the second choir and of the crowd, with no words.

The work has two parts and 16 numbers, and its planned length is 42.7 minutes.
It keeps the German words that Bach set: it selects sentences and lines, and it does not change a word.

The document [`docs/work.md`](docs/work.md) gives the plan: the numbers, the keys, and the method of each number.

## Project status

| Stage | Result | Status |
| --- | --- | --- |
| 1. Style study | Tables of measured and sourced style parameters | First edition complete. See [`docs/style-study.md`](docs/style-study.md). |
| 2. Design | Form, words, and material of the work | Complete. The owner must examine it. See [`design`](design). |
| 3. Composition | The music, written as code | 2 of 16 numbers are written (numbers 6 and 14). See [`docs/work.md`](docs/work.md). |
| 4. Engraving | Conductor score and parts | The score of the written numbers. The parts are not examined. |
| 5. Audio | Audio from sample libraries | First previews. An instrument plays the line of the voice: no sound library of the project has a solo singer. |
| 6. Video | Score video | Not started |

## Style study

The study is in the directory [`research`](research/README.md). The full report is [`docs/style-study.md`](docs/style-study.md).

- Measured: the 370 four-part chorales of Bach (11 of them from the Passion), and 14 movements of Bach as MIDI files: the range and the moves of each voice line and instrument line, the harmony, the bass lines, and the figures of the figured bass.
- Sourced: 39 works (Bach, music for one alto of his time, and later works that use the music of Bach or the form of the Passion), the 103 sections of the Passion, 35 motifs in the music language of the project, and 30 devices of counterpoint and form.
- Style profiles: target ranges for the new work.

## Decisions of the owner

| Item | Decision |
| --- | --- |
| Voice | One alto (a mezzo-soprano or a countertenor) has all the sung text |
| Orchestra | One baroque orchestra |
| Length | About 40 minutes |
| Text | The German texts that Bach set |

The file [`design/brief.toml`](design/brief.toml) records all decisions.
It also lists the decisions that the owner must examine.

## Commands

```bash
uv sync                       # install the Python environment
make study                    # download the open data, measure it, and write the report
make test                     # run the tests
uv run stmatthew check        # find music that a player cannot play
uv run stmatthew ears --bars 19-22   # the chord at each beat, the clashes, the parallel fifths
uv run stmatthew score        # engrave the score (LilyPond)
uv run stmatthew audio --engine musescore   # render the audio (MuseScore Studio with Muse Sounds)
```

The audio command needs MuseScore Studio, the Muse Sounds libraries, and the open sample
libraries of the project (for the organ). The file
[`src/stmatthew/audio/musescore.py`](src/stmatthew/audio/musescore.py) describes the method.

## Licence

- The code is under the MIT License. See [`LICENSE`](LICENSE).
- The music, the score, the parts, the audio, the video, and the documents are under the
  Creative Commons Attribution 4.0 International licence (CC BY 4.0).
  See [`LICENSE-CC-BY-4.0`](LICENSE-CC-BY-4.0).
- The style study measures open data from other authors. These data have their own licences.
  See [`research/README.md`](research/README.md).

This repository starts from the engine of
[*Night Music for Orchestra*](https://github.com/collide2954/night-music-for-orchestra).
