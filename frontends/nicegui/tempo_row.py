"""The tempo row, always in view: `Tempo [−] 85 % [+]  75 BPM (TAP) (metronome)  ○ Play at 100`, and
in Full controls the slider with 50 … 130 under it (docs/tempo-goal.md#python-player-full-controls-t231).
Simple has no TAP and no slider."""

from collections.abc import Callable

from common import tip
from layout import Shell
from nicegui import ui
from player import SPEEDS
from tempo_goal import TempoGoal

TEMPO_MARKS = range(50, 131, 10)  # % under the slider, each where the slider has it
CSS = """
.tempo-mark { position: absolute; transform: translateX(-50%); cursor: pointer; padding: 0 4px;
  border-radius: 4px; font-size: 13px; opacity: 0.65; }
.tempo-mark:hover { opacity: 1; background: rgba(79, 91, 213, 0.10); }
.tempo-mark.on { opacity: 1; color: #4f5bd5; font-weight: 700; }
.body--dark .tempo-mark.on { color: #8f98ff; }
.round-tool { width: 40px; height: 40px; }
.round-tool.q-btn--outline:before { border-color: rgba(128, 128, 128, 0.45); }
.round-tap { font-size: 11px; font-weight: 700; letter-spacing: 0.04em; }
"""
METRONOME_SVG = (
    '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:block">'
    '<path d="M9 3h6l4 18H5z"/><path d="M7 16h10"/><path d="M12 16l4.5-9"/></svg>'
)


class MetronomeButton:
    """Round like TAP: outlined with a metronome; while it ticks (at the BPM now) filled, with ■."""

    def __init__(self, goal: TempoGoal) -> None:
        self.goal = goal
        with ui.button(on_click=goal.toggle_metronome).props(
            "round outline padding=0"
        ) as self.button:
            self.icon = ui.html(METRONOME_SVG, sanitize=False)
            self.stop = ui.icon("stop", size="22px")
        self.button.classes("round-tool")
        self.tip = tip(self.button, "")
        self.on: bool | None = None
        goal.player.on("bpm", self.show)
        self.show()

    def show(self) -> None:
        goal = self.goal
        self.button.set_enabled(bool(goal.now))
        self.tip.text = (
            f"Stop the metronome ({goal.now:.0f} BPM)"
            if goal.metronome
            else f"Metronome at {goal.now:.0f} BPM"
            if goal.now
            else "The metronome needs the recording tempo (BPM tab)"
        )
        if goal.metronome == self.on:
            return
        self.on = goal.metronome
        self.icon.set_visibility(not self.on)
        self.stop.set_visibility(self.on)
        if self.on:
            self.button.props(add="unelevated", remove="outline")
        else:
            self.button.props(add="outline", remove="unelevated")


class TempoRow:
    def __init__(
        self, shell: Shell, goal: TempoGoal, open_bpm_tab: Callable[[], None]
    ) -> None:
        self.shell, self.goal, self.open_bpm_tab = shell, goal, open_bpm_tab
        self.player, self.engine = goal.player, goal.player.engine
        self.tap_shown: float | None = None
        ui.add_css(CSS)
        self.build()
        self.player.on("tempo", self.show_speed)
        self.player.on("bpm", self.show_bpm)
        self.player.on("layout", self.show_bpm)
        self.player.on("tick", self.on_tick)

    def build(self) -> None:
        player, goal, shell = self.player, self.goal, self.shell
        with ui.row().classes("w-full items-center gap-x-2 gap-y-0"):
            with ui.row().classes("items-center gap-1 no-wrap"):
                ui.label("Tempo").classes("text-subtitle2 mr-1")
                ui.button(icon="remove", on_click=lambda: player.tempo_step(-1)).props(
                    "flat round dense"
                ).tooltip("Slower (←)")
                self.speed = ui.label("100 %").classes(
                    "text-h6 font-bold w-16 text-center"
                )
                ui.button(icon="add", on_click=lambda: player.tempo_step(1)).props(
                    "flat round dense"
                ).tooltip("Faster (→)")
            with ui.row().classes("grow items-center gap-2 no-wrap"):
                self.now = ui.label("–").classes("whitespace-nowrap")
                tip(self.now, "What you hear: the recording tempo × the speed")
                self.tap = ui.button("TAP", on_click=goal.tap).props(
                    "round outline no-caps padding=0"
                )
                self.tap.classes("round-tool round-tap")
                self.tap_tip = tip(self.tap, "")
                shell.full_only.append(self.tap)
                MetronomeButton(goal)
                ui.space()
                self.switch = ui.switch(on_change=self.on_switch).props("dense")
                self.switch_tip = tip(self.switch, "")
                self.optimal = ui.label("Play at –").classes(
                    "whitespace-nowrap cursor-pointer"
                )
                self.optimal.on("click", lambda: self.on_switch(None))
        low, high = round(SPEEDS[0] * 100), round(SPEEDS[1] * 100)
        self.slider = ui.slider(
            min=low,
            max=high,
            step=1,
            value=100,
            on_change=lambda e: (
                player.set_speed(e.value / 100)
                if round(self.engine.speed * 100) != e.value
                else None
            ),
        ).props(":markers=5")
        # Absolute, at the slider's own positions: its track has no side padding.
        with ui.element("div").classes("relative w-full h-6 -mt-2") as marks:
            self.marks = {
                mark: ui.label(str(mark))
                .classes("tempo-mark")
                .style(f"left: {(mark - low) / (high - low) * 100}%")
                .on("click", lambda mark=mark: player.set_speed(mark / 100))
                for mark in TEMPO_MARKS
            }
        shell.full_only += [self.slider, marks]

    # ------------------------------------------------------------ actions

    def on_switch(self, e) -> None:
        """The switch shows the truth; a click asks for the other state."""
        goal = self.goal
        if e is not None and e.value == goal.at_optimal:
            return  # set by show()
        if not self.player.audio:
            self.show_bpm()
            return
        if not goal.at_optimal and not goal.optimal_speed:
            self.show_bpm()
            self.open_bpm_tab()
            ui.notify("Set the optimal tempo here (and the recording tempo)")
            return
        goal.toggle_optimal()
        self.show_bpm()

    # ------------------------------------------------------------ showing

    def show_speed(self) -> None:
        percent = round(self.engine.speed * 100)
        self.speed.text = f"{percent} %"
        self.slider.value = percent
        for mark, label in self.marks.items():
            if mark == percent:
                label.classes(add="on")
            else:
                label.classes(remove="on")

    def show_bpm(self) -> None:
        goal = self.goal
        self.now.text = f"{goal.now:.0f} BPM" if goal.now else goal.state_text()
        self.tap_shown = goal.tapped
        self.tap.text = f"{goal.tapped:.0f}" if goal.tapped else "TAP"
        self.tap.set_enabled(bool(goal.bpm))
        self.tap_tip.text = (
            "Tap the beat of another version: from the 4th tap the recording plays that fast (G)"
            if goal.bpm
            else "Tap needs the recording tempo (BPM tab)"
        )
        on = goal.at_optimal
        if self.switch.value != on:
            self.switch.value = on  # its on_change sees the truth and does nothing
        self.switch.props(f"color={'primary' if goal.optimal_speed else 'grey'}")
        self.optimal.text = (
            f"Play at {goal.optimal:.0f}" if goal.optimal else "Play at –"
        )
        self.optimal.classes(
            remove="text-grey" if goal.optimal_speed else "",
            add="" if goal.optimal_speed else "text-grey",
        )
        self.switch_tip.text = (
            f"Every recording of this song plays at {goal.optimal:.0f} BPM (now {goal.optimal_speed * 100:.0f} %) until you change the tempo; off goes back (X)"
            if goal.optimal_speed
            else "Set an optimal tempo in the BPM tab first (X)"
        )

    def on_tick(self) -> None:
        if self.goal.tapped != self.tap_shown:
            self.show_bpm()
