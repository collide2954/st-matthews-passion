"""The sound of the voice in the audio.

The alto sings words. No sound library of this project has a solo singer who
sings words. Thus a stand-in has the line of the voice in the audio. The
score and the video show the words.

The stand-ins are:

- `clarinet`: a clarinet of Muse Sounds. The clarinet is not an instrument of
  the orchestra of this work: thus the line of the voice has its own colour.
- `horn`: a horn of Muse Sounds.
- `chorus`: a group of women who sing the vowel "ah" (samples of the Sonatina
  Symphonic Orchestra). The sampler of this project plays them. The lowest
  sample is the note G4. The alto sings an octave below this note also: the
  sampler then makes a sample lower, and the sound of the voices becomes dark
  and not natural.

The environment variable `STMATTHEW_VOICE` selects the stand-in for one
render. The owner of the project has not made a decision about the voice:
see `voice_in_the_audio` in `design/brief.toml`.
"""

from __future__ import annotations

import os

SOURCES = ("clarinet", "horn", "chorus")
DEFAULT = "clarinet"
VARIABLE = "STMATTHEW_VOICE"


def source() -> str:
    """Return the name of the stand-in for the voice."""
    name = os.environ.get(VARIABLE) or DEFAULT
    if name not in SOURCES:
        raise ValueError(f"{VARIABLE} must be one of: {', '.join(SOURCES)}")
    return name
