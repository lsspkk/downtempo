"""The Trainer tab of Full controls: the step-up trainer raises the tempo every few loop repeats,
up to a target (the Player runs it; this shows its settings and status)."""

from common import BLUR_SELECT
from nicegui import ui
from player import TRAINER, Player


class TrainerTab:
    def __init__(self, player: Player) -> None:
        self.player = player
        self.switch = ui.switch(
            "Raise the tempo while looping",
            on_change=lambda e: (
                player.toggle_trainer(e.value)
                if e.value != player.trainer["on"]
                else None
            ),
        ).props("dense")
        self.inputs: dict[str, ui.select] = {}
        with ui.row().classes("items-center gap-2 no-wrap"):
            for key, options, after in (
                ("step", {0.05: "+5 %", 0.1: "+10 %"}, "every"),
                ("every", {n: str(n) for n in range(1, 6)}, "repeats, up to"),
                (
                    "target",
                    {round(v / 100, 2): f"{v} %" for v in range(60, 135, 5)},
                    "",
                ),
            ):
                self.inputs[key] = (
                    ui.select(
                        options,
                        value=TRAINER[key],
                        on_change=lambda e, key=key: player.set_trainer(key, e.value),
                    )
                    .props("dense outlined options-dense")
                    .on("popup-hide", js_handler=BLUR_SELECT)
                )
                if after:
                    ui.label(after)
        self.status = ui.label("").classes("text-caption text-grey")
        player.on("trainer", self.show)
        player.on("loop", self.show_status)
        player.on("tick", self.on_tick)
        self.show()

    def show(self) -> None:
        """Its inputs show the Player's values (set_trainer ignores unchanged ones), and the status."""
        for key, widget in self.inputs.items():
            widget.value = self.player.trainer[key]
        self.switch.value = self.player.trainer["on"]
        self.show_status()

    def on_tick(self) -> None:
        if self.player.audio and self.player.trainer["on"]:
            self.show_status()

    def show_status(self) -> None:
        player, engine, t = self.player, self.player.engine, self.player.trainer
        if not t["on"]:
            text = "Raise the tempo step by step while the loop repeats."
        elif not (player.loop and player.looping):
            text = "Set a loop to start."
        elif engine.speed >= t["target"] - 1e-6:
            text = f"Target {round(t['target'] * 100)} % reached."
        else:
            text = (
                f"Repeat {engine.repeats + 1} of {t['every']} at {round(engine.speed * 100)} %, "
                f"then {round(min(engine.speed + t['step'], t['target']) * 100)} %"
            )
        if self.status.text != text:
            self.status.text = text
