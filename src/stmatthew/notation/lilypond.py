"""Write the conductor score and the parts as LilyPond files."""

from __future__ import annotations

import bisect
from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import accumulate
from pathlib import Path

from . import combine, cues, frontmatter, music, techniques, turns
from .pitch import Interval
from .structure import Bar, global_to_lilypond
from .work import Instrument, Player, Work

LILYPOND_VERSION = "2.26.0"

STYLE = r"""
% Style of the St Matthew Passion. The build code writes this file.

#(define-markup-command (rehearsal layout props text) (markup?)
   "A rehearsal mark: a bold letter in a box. The size is in points."
   (interpret-markup layout props
     (markup #:override '(box-padding . 0.5) #:box #:bold #:abs-fontsize @REHEARSAL@ text)))

#(define-markup-command (tempochange layout props text) (markup?)
   "A gradual change of tempo, for example rit."
   (interpret-markup layout props
     (markup #:normal-text #:italic #:fontsize 1 text)))

#(define-markup-command (instrumentchange layout props text) (markup?)
   "A change of instrument for one player."
   (interpret-markup layout props
     (markup #:box #:pad-markup 0.3 #:fontsize -1 text)))

#(define-markup-command (tochange layout props text) (markup?)
   "The notice after the last note on an instrument: take a different instrument."
   (interpret-markup layout props
     (markup #:normal-text #:italic text)))

#(define-markup-command (cue layout props text) (markup?)
   "The name of the instrument of a cue in a part."
   (interpret-markup layout props
     (markup #:normal-text #:fontsize 2 text)))

#(define-markup-command (players layout props text) (markup?)
   "The players of a staff for two players: 1., 2., or a 2."
   (interpret-markup layout props
     (markup #:normal-text text)))

#(define-markup-command (pairname layout props name upper lower) (markup? markup? markup?)
   "The name of a staff for two players: the name, then the two numbers, one above the other."
   (interpret-markup layout props
     #{ \markup \line {
          \vcenter #name
          \vcenter \override #'(baseline-skip . 2.3) \column { #upper #lower }
        } #}))

#(define-markup-command (extraname layout props name player) (markup? markup?)
   "The name of a staff for the second instrument of a player, with the player below it."
   (interpret-markup layout props
     #{ \markup \override #'(baseline-skip . 2.3) \right-column {
          #name
          \fontsize #-1.5 #player
        } #}))

% Dynamic marks that LilyPond does not have.
sffz = #(make-dynamic-script "sffz")
sfpp = #(make-dynamic-script "sfpp")
ffp = #(make-dynamic-script "ffp")
pf = #(make-dynamic-script "pf")
"""

SCORE_LAYOUT = r"""
\layout {
  \context {
    % A line for the tempo marks and the rehearsal marks. The score has one above the
    % woodwinds and one above the strings: a conductor reads them near each group.
    \type Engraver_group
    \name MarkLine
    \consists Axis_group_engraver
    \consists Mark_engraver
    \consists Metronome_mark_engraver
    \override VerticalAxisGroup.staff-affinity = #DOWN
    \override VerticalAxisGroup.nonstaff-relatedstaff-spacing.padding = #1.8
    \override VerticalAxisGroup.nonstaff-unrelatedstaff-spacing.padding = #2.5
    \override MetronomeMark.font-size = #4.5
    \override RehearsalMark.self-alignment-X = #LEFT
    \override RehearsalMark.break-align-symbols = #'(left-edge staff-bar)
    \override RehearsalMark.extra-spacing-width = #'(+inf.0 . -inf.0)
    \override MetronomeMark.extra-spacing-width = #'(+inf.0 . -inf.0)
    % The marks have fixed places in this line: they do not look for a staff. The
    % tempo mark and the rehearsal mark are on the base line. A rehearsal mark at a
    % tempo mark is a part of the tempo mark: the two are side by side.
    \override RehearsalMark.outside-staff-priority = ##f
    \override MetronomeMark.outside-staff-priority = ##f
    \override MetronomeMark.Y-offset = #0
    \override RehearsalMark.Y-offset = #0
  }
  \context {
    % The first page shows all staves. The staves can be a little nearer than the
    % usual smallest distance: thus that page is not too full.
    \StaffGroup
    \override StaffGrouper.staff-staff-spacing.minimum-distance = #6.4
    \override StaffGrouper.staffgroup-staff-spacing.minimum-distance = #7.6
  }
  \context {
    \Score
    \remove Mark_engraver
    \remove Metronome_mark_engraver
    \accepts MarkLine
    \override BarNumber.font-size = #3
    \override BarNumber.font-shape = #'italic
    \override BarNumber.padding = #1.5
    \override InstrumentName.self-alignment-X = #RIGHT
    \override InstrumentName.padding = #0.8
    \override InstrumentName.font-size = #1
    \override Hairpin.minimum-length = #5
    \override SpacingSpanner.common-shortest-duration = #(ly:make-moment 1/16)
    skipBars = ##f
  }
  \context {
    \Staff
    \RemoveEmptyStaves
    \override VerticalAxisGroup.remove-first = ##f
    \override TextScript.font-size = #-0.5
    \override DynamicTextSpanner.style = #'none
  }
  \context {
    \PianoStaff
    \override InstrumentName.self-alignment-X = #RIGHT
  }
}
"""

PART_LAYOUT = r"""
\layout {
  \context {
    \Score
    \override BarNumber.font-size = #0
    \override BarNumber.font-shape = #'italic
    \override MetronomeMark.font-size = #1.5
    \override MetronomeMark.padding = #2.5
    % A tempo mark takes its own width. Thus the marks of a long rest are side by
    % side, and they are not one above the other.
    \override MetronomeMark.extra-spacing-width = #'(-0.5 . 1.0)
    \override RehearsalMark.extra-spacing-width = #'(-0.5 . 0.5)
    \override RehearsalMark.padding = #2.5
    \override MultiMeasureRest.expand-limit = #1
    % A hairpin after a dynamic mark in a bar with one note must have space.
    \override Hairpin.minimum-length = #8
    \override SpacingSpanner.common-shortest-duration = #(ly:make-moment 1/16)
    skipBars = ##t
  }
  \context {
    \Staff
    \override TextScript.font-size = #-0.5
    \override DynamicTextSpanner.style = #'none
  }
}
"""

SCORE_PAPER = r"""
\paper {
  #(set-paper-size "11x17")
  % Pages for a print on the two sides of the paper: the inner margin is for the binding.
  two-sided = ##t
  inner-margin = 18\mm
  outer-margin = 13\mm
  top-margin = 12\mm
  bottom-margin = 14\mm
  indent = 32\mm
  short-indent = 15\mm
  system-separator-markup = \slashSeparator
  ragged-last-bottom = ##f
  print-page-number = ##t
  bookpart-level-page-numbering = ##t
  % Space between the last staff of a page and the copyright line.
  last-bottom-spacing.padding = #2.5
  % The first page of music: the type of the score on the left, the title in the
  % middle, the composer on the right. The sizes are in points.
  bookTitleMarkup = \markup \column {
    \fill-line { \abs-fontsize #25 \bold \fromproperty #'header:title }
    \vspace #0.9
    \fill-line {
      \abs-fontsize #12 \italic \fromproperty #'header:poet
      \abs-fontsize #13 \fromproperty #'header:composer
    }
    \vspace #0.4
  }
  % The page number is in the outer corner, 14 point. The title is in each header.
  oddHeaderMarkup = \markup \fill-line {
    \null
    \unless \on-first-page-of-part \abs-fontsize #9 \italic \fromproperty #'header:title
    \if \should-print-page-number \abs-fontsize #14 \fromproperty #'page:page-number-string
  }
  evenHeaderMarkup = \markup \fill-line {
    \if \should-print-page-number \abs-fontsize #14 \fromproperty #'page:page-number-string
    \unless \on-first-page-of-part \abs-fontsize #9 \italic \fromproperty #'header:title
    \null
  }
}
"""

PART_PAPER = r"""
\paper {
  #(set-paper-size "arch a")
  % 9 x 12 inches: a usual size for parts, and the largest size for a digital part.
  % The margins are those of the guidelines of the orchestra librarians (20 mm).
  two-sided = ##t
  inner-margin = 19\mm
  outer-margin = 17\mm
  top-margin = 13\mm
  bottom-margin = 15\mm
  indent = 12\mm
  ragged-last-bottom = ##t
  print-page-number = ##t
  % A page turn is only at a bar line that the code permits: the player has a rest
  % there, and the rest gives the time to turn the page (see `turns.py`).
  page-breaking = #ly:page-turn-breaking
  % Not more than 12 staves on a page (the guidelines of the orchestra librarians):
  % the middle lines of two systems are 12 staff spaces apart or more.
  system-system-spacing.minimum-distance = #12
  % The first page: the instrument in the upper left corner, the composer on the right,
  % and the title in the middle below them. The name of an instrument can be long:
  % thus it is not on the line of the title. The sizes are in points.
  bookTitleMarkup = \markup \column {
    \fill-line {
      \abs-fontsize #15 \bold \fromproperty #'header:instrument
      \abs-fontsize #12 \fromproperty #'header:composer
    }
    \fill-line { \abs-fontsize #21 \bold \fromproperty #'header:title }
    \vspace #0.8
  }
  % Each subsequent page: the instrument and the title, and the page number in the
  % outer corner.
  oddHeaderMarkup = \markup \fill-line {
    \null
    \unless \on-first-page-of-part \abs-fontsize #9.5 \concat {
      \bold \fromproperty #'header:instrument "   " \italic \fromproperty #'header:title
    }
    \if \should-print-page-number \abs-fontsize #13 \fromproperty #'page:page-number-string
  }
  evenHeaderMarkup = \markup \fill-line {
    \if \should-print-page-number \abs-fontsize #13 \fromproperty #'page:page-number-string
    \unless \on-first-page-of-part \abs-fontsize #9.5 \concat {
      \bold \fromproperty #'header:instrument "   " \italic \fromproperty #'header:title
    }
    \null
  }
}
"""


def identifier(player_id: str) -> str:
    """Return a LilyPond variable name for a player (letters only)."""
    letters = "".join(
        chr(ord("A") + int(char) - 1) if char.isdigit() else char for char in player_id
    )
    return "music" + letters[0].upper() + letters[1:].replace(".", "")


@dataclass
class _Emitter:
    """Write the music of one player. The interval changes when the player changes instrument."""

    work: Work
    for_part: bool
    left_hand: bool = False
    interval: Interval | None = None
    pedal_down: bool = False  # the sustain pedal is down at this point of the file
    instrument_name: str = ""  # the instrument that the player has at this point

    def set_instrument(self, instrument: Instrument | None) -> None:
        self.instrument_name = instrument.name if instrument is not None else ""
        if instrument is None:
            self.interval = None
        else:
            self.interval = instrument.part_interval if self.for_part else instrument.score_interval

    def clef_of(self, instrument: Instrument | None) -> str:
        if instrument is None:
            return "percussion"
        clef = instrument.clef if self.for_part else instrument.score_clef
        if clef == "grand":
            return "bass" if self.left_hand else "treble"
        return clef

    def emit(self, elements: list[music.Element], *, top: bool = True) -> str:
        """Return the LilyPond text of the elements. `top` is true for all music of a player."""
        parts = []
        splits = _rest_splits(self.work) if top else frozenset()
        for element in _merge_full_bar_rests(elements, splits):
            if isinstance(element, music.Command) and element.name == "switch":
                name = element.arguments[0].strip('"')
                if name == self.instrument_name:
                    continue  # the player has this instrument: no mark
                instrument = self.work.orchestra.instruments.get(name)
                self.set_instrument(instrument)
                label = _change_label(name)
                parts.append(
                    f'\\clef {self.clef_of(instrument)} <>^\\markup \\instrumentchange "{label}"'
                )
            elif isinstance(element, music.Group) and element.kind == "cue":
                # The rests of the player are low, and the small notes of the cue have
                # stems up.
                rests, notes = (self.emit(child.children, top=False) for child in element.children)
                parts.append(
                    f"<< {{ \\voiceTwo {rests} \\oneVoice }} "
                    f"\\new CueVoice {{ \\voiceOne {notes} }} >>"
                )
            elif isinstance(element, music.Group) and element.kind == "parallel":
                voices = [
                    f"{{ {self.emit(child.children, top=False)} }}" for child in element.children
                ]
                parts.append("<< " + " \\\\ ".join(voices) + " >>")
            elif isinstance(element, music.Group):
                inner = self.emit(element.children, top=False)
                prefix = f"{element.header} " if element.kind != "sequence" else ""
                parts.append(f"{prefix}{{ {inner} }}")
            else:
                parts.append(music.to_lilypond(self._pedal(element), self.interval))
        return " ".join(parts).replace("\n ", "\n")

    def _pedal(self, element: music.Element) -> music.Element:
        """Remove a release of the sustain pedal that has no push before it in this file.

        A file with a part of the work (a page of the video) can start while the
        pedal is down. LilyPond does not print a pedal change that starts with a
        release only.
        """
        posts = getattr(element, "posts", None)
        if not posts:
            return element
        kept, changed = [], False
        for post in posts:
            if post.kind == "command" and post.value == "sustainOn":
                self.pedal_down = True
            elif post.kind == "command" and post.value == "sustainOff":
                if not self.pedal_down:
                    changed = True
                    continue
                self.pedal_down = False
            kept.append(post)
        return replace(element, posts=kept) if changed else element


def _rest_text(quarters: Fraction) -> str:
    """Return the length of a full-bar rest as LilyPond text, for example "1*7/8"."""
    whole = quarters / 4
    return f"1*{whole.numerator}" if whole.denominator == 1 else f"1*{whole}"


def _cut_long_rests(
    elements: list[music.Element], splits: frozenset[Fraction]
) -> list[music.Element]:
    """Cut each full-bar rest of many bars at the positions of `splits` that are in it."""
    if not splits:
        return elements
    ordered = sorted(splits)
    result: list[music.Element] = []
    position = Fraction(0)
    for element in elements:
        start = position
        position += music.length(element)
        if not (isinstance(element, music.Rest) and element.kind == "R"):
            result.append(element)
            continue
        low = bisect.bisect_right(ordered, start)
        inside = ordered[low : bisect.bisect_left(ordered, position)]
        if not inside:
            result.append(element)
            continue
        edges = [start, *inside, position]
        for number, (first, last) in enumerate(zip(edges, edges[1:], strict=False)):
            posts = list(element.posts) if number == 0 else []
            result.append(music.Rest("R", last - first, _rest_text(last - first), posts))
            if number < len(edges) - 2:
                result.append(music.BarCheck())
    return result


def _merge_full_bar_rests(
    elements: list[music.Element], splits: frozenset[Fraction] = frozenset()
) -> list[music.Element]:
    """Join adjacent full-bar rests into one rest.

    LilyPond shows one long rest as a rest with a number in the parts. It does
    not join rests that are written one bar at a time.

    `splits` are positions in the work (in quarter notes, from the first
    element) at which a new rest must start. A part shows each change of tempo
    also in a long rest: thus a long rest stops at a tempo mark.
    """
    merged: list[music.Element] = []
    run: music.Rest | None = None
    position = Fraction(0)
    for element in _cut_long_rests(elements, splits):
        start = position
        position += music.length(element)
        full_bar = isinstance(element, music.Rest) and element.kind == "R"
        plain_rest = full_bar and not element.posts
        # A full-bar rest at which a hairpin stops can be the first rest of a long rest.
        # A rest with the notice of a change of instrument also.
        stop_only = (
            full_bar
            and bool(element.posts)
            and all((p.kind, p.value) in (("hairpin", "!"), ("text", "to")) for p in element.posts)
        )
        if run is not None and full_bar and start in splits:
            merged.append(music.BarCheck())
            run = None
        if plain_rest or (stop_only and run is None):
            if run is None:
                run = music.Rest("R", element.duration, "", list(element.posts))
                merged.append(run)
            else:
                run.duration += element.duration
            run.duration_text = _rest_text(run.duration)
        elif isinstance(element, music.BarCheck) and run is not None:
            continue
        else:
            if run is not None:
                merged.append(music.BarCheck())
                run = None
            merged.append(element)
    if run is not None:
        merged.append(music.BarCheck())
    return merged


def _rest_splits(work: Work) -> frozenset[Fraction]:
    """Return the positions at which a long rest of a part must stop and start again.

    These are the start and the end of each bar that has a tempo mark or a
    change of tempo in words.
    """
    structure = work.structure
    positions: set[Fraction] = set()
    for point in structure.tempo_points:
        if point.text or point.unit:
            bar = structure.bar_at(min(point.position, structure.length - Fraction(1, 64)))
            positions.add(bar.start)
            if point.position > bar.start:
                positions.add(bar.end)
    return frozenset(positions)


def _pitches(elements: list[music.Element]) -> list[float]:
    """Return the MIDI numbers of all notes in the elements."""
    found: list[float] = []
    for element in elements:
        if isinstance(element, music.Note):
            found.extend(note_pitch.pitch.midi for note_pitch in element.pitches)
        elif isinstance(element, music.Group):
            found.extend(_pitches(element.children))
    return found


def best_clef(
    base: str, instrument: Instrument | None, written: list[float], current: str = ""
) -> str:
    """Return the clef for a passage: the usual clef, or a better clef for its range.

    `current` is the clef before the passage. A hand of a keyboard instrument
    keeps its clef until the notes are clearly in the range of the other clef.
    """
    if not written or instrument is None or base in ("percussion", "grand"):
        return current or base
    ordered = sorted(written)
    median, lowest = ordered[len(ordered) // 2], ordered[0]
    if instrument.clef == "grand":
        # Between A-flat 3 and E4 (the notes near middle C), the hand keeps its clef.
        # A passage with a very low note is in the bass clef (for example a low grace
        # note before a figure that goes up).
        if (current or base) == "bass":
            return "treble" if median >= 64 and lowest >= 55 else "bass"
        return "bass" if (median <= 56 and ordered[-1] <= 65) or lowest < 45 else "treble"
    if base == "treble" and instrument.name == "horn in F" and median < 55:
        return "bass"
    if base == "bass" and instrument.name == "bass clarinet" and median > 62:
        return "treble"
    tenor_instruments = ("bassoon", "violoncello", "tenor trombone")
    if base == "bass" and instrument.name in tenor_instruments and median > 66 and lowest >= 55:
        return "tenor"
    if base == "alto" and median > 81 and lowest > 67:
        return "treble"
    return base


def best_ottava(clef: str, instrument: Instrument | None, written: list[float]) -> int:
    """Return the octave sign for a passage: 1 = one octave higher, -1 = lower, 0 = none.

    A passage that is all very high is easier to read with an octave sign.
    The low octaves of a keyboard instrument get the sign for the lower octave.
    """
    if not written or instrument is None:
        return 0
    ordered = sorted(written)
    low_part = ordered[len(ordered) // 10]
    if clef == "treble" and ordered[-1] >= 93 and low_part >= 81:
        return 1
    if clef == "bass" and instrument.clef == "grand" and ordered[0] < 31 and ordered[-1] <= 55:
        return -1
    return 0


def _with_clefs(
    work: Work, player: Player, chunks: list[music.Group], emitter: _Emitter, instrument
) -> list[music.Element]:
    """Return the music of the chunks with a clef command where the best clef changes."""
    elements: list[music.Element] = []
    first_instrument = instrument
    # A staff starts with the usual clef of the instrument that plays first, also if
    # the player starts with rests.
    current = emitter.clef_of(_first_played(work, chunks, instrument))
    elements.append(music.Command("clef", [current]))
    ottava = 0
    position = Fraction(0)  # the start of the unit in the work, in quarter notes
    for chunk in chunks:
        # A hand of a keyboard instrument can change its clef in each bar: its music
        # moves through the full keyboard. Other instruments have one clef for a section.
        grand = instrument is not None and instrument.clef == "grand"
        units = _bars_of(chunk.children) if grand else _instrument_units(chunk.children)
        for unit in units:
            if len(unit) == 1 and _is_switch(unit[0]):
                # A change of instrument changes the usual clef.
                instrument = work.orchestra.instruments.get(unit[0].arguments[0].strip('"'))
                emitter.set_instrument(instrument)
                current = emitter.clef_of(instrument)
                elements.extend(unit)
                continue
            start = position
            position += sum((music.length(element) for element in unit), Fraction(0))
            shift = emitter.interval.semitones if emitter.interval else 0
            written = [midi + shift for midi in _pitches(unit)]
            if grand and not written:
                elements.extend(unit)
                continue
            pieces = [unit]
            if grand and max(written) - min(written) > WIDE_BAR:
                # A line that goes through much of the keyboard in one bar: each beat
                # group of the bar can have its own clef and its own octave sign.
                pieces = _beat_pieces(unit, _beat_groups(work.structure.bar_at(start)))
            for piece in pieces:
                notes = [midi + shift for midi in _pitches(piece)]
                if not notes:
                    elements.extend(piece)
                    continue
                clef = best_clef(emitter.clef_of(instrument), instrument, notes, current)
                if clef != current:
                    elements.append(music.Command("clef", [clef]))
                    current = clef
                octave = best_ottava(clef, instrument, notes)
                if octave != ottava:
                    elements.append(music.Command("ottava", [f"#{octave}"]))
                    ottava = octave
                elements.extend(piece)
    emitter.set_instrument(first_instrument)
    return _ottava_at_notes(elements)


def _is_switch(element: music.Element) -> bool:
    return isinstance(element, music.Command) and element.name == "switch"


def _instrument_units(elements: list[music.Element]) -> list[list[music.Element]]:
    """Divide the music of a section at each change of instrument.

    A change of instrument is a unit of its own. The music between two
    changes is one unit: it gets one clef.
    """
    units: list[list[music.Element]] = [[]]
    for element in elements:
        if _is_switch(element):
            units.extend([[element], []])
        else:
            units[-1].append(element)
    return [unit for unit in units if unit]


def placed_switches(work: Work, player: Player, chunks: list[music.Group]) -> list[music.Group]:
    """Put each change of instrument at the first note on the new instrument.

    The composer writes a change of instrument at some point of a rest. The
    player must know two things. After the last note on the old instrument,
    the words "to ..." tell the player to take the new instrument. At the
    first note on the new instrument, a box has its name.

    A percussion player has many instruments: the first note also gets the
    name of its instrument.
    """
    flat = [(index, element) for index, chunk in enumerate(chunks) for element in chunk.children]
    result: list[tuple[int, music.Element]] = []
    many = player.family == "percussion" and len(player.instruments) > 1
    current = "" if many else player.instruments[0]
    pending: music.Command | None = None
    last_note: int | None = None
    for index, element in flat:
        if _is_switch(element):
            pending = element
            continue
        if _pitches([element]):
            if pending is None and not current:
                pending = music.Command("switch", [f'"{player.instruments[0]}"'])
            if pending is not None:
                name = pending.arguments[0].strip('"')
                if name != current:
                    if current and last_note is not None:
                        _add_notice(result, last_note, name)
                    result.append((index, pending))
                    current = name
                pending = None
            last_note = len(result)
        result.append((index, element))
    return [
        music.Group("sequence", [element for number, element in result if number == index])
        for index in range(len(chunks))
    ]


def _change_label(name: str) -> str:
    return name[0].upper() + name[1:]


def _add_notice(result: list[tuple[int, music.Element]], last_note: int, name: str) -> None:
    """Give the words "to ..." to the first rest after the last note on the old instrument."""
    for number in range(last_note + 1, len(result)):
        index, element = result[number]
        if isinstance(element, music.Rest):
            notice = music.Post("text", f'^\\markup \\tochange "to {_change_label(name)}"', "to")
            posts = [*element.posts, notice]
            copy = music.Rest(element.kind, element.duration, element.duration_text, posts)
            result[number] = (index, copy)
            return


def _first_played(work: Work, chunks: list[music.Group], instrument: Instrument | None):
    """Return the instrument of the first note of a player (None: it has no pitch)."""
    for chunk in chunks:
        for element in chunk.children:
            if isinstance(element, music.Command) and element.name == "switch":
                return work.orchestra.instruments.get(element.arguments[0].strip('"'))
            if _pitches([element]):
                return instrument
    return instrument


# An octave sign stops at a silence of this length (in quarter notes) or more.
OTTAVA_REST = Fraction(4)


def _ottava_at_notes(elements: list[music.Element]) -> list[music.Element]:
    """Stop each octave sign at a long silence, and start it again at the subsequent note.

    LilyPond continues an octave sign until a command stops it. A sign that
    goes through the bars of a long rest is wrong.
    """
    # The length of the silence that starts at each element with no notes.
    silence: dict[int, Fraction] = {}
    index = 0
    while index < len(elements):
        scan, length = index, Fraction(0)
        while scan < len(elements) and not _pitches([elements[scan]]):
            length += music.length(elements[scan])
            scan += 1
        if scan > index:
            silence[index] = length
        index = max(scan, index + 1)
    result: list[music.Element] = []
    wanted = shown = 0
    for index, element in enumerate(elements):
        if isinstance(element, music.Command) and element.name == "ottava":
            wanted = int(element.arguments[0].lstrip("#"))
            continue  # the subsequent note gets the sign
        if silence.get(index, Fraction(0)) >= OTTAVA_REST and shown:
            result.append(music.Command("ottava", ["#0"]))
            shown = 0
        if wanted != shown and _pitches([element]):
            result.append(music.Command("ottava", [f"#{wanted}"]))
            shown = wanted
        result.append(element)
    return result


# A bar of one hand of a keyboard instrument that is wider than this (in semitones)
# can have more than one clef.
WIDE_BAR = 19


def _beat_groups(bar: Bar) -> list[Fraction]:
    """Return the length of each beat group of a bar, in quarter notes."""
    if bar.grouping:
        return [Fraction(4 * size, bar.denominator) for size in bar.grouping]
    beat = Fraction(3, 2) if bar.denominator == 8 and bar.numerator % 3 == 0 else Fraction(1)
    count = int(bar.length / beat)
    groups = [beat] * count
    if bar.length > beat * count:
        groups.append(bar.length - beat * count)
    return groups


def _beat_pieces(
    elements: list[music.Element], groups: list[Fraction]
) -> list[list[music.Element]]:
    """Divide the music of one bar at the ends of its beat groups.

    A tuplet or a different group stays in one piece. A grace note or a
    command at the start of a beat group goes with that beat group.
    """
    edges = list(accumulate(groups))
    pieces: list[list[music.Element]] = [[]]
    position = Fraction(0)
    has_time = False
    for element in elements:
        if has_time and edges and position >= edges[0]:
            pieces.append([])
            has_time = False
        while edges and position >= edges[0]:
            edges.pop(0)
        pieces[-1].append(element)
        duration = music.length(element)
        position += duration
        has_time = has_time or duration > 0
    return pieces


def _bars_of(elements: list[music.Element]) -> list[list[music.Element]]:
    """Divide the music of a section into bars. Each bar ends with its bar check."""
    bars: list[list[music.Element]] = []
    current: list[music.Element] = []
    for element in elements:
        current.append(element)
        if isinstance(element, music.BarCheck):
            bars.append(current)
            current = []
    if current:
        bars.append(current)
    return bars


def _with_cues(
    work: Work, player: Player, elements: list[music.Element], part_cues: list[cues.Cue]
) -> list[music.Element]:
    """Put the cues of a part into the music of a staff of the part.

    A cue replaces the full-bar rests before an entry. The notes of the cue
    are in the octave that is best for the clef of the staff at that point.
    """
    if not part_cues:
        return elements
    structure = work.structure
    edges = {
        bar.start
        for cue in part_cues
        for bar in structure.bars
        if cue.start <= bar.start <= cue.end
    }
    by_start = {cue.start: cue for cue in part_cues}
    tracker = _Emitter(work, True, left_hand=player.id.endswith(".lh"))
    instrument = work.orchestra.first_instrument(player.id)
    tracker.set_instrument(instrument)
    clef = tracker.clef_of(instrument)
    cut = _cut_long_rests(elements, frozenset(edges))
    result: list[music.Element] = []
    position = Fraction(0)
    index = 0
    while index < len(cut):
        element = cut[index]
        if isinstance(element, music.Command) and element.name == "clef":
            clef = element.arguments[0]
        elif isinstance(element, music.Command) and element.name == "switch":
            instrument = work.orchestra.instruments.get(element.arguments[0].strip('"'))
            tracker.set_instrument(instrument)
            clef = tracker.clef_of(instrument)
        cue = by_start.get(position)
        if cue is not None and isinstance(element, music.Rest) and element.kind == "R":
            rests: list[music.Element] = []
            scan, end = index, position
            while scan < len(cut) and end < cue.end:
                item = cut[scan]
                if isinstance(item, music.Rest) and item.kind == "R":
                    end += item.duration
                elif not isinstance(item, music.BarCheck):
                    break
                rests.append(item)
                scan += 1
            if end == cue.end:
                shift = tracker.interval.semitones if tracker.interval else 0
                unpitched = clef not in cues.CLEF_CENTRE
                notes = cues.fitted(
                    combine.copied(cue.elements), "treble" if unpitched else clef, shift
                )
                first = next(iter(combine.timed(notes)), None)
                if first is not None:
                    first.posts.insert(0, music.Post("text", f'^\\markup \\cue "{cue.label}"'))
                if unpitched:
                    # A staff for instruments with no pitch: the cue has its own clef.
                    notes.insert(0, music.Command("cueClef", ['"treble"']))
                    notes.append(music.Command("cueClefUnset"))
                groups = [music.Group("sequence", rests), music.Group("sequence", notes)]
                result.append(music.Group("cue", groups, cue.label))
                del by_start[position]
                position, index = end, scan
                continue
        result.append(element)
        position += music.length(element)
        index += 1
    return result


def _player_music(
    work: Work, player: Player, *, for_part: bool, part_cues: list[cues.Cue] | None = None
) -> str:
    emitter = _Emitter(work, for_part, left_hand=player.id.endswith(".lh"))
    instrument = work.orchestra.first_instrument(player.id)
    emitter.set_instrument(instrument)
    chunks = [chunk for _first_bar, chunk in work.chunks.get(player.id, [])]
    chunks = placed_switches(work, player, chunks)
    elements = _with_clefs(work, player, chunks, emitter, instrument)
    if part_cues:
        elements = _with_cues(work, player, elements, part_cues)
    if player.family == "percussion" and len(player.instruments) > 1:
        emitter.instrument_name = ""  # the first note gets the name of its instrument
    return emitter.emit(elements)


def _header(work: Work, instrument_line: str = "", document: str = "") -> str:
    """Return the header of the music: title, composer, and the name of the part.

    `document` is the type of a score ("Score in C" or "Transposed score"): it
    is in the upper left corner of the first page of music.
    """
    lines = [
        "\\header {",
        f'  title = "{work.title}"',
        f'  subtitle = "{work.subtitle}"' if work.subtitle else "",
        f'  composer = "{work.composer}"' if work.composer else "",
        f'  instrument = "{instrument_line}"' if instrument_line else "",
        f'  poet = "{document}"' if document else "",
        f'  copyright = "{frontmatter.copyright_line(work)}"',
        "  tagline = ##f",
        "}",
    ]
    return "\n".join(line for line in lines if line)


def shared_staves(work: Work, breaks: set[int]) -> dict[str, combine.SharedStaff]:
    """Return the staves of the conductor score that two players share.

    The key is the identifier of player 1. `breaks` are the bars after which a
    system of the score ends.
    """
    present = {player.id for player in work.orchestra.players}
    system_bars = frozenset({1} | {bar + 1 for bar in breaks})
    return {
        first: combine.shared_staff(work, first, second, system_bars)
        for first, second in combine.PAIRS
        if first in present and second in present
    }


def _shared_identifier(player_id: str, voice: int) -> str:
    return identifier(player_id).replace("music", "shared", 1) + ("One", "Two")[voice]


def _extra_identifier(extra: combine.Extra) -> str:
    letters = "".join(char for char in extra.instrument.title() if char.isalpha())
    return identifier(extra.player).replace("music", "extra", 1) + letters


def _shared_music(work: Work, staff: combine.SharedStaff, *, for_part: bool) -> tuple[str, str]:
    """Return the LilyPond text of the two voices of a shared staff."""
    instrument = work.orchestra.first_instrument(staff.first)
    emitters = [_Emitter(work, for_part), _Emitter(work, for_part)]
    for emitter in emitters:
        emitter.set_instrument(instrument)
    shift = emitters[0].interval.semitones if emitters[0].interval else 0
    current = emitters[0].clef_of(instrument)
    one: list[music.Element] = [music.Command("clef", [current])]
    two: list[music.Element] = []
    ottava = 0
    for first, second in staff.chunks:
        # One clef for a section, for the notes of the two players.
        notes = [midi + shift for midi in _pitches(first) + _pitches(second)]
        if notes:
            clef = best_clef(emitters[0].clef_of(instrument), instrument, notes, current)
            if clef != current:
                one.append(music.Command("clef", [clef]))
                current = clef
            octave = best_ottava(clef, instrument, notes)
            if octave != ottava:
                one.append(music.Command("ottava", [f"#{octave}"]))
                ottava = octave
        one.extend(first)
        two.extend(second)
    return emitters[0].emit(one), emitters[1].emit(two)


def _extra_music(work: Work, extra: combine.Extra, *, for_part: bool) -> str:
    """Return the LilyPond text of the staff for the second instrument of a player."""
    instrument = work.orchestra.instruments.get(extra.instrument)
    emitter = _Emitter(work, for_part)
    emitter.set_instrument(instrument)
    player = work.orchestra.player(extra.player)
    return emitter.emit(_with_clefs(work, player, extra.chunks, emitter, instrument))


def _definitions(
    work: Work,
    players: list[Player],
    *,
    for_part: bool,
    breaks: set[int] | None = None,
    shared: dict[str, combine.SharedStaff] | None = None,
    part_cues: list[cues.Cue] | None = None,
    page_turns: frozenset[int] = frozenset(),
) -> str:
    structure = work.structure if breaks is None else replace(work.structure, breaks=breaks)
    score = breaks is not None
    shared = shared or {}
    second_players = {staff.second for staff in shared.values()}
    blocks = [
        "global = {\n\\accidentalStyle Score.modern\n\\numericTimeSignature\n"
        + global_to_lilypond(
            structure,
            change_context=None if score else "Score.",
            # A part: a rehearsal mark and a tempo mark at one bar line are side by side.
            marks="none" if score else "line",
            turns=page_turns,
        )
        + "\n}"
    ]
    if score:
        # A score: the lines for the tempo marks and the rehearsal marks.
        blocks.append(
            "globalMarks = {\n"
            + global_to_lilypond(structure, change_context="", marks="line")
            + "\n}"
        )
    for player in players:
        if player.id in second_players:
            continue  # the music is in the staff of player 1
        if player.id in shared:
            staff = shared[player.id]
            for voice, text in enumerate(_shared_music(work, staff, for_part=for_part)):
                blocks.append(f"{_shared_identifier(player.id, voice)} = {{\n{text}\n}}")
            for extra in staff.extras:
                text = _extra_music(work, extra, for_part=for_part)
                blocks.append(f"{_extra_identifier(extra)} = {{\n{text}\n}}")
            continue
        # The cues of a part are in its first staff.
        mine = part_cues if player is players[0] else None
        text = _player_music(work, player, for_part=for_part, part_cues=mine)
        blocks.append(f"{identifier(player.id)} = {{\n{text}\n}}")
    return "\n\n".join(blocks)


def _staff(player: Player, *, names: bool = True) -> str:
    with_block = (
        f'\\with {{ instrumentName = "{player.name}" shortInstrumentName = "{player.short}" }} '
        if names
        else ""
    )
    return f'\\new Staff = "{player.id}" {with_block}<< \\global \\{identifier(player.id)} >>'


def _groups(work: Work) -> list[tuple[str, list[Player]]]:
    """Return the players in the groups of the score, in the sequence of the score.

    The sequence of the groups is the sequence of their first players in the
    orchestra file.
    """
    groups: dict[str, list[Player]] = {}
    for player in work.orchestra.players:
        groups.setdefault(player.group, []).append(player)
    return list(groups.items())


# The names of the instruments that have a staff of their own in the score when a
# player of a shared staff changes to them: the full name and the short name.
EXTRA_NAMES = {
    "alto flute": ("Alto Flute", "A. Fl."),
    "ocarina": ("Ocarina", "Oc."),
    "clarinet in E-flat": ("Clarinet in E-flat", "E-fl. Cl."),
}


def _pair_names(player: Player) -> tuple[str, str]:
    """Divide the name of a player into the instrument and the number: "Flute 1" -> "Flute", "1"."""
    name, _, number = player.name.rpartition(" ")
    return name, number


def _shared_staff_text(work: Work, staff: combine.SharedStaff) -> list[str]:
    """Return the LilyPond staves for a pair: the shared staff, then the extra staves."""
    first, second = work.orchestra.player(staff.first), work.orchestra.player(staff.second)
    name, upper = _pair_names(first)
    lower = _pair_names(second)[1]
    short = first.short.rpartition(" ")[0]
    staves = [
        f'\\new Staff = "{first.id}+{second.id}" \\with {{\n'
        f'    instrumentName = \\markup \\pairname "{name}" "{upper}" "{lower}"\n'
        f'    shortInstrumentName = \\markup \\pairname "{short}" "{upper}" "{lower}"\n'
        "    \\consists Merge_rests_engraver\n"
        "  } <<\n"
        "    \\global\n"
        f"    \\new Voice {{ \\{_shared_identifier(first.id, 0)} }}\n"
        f"    \\new Voice {{ \\{_shared_identifier(first.id, 1)} }}\n"
        "  >>"
    ]
    for extra in staff.extras:
        player = work.orchestra.player(extra.player)
        full, brief = EXTRA_NAMES.get(extra.instrument, (extra.instrument.title(),) * 2)
        staves.append(
            f'\\new Staff = "{extra.player} {extra.instrument}" \\with {{\n'
            f'    instrumentName = \\markup \\extraname "{full}" "({player.name})"\n'
            f'    shortInstrumentName = \\markup \\extraname "{brief}" "({player.short})"\n'
            "    \\override VerticalAxisGroup.remove-first = ##t\n"
            f"  }} << \\global \\{_extra_identifier(extra)} >>"
        )
    return staves


def _score_staves(work: Work, shared: dict[str, combine.SharedStaff] | None = None) -> str:
    shared = shared or {}
    second_players = {staff.second for staff in shared.values()}
    blocks = []
    for family, members in _groups(work):
        staves = []
        index = 0
        while index < len(members):
            player = members[index]
            if player.id in second_players:
                index += 1
            elif player.id in shared:
                staves.extend(_shared_staff_text(work, shared[player.id]))
                index += 1
            elif player.id.endswith(".rh"):
                lower = members[index + 1]
                base = player.id[: -len(".rh")]
                staves.append(
                    f'\\new PianoStaff = "{base}" \\with {{ instrumentName = "{player.name}" '
                    f'shortInstrumentName = "{player.short}" }} <<\n'
                    f"    {_staff(player, names=False)}\n    {_staff(lower, names=False)}\n  >>"
                )
                index += 2
            else:
                staves.append(_staff(player))
                index += 1
        joined = "\n  ".join(staves)
        if family in MARK_LINE_FAMILIES:
            blocks.append("\\new MarkLine { \\globalMarks }")
        blocks.append(f'\\new StaffGroup = "{family}" <<\n  {joined}\n>>')
    return "\n".join(blocks)


def score_notes(work: Work, *, transposed: bool = False) -> list[str]:
    """Return the notes for the performance on the first page of the score.

    The bar numbers come from the music. Thus they stay correct when the
    music changes. `transposed` is true for the transposed score.
    """
    from ..perform.events import perform  # at call time: that module imports this package

    structure = work.structure
    quarter: dict[str, set[int]] = {"alto flute": set(), "violoncello": set(), "woodwinds": set()}
    ocarina: set[int] = set()
    for player in work.orchestra.players:
        for note in perform(work, player.id):
            bar = structure.bar_at(note.start).number
            if note.instrument == "ocarina":
                ocarina.add(bar)
            if note.midi != round(note.midi):
                if note.instrument in quarter:
                    quarter[note.instrument].add(bar)
                elif player.family == "woodwinds":
                    quarter["woodwinds"].add(bar)
                else:
                    raise ValueError(f"no note about the quarter-tones of the {player.id}")

    def bars(numbers: set[int]) -> str:
        first, last = min(numbers), max(numbers)
        return f"bar {first}" if first == last else f"bars {first} to {last}"

    pitch = "The score is in C. The parts are transposed."
    if transposed:
        pitch = (
            "This score is transposed: each staff has the notes of the part of its player. "
            "The list of the instruments gives the key of each transposing instrument."
        )
    notes = [
        pitch,
        "Piccolo, celesta, and glockenspiel sound higher than written, by one or two octaves. "
        "Contrabassoon, contrabass clarinet, and double basses sound one octave lower than "
        "written.",
        "An accidental is for one bar and one octave only.",
    ]
    places = []
    if quarter["alto flute"]:
        places.append(f"the alto flute ({bars(quarter['alto flute'])})")
    if quarter["violoncello"]:
        places.append(f"one cello ({bars(quarter['violoncello'])})")
    series = ""
    if quarter["woodwinds"]:
        # The woodwinds hold their quarter-tones to the end of the section.
        marks = sorted(structure.marks)
        before = [number for number in marks if number <= min(quarter["woodwinds"])]
        after = [number for number in marks if number > max(quarter["woodwinds"])]
        first = before[-1] if before else 1
        last = after[0] - 1 if after else len(structure.bars)
        series = f"bars {first} to {last}"
        places.append(f"the woodwinds ({series})")
    if places:
        text = "Quarter-tones are in these parts: "
        text += places[0] if len(places) == 1 else ", ".join(places[:-1]) + ", and " + places[-1]
        text += "."
        if series:
            text += (
                f" In {series}, the quarter-tones are the notes of the harmonic series on D: "
                "play them with no vibrato."
            )
        notes.append(text)
    notes.append("l.v.: let the sound ring.")
    if ocarina:
        notes.append(
            f"Three players have an ocarina in C ({bars(ocarina)}): oboe 2, clarinet 1, and "
            "bassoon 2."
        )
    notes.append(
        "Seating: the first violins are on the left of the conductor, the second violins on "
        "the right."
    )
    minutes = round(structure.duration_seconds / 60)
    if minutes >= 1:
        notes.append(f"Duration: {minutes} minutes.")
    return notes


OVERFULL = 0.12  # a system can have this much more than its capacity


def system_breaks(widths: list[float], capacity: float, most_bars: int) -> set[int]:
    """Return the bars after which a new system starts, for the widths of the bars.

    The systems are as equally full as possible: the function finds the
    division with the lowest sum of the costs of the systems. A system that
    is not full costs the square of its empty share. A system can be a little
    more than full (`OVERFULL`): this costs more. The last system can be
    empty in part at no cost. Thus a short bar does not stay alone between
    two long bars.
    """
    count = len(widths)
    best = [0.0] + [float("inf")] * count  # the lowest cost for the first bars
    cut = [0] * (count + 1)  # the last bar of the system before
    for last in range(1, count + 1):
        load = 0.0
        for first in range(last, max(last - most_bars, 0), -1):
            load += widths[first - 1]
            if load > capacity * (1.0 + OVERFULL) and first < last:
                break
            if load > capacity:
                cost = (3.0 * (load - capacity) / capacity) ** 2
            else:
                cost = 0.0 if last == count else ((capacity - load) / capacity) ** 2
            if best[first - 1] + cost < best[last]:
                best[last], cut[last] = best[first - 1] + cost, first - 1
    breaks: set[int] = set()
    last = count
    while cut[last]:
        last = cut[last]
        breaks.add(last)
    return breaks


def score_breaks(work: Work, capacity: float = 56.0, most_bars: int = 10) -> set[int]:
    """Return the bars after which the conductor score starts a new system.

    The width of a bar depends on the number of different moments at which
    a note starts. The function `system_breaks` divides the bars into systems.
    """
    from ..perform.events import perform

    structure = work.structure
    starts = [float(bar.start) for bar in structure.bars]
    moments: list[set[float]] = [set() for _ in structure.bars]
    for player in work.orchestra.players:
        for note in perform(work, player.id):
            position = float(note.start)
            moments[bisect.bisect_right(starts, position) - 1].add(position)
    widths = [max(len(columns), 2) + 1.5 for columns in moments]
    return system_breaks(widths, capacity, most_bars)


# The groups of the score that have a line for the tempo marks and the rehearsal marks
# above them.
MARK_LINE_FAMILIES = ("woodwinds", "strings")
SCORE_PAGE = frontmatter.Page(279.4, 431.8, 13.0)  # 11 x 17 inches, staff of 4.6 mm
SCORE_REHEARSAL_POINTS = 20.0
PART_REHEARSAL_POINTS = 15.0


def style(rehearsal_points: float) -> str:
    """Return the style definitions for a document."""
    return STYLE.replace("@REHEARSAL@", f"{rehearsal_points:g}").strip()


def front_part(
    work: Work, page: frontmatter.Page, edition: str, *, transposed: bool = False
) -> str:
    """Return the pages before the music as one part of the book, with no page numbers."""
    pages = frontmatter.pages(work, page, edition, score_notes(work, transposed=transposed))
    body = "\n\n\\pageBreak\n\n".join(pages)
    return (
        "\\bookpart {\n"
        "\\paper {\n"
        "  two-sided = ##f\n"
        f"  left-margin = {page.margin_mm:g}\\mm\n"
        f"  right-margin = {page.margin_mm:g}\\mm\n"
        "  top-margin = 18\\mm\n"
        "  bottom-margin = 18\\mm\n"
        "  print-page-number = ##f\n"
        "  oddHeaderMarkup = ##f\n"
        "  evenHeaderMarkup = ##f\n"
        "  oddFooterMarkup = ##f\n"
        "  evenFooterMarkup = ##f\n"
        "}\n"
        "\\header { tagline = ##f }\n\n" + body + "\n}"
    )


def score_file(work: Work, *, transposed: bool = False) -> str:
    """Return the LilyPond text of the conductor score.

    The usual score is in C. If `transposed` is true, each instrument has the
    notes of its part: some orchestras ask for such a score.
    """
    breaks = score_breaks(work)
    shared = shared_staves(work, breaks)
    document = "Transposed score" if transposed else "Score in C"
    edition = "Full score, transposed" if transposed else "Full score in C"
    music_part = (
        "\\bookpart {\n"
        + _header(work, document=document)
        + "\n\\score {\n<<\n"
        + _score_staves(work, shared)
        + "\n>>\n"
        + SCORE_LAYOUT.strip()
        + "\n}\n}"
    )
    return (
        "\n\n".join(
            [
                f'\\version "{LILYPOND_VERSION}"',
                style(SCORE_REHEARSAL_POINTS),
                techniques.lilypond_definitions(),
                f"#(set-global-staff-size {SCORE_PAGE.staff_size:g})",
                SCORE_PAPER.strip(),
                _definitions(
                    work, work.orchestra.players, for_part=transposed, breaks=breaks, shared=shared
                ),
                front_part(work, SCORE_PAGE, edition, transposed=transposed),
                music_part,
            ]
        )
        + "\n"
    )


def part_players(work: Work) -> dict[str, list[Player]]:
    """Return the staves of each part. A keyboard part has two staves."""
    parts: dict[str, list[Player]] = {}
    for player in work.orchestra.players:
        base = player.id.split(".")[0]
        parts.setdefault(base, []).append(player)
    return parts


# The height of a staff in a part, in points. The guidelines of the orchestra
# librarians: 7.5 mm is the best, 7.0 mm is possible for winds, and less is not
# acceptable. Two string players read one part: they get the larger staff.
PART_STAFF_POINTS = 20.0  # 7.1 mm
STRING_PART_STAFF_POINTS = 21.0  # 7.4 mm
PART_PAGE = frontmatter.Page(228.6, 304.8, PART_STAFF_POINTS, margin_mm=18.0)  # 9 x 12 inches


def part_staff_size(family: str) -> float:
    return STRING_PART_STAFF_POINTS if family == "strings" else PART_STAFF_POINTS


def _instrument_title(name: str) -> str:
    """Return the name of an instrument for a title: "alto flute" -> "Alto Flute"."""
    words = [
        word if word == "in" or word[0].isupper() else word[0].upper() + word[1:]
        for word in name.split()
    ]
    return " ".join(words)


def _part_cover(
    work: Work, players: list[Player], name: str, has_cues: bool, *, empty_page: bool = False
) -> str:
    """Return the cover of a part as one part of the book, with no page number.

    If `empty_page` is true, an empty page comes after the cover: then the
    music starts on a right page.
    """
    from ..perform.events import perform  # at call time: that module imports this package

    first = players[0]
    used: list[str] = []
    for player in players:
        for note in perform(work, player.id):
            if note.instrument not in used:
                used.append(note.instrument)
    # A percussion player has a list of instruments in the notes for the player.
    many = first.family == "percussion" and len(first.instruments) > 1
    others = [instrument for instrument in used if instrument != first.instruments[0]]
    remark = ""
    if others and not many:
        remark = "also " + ", ".join(_instrument_title(instrument) for instrument in others)
    identifiers = [player.id for player in players]
    notes = frontmatter.part_notes(work, identifiers, has_cues)
    marks = frontmatter.used_marks(work, identifiers)
    body = frontmatter.part_cover(work, PART_PAGE, name, remark, notes, marks)
    if empty_page:
        body += "\n\n\\pageBreak\n\n\\markup \\null"
    return (
        "\\bookpart {\n"
        "\\paper {\n"
        "  % The cover is one page of text: it does not use the page turn rules.\n"
        "  page-breaking = #ly:minimal-breaking\n"
        "  print-page-number = ##f\n"
        "  oddHeaderMarkup = ##f\n"
        "  evenHeaderMarkup = ##f\n"
        "  oddFooterMarkup = ##f\n"
        "  evenFooterMarkup = ##f\n"
        "}\n"
        "\\header { tagline = ##f }\n\n" + body + "\n}"
    )


def part_file(
    work: Work,
    part_id: str,
    found: dict[str, list[cues.Cue]] | None = None,
    *,
    music_page: int = 2,
) -> str:
    """Return the LilyPond text of one part.

    `found` has the cues of all parts (see `cues.find_cues`). If it is not
    given, the function finds the cues.

    `music_page` is the page on which the music starts:

    - 2: page 1 is a cover with the notes for the player, and the music starts
      on a left page. The player sees two pages of music before the first
      page turn.
    - 3: an empty page comes after the cover, and the music starts on a right
      page.
    - 1: no cover.

    The guidelines of the orchestra librarians permit a cover and a start on
    page 2 for good page turns. The build makes the layouts 2 and 3 and keeps
    the better one (see `pages.py`).
    """
    if found is None:
        found = cues.find_cues(work)
    part_cues = found.get(part_id, [])
    cue_starts = frozenset(cue.start for cue in part_cues)
    players = part_players(work)[part_id]
    first = players[0]
    name = first.name
    instrument = work.orchestra.first_instrument(first.id)
    line = name
    if instrument and instrument.transposition % 12 and " in " in instrument.name:
        line = f"{name} in {instrument.name.split(' in ')[1]}"
    if len(players) == 1:
        staves = f"\\new Staff << \\global \\{identifier(first.id)} >>"
    else:
        inner = "\n  ".join(_staff(player, names=False) for player in players)
        staves = f"\\new PianoStaff <<\n  {inner}\n>>"
    score = "\\score {\n" + staves + "\n" + PART_LAYOUT.strip() + "\n}"
    if music_page > 1:
        pages = [
            _part_cover(work, players, line, bool(part_cues), empty_page=music_page == 3),
            "\\bookpart {\n" + _header(work, line) + "\n\n" + score + "\n}",
        ]
    else:
        key = ""
        if first.family == "percussion" and len(first.instruments) > 1:
            # A percussion player has many instruments: the part starts with a list of them.
            sentences = frontmatter.percussion_key(work, first.id)
            key = frontmatter.key_markup(PART_PAGE, sentences) if sentences else ""
        pages = [_header(work, line), *([key] if key else []), score]
    return (
        "\n\n".join(
            [
                f'\\version "{LILYPOND_VERSION}"',
                style(PART_REHEARSAL_POINTS),
                techniques.lilypond_definitions(),
                f"#(set-global-staff-size {part_staff_size(first.family):g})",
                PART_PAPER.strip(),
                _definitions(
                    work,
                    players,
                    for_part=True,
                    part_cues=part_cues,
                    page_turns=frozenset(turns.turn_bars(work, part_id, cue_starts)),
                ),
                *pages,
            ]
        )
        + "\n"
    )


# ----------------------------------------------------------------------------
# Score pages for the video: one file for each section of the work
# ----------------------------------------------------------------------------

VIDEO_PAGE_MM = (480.0, 270.0)
VIDEO_REHEARSAL_POINTS = 16.0
VIDEO_SECONDS_PER_SCREEN = 15.0
# The video for a telephone: the screen is tall and narrow. A screen shows less
# time, and the notes are larger.
MOBILE_PAGE_MM = (270.0, 480.0)
MOBILE_SECONDS_PER_SCREEN = 7.0

VIDEO_SCHEME = r"""
#(define (tag-when class)
   (lambda (grob)
     (let* ((column (ly:item-get-column grob))
            (when (ly:grob-property column 'when)))
       (list (cons 'class class)
             (cons 'data-when
                   (number->string (exact->inexact (ly:moment-main when))))))))
"""

VIDEO_LAYOUT = r"""
\layout {
  \context {
    \Score
    \override NoteHead.output-attributes = #(tag-when "nh")
    \override Rest.output-attributes = #(tag-when "rest")
    \override BarLine.output-attributes = #(tag-when "bar")
    \override BarNumber.font-size = #0
    \override MetronomeMark.font-size = #2
    \override MetronomeMark.padding = #2.5
    \override RehearsalMark.padding = #3
    \override InstrumentName.self-alignment-X = #RIGHT
    \override Hairpin.minimum-length = #5
  }
  \context {
    \Staff
    \RemoveAllEmptyStaves
    \override TextScript.font-size = #-0.5
    \override DynamicTextSpanner.style = #'none
  }
}
""".replace("\\\\", "\\")


# The names of the instruments are smaller on the narrow page: the staves are large.
MOBILE_LAYOUT = VIDEO_LAYOUT.replace(
    "\\override InstrumentName.self-alignment-X = #RIGHT",
    "\\override InstrumentName.self-alignment-X = #RIGHT\n"
    "    \\override InstrumentName.font-size = #-3",
)


def chunk_count(work: Work) -> int:
    """Return the number of sections of the work."""
    return max(len(chunks) for chunks in work.chunks.values())


def chunk_bars(work: Work, index: int) -> tuple[int, int]:
    """Return the first bar and the last bar of a section."""
    some_player = next(iter(work.chunks.values()))
    first = some_player[index][0]
    last = (
        some_player[index + 1][0] - 1 if index + 1 < len(some_player) else len(work.structure.bars)
    )
    return first, last


def _instrument_at(work: Work, player: Player, index: int) -> Instrument | None:
    """Return the instrument that a player has at the start of a section."""
    name = player.instruments[0]
    for _first_bar, chunk in work.chunks[player.id][:index]:
        for element in _walk_commands(chunk.children):
            if element.name == "switch":
                name = element.arguments[0].strip('"')
    return work.orchestra.instruments.get(name)


def _walk_commands(elements: list[music.Element]):
    for element in elements:
        if isinstance(element, music.Command):
            yield element
        elif isinstance(element, music.Group):
            yield from _walk_commands(element.children)


def _is_silent(elements: list[music.Element]) -> bool:
    """Return True if the music has no notes."""
    for element in elements:
        if isinstance(element, music.Note):
            return False
        if isinstance(element, music.Group) and not _is_silent(element.children):
            return False
    return True


def active_players(work: Work, index: int) -> list[Player]:
    """Return the players that have notes in a section."""
    return [
        player
        for player in work.orchestra.players
        if not _is_silent(work.chunks[player.id][index][1].children)
    ]


def video_file(work: Work, index: int, staff_size: float, *, mobile: bool = False) -> str:
    """Return the LilyPond text of one section, as a page for the video.

    If `mobile` is true, the page is for the video for a telephone.
    """
    from .structure import Structure, global_to_lilypond

    first, last = chunk_bars(work, index)
    source = work.structure
    part = Structure(final_bar=last == len(source.bars))
    for bar in source.bars[first - 1 : last]:
        part.add_bars(1, bar.numerator, bar.denominator, bar.grouping)
    start = source.bar(first).start
    end = source.bar(last).end
    for point in source.tempo_points:
        if start <= point.position < end:
            shifted = type(point)(**{**point.__dict__, "position": point.position - start})
            part.tempo_points.append(shifted)
    part.marks = {
        bar - first + 1: label for bar, label in source.marks.items() if first <= bar <= last
    }
    part.double_bars = {bar - first + 1 for bar in source.double_bars if first <= bar <= last}
    # A screen of the video shows about 15 seconds of music.
    shown_from = start
    for bar in source.bars[first - 1 : last - 1]:
        seconds = source.seconds(bar.end) - source.seconds(shown_from)
        if seconds >= (MOBILE_SECONDS_PER_SCREEN if mobile else VIDEO_SECONDS_PER_SCREEN):
            part.breaks.add(bar.number - first + 1)
            shown_from = bar.end

    blocks = [
        "global = {\n\\accidentalStyle Score.modern\n\\numericTimeSignature\n"
        f"\\set Score.currentBarNumber = #{first}\n" + global_to_lilypond(part) + "\n}"
    ]
    staves: dict[str, list[str]] = {}
    players = work.orchestra.players
    shown = {player.id for player in active_players(work, index)}
    # A keyboard instrument shows its two staves if one of them has notes.
    for player in players:
        base = player.id.split(".")[0]
        if "." in player.id and any(other.split(".")[0] == base for other in shown):
            shown.add(player.id)
    position = 0
    while position < len(players):
        player = players[position]
        position += 1
        if player.id not in shown:
            continue
        emitter = _Emitter(work, for_part=False, left_hand=player.id.endswith(".lh"))
        instrument = _instrument_at(work, player, index)
        emitter.set_instrument(instrument)
        children = work.chunks[player.id][index][1].children
        shift = emitter.interval.semitones if emitter.interval else 0
        clef = best_clef(
            emitter.clef_of(instrument), instrument, [midi + shift for midi in _pitches(children)]
        )
        body = emitter.emit(children, top=False)  # a page of the video: no long rests
        blocks.append(f"{identifier(player.id)} = {{\n\\clef {clef}\n{body}\n}}")
        tag = (
            f"\\override StaffSymbol.output-attributes = "
            f'#\'((class . "staff") (data-staff . "{player.id}"))'
        )
        names = f'instrumentName = "{player.short}" shortInstrumentName = "{player.short}"'
        own_names = "" if "." in player.id else names + " "
        staff = (
            f'\\new Staff = "{player.id}" \\with {{ {own_names}{tag} }} '
            f"<< \\global \\{identifier(player.id)} >>"
        )
        group = staves.setdefault(player.group, [])
        if player.id.endswith(".rh"):
            group.append(f"\\new PianoStaff \\with {{ {names} }} <<\n    {staff}")
        elif player.id.endswith(".lh"):
            group.append(f"    {staff}\n  >>")
        else:
            group.append(staff)
    groups = [
        f'\\new StaffGroup = "{name}" <<\n  ' + "\n  ".join(members) + "\n>>"
        for name, members in staves.items()
        if members
    ]
    width, height = MOBILE_PAGE_MM if mobile else VIDEO_PAGE_MM
    side = 6 if mobile else 10
    paper = (
        "\\paper {\n"
        f"  #(set-paper-size '(cons (* {width} mm) (* {height} mm)))\n"
        f"  top-margin = 8\\mm\n  bottom-margin = 8\\mm\n  left-margin = {side}\\mm\n"
        f"  right-margin = {side}\\mm\n  indent = 20\\mm\n  short-indent = 20\\mm\n"
        "  max-systems-per-page = 1\n  ragged-last = ##f\n  ragged-bottom = ##t\n"
        "  print-page-number = ##f\n  oddHeaderMarkup = ##f\n  evenHeaderMarkup = ##f\n"
        "  oddFooterMarkup = ##f\n  evenFooterMarkup = ##f\n}"
    )
    return (
        "\n\n".join(
            [
                f'\\version "{LILYPOND_VERSION}"',
                style(VIDEO_REHEARSAL_POINTS),
                VIDEO_SCHEME.strip(),
                techniques.lilypond_definitions(),
                f"#(set-global-staff-size {staff_size:.2f})",
                paper,
                "\n\n".join(blocks),
                "\\score {\n<<\n"
                + "\n".join(groups)
                + "\n>>\n"
                + (MOBILE_LAYOUT if mobile else VIDEO_LAYOUT).strip()
                + "\n}",
            ]
        )
        + "\n"
    )


def set_names(work: Work) -> dict[str, str]:
    """Return the file name of each document of the performance set, with no extension.

    The key is the name of the LilyPond file ("score", "part-fl1"). The names
    are those that the orchestra librarians ask for: the composer, the title,
    a number in the sequence of the score, and the instrument.
    """
    surname = work.composer.split()[-1].upper() if work.composer else "COMPOSER"
    names = {
        "score": f"{surname} {work.title} 00 - Score in C",
        "score-transposed": f"{surname} {work.title} 00 - Transposed score",
    }
    for number, (part_id, players) in enumerate(part_players(work).items(), start=1):
        names[f"part-{part_id}"] = f"{surname} {work.title} {number:02d} - {players[0].name}"
    return names


# The name of the file of a part in which the music starts on a right page.
RIGHT_START = "-right"


def write_all(work: Work, directory: Path) -> list[Path]:
    """Write the two score files and the files of all parts. Return the paths.

    Each part has two files: the music starts on page 2 (`part-fl1.ly`) or on
    page 3 (`part-fl1-right.ly`). The build keeps the better result.
    """
    directory.mkdir(parents=True, exist_ok=True)
    paths = [directory / "score.ly", directory / "score-transposed.ly"]
    paths[0].write_text(score_file(work), encoding="utf-8")
    paths[1].write_text(score_file(work, transposed=True), encoding="utf-8")
    found = cues.find_cues(work)
    for part_id in part_players(work):
        for name, music_page in ((f"part-{part_id}.ly", 2), (f"part-{part_id}{RIGHT_START}.ly", 3)):
            path = directory / name
            path.write_text(
                part_file(work, part_id, found, music_page=music_page), encoding="utf-8"
            )
            paths.append(path)
    return paths
