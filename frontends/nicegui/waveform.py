"""The waveform of the loaded recording: played part, playhead and loop drawn over it; click to
play from there, drag to set a loop (dragged out the side: to the song's start or end). The
controls pane has one; a song without sheets shows a large one in the sheet's place
(sheet_pane.py). Each draws itself from the Player's events."""

from common import LOOP_COLOR
from nicegui import events, ui
from player import Player

WAVE_W = 1000  # drawing units across; the height is per waveform
EDGE = 0.02  # a drag leaving this close to a side ends at the song's start or end


def wave_svg(peaks, height: int = 200) -> str:
    """The waveform as an SVG data URL: mirrored bars, one per peak bin."""
    mid = height / 2
    bars = " ".join(
        f"M{x} {mid - p * mid * 0.95:.1f}V{mid + p * mid * 0.95:.1f}"
        for x, p in enumerate(peaks)
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WAVE_W}" height="{height}" '
        f'viewBox="0 0 {WAVE_W} {height}"><path d="{bars}" '
        'stroke="%238a94b0" stroke-width="1"/></svg>'
    )
    return "data:image/svg+xml;utf8," + svg.replace("#", "%23").replace('"', "'")


class Waveform:
    def __init__(self, player: Player, height: int = 200, classes: str = "") -> None:
        self.player, self.engine, self.height = player, player.engine, height
        self.drag_from: float | None = None
        self.drag_to: float | None = None
        self.overlay = ""
        self.active = True  # off while hidden: no redraw every tick
        self.blank = wave_svg([0] * WAVE_W, height)
        self.image = ui.interactive_image(
            self.blank,
            events=["mousedown", "mousemove", "mouseup", "mouseleave"],
            on_mouse=self.on_mouse,
        ).classes("w-full cursor-pointer rounded " + classes)
        self.image.tooltip("Click: play from here · Drag: set a loop")
        player.on("audio", self.on_audio)
        player.on("tick", self.on_tick)
        player.on("loop", self.on_tick)

    def on_audio(self) -> None:
        if self.player.audio:
            self.image.set_source(wave_svg(self.engine.peaks, self.height))
        else:
            self.image.set_source(self.blank)
            self.image.content = self.overlay = ""

    def on_tick(self) -> None:
        if not self.player.audio or not self.active:
            return
        overlay = self.draw()
        if overlay != self.overlay:
            self.image.content = self.overlay = overlay

    def draw(self) -> str:
        player, engine, h = self.player, self.engine, self.height
        if not engine.duration:
            return ""
        x = lambda seconds: seconds / engine.duration * WAVE_W
        parts = [
            (
                f'<rect x="0" y="0" width="{x(player.now):.1f}" '
                f'height="{h}" fill="#4f5bd5" fill-opacity="0.18"/>'
            )
        ]
        region = (
            sorted((self.drag_from, self.drag_to))
            if self.drag_from is not None and self.drag_to is not None
            else player.loop
        )
        if region:
            a, b = x(region[0]), x(region[1])
            opacity = 0.3 if player.looping or self.drag_to is not None else 0.12
            parts.append(
                f'<rect x="{a:.1f}" y="0" width="{b - a:.1f}" height="{h}" '
                f'fill="{LOOP_COLOR}" fill-opacity="{opacity}"/>'
                f'<line x1="{a:.1f}" x2="{a:.1f}" y1="0" y2="{h}" stroke="{LOOP_COLOR}" stroke-width="2"/>'
                f'<line x1="{b:.1f}" x2="{b:.1f}" y1="0" y2="{h}" stroke="{LOOP_COLOR}" stroke-width="2"/>'
                f'<text x="{a + 4:.1f}" y="14" font-size="13" font-weight="bold" fill="{LOOP_COLOR}">A</text>'
                f'<text x="{b - 13:.1f}" y="14" font-size="13" font-weight="bold" fill="{LOOP_COLOR}">B</text>'
            )
        head = x(player.now)
        parts.append(
            f'<line x1="{head:.1f}" x2="{head:.1f}" y1="0" y2="{h}" stroke="#4f5bd5" stroke-width="2.5"/>'
        )
        return "".join(parts)

    def on_mouse(self, e: events.MouseEventArguments) -> None:
        player, engine = self.player, self.engine
        if not player.audio:
            return
        seconds = min(max(e.image_x, 0), WAVE_W) / WAVE_W * engine.duration
        match e.type:
            case "mousedown":
                self.drag_from, self.drag_to = seconds, None
            case "mousemove" if self.drag_from is not None and e.buttons & 1:
                if abs(seconds - self.drag_from) / engine.duration * WAVE_W > 4:
                    self.drag_to = seconds
            case "mouseup" if self.drag_from is not None:
                if self.drag_to is None:
                    player.seek(seconds)
                else:
                    player.set_loop(self.drag_from, seconds)
                    if player.loop:
                        player.seek(player.loop[0])
                self.drag_from = self.drag_to = None
            case "mouseleave" if self.drag_from is not None and e.buttons & 1:
                # Dragged out: out the side runs the loop to the song's start or end.
                if e.image_x <= WAVE_W * EDGE:
                    seconds = 0.0
                elif e.image_x >= WAVE_W * (1 - EDGE):
                    seconds = engine.duration
                player.set_loop(self.drag_from, seconds)
                if player.loop:
                    player.seek(player.loop[0])
                self.drag_from = self.drag_to = None
            case "mouseleave":
                self.drag_from = self.drag_to = None
