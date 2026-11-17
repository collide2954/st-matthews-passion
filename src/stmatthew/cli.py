"""Command line interface: build the score, the parts, the audio, and the video."""

from __future__ import annotations

import argparse
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

BUILD_DIR = Path("build")


def write_lilypond() -> list[Path]:
    """Write the LilyPond files of the score and the parts."""
    from .notation import lilypond
    from .work import build

    return lilypond.write_all(build(), BUILD_DIR / "ly")


def compile_pdf(path: Path, output: Path) -> None:
    """Compile one LilyPond file into a PDF file in the output directory."""
    output.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["lilypond", "-dno-point-and-click", "--loglevel=WARNING", "-o", str(output / path.stem),
         str(path)],
        capture_output=True,
        text=True,
        check=False,
    )  # fmt: skip
    if result.returncode != 0:
        raise RuntimeError(f"LilyPond failed for {path}:\n{result.stderr[-2000:]}")
    for line in result.stderr.splitlines():
        # LilyPond reports a page that it made a little smaller: this is not a problem.
        if ("warning" in line or "error" in line) and "compress" not in line:
            print(f"{path.name}: {line}")


def build_pdfs(*, parts: bool = True) -> None:
    """Build the PDF of the score in C. If `parts` is true, build the full set also.

    The full set has the transposed score and the parts. The directory
    `build/set` gets a copy of each document with the name that an orchestra
    librarian expects.
    """
    import shutil

    from .notation import lilypond, pages
    from .work import build

    paths = write_lilypond()
    scores = [path for path in paths if path.name.startswith("score")]
    others = [path for path in paths if not path.name.startswith("score")] if parts else []
    compile_pdf(scores[0], BUILD_DIR / "score")
    if not parts:
        return
    # The two scores are large: they are engraved one at a time. The parts are small.
    compile_pdf(scores[1], BUILD_DIR / "score")
    # Each part is engraved two times: the music starts on a left page or on a right page.
    layouts = BUILD_DIR / "parts-layouts"
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        list(pool.map(lambda path: compile_pdf(path, layouts), others))
    work = build()
    names = lilypond.set_names(work)
    target = BUILD_DIR / "set"
    target.mkdir(parents=True, exist_ok=True)
    (BUILD_DIR / "parts").mkdir(parents=True, exist_ok=True)
    for old in target.glob("*.pdf"):
        old.unlink()  # the documents of a build before this one
    for path in scores:
        shutil.copyfile(
            BUILD_DIR / "score" / f"{path.stem}.pdf", target / f"{names[path.stem]}.pdf"
        )
    starts = []
    for part_id, players in lilypond.part_players(work).items():
        stem = f"part-{part_id}"
        left, right = layouts / f"{stem}.pdf", layouts / f"{stem}{lilypond.RIGHT_START}.pdf"
        # The cover is page 1. With a start on a right page, page 2 is empty.
        start = pages.better_start(
            pages.staves_on_pages(left)[1:], pages.staves_on_pages(right)[2:], len(players)
        )
        starts.append(f"{part_id}:{start}")
        chosen = left if start == 2 else right
        shutil.copyfile(chosen, BUILD_DIR / "parts" / f"{stem}.pdf")
        shutil.copyfile(chosen, target / f"{names[stem]}.pdf")
    print("parts: the page on which the music starts: " + " ".join(starts))


def build_audio(
    bars: tuple[int, int] | None = None, engine: str = "open", profile: str = "Muse Sounds"
) -> None:
    """Render the audio master, or an excerpt of it.

    The engine "open" is the sampler of this project with open sample
    libraries. The engine "musescore" is MuseScore Studio with Muse Sounds.
    """
    from .audio import mix, musescore
    from .work import build

    if engine == "musescore":
        audio, report = musescore.render_master(build(), BUILD_DIR / "musescore", bars, profile)
    else:
        audio, report = mix.render(build(), bars=bars)
    name = "st-matthews-passion" if bars is None else f"excerpt-{bars[0]}-{bars[1]}"
    if engine == "musescore" and bars is not None:
        name += "-musescore"
    for path in mix.write(audio, BUILD_DIR / "audio", name):
        print(f"audio: {path}")
    print(report)


def check_work() -> int:
    """Find music that a player cannot play. Return the number of problems."""
    from .compose.check import check
    from .work import build

    work = build()
    problems = check(work)
    for problem in problems:
        print(problem)
    seconds = work.structure.duration_seconds
    print(f"{len(work.structure.bars)} bars, {seconds / 60:.1f} minutes, {len(problems)} problems")
    return len(problems)


def build_video(mobile: bool = False) -> None:
    """Render the score video. The audio master must exist.

    If `mobile` is true, the video is for a telephone (1080 x 1920).
    """
    from .video import pages, render
    from .work import build

    work = build()
    audio = BUILD_DIR / "audio" / "st-matthews-passion.flac"
    if mobile:
        screens = pages.build_pages(
            work, BUILD_DIR / "video" / "pages-mobile", width_px=1080, mobile=True
        )
        output = BUILD_DIR / "video" / "st-matthews-passion-mobile.mp4"
        path = render.render(work, screens, audio, output, width=1080, height=1920, mobile=True)
    else:
        screens = pages.build_pages(work, BUILD_DIR / "video" / "pages")
        path = render.render(work, screens, audio, BUILD_DIR / "video" / "st-matthews-passion.mp4")
    print(f"video: {path}")


def show_ears(
    bars: tuple[int, int] | None, step: str = "1", players: str = "", brief: bool = False
) -> None:
    """Print the notes that sound together at each step of some bars (see `compose/ears.py`)."""
    from fractions import Fraction

    from .compose import ears
    from .work import build

    work = build()
    first, last = bars or (1, len(work.structure.bars))
    names = players.split(",") if players else None
    found = ears.moments(work, first, last, Fraction(step), names)
    if not brief:
        for line in ears.report(found):
            print(line)
    for name, value in ears.summary(found).items():
        print(f"{name:28s} {value:.2f}")
    for parallel in ears.parallels(work, first, last, names):
        print(parallel)
    for name, value in ears.voice_summary(work).items():
        print(f"voice: {name:42s} {value:.2f}")
    long = [phrase for phrase in ears.phrases(work) if phrase.seconds > 9.0]
    for phrase in long:
        print(f"voice: a phrase of {phrase.seconds:.1f} s starts in bar {phrase.bar}")


def show_stats() -> None:
    """Print the numbers of the work as a table."""
    from .compose.stats import measure
    from .work import build

    for name, value in measure(build()).rows():
        print(f"{name:45s} {value}")


def fetch_audio() -> int:
    """Get the audio master from the release `audio`. Return 1 if it is not for this music."""
    from . import release
    from .work import build

    return 0 if release.fetch(build(), BUILD_DIR / "audio") else 1


def publish_audio() -> None:
    """Put the audio master of the directory `build/audio` in the release `audio`."""
    from . import release
    from .work import build

    release.publish(build(), BUILD_DIR / "audio", "MuseScore Studio with Muse Sounds")
    print("publish-audio: the release 'audio' has the new master")


def draw_chart() -> None:
    """Draw the loudness of the audio master against the time. The audio master must exist."""
    from .audio.chart import loudness_chart
    from .work import build

    audio = BUILD_DIR / "audio" / "st-matthews-passion.flac"
    print(f"chart: {loudness_chart(build(), audio, Path('docs') / 'loudness.svg')}")


def calibrate_levels(new_only: bool = False) -> None:
    """Measure the levels of MuseScore with Muse Sounds for each dynamic mark."""
    from .audio import calibrate

    folder = BUILD_DIR / "musescore" / "calibrate"
    print(f"calibrate: {calibrate.measure(folder, new_only=new_only)}")


def update_documents() -> None:
    """Write the bar numbers, the times, and the measured values of the work into the documents."""
    from . import documents
    from .work import build

    changed = documents.update_files(build())
    for path in changed:
        print(f"docs: updated {path}")
    if not changed:
        print("docs: the documents are up to date")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="stmatthew", description="Build the St Matthew Passion.")
    parser.add_argument(
        "command",
        choices=[
            "check",
            "stats",
            "ears",
            "ly",
            "score",
            "parts",
            "audio",
            "fetch-audio",
            "publish-audio",
            "video",
            "chart",
            "docs",
            "calibrate",
            "all",
        ],
    )
    parser.add_argument(
        "--bars", metavar="FIRST-LAST", help="only these bars (commands: audio, ears)"
    )
    parser.add_argument(
        "--step", default="1", help="the step of the report in quarter notes (command: ears)"
    )
    parser.add_argument(
        "--players", default="", help="only these players, with commas (command: ears)"
    )
    parser.add_argument(
        "--brief", action="store_true", help="print only the summary (command: ears)"
    )
    parser.add_argument(
        "--engine",
        choices=["open", "musescore"],
        default="open",
        help="source of the sound (command: audio)",
    )
    parser.add_argument(
        "--mobile",
        action="store_true",
        help="make the video for a telephone, 1080 x 1920 (command: video)",
    )
    parser.add_argument(
        "--new",
        action="store_true",
        help="measure only the tests that the table does not have (command: calibrate)",
    )
    parser.add_argument(
        "--profile",
        default="Muse Sounds",
        help='sound profile of MuseScore: "Muse Sounds" or "MuseScore Basic"',
    )
    args = parser.parse_args(argv)
    bars = None
    if args.bars:
        first, _, last = args.bars.partition("-")
        bars = (int(first), int(last or first))
    if args.command == "check":
        return 1 if check_work() else 0
    if args.command == "stats":
        show_stats()
        return 0
    if args.command == "ears":
        show_ears(bars, args.step, args.players, args.brief)
        return 0
    if args.command == "chart":
        draw_chart()
        return 0
    if args.command == "docs":
        update_documents()
        return 0
    if args.command == "calibrate":
        calibrate_levels(args.new)
        return 0
    if args.command == "fetch-audio":
        return fetch_audio()
    if args.command == "publish-audio":
        publish_audio()
        return 0
    if args.command == "ly":
        for path in write_lilypond():
            print(path)
    elif args.command == "score":
        build_pdfs(parts=False)
    elif args.command == "parts":
        build_pdfs(parts=True)
    elif args.command == "audio":
        build_audio(bars, args.engine, args.profile)
    elif args.command == "video":
        build_video(args.mobile)
    else:
        build_pdfs(parts=True)
        build_audio()
        build_video()
        build_video(mobile=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
