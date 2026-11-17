"""The music language of the project: a subset of LilyPond music syntax.

The composer writes each line of music as text in this language. One parser
reads the text. The score, the parts, the audio, and the video all use the
result of this parser, thus they always agree.

Supported syntax:

- Notes with absolute octaves: `d'4`, `bes,8.`, `ceh''2` (quarter-tone flat).
- Chords: `<d f a>2`. Rests: `r4`. Spacer rests: `s4`. Full-bar rests: `R1*3`.
- A duration stays in effect until the subsequent duration.
- Ties `~`, slurs `( )`, phrasing slurs `\\( \\)`, beams `[ ]`.
- Articulations: `-.` `->` `--` `-^` `-!` `-_` `-+`.
- Dynamics and hairpins: `\\pp`, `\\<`, `\\>`, `\\!`.
- Text: `^"text"`, `_"text"`, `^\\markup { ... }`.
- Tremolo: `c2:32`.
- Tuplets: `\\tuplet 3/2 { ... }`. Grace notes: `\\grace { ... }`, `\\acciaccatura { ... }`.
- Repeats: `\\repeat unfold 4 { ... }`, `\\repeat tremolo 8 { c16 e }`.
- Two voices on one staff: `<< { ... } \\\\ { ... } >>`.
- Bar checks: `|`.
- Commands with no argument, for example `\\breathe`. See `PREFIX_COMMANDS`.
- Commands of the project: `\\switch "alto flute"` (a player changes the instrument).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction

from .pitch import Interval, Pitch

DURATION_RE = re.compile(r"(128|64|32|16|8|4|2|1|\\breve)(\.*)((?:\*\d+(?:/\d+)?)*)")
BASE_QUARTERS = {
    "\\breve": Fraction(8),
    "1": Fraction(4),
    "2": Fraction(2),
    "4": Fraction(1),
    "8": Fraction(1, 2),
    "16": Fraction(1, 4),
    "32": Fraction(1, 8),
    "64": Fraction(1, 16),
    "128": Fraction(1, 32),
}

DYNAMICS = [
    "ppppp", "pppp", "ppp", "pp", "p", "mp", "mf", "f", "ff", "fff", "ffff", "fffff",
]  # fmt: skip
ACCENT_DYNAMICS = ["sf", "sff", "sfz", "sffz", "fz", "rfz", "fp", "sfp", "sfpp", "ffp", "pf"]
ARTICULATION_CHARS = {
    ".": "staccato",
    ">": "accent",
    "-": "tenuto",
    "^": "marcato",
    "!": "staccatissimo",
    "_": "portato",
    "+": "stopped",
}

# Commands that attach to the note before them.
POST_COMMANDS = {
    *DYNAMICS, *ACCENT_DYNAMICS,
    "cresc", "decresc", "dim", "endcresc", "enddecresc", "enddim",
    "fermata", "shortfermata", "longfermata", "verylongfermata",
    "trill", "prall", "mordent", "turn", "startTrillSpan", "stopTrillSpan",
    "flageolet", "harmonic", "open", "stopped", "upbow", "downbow", "snappizzicato",
    "glissando", "arpeggio", "laissezVibrer", "repeatTie",
    "staccato", "accent", "tenuto", "marcato", "staccatissimo", "portato", "espressivo",
    "startTextSpan", "stopTextSpan", "sustainOn", "sustainOff",
}  # fmt: skip

# Commands that stand alone and take no time. The value is the number of arguments.
PREFIX_COMMANDS = {
    "breathe": 0, "caesura": 0,
    "stemUp": 0, "stemDown": 0, "stemNeutral": 0,
    "voiceOne": 0, "voiceTwo": 0, "voiceThree": 0, "voiceFour": 0, "oneVoice": 0,
    "slurUp": 0, "slurDown": 0, "slurNeutral": 0, "slurDashed": 0, "slurSolid": 0,
    "tieUp": 0, "tieDown": 0, "tieNeutral": 0,
    "tupletUp": 0, "tupletDown": 0, "tupletNeutral": 0,
    "dynamicUp": 0, "dynamicDown": 0, "dynamicNeutral": 0,
    "autoBeamOff": 0, "autoBeamOn": 0, "noBeam": 0,
    "break": 0, "noBreak": 0, "pageBreak": 0, "noPageBreak": 0,
    "hideNotes": 0, "unHideNotes": 0, "glissandoSkipOn": 0, "glissandoSkipOff": 0,
    "clef": 1, "ottava": 1, "switch": 1, "set": 3, "unset": 1,
}  # fmt: skip


class MusicSyntaxError(ValueError):
    """The music text has an error."""


@dataclass
class Post:
    """An event that attaches to a note: an articulation, a dynamic, a slur, a text."""

    kind: str  # tie, slur, phrasing, beam, articulation, dynamic, hairpin, text, command, tremolo
    text: str  # the LilyPond text, written out again as it is
    value: str = ""


@dataclass
class NotePitch:
    """One pitch of a note or a chord."""

    pitch: Pitch
    marks: str = ""  # `!` or `?`: a forced or a cautionary accidental
    posts: list[Post] = field(default_factory=list)  # events on one chord note


@dataclass
class Note:
    """A note or a chord."""

    pitches: list[NotePitch]
    chord: bool
    duration: Fraction  # written duration in quarter notes
    duration_text: str  # empty if the note uses the duration of the note before it
    posts: list[Post] = field(default_factory=list)


@dataclass
class Rest:
    """A rest (`r`), a spacer rest (`s`), or a full-bar rest (`R`)."""

    kind: str
    duration: Fraction
    duration_text: str
    posts: list[Post] = field(default_factory=list)


@dataclass
class Command:
    """A command that takes no time."""

    name: str
    arguments: list[str] = field(default_factory=list)


@dataclass
class BarCheck:
    """A bar check: the position must be the start of a bar."""


@dataclass
class Group:
    """A group of elements.

    kind: `sequence`, `tuplet`, `grace`, `unfold`, `tremolo`, `parallel`, or `cue`.
    A `parallel` group has one child group for each voice.
    A `cue` group is in a part only: its first child has the rests of the
    player, and its second child has the notes of a different instrument.
    """

    kind: str
    children: list[Element]
    header: str = ""  # the LilyPond text before the braces
    ratio: Fraction = Fraction(1)  # tuplet: duration factor
    count: int = 1  # repeat count


Element = Note | Rest | Command | BarCheck | Group


class _Parser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.index = 0
        self.duration = Fraction(1)

    # ------------------------------------------------------------ helpers

    def error(self, message: str) -> MusicSyntaxError:
        line = self.text.count("\n", 0, self.index) + 1
        context = self.text[max(0, self.index - 30) : self.index + 30].replace("\n", " ")
        return MusicSyntaxError(f"{message} (line {line}, near: ...{context}...)")

    def skip_space(self) -> None:
        while self.index < len(self.text):
            char = self.text[self.index]
            if char.isspace():
                self.index += 1
            elif char == "%":
                end = self.text.find("\n", self.index)
                self.index = len(self.text) if end < 0 else end
            else:
                break

    def peek(self, count: int = 1) -> str:
        return self.text[self.index : self.index + count]

    def read_word(self) -> str:
        match = re.compile(r"[A-Za-z]+").match(self.text, self.index)
        if not match:
            raise self.error("a word is necessary here")
        self.index = match.end()
        return match.group(0)

    def read_string(self) -> str:
        if self.peek() != '"':
            raise self.error('a string in "quotes" is necessary here')
        end = self.index + 1
        while end < len(self.text) and self.text[end] != '"':
            end += 2 if self.text[end] == "\\" else 1
        if end >= len(self.text):
            raise self.error("the string has no end")
        value = self.text[self.index : end + 1]
        self.index = end + 1
        return value

    def read_braces(self) -> str:
        """Read a `{ ... }` block as text (for markup). Return it with its braces."""
        if self.peek() != "{":
            raise self.error("a { is necessary here")
        depth, end = 0, self.index
        while end < len(self.text):
            char = self.text[end]
            if char == '"':
                close = end + 1
                while close < len(self.text) and self.text[close] != '"':
                    close += 2 if self.text[close] == "\\" else 1
                end = close
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    break
            end += 1
        if depth:
            raise self.error("the { has no }")
        value = self.text[self.index : end + 1]
        self.index = end + 1
        return value

    def read_argument(self) -> str:
        """Read one argument of a command: a word, a string, or a Scheme value."""
        self.skip_space()
        if self.peek() == '"':
            return self.read_string()
        match = re.compile(r"#?[^\s{}]+").match(self.text, self.index)
        if not match:
            raise self.error("an argument is necessary here")
        self.index = match.end()
        return match.group(0)

    def read_duration(self) -> tuple[Fraction, str]:
        match = DURATION_RE.match(self.text, self.index)
        if not match:
            return self.duration, ""
        base, dots, multipliers = match.groups()
        duration = BASE_QUARTERS[base] * (2 - Fraction(1, 2 ** len(dots)))
        for multiplier in re.findall(r"\*(\d+)(?:/(\d+))?", multipliers):
            duration *= Fraction(int(multiplier[0]), int(multiplier[1] or 1))
        self.index = match.end()
        # A multiplier applies to one note only. The base duration stays in effect.
        self.duration = BASE_QUARTERS[base] * (2 - Fraction(1, 2 ** len(dots)))
        return duration, match.group(0)

    # ------------------------------------------------------------ elements

    def parse_sequence(self, closing: str | None) -> list[Element]:
        elements: list[Element] = []
        while True:
            self.skip_space()
            if self.index >= len(self.text):
                if closing:
                    raise self.error(f"the group has no {closing}")
                return elements
            if closing and self.text.startswith(closing, self.index):
                self.index += len(closing)
                return elements
            self.parse_element(elements)

    def last_note(self, elements: list[Element]) -> Note | Rest:
        for element in reversed(elements):
            if isinstance(element, Note | Rest):
                return element
            if isinstance(element, Group) and element.kind != "parallel":
                found = self._last_in_group(element)
                if found:
                    return found
        raise self.error("this event needs a note before it")

    def _last_in_group(self, group: Group) -> Note | Rest | None:
        for element in reversed(group.children):
            if isinstance(element, Note | Rest):
                return element
            if isinstance(element, Group) and element.kind != "parallel":
                found = self._last_in_group(element)
                if found:
                    return found
        return None

    def parse_element(self, elements: list[Element]) -> None:
        char = self.peek()
        if char == "|":
            self.index += 1
            elements.append(BarCheck())
        elif self.peek(2) == "<<":
            self.index += 2
            elements.append(self.parse_parallel())
        elif char == "<":
            elements.append(self.parse_chord())
        elif char == "{":
            self.index += 1
            elements.append(Group("sequence", self.parse_sequence("}")))
        elif char == "\\":
            self.parse_backslash(elements)
        elif char in "~()[]":
            self.index += 1
            kind = {"~": "tie", "(": "slur", ")": "slur", "[": "beam", "]": "beam"}[char]
            self.last_note(elements).posts.append(Post(kind, char, char))
        elif char in "-^_":
            self.last_note(elements).posts.append(self.parse_directed())
        elif char == ":":
            match = re.compile(r":(\d+)").match(self.text, self.index)
            if not match:
                raise self.error("a tremolo needs a number, for example :32")
            self.index = match.end()
            self.last_note(elements).posts.append(Post("tremolo", match.group(0), match.group(1)))
        elif char in "rsR" and not self.text[self.index : self.index + 2].isalpha():
            self.index += 1
            duration, text = self.read_duration()
            elements.append(Rest(char, duration, text))
        elif char in "abcdefg":
            elements.append(self.parse_note())
        else:
            raise self.error(f"unknown text {char!r}")

    def parse_pitch(self) -> NotePitch:
        try:
            pitch, rest = Pitch.parse_prefix(self.text[self.index : self.index + 12])
        except ValueError as problem:
            raise self.error(str(problem)) from None
        self.index += len(self.text[self.index : self.index + 12]) - len(rest)
        marks = ""
        while self.peek() in ("!", "?"):
            marks += self.peek()
            self.index += 1
        return NotePitch(pitch, marks)

    def parse_note(self) -> Note:
        pitch = self.parse_pitch()
        duration, text = self.read_duration()
        return Note([pitch], False, duration, text)

    def parse_chord(self) -> Note:
        self.index += 1  # <
        pitches: list[NotePitch] = []
        while True:
            self.skip_space()
            if self.peek() == ">":
                self.index += 1
                break
            if self.index >= len(self.text):
                raise self.error("the chord has no >")
            if self.peek() == "\\":
                # An event on one chord note, for example \harmonic.
                self.index += 1
                name = self.read_word()
                if not pitches:
                    raise self.error(f"\\{name} needs a chord note before it")
                pitches[-1].posts.append(Post("command", f"\\{name}", name))
            else:
                pitches.append(self.parse_pitch())
        if not pitches:
            raise self.error("the chord is empty")
        duration, text = self.read_duration()
        return Note(pitches, True, duration, text)

    def parse_directed(self) -> Post:
        """Parse an event with a direction sign, for example `-.` or `^"text"`."""
        direction = self.peek()
        self.index += 1
        char = self.peek()
        if char == '"':
            return Post("text", direction + self.read_string())
        if char == "\\":
            self.index += 1
            name = self.read_word()
            if name == "markup":
                self.skip_space()
                return Post("text", f"{direction}\\markup {self.read_braces()}")
            if name in DYNAMICS or name in ACCENT_DYNAMICS:
                return Post("dynamic", f"{direction}\\{name}", name)
            return Post("command", f"{direction}\\{name}", name)
        if direction == "-" and char.isdigit():
            self.index += 1
            return Post("fingering", f"-{char}", char)
        if char in ARTICULATION_CHARS:
            self.index += 1
            return Post("articulation", direction + char, ARTICULATION_CHARS[char])
        raise self.error(f"unknown event after {direction!r}")

    def parse_backslash(self, elements: list[Element]) -> None:
        start = self.index
        self.index += 1
        char = self.peek()
        if char in "()":
            self.index += 1
            self.last_note(elements).posts.append(Post("phrasing", "\\" + char, char))
            return
        if char in "<>!":
            self.index += 1
            self.last_note(elements).posts.append(Post("hairpin", "\\" + char, char))
            return
        if char == "\\":
            raise self.error("\\\\ is only permitted between the voices of << >>")
        name = self.read_word()
        if name in DYNAMICS or name in ACCENT_DYNAMICS:
            self.last_note(elements).posts.append(Post("dynamic", f"\\{name}", name))
        elif name in POST_COMMANDS or name in TECHNIQUE_NAMES:
            self.last_note(elements).posts.append(Post("command", f"\\{name}", name))
        elif name == "tuplet":
            self.skip_space()
            match = re.compile(r"(\d+)/(\d+)").match(self.text, self.index)
            if not match:
                raise self.error("\\tuplet needs a fraction, for example 3/2")
            self.index = match.end()
            ratio = Fraction(int(match.group(2)), int(match.group(1)))
            children = self.parse_braced()
            elements.append(Group("tuplet", children, f"\\tuplet {match.group(0)}", ratio))
        elif name in ("grace", "acciaccatura", "appoggiatura", "slashedGrace"):
            saved = self.duration
            children = self.parse_braced()
            self.duration = saved
            elements.append(Group("grace", children, f"\\{name}"))
        elif name == "repeat":
            kind = self.read_argument()
            count = int(self.read_argument())
            if kind not in ("unfold", "tremolo"):
                raise self.error("only \\repeat unfold and \\repeat tremolo are permitted")
            children = self.parse_braced()
            elements.append(Group(kind, children, f"\\repeat {kind} {count}", count=count))
        elif name == "markup":
            raise self.error("\\markup needs a direction sign before it: ^\\markup or _\\markup")
        elif name in PREFIX_COMMANDS:
            arguments = [self.read_argument() for _ in range(PREFIX_COMMANDS[name])]
            elements.append(Command(name, arguments))
        else:
            self.index = start
            raise self.error(f"unknown command \\{name}")

    def parse_braced(self) -> list[Element]:
        self.skip_space()
        if self.peek() != "{":
            raise self.error("a { is necessary here")
        self.index += 1
        return self.parse_sequence("}")

    def parse_parallel(self) -> Group:
        voices: list[Element] = []
        while True:
            self.skip_space()
            if self.peek(2) == ">>":
                self.index += 2
                break
            if self.peek(2) == "\\\\":
                self.index += 2
                continue
            saved = self.duration
            voices.append(Group("sequence", self.parse_braced()))
            self.duration = saved
        if len(voices) < 2:
            raise self.error("<< >> needs two or more voices")
        return Group("parallel", voices)


# Names of the playing techniques. The module `techniques` fills this set.
TECHNIQUE_NAMES: set[str] = set()


def parse(text: str) -> Group:
    """Parse music text. Return the music as a sequence group."""
    parser = _Parser(text)
    return Group("sequence", parser.parse_sequence(None))


# ----------------------------------------------------------------------------
# Duration and output
# ----------------------------------------------------------------------------


def length(element: Element) -> Fraction:
    """Return the duration of an element in quarter notes."""
    if isinstance(element, Note | Rest):
        return element.duration
    if isinstance(element, Group):
        if element.kind == "grace":
            return Fraction(0)
        if element.kind == "cue":
            return length(element.children[0])
        if element.kind == "parallel":
            lengths = {length(child) for child in element.children}
            if len(lengths) != 1:
                shown = ", ".join(str(value) for value in sorted(lengths))
                raise MusicSyntaxError(f"the voices of << >> have different lengths: {shown}")
            return lengths.pop()
        inner = sum((length(child) for child in element.children), Fraction(0))
        return inner * element.ratio * element.count
    return Fraction(0)


def _posts_text(posts: list[Post]) -> str:
    return "".join(post.text for post in posts)


def to_lilypond(element: Element, interval: Interval | None = None) -> str:
    """Write an element as LilyPond text.

    `interval` moves all pitches (for a transposing instrument). The function
    makes unusual spellings simpler after the transposition.
    """

    def name(note_pitch: NotePitch) -> str:
        pitch = note_pitch.pitch
        if interval is not None:
            pitch = pitch.transposed(interval).simplified()
        return pitch.name + note_pitch.marks + _posts_text(note_pitch.posts)

    if isinstance(element, Note):
        if element.chord:
            core = "<" + " ".join(name(p) for p in element.pitches) + ">"
        else:
            core = name(element.pitches[0])
        return core + element.duration_text + _posts_text(element.posts)
    if isinstance(element, Rest):
        return element.kind + element.duration_text + _posts_text(element.posts)
    if isinstance(element, Command):
        return " ".join([f"\\{element.name}", *element.arguments])
    if isinstance(element, BarCheck):
        return "|\n"
    if element.kind == "parallel":
        voices = [f"{{ {_children_text(child.children, interval)} }}" for child in element.children]
        return "<< " + " \\\\ ".join(voices) + " >>"
    inner = _children_text(element.children, interval)
    if element.kind == "sequence":
        return f"{{ {inner} }}"
    return f"{element.header} {{ {inner} }}"


def _children_text(children: list[Element], interval: Interval | None) -> str:
    return " ".join(to_lilypond(child, interval) for child in children).replace("\n ", "\n")


def body_to_lilypond(music: Group, interval: Interval | None = None) -> str:
    """Write the elements of a sequence group without the outer braces."""
    return _children_text(music.children, interval).strip()
