"""Draw the frames of the score video and encode them with the audio.

Each frame shows one system of the score. A cursor shows the present moment.
A colour band shows each staff that sounds at this moment. A ribbon at the
bottom shows all instruments of the orchestra: an instrument is lit while it
plays. Thus the viewer can follow each part.
"""

from __future__ import annotations

import multiprocessing
import os
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from ..notation.structure import Structure
from ..notation.work import Work
from ..perform.events import perform
from .pages import Page

PAPER = np.array([250, 247, 240], dtype=np.float32)
INK = (38, 38, 44)
CURSOR = np.array([36, 64, 128], dtype=np.float32)
FAMILY_COLOURS = {
    "woodwinds": (70, 148, 92),
    "brass": (204, 142, 30),
    "percussion": (142, 98, 172),
    "plucked": (40, 146, 160),
    "keyboards": (40, 146, 160),
    "strings": (188, 74, 62),
}
TOP_BAND = 64  # pixels at 1080p
BOTTOM_BAND = 128
# The video for a telephone (1080 x 1920): the top band has two lines of text, and
# the ribbon has four rows.
MOBILE_TOP_BAND = 118  # pixels at a width of 1080
MOBILE_BOTTOM_BAND = 276
# The space above and below the staves of a system that the frame shows (pixels at
# 1080p). The staves of the video for a telephone are larger: the tempo text and the
# rehearsal mark are farther from the top staff.
MARGINS = (80, 60)
MOBILE_MARGINS = (210, 90)
RING_SECONDS = 0.5  # shortest time that an instrument is lit
MAX_WORKERS = 8  # largest number of parallel processes

# The data of the present render. The worker processes get it when they start.
_JOB: dict = {}


def _draw_part(job: tuple[int, int, Path]) -> None:
    _JOB["draw"](*job)


def _font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    pattern = "C059:bold" if bold else "C059"
    path = subprocess.run(
        ["fc-match", "-f", "%{file}", pattern], capture_output=True, text=True, check=True
    ).stdout
    return ImageFont.truetype(path, size)


@dataclass
class _Screen:
    """A page that is ready for drawing: the picture and the positions on the frame."""

    base: np.ndarray  # float32 picture of the full frame
    times: np.ndarray
    xs: np.ndarray
    staves: dict[str, tuple[int, int]]
    left: int
    right: int
    top: int
    bottom: int


def _prepare(
    page: Page,
    width: int,
    height: int,
    scale: float,
    top_band: int,
    bottom_band: int,
    margins: tuple[int, int] = MARGINS,
) -> _Screen:
    """Put the system of a page in the centre of the score area of the frame."""
    picture = np.asarray(Image.open(page.image).convert("RGB"), dtype=np.float32) / 255.0
    picture = picture[:, :width]  # the page picture can be one pixel wider than the frame
    area_top, area_bottom = top_band + int(8 * scale), height - bottom_band - int(8 * scale)
    area_height = area_bottom - area_top
    crop_top = max(0, int(page.top - margins[0] * scale))
    crop_bottom = min(picture.shape[0], int(page.bottom + margins[1] * scale))
    crop = picture[crop_top:crop_bottom]
    factor = min(1.0, area_height / crop.shape[0])
    if factor < 1.0:
        size = (int(crop.shape[1] * factor), int(crop.shape[0] * factor))
        resized = Image.fromarray((crop * 255).astype(np.uint8)).resize(size, Image.LANCZOS)
        crop = np.asarray(resized, dtype=np.float32) / 255.0
    offset_x = (width - crop.shape[1]) // 2
    offset_y = area_top + (area_height - crop.shape[0]) // 2
    base = np.broadcast_to(PAPER, (height, width, 3)).copy()
    region = base[offset_y : offset_y + crop.shape[0], offset_x : offset_x + crop.shape[1]]
    region *= crop  # the white of the page takes the colour of the paper

    def to_x(value: float) -> int:
        return int(offset_x + value * factor)

    def to_y(value: float) -> int:
        return int(offset_y + (value - crop_top) * factor)

    return _Screen(
        base=base,
        times=page.times,
        xs=offset_x + page.xs * factor,
        staves={name: (to_y(a), to_y(b)) for name, (a, b) in page.staves.items()},
        left=to_x(page.left),
        right=to_x(page.right),
        top=to_y(page.top),
        bottom=to_y(page.bottom),
    )


def _activity(work: Work, fps: int, frames: int) -> dict[str, np.ndarray]:
    """Return, for each instrument, the frames in which it sounds."""
    structure = work.structure
    active: dict[str, np.ndarray] = {}
    for player in work.orchestra.players:
        name = player.id.split(".")[0]
        flags = active.setdefault(name, np.zeros(frames, dtype=bool))
        for note in perform(work, player.id):
            start = structure.seconds(note.start)
            end = max(structure.seconds(note.start + note.duration), start + RING_SECONDS)
            flags[int(start * fps) : int(end * fps) + 1] = True
    return active


def _positions(structure: Structure, fps: int, frames: int) -> np.ndarray:
    """Return the position (quarter notes) of each frame."""
    grid = np.arange(0.0, float(structure.length) + 0.126, 0.125)
    seconds = np.array([structure.seconds(Fraction(value).limit_denominator(8)) for value in grid])
    return np.interp(np.arange(frames) / fps, seconds, grid)


def render(
    work: Work,
    pages: list[Page],
    audio: Path,
    output: Path,
    *,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    mobile: bool = False,
) -> Path:
    """Write the score video.

    If `mobile` is true, the video is for a telephone: the frame is tall and
    narrow, and the text and the ribbon are larger.
    """
    scale = width / 1080.0 if mobile else height / 1080.0
    top_band = int((MOBILE_TOP_BAND if mobile else TOP_BAND) * scale)
    bottom_band = int((MOBILE_BOTTOM_BAND if mobile else BOTTOM_BAND) * scale)
    structure = work.structure
    duration = float(
        subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
             str(audio)],
            capture_output=True, text=True, check=True,
        ).stdout
    )  # fmt: skip
    frames = int(duration * fps)
    positions = _positions(structure, fps, frames)
    activity = _activity(work, fps, frames)
    names = [name for name in activity]
    families = {player.id.split(".")[0]: player.family for player in work.orchestra.players}
    shorts = {player.id.split(".")[0]: player.short for player in work.orchestra.players}

    title_font = _font(True, int((30 if mobile else 26) * scale))
    info_font = _font(False, int((28 if mobile else 24) * scale))
    label_font = _font(False, int((21 if mobile else 17) * scale))

    # The ribbon: one label for each instrument, in the sequence of the score.
    label_boxes: dict[str, tuple[int, int, int, int]] = {}
    ribbon_top = height - bottom_band + int(14 * scale)
    row_height = int((56 if mobile else 46) * scale)
    rows = 4 if mobile else 2
    per_row = -(-len(names) // rows)
    gap = int(6 * scale)
    box_width = (width - int(40 * scale) - gap * (per_row - 1)) // per_row
    for number, name in enumerate(names):
        row, column = divmod(number, per_row)
        x = int(20 * scale) + column * (box_width + gap)
        y = ribbon_top + row * (row_height + gap)
        label_boxes[name] = (x, y, x + box_width, y + row_height - gap)

    @lru_cache(maxsize=8)
    def screen(index: int) -> _Screen:
        margins = MOBILE_MARGINS if mobile else MARGINS
        return _prepare(pages[index], width, height, scale, top_band, bottom_band, margins)

    band_top = top_band
    band_bottom = height - bottom_band

    @lru_cache(maxsize=64)
    def chrome(
        bar: int, mark: str, tempo: str, second: int, lit: tuple[bool, ...]
    ) -> tuple[np.ndarray, np.ndarray]:
        """Return the pictures of the top band and of the ribbon."""
        layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        baseline = int((14 if mobile else 18) * scale)
        draw.text((int(24 * scale), baseline), work.title, font=title_font, fill=INK)
        centre = f"{tempo}     bar {bar}" + (f"     [{mark}]" if mark else "")
        box = draw.textbbox((0, 0), centre, font=info_font)
        # On a telephone, the tempo and the bar number are on a second line.
        second_line = int(66 * scale) if mobile else baseline
        draw.text(((width - box[2]) // 2, second_line), centre, font=info_font, fill=INK)
        clock = f"{second // 60}:{second % 60:02d} / {int(duration) // 60}:{int(duration) % 60:02d}"
        box = draw.textbbox((0, 0), clock, font=info_font)
        draw.text((width - box[2] - int(24 * scale), baseline), clock, font=info_font, fill=INK)
        draw.line([(0, top_band - 1), (width, top_band - 1)], fill=(*INK, 60), width=1)
        for name, is_lit in zip(names, lit, strict=True):
            x0, y0, x1, y1 = label_boxes[name]
            colour = FAMILY_COLOURS[families[name]]
            if is_lit:
                draw.rounded_rectangle((x0, y0, x1, y1), int(6 * scale), fill=(*colour, 255))
                text_colour = (255, 255, 255, 255)
            else:
                draw.rounded_rectangle(
                    (x0, y0, x1, y1), int(6 * scale), outline=(*colour, 110), width=1
                )
                text_colour = (*INK, 120)
            box = draw.textbbox((0, 0), shorts[name], font=label_font)
            draw.text(
                (x0 + (x1 - x0 - box[2]) // 2, y0 + (y1 - y0 - box[3]) // 2 - int(2 * scale)),
                shorts[name], font=label_font, fill=text_colour,
            )  # fmt: skip
        pixels = np.asarray(layer, dtype=np.float32)
        alpha = pixels[:, :, 3:4] / 255.0
        solid = (PAPER * (1.0 - alpha) + pixels[:, :, :3] * alpha).astype(np.uint8)
        return solid[:band_top].copy(), solid[band_bottom:].copy()

    marks = sorted(structure.marks.items())
    tempos = [point for point in structure.tempo_points if point.text]
    starts = np.array([page.start for page in pages])

    output.parent.mkdir(parents=True, exist_ok=True)

    @lru_cache(maxsize=24)
    def tinted(index: int, sounding: tuple[str, ...]) -> np.ndarray:
        """Return the screen with a colour band on each staff that sounds."""
        current = screen(index)
        picture = current.base.copy()
        pad = int(7 * scale)
        for name in sounding:
            top, bottom = current.staves[name]
            colour = np.array(FAMILY_COLOURS[families[name]], dtype=np.float32)
            band = picture[top - pad : bottom + pad, current.left : current.right]
            band += 0.13 * (colour - band)
            marker = picture[
                top - pad : bottom + pad,
                current.left - int(16 * scale) : current.left - int(7 * scale),
            ]
            marker += 0.9 * (colour - marker)
        return np.clip(picture, 0, 255).astype(np.uint8)

    def draw(first: int, last: int, path: Path) -> None:
        """Draw the frames `first` to `last` (not included) and encode them (no sound)."""
        encoder = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps),
             "-i", "-", "-c:v", "libopenh264", "-b:v", "6M", "-pix_fmt", "yuv420p", str(path)],
            stdin=subprocess.PIPE,
        )  # fmt: skip
        assert encoder.stdin is not None
        for number in range(first, last):
            encoder.stdin.write(frame_of(number).tobytes())
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError("the video encoder failed")

    def frame_of(number: int) -> np.ndarray:
        position = float(positions[number])
        index = max(0, int(np.searchsorted(starts, position, side="right")) - 1)
        current = screen(index)
        sounding = tuple(name for name in current.staves if activity[name][number])
        frame = tinted(index, sounding).copy()

        # The cursor.
        x = int(np.interp(position, current.times, current.xs)) + int(6 * scale)
        top, bottom = current.top - int(16 * scale), current.bottom + int(16 * scale)
        left, right = x - int(7 * scale), x + int(8 * scale)
        strip = frame[top:bottom, left:right].astype(np.float32)
        strip += 0.14 * (CURSOR - strip)
        centre = slice(x - 1 - left, x + max(2, int(2 * scale)) - left)
        strip[:, centre] += 0.85 * (CURSOR - strip[:, centre])
        frame[top:bottom, left:right] = strip.astype(np.uint8)

        # The top band, the ribbon, and the progress line.
        bar = structure.bar_at(Fraction(position).limit_denominator(64)).number
        mark = next((label for start, label in reversed(marks) if start <= bar), "")
        tempo = next(
            (point.text for point in reversed(tempos) if float(point.position) <= position), ""
        )
        lit = tuple(bool(activity[name][number]) for name in names)
        upper, lower = chrome(bar, mark, tempo, number // fps, lit)
        frame[:band_top] = upper
        frame[band_bottom:] = lower
        done = int(width * number / max(frames - 1, 1))
        frame[height - int(5 * scale) :, :done] = CURSOR.astype(np.uint8)
        return frame

    # Each process draws one part of the video. Then the parts are joined, with the sound.
    workers = max(1, min(os.cpu_count() or 1, MAX_WORKERS, frames // (fps * 20) + 1))
    edges = [frames * number // workers for number in range(workers + 1)]
    parts = [output.with_name(f"{output.stem}-part{number:02d}.mp4") for number in range(workers)]
    jobs = list(zip(edges[:-1], edges[1:], parts, strict=True))
    _JOB["draw"] = draw
    try:
        if workers == 1:
            draw(*jobs[0])
        else:
            # The worker processes are copies of this process: they have the job data.
            with multiprocessing.get_context("fork").Pool(workers) as pool:
                pool.map(_draw_part, jobs, chunksize=1)
    finally:
        _JOB.clear()
    listing = output.with_name(f"{output.stem}-parts.txt")
    listing.write_text("".join(f"file '{part.name}'\n" for part in parts), encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", listing.name,
         "-i", str(audio.resolve()), "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest",
         "-movflags", "+faststart", output.name],
        cwd=output.parent,
        check=True,
    )  # fmt: skip
    for path in [*parts, listing]:
        path.unlink()
    return output
