"""The Pitch tab of Full controls: semitones −/+ and Reset, the volume and mute."""

from nicegui import ui
from player import Player


class PitchTab:
    def __init__(self, player: Player) -> None:
        self.player, engine = player, player.engine
        with ui.row().classes("w-full items-center gap-1 no-wrap"):
            ui.label("Pitch").classes("w-16")
            ui.button(
                icon="remove",
                on_click=lambda: player.set_semitones(engine.semitones - 1),
            ).props("flat round dense").tooltip("Down a semitone")
            self.pitch = ui.label("0").classes("font-mono w-8 text-center")
            ui.button(
                icon="add", on_click=lambda: player.set_semitones(engine.semitones + 1)
            ).props("flat round dense").tooltip("Up a semitone")
            ui.label("semitones").classes("text-caption text-grey")
            ui.space()
            ui.button("Reset", on_click=lambda: player.set_semitones(0)).props(
                "flat dense no-caps"
            )
        with ui.row().classes("w-full items-center gap-1 no-wrap"):
            ui.label("Volume").classes("w-16")
            self.mute = (
                ui.button(icon="volume_up", on_click=player.toggle_mute)
                .props("flat round dense")
                .tooltip("Mute (M)")
            )
            ui.slider(
                min=0,
                max=100,
                value=player.state.get("volume", 80),
                on_change=lambda e: player.set_volume(e.value),
            ).classes("grow")
        player.on("tempo", self.show_pitch)
        player.on("sound", self.show_sound)

    def show_pitch(self) -> None:
        semitones = self.player.engine.semitones
        self.pitch.text = f"{semitones:+d}" if semitones else "0"

    def show_sound(self) -> None:
        self.mute.props(f"icon={'volume_off' if self.player.muted else 'volume_up'}")
