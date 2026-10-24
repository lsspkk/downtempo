"""The controls pane: one surface with thin dividers (docs/tempo-goal.md#python-player-full-controls-t231):
the recording dropdown, the waveform and transport, the tempo row, and in Full controls the tabs
Pitch · Trainer · Loop · BPM (one module each). Also the short form in the header (mini_bar.py),
the loading card and "No recording" for sheet-only songs."""

import time
from collections.abc import Awaitable, Callable
from pathlib import Path

from bpm_tab import BpmTab
from common import clock, tip
from layout import Shell
from loop_tab import LoopTab
from mini_bar import MiniBar
from nicegui import ui
from pitch_tab import PitchTab
from player import Player
from recordings import RecordingPicker
from tempo_goal import TempoGoal
from tempo_row import TempoRow
from trainer_tab import TrainerTab
from waveform import Waveform

TABS = {"pitch": "Pitch", "trainer": "Trainer", "loop": "Loop", "bpm": "BPM"}
# The tabs are folder tabs on a slot that fills the pane's height: the open tab joins the slot.
CSS = """
:root { --slot-bg: #f4f5f8; --slot-line: #d4d6dc; }
.body--dark { --slot-bg: #202024; --slot-line: #3c3c42; }
.controls-surface { border: 1px solid rgba(128, 128, 128, 0.25); border-radius: 8px; }
.controls-surface > .q-separator { margin: 0 -8px; width: calc(100% + 16px); }
.controls-tabs { border-bottom: 1px solid var(--slot-line); overflow: visible; }
.controls-tabs .q-tabs__content { overflow: visible; gap: 2px; padding-left: 8px; }
.controls-tabs .q-tab {
  min-height: 34px; padding: 0 16px; margin-bottom: -1px; opacity: 0.75;
  border: 1px solid transparent; border-bottom: none; border-radius: 8px 8px 0 0;
}
.controls-tabs .q-tab:hover { background: var(--slot-bg); opacity: 1; }
.controls-tabs .q-tab--active {
  background: var(--slot-bg); border-color: var(--slot-line); opacity: 1;
  box-shadow: 0 1px 0 var(--slot-bg); font-weight: 600;
}
.controls-tabs .q-tab__label { font-size: 14px; }
.controls-slot {
  background: var(--slot-bg); border: 1px solid var(--slot-line); border-top: none;
  border-radius: 0 0 8px 8px; min-height: 160px;
}
"""


class Controls:
    def __init__(
        self,
        shell: Shell,
        player: Player,
        open_editor: Callable[[], Awaitable[None]],
        goal: TempoGoal,
    ) -> None:
        self.player, self.engine, self.shell = player, player.engine, shell
        self.playing: bool | None = None
        self.loading_since = 0.0
        ui.add_css(CSS)
        MiniBar(shell.mini_bar, player, open_editor)
        with shell.pane:
            self.build(open_editor, goal)
        player.on("audio", self.on_audio)
        player.on("tempo", self.show_length)
        player.on("loop", self.show_loop)
        player.on("tick", self.on_tick)

    def build(
        self, open_editor: Callable[[], Awaitable[None]], goal: TempoGoal
    ) -> None:
        player = self.player
        RecordingPicker(player)

        # While a recording loads: in the place of the waveform and the player.
        with ui.column().classes(
            "controls-surface w-full p-6 items-center gap-2"
        ) as self.loading:
            ui.spinner(size="lg")
            ui.label("Loading the recording…").classes("text-subtitle1")
            self.loading_name = ui.label("").classes("text-caption text-grey")
            self.loading_time = ui.label("").classes("text-caption text-grey")
        self.loading.set_visibility(False)

        # A song with only sheets: the pane narrows to this, the sheet gets the room (layout.py).
        with ui.column().classes("w-full gap-1 pt-2") as self.no_audio:
            self.no_audio_title = ui.label("").classes("text-h6 leading-tight")
            with ui.row().classes("items-center gap-1 text-grey no-wrap"):
                ui.icon("volume_off", size="20px")
                ui.label("No recording")
            ui.label("This song has only sheet music.").classes(
                "text-caption text-grey"
            )
        self.no_audio.set_visibility(False)

        with ui.column().classes("w-full grow gap-6 no-wrap") as self.player_box:
            self.build_player(open_editor, goal)
            self.build_tabs(open_editor, goal)

    def build_player(
        self, open_editor: Callable[[], Awaitable[None]], goal: TempoGoal
    ) -> None:
        player, shell = self.player, self.shell
        with ui.column().classes("controls-surface w-full p-2 gap-2"):
            Waveform(player)
            with ui.row().classes("w-full items-center gap-1 no-wrap"):
                self.time = ui.label("0:00 / 0:00").classes(
                    "font-mono text-caption whitespace-nowrap"
                )
                self.length_tip = tip(self.time, "")
                ui.space()
                ui.button(icon="skip_previous", on_click=player.to_start).props(
                    "flat round dense"
                ).tooltip("To start (0)")
                shell.full_only.append(
                    ui.button(icon="replay_5", on_click=lambda: player.skip(-5))
                    .props("flat round dense")
                    .tooltip("Back 5 s ( , )")
                )
                self.play = ui.button(
                    icon="play_arrow", on_click=player.toggle_play
                ).props("round unelevated")
                self.play_tip = tip(self.play, "Play (Space)")
                shell.full_only.append(
                    ui.button(icon="forward_5", on_click=lambda: player.skip(5))
                    .props("flat round dense")
                    .tooltip("Forward 5 s ( . )")
                )
                self.loop = ui.button(icon="repeat", on_click=player.toggle_loop).props(
                    "flat round dense color=grey"
                )
                self.loop_tip = tip(self.loop, "Loop on (R)")
                # Simple has no Loop tab: the editor sits next to the loop button
                shell.simple_only.append(
                    ui.button(icon="open_in_full", on_click=open_editor)
                    .props("flat round dense")
                    .tooltip("Loop editor: zoom in, set the loop exactly (E)")
                )
                ui.space()
            ui.separator()
            TempoRow(shell, goal, lambda: self.open_tab("bpm"))

    def build_tabs(
        self, open_editor: Callable[[], Awaitable[None]], goal: TempoGoal
    ) -> None:
        player, shell = self.player, self.shell
        tab = shell.view.get("tab", "loop")
        with ui.column().classes("w-full grow gap-0 no-wrap") as tabbed:
            with (
                ui.tabs(value=tab, on_change=lambda e: shell.set_view(tab=e.value))
                .props("dense no-caps align=left indicator-color=transparent")
                .classes("controls-tabs w-full") as self.tabs
            ):
                for name, label in TABS.items():
                    ui.tab(name, label)
            with (
                ui.tab_panels(self.tabs, value=tab)
                .props("animated=false keep-alive")
                .classes("controls-slot w-full grow") as panels
            ):
                panels.props("transition-prev=none transition-next=none")
                with ui.tab_panel("pitch").classes("p-4 gap-1"):
                    PitchTab(player)
                with ui.tab_panel("trainer").classes("p-4 gap-1"):
                    TrainerTab(player)
                with ui.tab_panel("loop").classes("p-4 gap-1"):
                    LoopTab(player, open_editor)
                with ui.tab_panel("bpm").classes("p-4 gap-1"):
                    BpmTab(goal)
        shell.full_only.append(tabbed)

    # ------------------------------------------------------------ actions

    def open_tab(self, name: str) -> None:
        """The Play at switch without an optimal tempo opens the BPM tab (from Simple too)."""
        if self.shell.view["controls"] != "full":
            self.shell.set_controls("full")
        self.tabs.value = name

    # ------------------------------------------------------------ showing the Player's state

    def on_audio(self) -> None:
        player = self.player
        self.loading.set_visibility(player.loading)
        if player.loading:
            self.loading_since = time.monotonic()
            self.loading_name.text = Path(player.selection.audio).name
            self.loading_time.text = ""
        has_audio = bool(player.selection.audio)
        self.player_box.set_visibility(
            has_audio and not player.failed and not player.loading
        )
        self.no_audio.set_visibility(not has_audio)
        self.no_audio_title.text = player.song["title"]
        self.shell.set_audio_less(not has_audio)

    def show_length(self) -> None:
        engine = self.engine
        if self.player.audio:
            self.length_tip.text = (
                f"The song takes {clock(engine.duration / engine.speed)} at this tempo"
            )

    def show_loop(self) -> None:
        on = bool(self.player.loop and self.player.looping)
        self.loop.props(f"color={'accent' if on else 'grey'}")
        self.loop_tip.text = "Loop off (R)" if on else "Loop on (R)"

    def on_tick(self) -> None:
        player, engine = self.player, self.engine
        if player.loading:
            seconds = int(time.monotonic() - self.loading_since)
            self.loading_time.text = f"{seconds} s" if seconds >= 2 else ""
        if not player.audio:
            return
        now = f"{clock(player.now)} / {clock(engine.duration)}"
        if now != self.time.text:
            self.time.text = now
        if engine.playing != self.playing:
            self.playing = engine.playing
            self.play.props(f"icon={'pause' if engine.playing else 'play_arrow'}")
            self.play_tip.text = "Pause (Space)" if engine.playing else "Play (Space)"
