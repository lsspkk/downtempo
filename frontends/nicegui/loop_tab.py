"""The Loop tab of Full controls: the loop's line (on / off, length, pause, Clear, Loop editor), Start
and End as cards (Set here, nudges), and the saved loops; also the Save loop dialog (S)."""

from collections.abc import Awaitable, Callable

from common import BLUR_SELECT, clock, clock_tenths, tip
from nicegui import ui
from player import Player

CSS = """
.loop-edge { background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); }
"""
GAPS = {0.0: "no pause", 1.0: "1 s pause", 2.0: "2 s pause", 4.0: "4 s pause"}


def save_loop_dialog(player: Player) -> None:
    """Name the loop and keep it with the recording (S)."""
    if not player.audio:
        return
    if not player.loop:
        ui.notify("Set a loop first: press A and B, or drag over the waveform")
        return
    with ui.dialog() as dialog, ui.card().classes("min-w-[320px]"):
        ui.label("Save loop").classes("text-h6")
        ui.label(f"{clock(player.loop[0])} – {clock(player.loop[1])}").classes(
            "text-grey"
        )
        name = ui.input("Name", value=f"Part {len(player.saved_loops) + 1}").props(
            "autofocus"
        )

        def save() -> None:
            player.save_loop(name.value)
            dialog.close()

        name.on("keydown.enter", save)
        with ui.row().classes("w-full justify-end"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Save", on_click=save)
    dialog.open()


class LoopTab:
    """Three parts, top to bottom (docs/loop-editor.md#the-loop-tab-t241): the loop's line (on / off,
    its range and length, the pause between repeats, Clear, Loop editor), Start and End as two cards
    (time, Set here = the play position, nudges), and the saved loops with Save."""

    def __init__(
        self, player: Player, open_editor: Callable[[], Awaitable[None]]
    ) -> None:
        self.player = player
        ui.add_css(CSS)
        with ui.column().classes("w-full gap-4"):
            self.build_head(open_editor)
            with ui.grid(columns=2).classes("w-full gap-3"):
                self.a = self.edge_card(0)
                self.b = self.edge_card(1)
            self.build_saved()
        player.on("loop", self.show)

    def build_head(self, open_editor: Callable[[], Awaitable[None]]) -> None:
        player = self.player
        with ui.row().classes("w-full items-center gap-2 no-wrap"):
            self.switch = ui.switch(
                "Loop",
                on_change=lambda e: (
                    player.toggle_loop()
                    if e.value != bool(player.loop and player.looping)
                    else None
                ),
            ).props("color=accent dense")
            tip(self.switch, "Loop on / off (R)")
            self.range = ui.label("").classes(
                "text-caption text-grey whitespace-nowrap"
            )
            ui.space()
            ui.select(
                GAPS,
                value=player.state.get("loop_gap", 0.0),
                on_change=lambda e: player.set_gap(e.value),
            ).props("dense borderless options-dense").classes("text-caption").on(
                "popup-hide", js_handler=BLUR_SELECT
            ).tooltip("Pause between repeats")
            self.clear = ui.button(icon="close", on_click=player.clear_loop).props(
                "flat round dense size=sm"
            )
            tip(self.clear, "Clear the loop (C)")
            editor = ui.button(
                "Loop editor", icon="open_in_full", on_click=open_editor
            ).props("outline dense no-caps color=accent")
            editor.classes("px-3")
            tip(editor, "Zoom in on the waveform and set the loop exactly (E)")

    def edge_card(self, edge: int) -> ui.label:
        """Start or End: its time, Set here, and nudges « ‹ › » (1 s, 0.1 s)."""
        name, key = ("Start", "A") if edge == 0 else ("End", "B")
        with ui.column().classes("loop-edge rounded-borders p-2 gap-1 items-stretch"):
            with ui.row().classes("w-full items-center no-wrap gap-1"):
                ui.label(name).classes("text-subtitle2")
                ui.space()
                here = ui.button(
                    "Set here",
                    icon="vertical_align_center",
                    on_click=self.player.set_a if edge == 0 else self.player.set_b,
                ).props("flat dense no-caps size=sm color=accent")
                tip(here, f"{name} at the play position ({key})")
            time = ui.label("–").classes("font-mono text-h6 text-center leading-tight")
            with ui.row().classes("w-full justify-center items-center gap-0 no-wrap"):
                self.nudge(edge, -1.0, "keyboard_double_arrow_left")
                self.nudge(edge, -0.1, "chevron_left")
                self.nudge(edge, 0.1, "chevron_right")
                self.nudge(edge, 1.0, "keyboard_double_arrow_right")
        return time

    def build_saved(self) -> None:
        player = self.player
        ui.separator()
        with ui.row().classes("w-full items-center gap-2 no-wrap -mt-1"):
            ui.label("Saved loops").classes("text-subtitle2")
            ui.space()
            self.save = ui.button(
                "Save loop",
                icon="bookmark_add",
                on_click=lambda: save_loop_dialog(player),
            ).props("flat dense no-caps color=accent")
            tip(self.save, "Keep this loop with the recording, under a name (S)")
        self.saved = ui.row().classes("w-full gap-2")

    def nudge(self, edge: int, seconds: float, icon: str) -> None:
        """Moves the loop's start (edge 0) or end (1): ‹ › by 0.1 s, « » by 1 s."""
        step = f"{abs(seconds):g} s {'earlier' if seconds < 0 else 'later'}"
        ui.button(icon=icon, on_click=lambda: self.player.nudge(edge, seconds)).props(
            "flat dense round size=sm"
        ).tooltip(step)

    def show(self) -> None:
        player = self.player
        loop, on = player.loop, bool(player.loop and player.looping)
        self.a.text = clock_tenths(loop[0]) if loop else "–"
        self.b.text = clock_tenths(loop[1]) if loop else "–"
        self.range.text = (
            f"{loop[1] - loop[0]:.1f} s"
            if loop
            else "Set Start and End, or drag over the waveform"
        )
        self.switch.value = on
        self.switch.set_enabled(bool(loop))
        self.clear.set_enabled(bool(loop))
        self.save.set_enabled(bool(loop))
        self.saved.clear()
        with self.saved:
            if not player.saved_loops:
                ui.label("None yet: set a loop, then Save loop").classes(
                    "text-caption text-grey"
                )
            for saved in player.saved_loops:
                ui.chip(
                    f"{saved['name']}  {clock(saved['a'])}–{clock(saved['b'])}",
                    icon="repeat",
                    removable=True,
                    on_click=lambda saved=saved: player.use_saved_loop(saved),
                    on_value_change=lambda e, saved=saved: player.delete_saved_loop(
                        saved
                    ),
                ).props("outline dense color=accent").classes("shrink-0")
