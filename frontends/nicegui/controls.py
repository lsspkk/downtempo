"""The controls: the left pane (recordings, waveform, transport, tempo, trainer, loop, pitch,
volume) and its short form in the header while the pane is hidden (sheet only)."""

from collections.abc import Awaitable, Callable
from typing import Any

from common import BLUR_SELECT, clock, tip
from layout import Shell
from nicegui import ui
from player import SPEEDS, TRAINER, Player
from waveform import Waveform

TEMPO_MARKS = range(50, 131, 10)  # % under the slider, each where the slider has it
CSS = """
.loop-edge { background: rgba(245, 158, 11, 0.08); }
.tempo-mark { position: absolute; transform: translateX(-50%); cursor: pointer; padding: 0 4px;
  border-radius: 4px; font-size: 13px; opacity: 0.65; }
.tempo-mark:hover { opacity: 1; background: rgba(79, 91, 213, 0.10); }
.tempo-mark.on { opacity: 1; color: #4f5bd5; font-weight: 700; }
.body--dark .tempo-mark.on { color: #8f98ff; }
"""


def recording_name(label: str, title: str) -> str:
    """`<Title> - live 2025` -> `live 2025`; the title is shown elsewhere."""
    return label.replace(title, "").strip(" -_()") or label


def recording_names(player: Player) -> dict[str, str]:
    song = player.song
    return {a["path"]: recording_name(a["label"], song["title"]) for a in song["audio"]}


def recording_chips(box: ui.element, player: Player) -> None:
    """One chip per recording when there are several; clicks only, so no value for code to set
    (docs/player-switching.md, option E). The loop editor shows the same chips."""
    box.clear()
    names = recording_names(player)
    if len(names) < 2:
        return
    current = player.selection.audio
    with box, ui.row().classes("w-full items-center gap-1"):
        ui.icon("audiotrack", size="20px").classes("text-grey")
        for path, name in names.items():
            chip = ui.chip(
                name, on_click=lambda path=path: player.pick_recording(path)
            ).props(
                "dense clickable square color=primary"
                + (" text-color=white" if path == current else " outline")
            )
            tip(chip, "Recording (T: next)")


class Controls:
    def __init__(
        self, shell: Shell, player: Player, open_editor: Callable[[], Awaitable[None]]
    ) -> None:
        self.player, self.engine, self.shell = player, player.engine, shell
        self.last: dict[str, Any] = {"time": "", "playing": None}
        ui.add_css(CSS)
        self.build_mini_bar(shell.mini_bar, open_editor)
        with shell.pane:
            self.build_pane(shell, open_editor)
        player.on("selection", self.on_selection)
        player.on("audio", self.on_audio)
        player.on("tempo", self.show_tempo)
        player.on("sound", self.show_sound)
        player.on("loop", self.show_loop)
        player.on("trainer", self.show_trainer)
        player.on("tick", self.on_tick)
        self.show_trainer()

    # ------------------------------------------------------------ building

    def build_mini_bar(
        self, bar: ui.row, open_editor: Callable[[], Awaitable[None]]
    ) -> None:
        player = self.player
        with bar:
            self.mini_no_audio = ui.label("No recording").classes("text-grey mx-2")
            self.mini_no_audio.set_visibility(False)
            self.mini_audio = ui.row().classes("items-center gap-1 no-wrap")
        with self.mini_audio:
            self.mini_play = ui.button(
                icon="play_arrow", on_click=player.toggle_play
            ).props("round unelevated dense")
            self.mini_play_tip = tip(self.mini_play, "Play (Space)")
            self.mini_time = ui.label("").classes("font-mono text-caption mx-1")
            ui.button(icon="remove", on_click=lambda: player.tempo_step(-1)).props(
                "flat round dense"
            ).tooltip("Slower (←)")
            self.mini_speed = ui.label("100 %").classes("font-bold w-12 text-center")
            ui.button(icon="add", on_click=lambda: player.tempo_step(1)).props(
                "flat round dense"
            ).tooltip("Faster (→)")
            self.mini_loop = ui.button(
                icon="repeat", on_click=player.toggle_loop
            ).props("flat round dense color=grey")
            self.mini_loop_tip = tip(self.mini_loop, "Loop on (R)")
            ui.button(icon="open_in_full", on_click=open_editor).props(
                "flat round dense"
            ).tooltip("Loop editor (E)")
            self.mini_recordings = ui.element("div")  # on_selection()
        with bar:
            ui.separator().props("vertical").classes("mx-1")

    def build_pane(
        self, shell: Shell, open_editor: Callable[[], Awaitable[None]]
    ) -> None:
        player, engine = self.player, self.engine
        full_only, simple_only = shell.full_only, shell.simple_only
        with ui.row().classes("w-full items-center gap-2"):
            self.recording_box = ui.element("div").classes("grow")  # on_selection()
            self.recording_label = ui.label("").classes("text-subtitle2 text-grey")
            self.loading = ui.spinner(size="sm")
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

        with ui.column().classes("w-full gap-3") as self.player_box:
            # Waveform + transport
            with ui.card().classes("w-full p-3 gap-2"):
                Waveform(player)
                with ui.row().classes("w-full items-center justify-between"):
                    self.time_label = ui.label("0:00 / 0:00").classes("font-mono")
                    self.speed_hint = ui.label("").classes("text-caption text-grey")
                with ui.row().classes("w-full items-center justify-center gap-1"):
                    ui.button(icon="skip_previous", on_click=player.to_start).props(
                        "flat round"
                    ).tooltip("To start (0)")
                    full_only.append(
                        ui.button(icon="replay_5", on_click=lambda: player.skip(-5))
                        .props("flat round")
                        .tooltip("Back 5 s ( , )")
                    )
                    self.play_button = ui.button(
                        icon="play_arrow", on_click=player.toggle_play
                    ).props("round size=lg unelevated")
                    self.play_tip = tip(self.play_button, "Play (Space)")
                    full_only.append(
                        ui.button(icon="forward_5", on_click=lambda: player.skip(5))
                        .props("flat round")
                        .tooltip("Forward 5 s ( . )")
                    )
                    self.loop_button = ui.button(
                        icon="repeat", on_click=player.toggle_loop
                    ).props("flat round color=grey")
                    self.loop_tip = tip(self.loop_button, "Loop on (R)")
                    # Simple has no loop card: the editor sits next to the loop button
                    simple_only.append(
                        ui.button("Loop", icon="open_in_full", on_click=open_editor)
                        .props("flat dense no-caps")
                        .tooltip("Loop editor: zoom in, set the loop exactly (E)")
                    )

            # Tempo
            with ui.card().classes("w-full p-3 gap-1"):
                with ui.row().classes("w-full items-center gap-1 no-wrap"):
                    ui.label("Tempo").classes("text-subtitle2")
                    ui.space()
                    ui.button(
                        icon="remove", on_click=lambda: player.tempo_step(-1)
                    ).props("flat round dense").tooltip("Slower (←)")
                    self.speed_label = ui.label("100 %").classes(
                        "text-h5 font-bold w-20 text-center"
                    )
                    ui.button(icon="add", on_click=lambda: player.tempo_step(1)).props(
                        "flat round dense"
                    ).tooltip("Faster (→)")
                self.speed_slider = ui.slider(
                    min=round(SPEEDS[0] * 100),
                    max=round(SPEEDS[1] * 100),
                    step=1,
                    value=100,
                    on_change=lambda e: (
                        player.set_speed(e.value / 100)
                        if round(engine.speed * 100) != e.value
                        else None
                    ),
                ).props(":markers=5")
                # Absolute, at the slider's own positions: its track has no side padding.
                low, high = round(SPEEDS[0] * 100), round(SPEEDS[1] * 100)
                with ui.element("div").classes("relative w-full h-6 -mt-2") as presets:
                    self.tempo_marks = {
                        mark: ui.label(str(mark))
                        .classes("tempo-mark")
                        .style(f"left: {(mark - low) / (high - low) * 100}%")
                        .on("click", lambda mark=mark: player.set_speed(mark / 100))
                        for mark in TEMPO_MARKS
                    }

                with (
                    ui.expansion("Step-up trainer", icon="trending_up")
                    .classes("w-full")
                    .props("dense") as trainer_box
                ):
                    ui.switch(
                        "Raise tempo while looping",
                        on_change=lambda e: player.toggle_trainer(e.value),
                    )
                    self.trainer_inputs: dict[str, ui.select] = {}
                    with ui.row().classes("items-center gap-2 no-wrap"):
                        for key, options, after in (
                            ("step", {0.05: "+5 %", 0.1: "+10 %"}, "every"),
                            (
                                "every",
                                {n: str(n) for n in range(1, 6)},
                                "repeats, up to",
                            ),
                            (
                                "target",
                                {
                                    round(v / 100, 2): f"{v} %"
                                    for v in range(60, 135, 5)
                                },
                                "",
                            ),
                        ):
                            self.trainer_inputs[key] = (
                                ui.select(
                                    options,
                                    value=TRAINER[key],
                                    on_change=lambda e, key=key: player.set_trainer(
                                        key, e.value
                                    ),
                                )
                                .props("dense outlined options-dense")
                                .on("popup-hide", js_handler=BLUR_SELECT)
                            )
                            if after:
                                ui.label(after)
                    self.trainer_status = ui.label("").classes("text-caption text-grey")

            # Loop
            with ui.card().classes("w-full p-3 gap-2") as loop_card:
                with ui.row().classes("w-full items-center"):
                    ui.label("Loop").classes("text-subtitle2")
                    self.loop_switch = ui.switch(
                        on_change=lambda e: (
                            player.toggle_loop()
                            if e.value != bool(player.loop and player.looping)
                            else None
                        )
                    ).props("color=accent dense")
                    ui.space()
                    edit_button = ui.button(
                        "Edit", icon="open_in_full", on_click=open_editor
                    ).props("flat dense no-caps")
                    tip(edit_button, "Loop editor: zoom in, set the loop exactly (E)")
                loop_times = []
                with ui.grid(columns=2).classes("w-full gap-2"):
                    for edge in (0, 1):
                        with ui.column().classes(
                            "items-center gap-0 py-1 rounded-borders loop-edge"
                        ):
                            ui.label("Start" if edge == 0 else "End").classes(
                                "text-caption text-grey"
                            )
                            with ui.row().classes("items-center gap-0 no-wrap"):
                                self.nudge_button(
                                    edge, -1.0, "keyboard_double_arrow_left"
                                )
                                self.nudge_button(edge, -0.1, "chevron_left")
                                loop_times.append(
                                    ui.label("–").classes(
                                        "font-mono text-subtitle1 w-16 text-center"
                                    )
                                )
                                self.nudge_button(edge, 0.1, "chevron_right")
                                self.nudge_button(
                                    edge, 1.0, "keyboard_double_arrow_right"
                                )
                self.loop_a, self.loop_b = loop_times
                with ui.row().classes("w-full items-center gap-1"):
                    ui.button(
                        "Save loop", icon="bookmark_add", on_click=self.save_loop_dialog
                    ).props("dense flat no-caps").tooltip("Save loop (S)")
                    ui.button("Clear", icon="close", on_click=player.clear_loop).props(
                        "dense flat no-caps"
                    ).tooltip("Clear loop (C)")
                with ui.row().classes("items-center gap-2"):
                    ui.label("Pause between repeats").classes("text-caption")
                    ui.toggle(
                        {0.0: "none", 1.0: "1 s", 2.0: "2 s", 4.0: "4 s"},
                        value=player.state.get("loop_gap", 0.0),
                        on_change=lambda e: player.set_gap(e.value),
                    ).props("dense no-caps toggle-color=accent")
                self.saved_loops = ui.row().classes("w-full gap-1")

            # Pitch + volume
            with ui.card().classes("w-full p-3 gap-1") as pitch_card:
                with ui.row().classes("w-full items-center gap-1 no-wrap"):
                    ui.label("Pitch").classes("text-subtitle2 w-14")
                    ui.button(
                        icon="remove",
                        on_click=lambda: player.set_semitones(engine.semitones - 1),
                    ).props("flat round dense").tooltip("Down a semitone")
                    self.pitch_label = ui.label("0").classes(
                        "font-mono w-8 text-center"
                    )
                    ui.button(
                        icon="add",
                        on_click=lambda: player.set_semitones(engine.semitones + 1),
                    ).props("flat round dense").tooltip("Up a semitone")
                    ui.label("semitones").classes("text-caption text-grey")
                    ui.space()
                    ui.button("Reset", on_click=lambda: player.set_semitones(0)).props(
                        "flat dense no-caps"
                    )
                with ui.row().classes("w-full items-center gap-1 no-wrap"):
                    self.mute_button = (
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

        full_only += [
            self.speed_hint,
            self.speed_slider,
            presets,
            trainer_box,
            loop_card,
            pitch_card,
        ]

    # ------------------------------------------------------------ actions with a dialog

    def nudge_button(self, edge: int, seconds: float, icon: str) -> None:
        """Moves the loop's start (edge 0) or end (1): ‹ › by 0.1 s, « » by 1 s."""
        step = f"{abs(seconds):g} s {'earlier' if seconds < 0 else 'later'}"
        ui.button(icon=icon, on_click=lambda: self.player.nudge(edge, seconds)).props(
            "flat dense round size=sm"
        ).tooltip(step)

    def save_loop_dialog(self) -> None:
        player = self.player
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

    # ------------------------------------------------------------ showing the Player's state

    def on_selection(self, new_song: bool) -> None:
        player = self.player
        recording_chips(self.recording_box, player)
        names = recording_names(player)
        self.mini_recordings.clear()
        self.mini_recordings.set_visibility(len(names) > 1)
        if len(names) > 1:
            current = player.selection.audio
            number = list(names).index(current) + 1 if current in names else 0
            with (
                self.mini_recordings,
                ui.button(f"{number}/{len(names)}", icon="audiotrack").props(
                    "flat dense no-caps"
                ),
            ):
                ui.tooltip("Recording (T: next)")
                with ui.menu():
                    for path, name in names.items():
                        ui.menu_item(
                            name, on_click=lambda path=path: player.pick_recording(path)
                        ).classes("text-primary font-medium" if path == current else "")
        if new_song:
            song = player.song
            self.recording_label.text = next(
                (
                    a["label"]
                    for a in song["audio"]
                    if a["path"] == player.selection.audio
                ),
                "",
            )
            # a single recording is named after the song most of the time: then the title says it
            self.recording_label.set_visibility(
                len(song["audio"]) == 1 and self.recording_label.text != song["title"]
            )

    def on_audio(self) -> None:
        player = self.player
        self.loading.set_visibility(player.loading)
        has_audio = bool(player.selection.audio)
        self.player_box.set_visibility(has_audio and not player.failed)
        self.no_audio.set_visibility(not has_audio)
        self.no_audio_title.text = player.song["title"]
        self.mini_audio.set_visibility(has_audio)
        self.mini_no_audio.set_visibility(not has_audio)
        self.shell.set_audio_less(not has_audio)

    def show_tempo(self) -> None:
        engine = self.engine
        percent = round(engine.speed * 100)
        self.speed_label.text = self.mini_speed.text = f"{percent} %"
        self.speed_slider.value = percent
        for mark, label in self.tempo_marks.items():
            if mark == percent:
                label.classes(add="on")
            else:
                label.classes(remove="on")
        if self.player.audio:
            self.speed_hint.text = (
                f"Song takes {clock(engine.duration / engine.speed)} at this tempo"
            )
        self.pitch_label.text = f"{engine.semitones:+d}" if engine.semitones else "0"

    def show_sound(self) -> None:
        self.mute_button.props(
            f"icon={'volume_off' if self.player.muted else 'volume_up'}"
        )

    def show_loop(self) -> None:
        player = self.player
        loop, on = player.loop, bool(player.loop and player.looping)
        for button in (self.loop_button, self.mini_loop):
            button.props(f"color={'accent' if on else 'grey'}")
        self.loop_tip.text = self.mini_loop_tip.text = (
            "Loop off (R)" if on else "Loop on (R)"
        )
        self.loop_a.text = (
            clock(loop[0]) + f".{int(loop[0] * 10) % 10}" if loop else "–"
        )
        self.loop_b.text = (
            clock(loop[1]) + f".{int(loop[1] * 10) % 10}" if loop else "–"
        )
        self.loop_switch.value = on
        self.loop_switch.set_enabled(bool(loop))
        self.show_status()
        self.saved_loops.clear()
        with self.saved_loops:
            if not player.saved_loops:
                ui.label("No saved loops yet").classes("text-caption text-grey")
            for saved in player.saved_loops:
                ui.chip(
                    f"{saved['name']}  {clock(saved['a'])}–{clock(saved['b'])}",
                    icon="repeat",
                    removable=True,
                    on_click=lambda saved=saved: player.use_saved_loop(saved),
                    on_value_change=lambda e, saved=saved: player.delete_saved_loop(
                        saved
                    ),
                ).props("outline color=accent")

    def show_trainer(self) -> None:
        """Its inputs show the Player's values (set_trainer ignores unchanged ones), and the status."""
        for key, widget in self.trainer_inputs.items():
            widget.value = self.player.trainer[key]
        self.show_status()

    def show_status(self) -> None:
        player, engine, t = self.player, self.engine, self.player.trainer
        if not t["on"]:
            self.trainer_status.text = (
                "Raise the tempo step by step while the loop repeats."
            )
        elif not (player.loop and player.looping):
            self.trainer_status.text = "Set a loop to start."
        elif engine.speed >= t["target"] - 1e-6:
            self.trainer_status.text = f"Target {round(t['target'] * 100)} % reached."
        else:
            self.trainer_status.text = (
                f"Repeat {engine.repeats + 1} of {t['every']} at {round(engine.speed * 100)} %, "
                f"then {round(min(engine.speed + t['step'], t['target']) * 100)} %"
            )

    def on_tick(self) -> None:
        player, engine, last = self.player, self.engine, self.last
        if not player.audio:
            return
        if player.trainer["on"]:
            self.show_status()
        now = f"{clock(player.now)} / {clock(engine.duration)}"
        if now != last["time"]:
            self.time_label.text = self.mini_time.text = last["time"] = now
        if engine.playing != last["playing"]:
            last["playing"] = engine.playing
            for button in (self.play_button, self.mini_play):
                button.props(f"icon={'pause' if engine.playing else 'play_arrow'}")
            self.play_tip.text = self.mini_play_tip.text = (
                "Pause (Space)" if engine.playing else "Play (Space)"
            )
