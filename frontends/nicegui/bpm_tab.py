"""The BPM tab of Full controls: the recording tempo and the song's optimal tempo (−/+, typed), and
the speed the optimal tempo needs (docs/tempo-goal.md#python-player-full-controls-t231)."""

from collections.abc import Callable

from common import tip
from nicegui import ui
from tempo_goal import TempoGoal


def bpm_stepper(
    on_change: Callable[[float | None], None], current: Callable[[], float | None]
) -> ui.number:
    """−, a BPM field, +: 1 BPM steps from the current value; a typed value counts on Enter or
    when leaving the field, so code may set the field's .value freely."""
    ui.button(icon="remove", on_click=lambda: on_change((current() or 1) - 1)).props(
        "flat round dense size=sm"
    )
    field = ui.number(min=20, max=400, step=1, format="%.0f").props(
        "dense outlined hide-bottom-space input-class=text-center"
    )
    field.classes("w-16")

    def typed() -> None:
        now = current()
        if field.value != (round(now) if now else None):  # unchanged is no change
            on_change(field.value)

    field.on("keydown.enter", typed)
    field.on("blur", typed)
    ui.button(icon="add", on_click=lambda: on_change((current() or 99) + 1)).props(
        "flat round dense size=sm"
    )
    return field


class BpmTab:
    def __init__(self, goal: TempoGoal) -> None:
        self.goal = goal
        with ui.grid(columns="auto auto 1fr").classes(
            "w-full items-center gap-x-3 gap-y-3"
        ):
            ui.label("Recording tempo").classes("whitespace-nowrap")
            with ui.row().classes("items-center gap-0 no-wrap"):
                self.bpm = bpm_stepper(goal.set_bpm, lambda: goal.bpm)
                ui.label("BPM").classes("text-caption text-grey ml-1")
            self.state = ui.label("").classes("text-caption text-grey")
            ui.label("Optimal tempo").classes("whitespace-nowrap")
            with ui.row().classes("items-center gap-0 no-wrap"):
                # the first − / + of an empty optimal tempo starts from the recording tempo
                self.optimal = bpm_stepper(
                    goal.set_optimal,
                    lambda: goal.optimal or (round(goal.bpm) if goal.bpm else None),
                )
                ui.label("BPM").classes("text-caption text-grey ml-1")
            ui.element("div")
            ui.element("div")
            self.needs = ui.label("").classes("col-span-2 text-caption text-grey -mt-2")
            tip(self.needs, "Empty: no optimal tempo. X or the Play at switch plays it")
        goal.player.on("bpm", self.show)
        self.show()

    def show(self) -> None:
        goal = self.goal
        bpm = goal.bpm
        if self.bpm.value != (round(bpm) if bpm else None):
            self.bpm.value = round(bpm) if bpm else None
        self.state.text = "" if bpm else goal.state_text()
        optimal = goal.optimal
        if self.optimal.value != (round(optimal) if optimal else None):
            self.optimal.value = round(optimal) if optimal else None
        self.needs.text = (
            f"→ {optimal / bpm * 100:.0f} % of this recording"
            if optimal and bpm
            else ""
        )
