"""The loop editor: the waveform over the whole window to zoom and set the loop exactly
(docs/loop-editor.md). Drawing and gestures run in the page (loop_editor.js); it sends le_loop /
le_seek / le_undo here and gets the loop and the play position back."""

import base64
import json
from pathlib import Path
from typing import Any

from common import clock_tenths, event_arg, parse_clock, tip
from controls import recording_chips
from engine import DETAIL_FRAMES
from nicegui import events, run, ui
from player import Player

LOOP_EDITOR_JS = (Path(__file__).parent / "loop_editor.js").read_text(encoding="utf-8")
CSS = ".le-header { border-bottom: 1px solid rgba(128, 128, 128, 0.25); }"


class LoopEditor:
    def __init__(self, player: Player) -> None:
        self.player, self.engine = player, player.engine
        self.is_open = False
        self.undo_base: Any = None  # (loop, looping) the undo starts from
        self.history: list[Any] = []  # earlier (loop, looping), newest last
        self.last_play: Any = None  # the play position last sent to the page
        self.last_playing: bool | None = None
        ui.add_body_html(f"<script>{LOOP_EDITOR_JS}</script>")
        ui.add_css(CSS)
        self.build()
        player.on(
            "selection", lambda new_song: recording_chips(self.recordings, player)
        )
        player.on("audio", self.on_audio)
        player.on("tempo", self.show_tempo)
        player.on("loop", self.on_loop)
        player.on("tick", self.on_tick)
        ui.on("le_loop", self.page_loop)
        ui.on("le_seek", lambda e: player.seek(float(event_arg(e))))
        ui.on("le_undo", self.undo)

    def build(self) -> None:
        player = self.player
        with (
            ui.dialog().props(
                "maximized persistent transition-show=none transition-hide=none"
            ) as self.dialog,
            ui.card().classes("w-full h-full p-0 gap-0 no-wrap"),
        ):
            with ui.row().classes(
                "le-header w-full items-center gap-2 px-4 py-1 min-h-[52px] no-wrap"
            ):
                ui.label("Loop").classes("text-subtitle1 font-bold text-primary")
                self.title = ui.label("").classes("text-h6 truncate")
                self.recordings = ui.element("div").classes(
                    "min-w-0"
                )  # recording_chips()
                ui.space()
                self.undo_button = ui.button(
                    "Undo", icon="undo", on_click=self.undo
                ).props("flat no-caps")
                tip(self.undo_button, "Back to the previous loop (Ctrl+Z)")
                done_button = ui.button("Done", on_click=self.close).props(
                    "unelevated no-caps"
                )
                tip(done_button, "Back to the player (E, Esc)")
            with ui.row().classes("w-full items-center gap-2 px-4 py-2 no-wrap"):
                ui.button(
                    icon="zoom_out",
                    on_click=lambda: ui.run_javascript("le.zoomBy(0.5)"),
                ).props("flat round dense").tooltip("Zoom out (−)")
                ui.label("1×").classes("le-zoom font-mono w-12 text-center")
                ui.button(
                    icon="zoom_in", on_click=lambda: ui.run_javascript("le.zoomBy(2)")
                ).props("flat round dense").tooltip("Zoom in (+), also pinch")
                ui.button(
                    "Whole song", on_click=lambda: ui.run_javascript("le.wholeSong()")
                ).props("outline no-caps dense").classes("px-2")
                ui.button(
                    "Zoom to loop",
                    on_click=lambda: ui.run_javascript("le.zoomToLoop()"),
                ).props("outline no-caps dense").classes("px-2")
                ui.separator().props("vertical").classes("mx-2")
                self.play_button = ui.button(
                    icon="play_arrow", on_click=player.toggle_play
                ).props("round unelevated dense")
                self.play_tip = tip(self.play_button, "Play (Space)")
                hear_button = (
                    ui.button("Hear end", icon="skip_next", on_click=self.hear_end)
                    .props("outline no-caps dense")
                    .classes("px-2")
                )
                tip(
                    hear_button,
                    "The last 2 s of the loop and the jump back to its start (Shift+Space)",
                )
                ui.space()
                ui.label("Tempo").classes("text-caption text-grey")
                ui.button(icon="remove", on_click=lambda: player.tempo_step(-1)).props(
                    "flat round dense"
                ).tooltip("Slower (←)")
                self.speed = ui.label("100 %").classes("font-bold w-12 text-center")
                ui.button(icon="add", on_click=lambda: player.tempo_step(1)).props(
                    "flat round dense"
                ).tooltip("Faster (→)")
            with ui.column().classes("w-full grow min-h-0 gap-1 px-4 no-wrap"):
                ui.element("canvas").classes("le-overview w-full h-12 block").style(
                    "touch-action: none; cursor: grab"
                ).tooltip("The whole song: drag the box to scroll")
                ui.element("canvas").classes("le-ruler w-full h-6 block").style(
                    "touch-action: none; cursor: pointer"
                ).tooltip("Click: play from here · drag down / up: zoom in / out")
                with ui.element("div").classes("w-full grow min-h-0 relative"):
                    ui.element("canvas").classes(
                        "le-main absolute inset-0 w-full h-full block"
                    ).style("touch-action: none; cursor: crosshair")
            with ui.row().classes("w-full items-center gap-1 px-4 py-1 no-wrap"):
                self.edge_fields = []
                for edge, name in ((0, "Start"), (1, "End")):
                    if edge == 1:
                        ui.space()
                    ui.label(name).classes("text-caption text-grey")
                    ui.button(
                        icon="chevron_left",
                        on_click=lambda edge=edge: player.nudge(edge, -0.1),
                    ).props("flat dense round size=sm").tooltip("0.1 s earlier")
                    time_input = (
                        ui.input()
                        .props("dense outlined input-class=text-center")
                        .classes("w-24 font-mono")
                    )
                    time_input.on(
                        "keydown.enter",
                        lambda e, edge=edge: self.type_edge(edge, e.sender.value),
                    )
                    time_input.on(
                        "blur",
                        lambda e, edge=edge: self.type_edge(edge, e.sender.value),
                    )
                    self.edge_fields.append(time_input)
                    ui.button(
                        icon="chevron_right",
                        on_click=lambda edge=edge: player.nudge(edge, 0.1),
                    ).props("flat dense round size=sm").tooltip("0.1 s later")
            ui.label("").classes("le-hint text-caption text-grey px-4 pb-2")

    # ------------------------------------------------------------ open and close

    async def open(self) -> None:
        if self.is_open:
            return
        if not self.player.audio:
            ui.notify("No recording loaded")
            return
        self.is_open = True
        self.dialog.open()
        await self.show()

    async def show(self) -> None:
        """Peaks to the page and the editor drawn at this recording's last view."""
        player, engine = self.player, self.engine
        audio, data = player.audio, await run.io_bound(engine.detail_peaks)
        if not self.is_open or player.audio != audio:
            return
        b64 = base64.b64encode(data).decode("ascii")
        ui.run_javascript(
            f"le.load('{b64}', {DETAIL_FRAMES / engine.rate}, {engine.duration})"
        )
        loop = json.dumps(list(player.loop) if player.loop else None)
        view = json.dumps(player.recording_state.get("editor_view"))
        ui.run_javascript(f"le.show({view}, {loop}, {json.dumps(player.looping)})")
        self.title.text = player.song["title"]
        self.history.clear()
        self.undo_base = (player.loop, player.looping)
        self.last_play = None  # the tick sends the play position again
        self.show_loop()

    async def close(self) -> None:
        if not self.is_open:
            return
        self.is_open = False
        self.dialog.close()
        try:
            view = await ui.run_javascript("le.hide()")
        except TimeoutError:
            return
        if view and self.player.audio:
            self.player.recording_state["editor_view"] = view
            self.player.dirty = True

    async def on_audio(self) -> None:
        player = self.player
        if not player.selection.audio:
            await self.close()
        elif player.audio and self.is_open:
            await self.show()

    # ------------------------------------------------------------ the loop

    def on_loop(self) -> None:
        player = self.player
        if self.is_open and (player.loop, player.looping) != self.undo_base:
            self.history.append(self.undo_base)
            self.undo_base = (player.loop, player.looping)
        self.show_loop()

    def show_loop(self) -> None:
        if not self.is_open:
            return
        player = self.player
        loop, on = player.loop, bool(player.loop and player.looping)
        self.edge_fields[0].value = clock_tenths(loop[0]) if loop else ""
        self.edge_fields[1].value = clock_tenths(loop[1]) if loop else ""
        self.undo_button.set_enabled(bool(self.history))
        ui.run_javascript(
            f"le.setLoop({json.dumps(list(loop) if loop else None)}, {json.dumps(on)})"
        )

    def page_loop(self, e: events.GenericEventArguments) -> None:
        player = self.player
        if not player.audio:
            return
        selection = event_arg(e)
        before = player.loop
        player.set_loop(float(selection["a"]), float(selection["b"]))
        if player.loop == before:
            self.show_loop()  # too short: the page shows the loop that stays
        elif not selection.get("edge"):
            player.seek(player.loop[0])  # a new loop plays from its start

    def undo(self, _: Any = None) -> None:
        if not self.history:
            ui.notify("Nothing to undo", timeout=1000)
            return
        player = self.player
        player.loop, player.looping = self.undo_base = self.history.pop()
        player.apply_loop()

    def hear_end(self) -> None:
        """The last 2 s of the loop and the jump back to its start: the seam that needs fixing."""
        player = self.player
        if not (player.audio and player.loop):
            ui.notify("Set a loop first: drag over the waveform")
            return
        if not player.looping:
            player.looping = True
            player.apply_loop()
        player.seek(max(player.loop[0], player.loop[1] - 2))
        self.engine.play()

    def type_edge(self, edge: int, text: str) -> None:
        player = self.player
        shown = clock_tenths(player.loop[edge]) if player.loop else ""
        if text.strip() in (
            "",
            shown,
        ):  # unchanged: keep the exact time, not the rounded one
            return
        seconds = parse_clock(text)
        if seconds is None or not player.audio:
            ui.notify("Type a time like 1:11.2", type="warning")
            self.show_loop()
            return
        loop = list(player.loop) if player.loop else [0.0, self.engine.duration]
        loop[edge] = seconds
        player.set_loop(*loop)
        self.show_loop()
        ui.run_javascript("document.activeElement.blur()")

    # ------------------------------------------------------------ tempo and play position

    def show_tempo(self) -> None:
        self.speed.text = f"{round(self.engine.speed * 100)} %"

    def on_tick(self) -> None:
        player, engine = self.player, self.engine
        if not player.audio:
            return
        if self.is_open:  # the page moves the playhead between these updates
            now = (round(player.now, 3), engine.playing)
            if engine.playing or now != self.last_play:
                self.last_play = now
                ui.run_javascript(
                    f"le.setPlay({now[0]}, {json.dumps(now[1])}, {engine.speed})"
                )
        if engine.playing != self.last_playing:
            self.last_playing = engine.playing
            self.play_button.props(
                f"icon={'pause' if engine.playing else 'play_arrow'}"
            )
            self.play_tip.text = "Pause (Space)" if engine.playing else "Play (Space)"
