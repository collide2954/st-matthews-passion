"""Playing techniques and expression words.

Each technique is a command of the music language, for example `\\pizz`.
A technique has two effects:

- In the score, it prints a text mark.
- In the audio, it changes the state of the player (for example from bowed to plucked).
"""

from __future__ import annotations

from dataclasses import dataclass

from . import music


@dataclass(frozen=True)
class Technique:
    """One technique command.

    `state` is the part of the player state that the command changes, and
    `value` is the new value. An empty `state` is a text mark with no effect
    on the audio.
    """

    name: str
    text: str
    state: str = ""
    value: str = ""
    italic: bool = False
    below: bool = False


_T = Technique

TECHNIQUES: dict[str, Technique] = {
    technique.name: technique
    for technique in [
        # Strings: how the string vibrates.
        _T("pizz", "pizz.", "attack", "pizzicato"),
        _T("arco", "arco", "attack", "arco"),
        _T("collegno", "col legno batt.", "attack", "col legno"),
        _T("spicc", "spicc.", "attack", "spiccato"),
        # Strings: where the bow touches the string.
        _T("sulpont", "sul pont.", "place", "sul ponticello"),
        _T("sultasto", "sul tasto", "place", "sul tasto"),
        _T("ord", "ord.", "place", "ordinario"),
        # Mutes.
        _T("consord", "con sord.", "mute", "on"),
        _T("senzasord", "senza sord.", "mute", "off"),
        _T("practicemute", "practice mute", "mute", "practice"),
        # Vibrato.
        _T("nonvib", "non vib.", "vibrato", "none"),
        _T("pocovib", "poco vib.", "vibrato", "little"),
        _T("vib", "vib.", "vibrato", "normal"),
        _T("moltovib", "molto vib.", "vibrato", "much"),
        # Section size.
        _T("solo", "solo", "desk", "solo"),
        _T("tutti", "tutti", "desk", "tutti"),
        _T("div", "div.", "", ""),
        _T("unis", "unis.", "", ""),
        # Winds and brass.
        _T("flz", "flz.", "tongue", "flutter"),
        _T("nat", "nat.", "tongue", "normal"),
        _T("airtone", "air tone", "tone", "air"),
        _T("bellsup", "bells up", "", ""),
        _T("cuivre", "cuivré", "tone", "brassy"),
        # Percussion, harp, keyboards.
        _T("lv", "l.v.", "ring", "on"),
        _T("damp", "damp", "ring", "off"),
        _T("bowed", "with a bow", "attack", "bowed"),
        _T("mallets", "with mallets", "attack", "arco"),
        _T("softmallets", "soft mallets", "mallet", "soft"),
        _T("hardmallets", "hard mallets", "mallet", "hard"),
        _T("motoron", "motor on", "motor", "on"),
        _T("motoroff", "motor off", "motor", "off"),
        # Expression words. These have no effect on the audio.
        _T("espr", "espr.", italic=True, below=True),
        _T("moltoespr", "molto espr.", italic=True, below=True),
        _T("dolce", "dolce", italic=True, below=True),
        _T("sost", "sost.", italic=True, below=True),
        _T("cantabile", "cantabile", italic=True, below=True),
        _T("lontano", "lontano", italic=True, below=True),
        _T("morendo", "morendo", italic=True, below=True),
        _T("sempre", "sempre", italic=True, below=True),
        _T("subito", "sub.", italic=True, below=True),
        _T("pocoapoco", "poco a poco", italic=True, below=True),
        _T("niente", "niente", italic=True, below=True),
        _T("martellato", "martellato", italic=True, below=True),
        _T("brillante", "brillante", italic=True, below=True),
        _T("leggiero", "leggiero", italic=True, below=True),
        _T("senzaped", "senza Ped.", italic=True, below=True),
        _T("quasiarpa", "quasi arpa, liberamente", italic=True, below=True),
    ]
}

music.TECHNIQUE_NAMES.update(TECHNIQUES)


def lilypond_definitions() -> str:
    """Return the LilyPond definitions of all technique commands."""
    lines = []
    for technique in TECHNIQUES.values():
        direction = "_" if technique.below else "^"
        style = "\\italic " if technique.italic else ""
        lines.append(f'{technique.name} = {direction}\\markup {{ {style}"{technique.text}" }}')
    return "\n".join(lines)
