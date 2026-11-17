"""The words of the voice: the text below the notes.

The composer writes the words of a section in the lyric syntax of LilyPond:

- Syllables have spaces between them: `Kommt, ihr Töch -- ter`.
- ` -- ` is the hyphen between two syllables of one word.
- ` __ ` is the line after a syllable that has more than one note.
- `_` is a note with no syllable.

Each note of the voice takes one syllable. A note does not take a syllable
if a tie comes to it from the note before it, or if it is inside a slur:
thus a slur shows a syllable with more than one note. A phrasing slur
(`\\(` and `\\)`) has no effect on the words. Grace notes take no syllable.

The code counts the notes and the syllables of each section. If the two
numbers are different, the composer gets a message for that section: in the
engraved score, all words after the error would be at wrong notes.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import music

MARKS = ("--", "__")

# LilyPond: a manual beam is not a sign for a syllable with more than one note.
VOICE_SETTINGS = (
    "\\set melismaBusyProperties = #'(melismaBusy slurMelismaBusy tieMelismaBusy) \\dynamicUp"
)


@dataclass
class State:
    """The state of the voice at the end of a section."""

    in_slur: bool = False
    tied: bool = False  # the last note has a tie to the subsequent note


def syllables(text: str) -> list[str]:
    """Return the syllables of lyric text (a `_` is a note with no syllable)."""
    return [word for word in text.split() if word not in MARKS]


def words(text: str) -> str:
    """Return lyric text as plain words: "Töch -- ter" becomes "Töchter"."""
    plain = text.replace(" -- ", "").replace(" __", "")
    return " ".join(word for word in plain.split() if word != "_")


def slots(elements: list[music.Element], state: State) -> int:
    """Return the number of notes that take a syllable. Update the state."""
    count = 0
    for element in elements:
        if isinstance(element, music.Note):
            if not (state.tied or state.in_slur):
                count += 1
            state.tied = any(post.kind == "tie" for post in element.posts)
            for post in element.posts:
                if post.kind == "slur":
                    state.in_slur = post.value == "("
        elif isinstance(element, music.Group):
            if element.kind == "grace":
                continue
            if element.kind == "parallel":
                raise music.MusicSyntaxError("the voice with words cannot have two voices (<< >>)")
            repeats = element.count if element.kind in ("unfold", "tremolo") else 1
            for _ in range(repeats):
                count += slots(element.children, state)
    return count


def check(elements: list[music.Element], text: str, state: State) -> None:
    """Make sure that the words of a section fit its notes. Update the state."""
    notes = slots(elements, state)
    given = len(syllables(text))
    if notes != given:
        raise music.MusicSyntaxError(
            f"the music has {notes} notes for syllables, and the words have {given} syllables"
        )
    for word in text.split():
        if '"' in word or "{" in word or "}" in word or "\\" in word:
            raise music.MusicSyntaxError(f"this text is not permitted in the words: {word!r}")
