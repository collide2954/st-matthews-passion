"""The work: the orchestra, the structure, and the music of each player."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

from . import (  # noqa: F401  (the import of techniques registers the technique names)
    hairpins,
    lyrics,
    music,
    techniques,
)
from .pitch import Interval
from .structure import Structure

DESIGN_DIR = Path("design")

# Families whose players each have one staff, also when the orchestra file gives a count.
SEPARATE_STAVES = {"brass", "percussion"}


@dataclass(frozen=True)
class Instrument:
    """One instrument with its notation data."""

    name: str
    transposition: int  # semitones from the sound up to the written note, in the part
    score_transposition: int  # the same for the conductor score (the score is in C)
    clef: str
    score_clef: str
    low: int
    high: int

    @staticmethod
    def _interval(semitones: int) -> Interval | None:
        if semitones == 0:
            return None
        return Interval(round(semitones * 7 / 12), semitones)

    @property
    def part_interval(self) -> Interval | None:
        return self._interval(self.transposition)

    @property
    def score_interval(self) -> Interval | None:
        return self._interval(self.score_transposition)


@dataclass
class Player:
    """One staff of the score: one player, or one string section."""

    id: str
    name: str
    short: str
    family: str
    count: int
    instruments: list[str]
    group: str = ""  # the bracket of the score; empty = the family

    def __post_init__(self) -> None:
        if not self.group:
            self.group = self.family


@dataclass
class Orchestra:
    players: list[Player]
    instruments: dict[str, Instrument]

    def player(self, player_id: str) -> Player:
        for player in self.players:
            if player.id == player_id:
                return player
        raise KeyError(player_id)

    def first_instrument(self, player_id: str) -> Instrument | None:
        """Return the instrument that a player starts with (None for unpitched percussion)."""
        return self.instruments.get(self.player(player_id).instruments[0])


def load_orchestra(path: Path | None = None) -> Orchestra:
    """Read the orchestra from the design data."""
    with (path or DESIGN_DIR / "orchestra.toml").open("rb") as handle:
        data = tomllib.load(handle)
    instruments = {
        name: Instrument(
            name=name,
            transposition=entry["transposition"],
            score_transposition=entry.get("score_transposition", 0),
            clef=entry["clef"],
            score_clef=entry.get("score_clef", entry["clef"]),
            low=entry["range"][0],
            high=entry["range"][1],
        )
        for name, entry in data["instrument"].items()
    }
    players: list[Player] = []
    for entry in data["player"]:
        count = entry.get("count", 1)
        group = entry.get("group", "")
        first = instruments.get(entry["instruments"][0])
        if first is not None and first.clef == "grand":
            # A keyboard instrument or a harp has two staves: right hand and left hand.
            for hand in ("rh", "lh"):
                players.append(
                    Player(
                        f"{entry['id']}.{hand}",
                        entry["name"],
                        entry["short"],
                        entry["family"],
                        1,
                        entry["instruments"],
                        group,
                    )
                )
        elif entry["family"] in SEPARATE_STAVES and count > 1:
            for number in range(1, count + 1):
                players.append(
                    Player(
                        f"{entry['id']}{number}",
                        f"{entry['name']} {number}",
                        f"{entry['short']} {number}",
                        entry["family"],
                        1,
                        entry["instruments"],
                        group,
                    )
                )
        else:
            players.append(
                Player(
                    entry["id"],
                    entry["name"],
                    entry["short"],
                    entry["family"],
                    count,
                    entry["instruments"],
                    group,
                )
            )
    return Orchestra(players, instruments)


class WorkError(ValueError):
    """The music of a player does not agree with the structure of the work."""


@dataclass
class Section:
    """A block of bars. The composer writes the music of each player for the block."""

    work: Work
    first_bar: int
    last_bar: int
    written: set[str] = field(default_factory=set)

    @property
    def start(self) -> Fraction:
        return self.work.structure.bar(self.first_bar).start

    @property
    def end(self) -> Fraction:
        return self.work.structure.bar(self.last_bar).end

    def bar(self, offset: int) -> int:
        """Return the bar number of the bar `offset` of this section (1 = first bar)."""
        return self.first_bar + offset - 1

    def write(self, player_id: str, text: str) -> None:
        """Give the music of one player for this section. The text must fill the section."""
        if player_id in self.written:
            raise WorkError(f"{player_id}: music written two times for bars {self.label}")
        self.work.orchestra.player(player_id)  # make sure that the player exists
        try:
            parsed = music.parse(text)
            self._check(parsed)
        except (music.MusicSyntaxError, WorkError) as problem:
            raise WorkError(f"{player_id}, bars {self.label}: {problem}") from None
        _drop_repeated_dynamics(parsed.children, _DynamicState())
        self.work.chunks.setdefault(player_id, []).append((self.first_bar, parsed))
        self.written.add(player_id)
        self.work.revision += 1

    def sing(self, player_id: str, music_text: str, words: str) -> None:
        """Give the music and the words of a voice for this section.

        `words` is lyric text (see `lyrics.py`). Each note that takes a
        syllable must have one syllable.
        """
        self.write(player_id, music_text)
        parsed = self.work.chunks[player_id][-1][1]
        state = self.work.lyric_states.setdefault(player_id, lyrics.State())
        try:
            lyrics.check(parsed.children, words, state)
        except music.MusicSyntaxError as problem:
            raise WorkError(f"{player_id}, bars {self.label}: {problem}") from None
        self.work.lyrics.setdefault(player_id, []).append((self.first_bar, words))

    def close(self) -> None:
        """Give full-bar rests to all players that have no music in this section."""
        rests = " ".join(
            f"R1*{bar.numerator}/{bar.denominator} |"
            for bar in self.work.structure.bars[self.first_bar - 1 : self.last_bar]
        )
        for player in self.work.orchestra.players:
            if player.id not in self.written:
                self.write(player.id, rests)
            elif player.family == "voice":
                sung = self.work.lyrics.get(player.id, [])
                if not (sung and sung[-1][0] == self.first_bar):
                    # A voice with notes and no words: all later words would move.
                    chunk = self.work.chunks[player.id][-1][1]
                    state = self.work.lyric_states.setdefault(player.id, lyrics.State())
                    if lyrics.slots(chunk.children, state):
                        raise WorkError(
                            f"{player.id}, bars {self.label}: the voice has notes but no words"
                        )
        self._stop_hairpins_at_rests()
        self.work.revision += 1

    def _stop_hairpins_at_rests(self) -> None:
        """Stop each hairpin of this section at a silence (see `hairpins.py`)."""
        chunks = {
            player.id: self.work.chunks[player.id][-1][1] for player in self.work.orchestra.players
        }
        for player_id, chunk in chunks.items():
            # A player with two staves: a rest in one hand is not a silence while the
            # other hand plays.
            base, _, hand = player_id.partition(".")
            other = f"{base}.{'lh' if hand == 'rh' else 'rh'}" if hand in ("rh", "lh") else ""
            spans = hairpins.sounding(chunks[other].children, self.start) if other in chunks else []
            state = self.work.hairpin_states.setdefault(player_id, hairpins.State())
            hairpins.stop_at_rests(chunk.children, self.start, state, spans)

    @property
    def label(self) -> str:
        return f"{self.first_bar}-{self.last_bar}"

    def _check(self, parsed: music.Group) -> None:
        boundaries = {
            bar.start - self.start
            for bar in self.work.structure.bars[self.first_bar - 1 : self.last_bar]
        } | {self.end - self.start}
        position = _check_bar_lines(parsed.children, Fraction(0), Fraction(1), boundaries)
        if position != self.end - self.start:
            raise WorkError(
                f"the music has {position} quarter notes; the section has {self.end - self.start}"
            )


@dataclass
class _DynamicState:
    """The dynamic mark in effect while the code reads the music of a player."""

    mark: str = ""
    changed: bool = False  # a hairpin came after the mark
    silence: Fraction = Fraction(0)  # rests after the last note, in quarter notes


REPEAT_AFTER_SILENCE = Fraction(8)  # after this silence, a dynamic mark is given again


def _drop_repeated_dynamics(elements: list[music.Element], state: _DynamicState) -> None:
    """Remove a dynamic mark that is the same as the mark in effect.

    The composer makes music from repeated patterns. Each pattern has its
    dynamic mark. In the score, the mark must show only one time.
    """
    for element in elements:
        if isinstance(element, music.Command) and element.name == "switch":
            state.mark = ""
        elif isinstance(element, music.Rest):
            state.silence += element.duration
        elif isinstance(element, music.Note):
            kept = []
            for post in element.posts:
                if post.kind == "dynamic" and post.value in music.DYNAMICS:
                    repeated = (
                        post.value == state.mark
                        and not state.changed
                        and state.silence < REPEAT_AFTER_SILENCE
                    )
                    state.mark, state.changed = post.value, False
                    if repeated:
                        continue
                elif post.kind == "hairpin":
                    state.changed = True
                kept.append(post)
            element.posts[:] = kept
            state.silence = Fraction(0)
        elif isinstance(element, music.Group):
            _drop_repeated_dynamics(element.children, state)


def _check_bar_lines(
    elements: list[music.Element], position: Fraction, scale: Fraction, boundaries: set[Fraction]
) -> Fraction:
    """Walk the elements. Make sure that each bar check is at a bar line. Return the end."""
    for element in elements:
        if isinstance(element, music.BarCheck):
            if position not in boundaries:
                bar_index = sum(1 for b in boundaries if b <= position)
                raise WorkError(
                    f"bar check at the wrong position ({position} quarter notes, "
                    f"in bar {bar_index} of the section)"
                )
        elif isinstance(element, music.Note | music.Rest):
            end = position + element.duration * scale
            full_bars = isinstance(element, music.Rest) and element.kind == "R"
            if not full_bars and any(position < boundary < end for boundary in boundaries):
                bar_index = sum(1 for b in boundaries if b <= position)
                raise WorkError(
                    f"a note or a rest goes across a bar line (it starts at {position} quarter "
                    f"notes, in bar {bar_index} of the section): write two tied notes"
                )
            position = end
        elif isinstance(element, music.Group):
            if element.kind == "grace":
                continue
            if element.kind == "parallel":
                ends = {
                    _check_bar_lines(child.children, position, scale, boundaries)
                    for child in element.children
                }
                if len(ends) != 1:
                    raise WorkError(f"the voices of << >> have different lengths at {position}")
                position = ends.pop()
            elif element.kind in ("unfold", "tremolo"):
                for _ in range(element.count):
                    position = _check_bar_lines(element.children, position, scale, boundaries)
            else:
                position = _check_bar_lines(
                    element.children, position, scale * element.ratio, boundaries
                )
    return position


@dataclass
class Work:
    """The full work."""

    title: str
    orchestra: Orchestra
    structure: Structure = field(default_factory=Structure)
    chunks: dict[str, list[tuple[int, music.Group]]] = field(default_factory=dict)
    composer: str = ""
    subtitle: str = ""
    # The words of each voice: the first bar of a section, and its lyric text.
    lyrics: dict[str, list[tuple[int, str]]] = field(default_factory=dict)
    lyric_states: dict[str, lyrics.State] = field(default_factory=dict, repr=False)
    # The dynamic marks of each player at the end of the last complete section.
    hairpin_states: dict[str, hairpins.State] = field(default_factory=dict, repr=False)
    # The number of changes of the music. Code that keeps a result uses it.
    revision: int = field(default=0, repr=False, compare=False)

    def section(
        self, bars: int, numerator: int, denominator: int, grouping: tuple[int, ...] = ()
    ) -> Section:
        """Add bars with one metre and return the section for them."""
        first = self.structure.add_bars(bars, numerator, denominator, grouping)
        return Section(self, first, first + bars - 1)

    def section_of(
        self, metres: list[tuple[int, int] | tuple[int, int, tuple[int, ...]]]
    ) -> Section:
        """Add bars with different metres (one entry for each bar) and return the section."""
        first = len(self.structure.bars) + 1
        for metre in metres:
            grouping = metre[2] if len(metre) > 2 else ()
            self.structure.add_bars(1, metre[0], metre[1], grouping)
        return Section(self, first, len(self.structure.bars))

    def music_of(self, player_id: str) -> music.Group:
        """Return all music of one player as one sequence."""
        children: list[music.Element] = []
        for _first_bar, chunk in self.chunks.get(player_id, []):
            children.extend(chunk.children)
        return music.Group("sequence", children)

    def check_complete(self) -> None:
        """Make sure that each player has music for all bars."""
        total = self.structure.length
        for player in self.orchestra.players:
            written = sum(
                (music.length(chunk) for _bar, chunk in self.chunks.get(player.id, [])),
                Fraction(0),
            )
            if written != total:
                raise WorkError(
                    f"{player.id}: music for {written} quarter notes; the work has {total}"
                )
