"""The controls' short form in the header while the pane is hidden (Sheet): play, time, tempo −/+,
loop, the loop editor and the "♪ 2/3" recordings menu."""

from collections.abc import Awaitable, Callable

from common import clock, tip
from nicegui import ui
from player import Player
from recordings import menu_rows, recording_names


class MiniBar:
    def __init__(
        self, bar: ui.row, player: Player, open_editor: Callable[[], Awaitable[None]]
    ) -> None:
        self.player, self.engine = player, player.engine
        self.playing: bool | None = None
        with bar:
            self.no_audio = ui.label("No recording").classes("text-grey mx-2")
            self.no_audio.set_visibility(False)
            self.audio = ui.row().classes("items-center gap-1 no-wrap")
        with self.audio:
            self.play = ui.button(icon="play_arrow", on_click=player.toggle_play).props(
                "round unelevated dense"
            )
            self.play_tip = tip(self.play, "Play (Space)")
            self.time = ui.label("").classes("font-mono text-caption mx-1")
            ui.button(icon="remove", on_click=lambda: player.tempo_step(-1)).props(
                "flat round dense"
            ).tooltip("Slower (←)")
            self.speed = ui.label("100 %").classes("font-bold w-12 text-center")
            ui.button(icon="add", on_click=lambda: player.tempo_step(1)).props(
                "flat round dense"
            ).tooltip("Faster (→)")
            self.loop = ui.button(icon="repeat", on_click=player.toggle_loop).props(
                "flat round dense color=grey"
            )
            self.loop_tip = tip(self.loop, "Loop on (R)")
            ui.button(icon="open_in_full", on_click=open_editor).props(
                "flat round dense"
            ).tooltip("Loop editor (E)")
            self.recordings = ui.element("div")
        with bar:
            ui.separator().props("vertical").classes("mx-1")
        player.on("selection", lambda new_song: self.show_recordings())
        player.on("audio", self.on_audio)
        player.on("tempo", self.show_speed)
        player.on("loop", self.show_loop)
        player.on("tick", self.on_tick)

    def show_recordings(self) -> None:
        player = self.player
        names = recording_names(player)
        self.recordings.clear()
        self.recordings.set_visibility(len(names) > 1)
        if len(names) < 2:
            return
        current = player.selection.audio
        number = list(names).index(current) + 1 if current in names else 0
        with (
            self.recordings,
            ui.button(f"{number}/{len(names)}", icon="audiotrack").props(
                "flat dense no-caps"
            ),
        ):
            ui.tooltip("Recording (T: next)")
            with ui.menu():
                ui.label("Recording").classes("text-caption text-grey px-4 pt-2")
                menu_rows(player)

    def on_audio(self) -> None:
        has_audio = bool(self.player.selection.audio)
        self.audio.set_visibility(has_audio)
        self.no_audio.set_visibility(not has_audio)

    def show_speed(self) -> None:
        self.speed.text = f"{round(self.engine.speed * 100)} %"

    def show_loop(self) -> None:
        on = bool(self.player.loop and self.player.looping)
        self.loop.props(f"color={'accent' if on else 'grey'}")
        self.loop_tip.text = "Loop off (R)" if on else "Loop on (R)"

    def on_tick(self) -> None:
        player, engine = self.player, self.engine
        if not player.audio:
            return
        now = f"{clock(player.now)} / {clock(engine.duration)}"
        if self.time.text != now:
            self.time.text = now
        if engine.playing != self.playing:
            self.playing = engine.playing
            self.play.props(f"icon={'pause' if engine.playing else 'play_arrow'}")
            self.play_tip.text = "Pause (Space)" if engine.playing else "Play (Space)"
