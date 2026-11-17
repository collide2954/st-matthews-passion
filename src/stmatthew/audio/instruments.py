"""The sound of each instrument: which samples to use, and how the instrument behaves."""

from __future__ import annotations

from dataclasses import dataclass, field

from .library import Source

SSO = "Sonatina Symphonic Orchestra/Samples/"
VCSL_STRUCK = "Idiophones/Struck Idiophones/"

V2 = (("v1", 0.35), ("v2", 0.8))
V13 = (("v1", 0.35), ("v3", 0.8))
V3 = (("v1", 0.3), ("v2", 0.55), ("v3", 0.8))
V4 = (("v1", 0.25), ("v2", 0.5), ("v3", 0.72), ("v4", 0.92))
SOFT_LOUD = (("pp", 0.25), ("p", 0.38), ("mp", 0.5), ("mf", 0.6), ("f", 0.75), ("ff", 0.9))


def vsco(folder: str, pattern: str = r".*", layers=(), **options) -> Source:
    return Source("vsco2", folder, pattern, tuple(layers), **options)


def sso(folder: str, pattern: str = r".*", layers=(), **options) -> Source:
    return Source("sso", SSO + folder, pattern, tuple(layers), **options)


def vcsl(folder: str, pattern: str = r".*", layers=(), **options) -> Source:
    return Source("vcsl", folder, pattern, tuple(layers), **options)


@dataclass(frozen=True)
class Sound:
    """How one instrument sounds.

    `sources` maps a way to play to the samples for it. The key `sustain` is
    necessary. Other keys: `short`, `pizzicato`, `tremolo`, `harmonics`,
    `collegno`, `mute`, `nonvib`, `bowed`, `soft`.
    """

    sources: dict[str, tuple[Source, ...]]
    family: str  # strings, woodwinds, brass, percussion, plucked, keyboards
    loud_db: float  # level of the loudest playing, relative to the loudest instruments
    range_db: float  # difference between the loudest and the softest playing
    release: float = 0.15  # seconds of fade after the end of a note
    lead: float = 0.03  # seconds that the sample starts before the written time
    ensemble: int = 1  # number of sample players that sound together for one note
    detune_cents: float = 4.0  # random tuning difference between ensemble players
    timing_ms: float = 8.0  # random timing difference (standard deviation)
    decays: bool = False  # the sound decays by itself (percussion, harp, piano)
    lowcut_hz: float = 40.0  # frequency of the high-pass filter
    max_shift: float = 7.0  # largest pitch shift of a sample, in semitones
    unpitched: bool = False  # the written pitch selects a sample; it is not a real pitch
    extra: dict[str, float] = field(default_factory=dict)
    # Equalization of the instrument: ("low", Hz, dB), ("high", Hz, dB), ("peak", Hz, dB, Q).
    eq: tuple[tuple, ...] = ()
    # A louder note is brighter. This is the change of the high frequencies (dB)
    # from a middle loudness to the loudest playing. None = the value of the family.
    bright_db: float | None = None


RR = r"(?:_rr|_RR|_)(?P<rr>\d)"

SOUNDS: dict[str, Sound] = {
    # ---------------------------------------------------------------- strings
    "violin": Sound(
        {
            "sustain": (
                vsco("Strings/Violin Section/susVib", r".*_(?P<layer>v\d)", V2, low_hz=150),
            ),
            "second": (sso("1st Violins", r"1st-violins-sus-.*", low_hz=150),),
            "short": (
                vsco("Strings/Violin Section/Spic", r".*_(?P<layer>v\d)" + RR, V3, held=False),
            ),
            "pizzicato": (
                vsco("Strings/Violin Section/Pizz", r".*_(?P<layer>v\d)" + RR, V3, held=False),
            ),
            "tremolo": (vsco("Strings/Violin Section/Trem", r".*_(?P<layer>v\d)", V2, low_hz=150),),
            "harmonics": (sso("1st Violins", r"1st-violins-hrm-.*", low_hz=300, high_hz=5000),),
            "collegno": (sso("1st Violins", r"1st-violins-col-.*", held=False),),
            "solo": (
                vsco(
                    "Strings/Solo Violin/Arco Vib", r".*_(?P<layer>p|mf|f)", SOFT_LOUD, low_hz=150
                ),
            ),
        },
        "strings",
        loud_db=-7,
        range_db=40,
        release=0.22,
        lead=0.06,
        ensemble=3,
        lowcut_hz=170,
        eq=(("high", 2500.0, 2.0),),
    ),
    "viola": Sound(
        {
            "sustain": (
                vsco("Strings/Viola Section/susvib", r".*_(?P<layer>v\d)" + RR, V13, low_hz=100),
            ),
            "second": (sso("Violas", r"violas-sus-.*", low_hz=100),),
            "short": (
                vsco("Strings/Viola Section/spic", r".*_(?P<layer>v\d)" + RR, V3, held=False),
            ),
            "pizzicato": (
                vsco("Strings/Viola Section/pizz", r".*_(?P<layer>v\d)" + RR, V3, held=False),
            ),
            "tremolo": (
                vsco("Strings/Viola Section/trem", r".*_(?P<layer>v\d)" + RR, V13, low_hz=100),
            ),
            "harmonics": (sso("Violas", r"violas-hrm-.*", low_hz=200, high_hz=4000),),
            "collegno": (sso("Violas", r"violas-col-.*", held=False),),
        },
        "strings",
        loud_db=-8,
        range_db=40,
        release=0.24,
        lead=0.07,
        ensemble=3,
        lowcut_hz=110,
        eq=(("high", 2500.0, 2.0),),
    ),
    "violoncello": Sound(
        {
            "sustain": (
                vsco(
                    "Strings/Cello Section/susvib",
                    r".*_(?P<layer>v\d)" + RR,
                    V13,
                    low_hz=50,
                    high_hz=1500,
                ),
            ),
            "second": (sso("Celli", r"celli-sus-.*", low_hz=50, high_hz=1500),),
            "short": (
                vsco("Strings/Cello Section/spic", r".*_(?P<layer>v\d)" + RR, V3, held=False),
            ),
            "pizzicato": (
                vsco("Strings/Cello Section/pizzT", r".*_(?P<layer>v\d)" + RR, V3, held=False),
            ),
            "tremolo": (
                vsco(
                    "Strings/Cello Section/trem",
                    r".*_(?P<layer>v\d)" + RR,
                    V13,
                    low_hz=50,
                    high_hz=1500,
                ),
            ),
            "harmonics": (sso("Celli", r"celli-hrm-.*", low_hz=100, high_hz=3000),),
            "collegno": (sso("Celli", r"celli-col-.*", held=False),),
        },
        "strings",
        loud_db=-7,
        range_db=40,
        release=0.28,
        lead=0.08,
        ensemble=3,
        lowcut_hz=55,
    ),
    "double bass": Sound(
        {
            "sustain": (
                vsco(
                    "Strings/Solo Contrabass/SusVib",
                    r".*_(?P<layer>v\d)" + RR,
                    V13,
                    low_hz=25,
                    high_hz=600,
                ),
            ),
            "second": (sso("Basses", r"basses-sus-.*", low_hz=25, high_hz=600),),
            "nonvib": (
                vsco(
                    "Strings/Solo Contrabass/SusNV",
                    r".*_(?P<layer>v\d)" + RR,
                    V13,
                    low_hz=25,
                    high_hz=600,
                ),
            ),
            "short": (
                vsco("Strings/Solo Contrabass/Spic", r".*_(?P<layer>v\d)" + RR, V3, held=False),
            ),
            "pizzicato": (
                vsco("Strings/Solo Contrabass/Pizz", r".*_(?P<layer>v\d)" + RR, V3, held=False),
            ),
            "tremolo": (
                vsco(
                    "Strings/Solo Contrabass/Trem",
                    r".*_(?P<layer>v\d)" + RR,
                    V13,
                    low_hz=25,
                    high_hz=600,
                ),
            ),
            "collegno": (sso("Basses", r"basses-col-.*", held=False),),
        },
        "strings",
        loud_db=-6,
        range_db=38,
        release=0.3,
        lead=0.09,
        ensemble=3,
        lowcut_hz=28,
    ),
    # -------------------------------------------------------------- woodwinds
    "flute": Sound(
        {
            "sustain": (vsco("Woodwinds/Flute/susvib", r".*_(?P<layer>v\d)" + RR, V2, low_hz=200),),
            "nonvib": (vsco("Woodwinds/Flute/susNV", r".*_(?P<layer>v\d)" + RR, V2, low_hz=200),),
            "short": (vsco("Woodwinds/Flute/stac", r".*_(?P<layer>v\d)" + RR, V3, held=False),),
        },
        "woodwinds",
        loud_db=-12,
        range_db=26,
        release=0.12,
        lowcut_hz=220,
    ),
    "piccolo": Sound(
        {"sustain": (sso("Piccolo", low_hz=400, high_hz=5000),)},
        "woodwinds",
        loud_db=-9,
        range_db=24,
        release=0.1,
        lowcut_hz=450,
    ),
    "alto flute": Sound(
        {"sustain": (sso("Alto Flute", low_hz=150, high_hz=2500),)},
        "woodwinds",
        loud_db=-15,
        range_db=24,
        release=0.14,
        lowcut_hz=160,
    ),
    "oboe": Sound(
        {
            "sustain": (vsco("Woodwinds/Oboe/Vib", r".*_(?P<layer>v\d)_Main", V2, low_hz=200),),
            "nonvib": (vsco("Woodwinds/Oboe/Sus", r".*_(?P<layer>v\d)_Main", V2, low_hz=200),),
            "short": (
                vsco(
                    "Woodwinds/Oboe/Stacc", r".*_(?P<layer>v\d)_rr(?P<rr>\d)_Main", V3, held=False
                ),
            ),
        },
        "woodwinds",
        loud_db=-11,
        range_db=24,
        release=0.1,
        lowcut_hz=210,
    ),
    "English horn": Sound(
        {"sustain": (sso("Cor Anglais", low_hz=120, high_hz=1500),)},
        "woodwinds",
        loud_db=-12,
        range_db=24,
        release=0.12,
        lowcut_hz=140,
    ),
    "clarinet in B-flat": Sound(
        {
            "sustain": (
                vsco(
                    "Woodwinds/Clarinet/susLong",
                    r".*_(?P<layer>v\d)_rr(?P<rr>\d)_sum",
                    V3,
                    low_hz=100,
                    high_hz=2500,
                ),
            ),
            "short": (
                vsco(
                    "Woodwinds/Clarinet/stac", r".*_(?P<layer>v\d)_rr(?P<rr>\d)_sum", V3, held=False
                ),
            ),
        },
        "woodwinds",
        loud_db=-11,
        range_db=36,
        release=0.1,
        lowcut_hz=130,
    ),
    "bass clarinet": Sound(
        {"sustain": (sso("Bass Clarinet", low_hz=50, high_hz=1200),)},
        "woodwinds",
        loud_db=-11,
        range_db=34,
        release=0.14,
        lowcut_hz=40,
        max_shift=14,
    ),
    "bassoon": Sound(
        {
            "sustain": (
                vsco(
                    "Woodwinds/Bassoon/vib", r".*_(?P<layer>v\d)" + RR, V2, low_hz=45, high_hz=1200
                ),
            ),
            "nonvib": (
                vsco(
                    "Woodwinds/Bassoon/sus", r".*_(?P<layer>v\d)" + RR, V2, low_hz=45, high_hz=1200
                ),
            ),
            "short": (vsco("Woodwinds/Bassoon/stac", r".*_(?P<layer>v\d)" + RR, V3, held=False),),
        },
        "woodwinds",
        loud_db=-11,
        range_db=28,
        release=0.12,
        lowcut_hz=50,
    ),
    "contrabassoon": Sound(
        {"sustain": (sso("Contrabassoon", low_hz=25, high_hz=600),)},
        "woodwinds",
        loud_db=-10,
        range_db=26,
        release=0.16,
        lowcut_hz=26,
    ),
    # ------------------------------------------------------------------ brass
    "horn in F": Sound(
        {
            "sustain": (
                vsco("Brass/F Horn/sus", r".*_(?P<layer>v\d)" + RR, V4, low_hz=35, high_hz=1200),
            ),
            "short": (vsco("Brass/F Horn/stac", r".*_(?P<layer>v\d)" + RR, V3, held=False),),
            "mute": (
                vsco("Brass/F Horn/mute", r".*_(?P<layer>v\d)" + RR, V2, low_hz=35, high_hz=1200),
            ),
        },
        "brass",
        loud_db=-4,
        range_db=38,
        release=0.16,
        lead=0.05,
        lowcut_hz=60,
        eq=(("peak", 620.0, -2.5, 1.2),),
    ),
    "trumpet in C": Sound(
        {
            "sustain": (vsco("Brass/Trumpet/sus", r".*_(?P<layer>v\d)" + RR, V3, low_hz=120),),
            "short": (vsco("Brass/Trumpet/stac", r".*_(?P<layer>v\d)" + RR, V3, held=False),),
            "mute": (
                vsco("Brass/Trumpet/straightM-sus", r".*_(?P<layer>v\d)" + RR, V2, low_hz=120),
            ),
        },
        "brass",
        loud_db=-1,
        range_db=36,
        release=0.12,
        lead=0.03,
        lowcut_hz=150,
    ),
    "tenor trombone": Sound(
        {
            "sustain": (
                vsco(
                    "Brass/Tenor Trombone/sus",
                    r".*_(?P<layer>v\d)" + RR,
                    V3,
                    low_hz=35,
                    high_hz=1200,
                ),
            ),
            "short": (
                vsco("Brass/Tenor Trombone/stac", r".*_(?P<layer>v\d)" + RR, V3, held=False),
            ),
        },
        "brass",
        loud_db=-1,
        range_db=36,
        release=0.14,
        lead=0.04,
        lowcut_hz=45,
    ),
    "bass trombone": Sound(
        {"sustain": (sso("Bass Trombone", low_hz=30, high_hz=900),)},
        "brass",
        loud_db=-1,
        range_db=34,
        release=0.16,
        lead=0.05,
        lowcut_hz=32,
    ),
    "tuba": Sound(
        {
            "sustain": (
                vsco(
                    "Brass/Tuba/sus",
                    r".*_(?P<layer>v\d)_rr(?P<rr>\d)_Mid",
                    V3,
                    low_hz=25,
                    high_hz=600,
                ),
            ),
            "short": (
                vsco("Brass/Tuba/stac", r".*_(?P<layer>v\d)_rr(?P<rr>\d)_Sum", V3, held=False),
            ),
        },
        "brass",
        loud_db=-3,
        range_db=32,
        release=0.18,
        lead=0.06,
        lowcut_hz=28,
    ),
    # ------------------------------------------------------- pitched percussion
    "timpani": Sound(
        {
            "sustain": (
                sso(
                    "Percussion",
                    r"timpani-(?P<layer>p|f)-(?:lh|rh)-.*",
                    SOFT_LOUD,
                    held=False,
                    octave_shift=1,
                ),
            ),
            "tremolo": (sso("Percussion", r"timpani-roll-[a-g]#?\d", octave_shift=1),),
        },
        "percussion",
        loud_db=-2,
        range_db=40,
        decays=True,
        lowcut_hz=35,
        max_shift=4,
    ),
    "vibraphone": Sound(
        {
            "sustain": (
                vcsl(VCSL_STRUCK + "Vibraphone/Soft Mallets", r".*", held=False, high_hz=3000),
            ),
            "hard": (vcsl(VCSL_STRUCK + "Vibraphone/Hard Mallets", r".*", held=False),),
            "bowed": (vcsl(VCSL_STRUCK + "Vibraphone/Bowed", r".*", held=False),),
        },
        "percussion",
        loud_db=-14,
        range_db=30,
        decays=True,
        lowcut_hz=120,
    ),
    "marimba": Sound(
        {
            "sustain": (
                sso(
                    "Marimba", r"marimba-yarn-(?P<layer>pp|p|mp|mf|f|ff)-.*", SOFT_LOUD, held=False
                ),
            )
        },
        "percussion",
        loud_db=-14,
        range_db=30,
        decays=True,
        lowcut_hz=60,
    ),
    "glockenspiel": Sound(
        {
            "sustain": (
                vcsl(VCSL_STRUCK + "Glockenspiel", r".*", held=False, low_hz=400, high_hz=8000),
            )
        },
        "percussion",
        loud_db=-16,
        range_db=26,
        decays=True,
        lowcut_hz=500,
    ),
    "crotales": Sound(
        {
            "sustain": (
                sso(
                    "Crotales",
                    r"crotale-.*-(?P<layer>pp|ff)",
                    SOFT_LOUD,
                    held=False,
                    low_hz=800,
                    high_hz=9000,
                ),
            )
        },
        "percussion",
        loud_db=-16,
        range_db=26,
        decays=True,
        lowcut_hz=900,
    ),
    "xylophone": Sound(
        {
            "sustain": (
                vcsl(
                    VCSL_STRUCK + "Xylophone/Medium Mallets",
                    r".*_(?P<layer>pp|p|mf|f|ff)_.*",
                    SOFT_LOUD,
                    held=False,
                    low_hz=150,
                ),
            )
        },
        "percussion",
        loud_db=-10,
        range_db=28,
        decays=True,
        lowcut_hz=250,
    ),
    "tubular bells": Sound(
        {
            "sustain": (
                vcsl(
                    VCSL_STRUCK + "Tubular Bells 1",
                    r"chimes_.*_(?P<layer>pp|p|mf|f|ff)_rr(?P<rr>\d)",
                    SOFT_LOUD,
                    held=False,
                ),
            )
        },
        "percussion",
        loud_db=-8,
        range_db=30,
        decays=True,
        lowcut_hz=150,
    ),
    # --------------------------------------------------- harp, keyboards, plucked
    "harp": Sound(
        {
            "sustain": (
                vcsl(
                    "Chordophones/Composite Chordophones/Concert Harp",
                    r"KSHarp_.*_(?P<layer>p|mp|mf|f|ff)\d",
                    SOFT_LOUD,
                    held=False,
                ),
            )
        },
        "plucked",
        loud_db=-14,
        range_db=30,
        decays=True,
        lowcut_hz=30,
    ),
    "celesta": Sound(
        {
            "sustain": (
                sso(
                    "Celeste",
                    r"celeste-.*-(?P<layer>soft|hard)",
                    (("soft", 0.35), ("hard", 0.75)),
                    held=False,
                    low_hz=200,
                    high_hz=6000,
                ),
            )
        },
        "keyboards",
        loud_db=-20,
        range_db=24,
        decays=True,
        lowcut_hz=200,
    ),
    "piano": Sound(
        {
            "sustain": (
                vcsl(
                    "Chordophones/Zithers/Grand Piano, Kawai/Sustains",
                    r".*_(?P<layer>v\d)_rr(?P<rr>\d)_.*",
                    V4,
                    held=False,
                ),
            )
        },
        "keyboards",
        loud_db=-8,
        range_db=38,
        decays=True,
        lowcut_hz=25,
    ),
    "mandolin": Sound(
        {"sustain": (Source("mandolin", "samples", r".*", held=False, low_hz=150),)},
        "plucked",
        loud_db=-18,
        range_db=26,
        decays=True,
        lowcut_hz=180,
    ),
    "cimbalom": Sound(
        {"sustain": (Source("zither", "Samples/mel", r".*", held=False, low_hz=80),)},
        "plucked",
        loud_db=-13,
        range_db=30,
        decays=True,
        lowcut_hz=60,
        max_shift=31,
    ),
    # The accordion: the samples are from a chromatic harmonica. The two
    # instruments make their sound with the same type of free reed.
    "accordion": Sound(
        {
            "sustain": (
                vcsl("Aerophones/Free Aerophones/Harmonica-Hohner-Super64/Sustains/Normal"),
            ),
        },
        "keyboards",
        loud_db=-21,
        range_db=20,
        release=0.14,
        lead=0.05,
        lowcut_hz=90,
        max_shift=6,
        eq=(("high", 1800.0, -7.0), ("peak", 3500.0, -4.0, 1.0)),
        bright_db=8.0,
    ),
    "ocarina": Sound(
        {
            "sustain": (
                vcsl(
                    "Aerophones/Edge-blown Aerophones/Ocarina, Typical/Sustains/Sus",
                    r".*",
                    low_hz=300,
                    high_hz=3000,
                ),
            )
        },
        "woodwinds",
        loud_db=-16,
        range_db=18,
        release=0.08,
        lowcut_hz=350,
    ),
}

_HIT = {"pitched": False, "held": False}


def _unpitched(
    source: Source, *, loud_db: float, lowcut_hz: float, tremolo: Source | None = None
) -> Sound:
    """Return the sound of a percussion instrument with no pitch."""
    sources = {"sustain": (source,)}
    if tremolo is not None:
        sources["tremolo"] = (tremolo,)
    return Sound(
        sources, "percussion", loud_db=loud_db, range_db=40, decays=True, lowcut_hz=lowcut_hz,
        unpitched=True,
    )  # fmt: skip


SOUNDS.update(
    {
        "tam-tams": Sound(
            {"sustain": (sso("Percussion", r"tamtam-.*", pitched=False, held=False),)},
            "percussion",
            loud_db=-5,
            range_db=42,
            decays=True,
            lowcut_hz=30,
            unpitched=True,
        ),
        "bass drum": _unpitched(
            vcsl(
                "Membranophones/Struck Membranophones/Bass Drum 2",
                r"bassdrum_hit_(?P<layer>mp|mf|f|ff)(?P<rr>\d)?",
                SOFT_LOUD,
                **_HIT,
            ),
            loud_db=-2,
            lowcut_hz=25,
        ),
        "suspended cymbals": _unpitched(
            vcsl(
                VCSL_STRUCK + "Suspended Cymbal 1",
                r"susCymb1_hit_(?P<layer>pp|mp|f|fff)1",
                (("pp", 0.25), ("mp", 0.5), ("f", 0.75), ("fff", 0.95)),
                **_HIT,
            ),
            loud_db=-6,
            lowcut_hz=200,
            tremolo=vcsl(
                VCSL_STRUCK + "Suspended Cymbal 1",
                r"susCymb1_roll_(?P<layer>mp|f|ff)\d_nloop",
                (("mp", 0.45), ("f", 0.72), ("ff", 0.9)),
                pitched=False,
            ),
        ),
        "crash cymbals": _unpitched(
            vcsl(
                VCSL_STRUCK + "Clash Cymbals 1",
                r"cymbal_crash1_(?P<layer>pp|mp|mf|ff)(?P<rr>\d)",
                SOFT_LOUD,
                **_HIT,
            ),
            loud_db=-3,
            lowcut_hz=200,
        ),
        "wood blocks": _unpitched(
            vcsl(
                VCSL_STRUCK + "Woodblock", r"wood_click_(?P<layer>pp|mp|f|ff).*", SOFT_LOUD, **_HIT
            ),
            loud_db=-12,
            lowcut_hz=300,
        ),
        "claves": _unpitched(
            vcsl(
                VCSL_STRUCK + "Claves", r"Claves1_Hit_(?P<layer>v\d)_rr(?P<rr>\d)_Mid", V3, **_HIT
            ),
            loud_db=-12,
            lowcut_hz=400,
        ),
        "frame drum": _unpitched(
            vcsl(
                "Membranophones/Struck Membranophones/Frame Drum",
                r"HDrumL_Hit_(?P<layer>v\d)_rr(?P<rr>\d)_Sum",
                (("v2", 0.5), ("v3", 0.8)),
                **_HIT,
            ),
            loud_db=-10,
            lowcut_hz=60,
        ),
        "snare drum": _unpitched(
            vcsl(
                "Membranophones/Struck Membranophones/Snare Drum, Modern 1",
                r"Snare2_HitSN_(?P<layer>v\d)_rr(?P<rr>\d)_Mid",
                (("v3", 0.3), ("v5", 0.5), ("v6", 0.65), ("v7", 0.8), ("v9", 0.95)),
                **_HIT,
            ),
            loud_db=-6,
            lowcut_hz=120,
        ),
        "tom-toms": _unpitched(
            vcsl(
                "Membranophones/Struck Membranophones/Tom 2/Stick",
                r"TomL_HitS_(?P<layer>v\d)_rr(?P<rr>\d)_Mid",
                (("v2", 0.4), ("v3", 0.65), ("v4", 0.9)),
                **_HIT,
            ),
            loud_db=-4,
            lowcut_hz=50,
        ),
        "triangle": _unpitched(
            vcsl(
                VCSL_STRUCK + "Triangles",
                r"Triangle1_Hit_(?P<layer>v\d)_rr(?P<rr>\d)_Mid",
                V3,
                **_HIT,
            ),
            loud_db=-16,
            lowcut_hz=800,
        ),
    }
)

# Instruments that use the sound of a different instrument until the project has samples.
ALIASES = {
    "clarinet in E-flat": "clarinet in B-flat",
    "contrabass clarinet": "bass clarinet",
    "tuned gongs": "tubular bells",
    "taiko": "bass drum",
}


def sound_of(instrument: str) -> Sound:
    """Return the sound of an instrument."""
    return SOUNDS[ALIASES.get(instrument, instrument)]
