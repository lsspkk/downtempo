"""What plays and what's remembered: the picked song, loading its recording, tempo, pitch, volume,
loop, step-up trainer, autosave. One Player per page; no widgets.

It changes the engine and the remembered state, then tells the page's parts what changed; they
redraw from the Player's fields. Topics (`on` / `emit`):
- "selection" (new_song): a song or recording was picked
- "audio": a recording started loading, loaded or failed (listeners may be async)
- "sheet" (sel, ticket): load this sheet (listeners may be async)
- "tempo": speed or pitch; "sound": volume or mute; "loop": the loop or the saved loops
- "trainer": the trainer's settings or on/off; "tick": every 0.1 s

Switching (docs/player-switching.md): user actions make a new Selection; the loaders work on that
snapshot and give up when a newer one of their part (audio, sheet) was asked for.
"""

import inspect
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import sounddevice as sd
from engine import Engine
from nicegui import run, ui
from state import save_state

from downtempo.catalog import Song
from downtempo.config import DATA_DIR

SPEEDS = (0.5, 1.3)  # min, max
TRAINER = {"step": 0.05, "every": 2, "target": 1.0}  # defaults; remembered per song
SAVE_EVERY = 20  # ticks: 2 s


def song_key(song: Song) -> str:
    return f"{song['collection']}/{song['title']}"


@dataclass(frozen=True, eq=False)
class Selection:
    """What the user picked. Only user actions make a new one; loaders work on this snapshot."""

    song: Song
    audio: str  # "" when the song has no recording
    pdf: str  # "" when the song has no sheet


class Player:
    def __init__(
        self, engine: Engine, state: dict[str, Any], songs: list[Song]
    ) -> None:
        self.engine, self.state, self.songs = engine, state, songs
        self.selection: Selection | None = None
        self.audio = ""  # path of the loaded recording; "" while loading
        self.loading = False
        self.failed = False  # the selected recording couldn't be played
        self.loop: tuple[float, float] | None = (
            None  # seconds, kept while looping is off
        )
        self.looping = False
        self.muted = False
        self.trainer: dict[str, Any] = {"on": False, **TRAINER}
        self.dirty = False  # state changed since the last save
        # Newest-wins tickets per part, separate so a sheet tab click doesn't cancel the song's
        # audio load (and the other way).
        self.tickets = {"audio": 0, "sheet": 0}
        self._listeners: dict[str, list[Callable[..., Any]]] = defaultdict(list)
        self._ticks = 0
        engine.volume = (state.get("volume", 80) / 100) ** 2
        engine.loop_gap = state.get("loop_gap", 0.0)

    # ------------------------------------------------------------ telling the parts

    def on(self, topic: str, listener: Callable[..., Any]) -> None:
        self._listeners[topic].append(listener)

    def emit(self, topic: str, *args: Any) -> None:
        for listener in self._listeners[topic]:
            listener(*args)

    async def emit_async(self, topic: str, *args: Any) -> None:
        for listener in self._listeners[topic]:
            if inspect.isawaitable(result := listener(*args)):
                await result

    # ------------------------------------------------------------ what is remembered

    @property
    def song(self) -> Song | None:
        return self.selection.song if self.selection else None

    @property
    def song_state(self) -> dict[str, Any]:
        return (
            self.state["songs"].setdefault(song_key(self.song), {}) if self.song else {}
        )

    @property
    def recording_state(self) -> dict[str, Any]:
        return self.state["recordings"].setdefault(self.audio, {}) if self.audio else {}

    @property
    def now(self) -> float:
        """The play position in seconds."""
        return self.engine.position / self.engine.rate

    def remember(self, **song_values: Any) -> None:
        self.song_state.update(song_values)
        self.dirty = True

    def loaded(self, sel: Selection) -> None:
        """Remember the song only once something of it loaded (S6)."""
        if self.state.get("last_song") != song_key(sel.song):
            self.state["last_song"] = song_key(sel.song)
            self.dirty = True

    def save_position(self) -> None:
        if self.audio:
            self.recording_state["position"] = round(self.now, 2)
            self.dirty = True

    # ------------------------------------------------------------ switching

    async def open_song(self, song: Song) -> None:
        self.engine.pause()
        self.save_position()
        saved = self.state["songs"].get(song_key(song), {})
        audios = [a["path"] for a in song["audio"]]
        audio = saved.get("audio")
        if audio not in audios:
            audio = audios[0] if audios else ""
        pdf = saved.get("pdf")
        if pdf not in song["pdf"]:
            pdf = song["pdf"][0] if song["pdf"] else ""
        sel = self.selection = Selection(song, audio, pdf)
        self.audio = ""
        audio_ticket, sheet_ticket = self.ticket("audio"), self.ticket("sheet")
        self.emit("selection", True)
        await self.load_audio(sel, audio_ticket)
        await self.emit_async("sheet", sel, sheet_ticket)

    async def step_song(self, shown: list[Song], offset: int) -> None:
        if not shown:
            return
        index = shown.index(self.song) if self.song in shown else -1
        await self.open_song(shown[(index + offset) % len(shown)])

    async def pick_recording(self, path: str | None) -> None:
        if not path or not self.selection or path == self.selection.audio:
            return
        self.engine.pause()
        self.save_position()
        sel = self.selection = replace(self.selection, audio=path)
        self.audio = ""
        self.emit("selection", False)
        await self.load_audio(sel, self.ticket("audio"))

    async def step_recording(self, offset: int) -> None:
        if not self.selection:
            return
        paths = [a["path"] for a in self.selection.song["audio"]]
        if len(paths) > 1:
            index = (
                paths.index(self.selection.audio)
                if self.selection.audio in paths
                else 0
            )
            await self.pick_recording(paths[(index + offset) % len(paths)])

    async def pick_sheet(self, pdf: str | None) -> None:
        if not pdf or not self.selection or pdf == self.selection.pdf:
            return
        sel = self.selection = replace(self.selection, pdf=pdf)
        await self.emit_async("sheet", sel, self.ticket("sheet"))

    def ticket(self, part: str) -> int:
        self.tickets[part] += 1
        return self.tickets[part]

    async def load_audio(self, sel: Selection, ticket: int) -> None:
        def wanted() -> bool:
            return ticket == self.tickets["audio"]

        self.loading, self.failed = bool(sel.audio), False
        await self.emit_async("audio")
        if not sel.audio:
            await run.io_bound(self.engine.close)
            return
        try:
            done = await run.io_bound(self.engine.load, DATA_DIR / sel.audio, wanted)
        except (OSError, RuntimeError, sd.PortAudioError) as error:
            if wanted():
                ui.notify(
                    f"Cannot play {Path(sel.audio).name}: {error}",
                    type="negative",
                    multi_line=True,
                )
                self.loading, self.failed = False, True
                await self.emit_async("audio")
            return
        if not done or not wanted():
            return
        # Still the newest audio load, so no other song was opened: self.song is sel.song.
        self.loading = False
        self.audio = sel.audio
        self.remember(audio=sel.audio)
        self.loaded(sel)
        self.set_speed(self.song_state.get("speed", 1.0))
        self.set_semitones(self.song_state.get("semitones", 0))
        self.restore_trainer()
        loop = self.recording_state.get("loop")
        self.loop, self.looping = (tuple(loop), True) if loop else (None, False)
        self.apply_loop()
        self.seek(self.recording_state.get("position", 0.0))
        await self.emit_async("audio")

    # ------------------------------------------------------------ playing

    def toggle_play(self) -> None:
        if not self.audio:
            return
        self.engine.pause() if self.engine.playing else self.engine.play()

    def seek(self, seconds: float) -> None:
        if self.audio:
            self.engine.seek(seconds * self.engine.rate)

    def skip(self, seconds: float) -> None:
        self.seek(self.now + seconds)

    def to_start(self) -> None:
        self.seek(self.loop[0] if self.loop and self.looping else 0)

    def set_speed(self, value: float) -> None:
        if not self.audio:  # loading: the value would land on the new song
            return
        self.engine.speed = round(min(max(value, SPEEDS[0]), SPEEDS[1]), 2)
        self.remember(speed=self.engine.speed)
        self.emit("tempo")

    def tempo_step(self, direction: int) -> None:
        self.set_speed(
            self.engine.speed + direction * self.state["settings"]["tempo_step"] / 100
        )

    def set_semitones(self, value: int) -> None:
        if not self.audio:
            return
        self.engine.semitones = max(-12, min(12, value))
        self.remember(semitones=self.engine.semitones)
        self.emit("tempo")

    def set_volume(self, value: float) -> None:
        self.state["volume"] = value
        self.dirty = True
        self.engine.volume = 0.0 if self.muted else (value / 100) ** 2

    def toggle_mute(self) -> None:
        self.muted = not self.muted
        self.set_volume(self.state.get("volume", 80))
        self.emit("sound")

    # ------------------------------------------------------------ loop

    def apply_loop(self) -> None:
        frames = None
        if self.loop and self.looping:
            frames = (
                int(self.loop[0] * self.engine.rate),
                int(self.loop[1] * self.engine.rate),
            )
        self.engine.set_loop(frames)
        self.recording_state["loop"] = (
            list(self.loop) if self.loop and self.looping else None
        )
        self.dirty = True
        self.emit("loop")

    def set_loop(self, a: float, b: float) -> None:
        a, b = sorted((max(a, 0), min(b, self.engine.duration)))
        if b - a < 0.2:
            ui.notify("Loop too short: at least 0.2 s", type="warning")
            return
        self.loop, self.looping = (a, b), True
        self.apply_loop()

    def set_a(self) -> None:
        now = self.now
        b = (
            self.loop[1]
            if self.loop and self.loop[1] > now + 0.2
            else self.engine.duration
        )
        self.set_loop(now, b)

    def set_b(self) -> None:
        now = self.now
        a = self.loop[0] if self.loop and self.loop[0] < now - 0.2 else 0.0
        self.set_loop(a, now)

    def nudge(self, edge: int, seconds: float) -> None:
        if self.loop:
            loop = list(self.loop)
            loop[edge] += seconds
            self.set_loop(*loop)

    def toggle_loop(self) -> None:
        if not self.loop:
            ui.notify("Set a loop first: press A and B, or drag over the waveform")
            return
        self.looping = not self.looping
        self.apply_loop()

    def clear_loop(self) -> None:
        self.loop, self.looping = None, False
        self.apply_loop()

    def set_gap(self, value: float) -> None:
        self.engine.loop_gap = value
        self.state["loop_gap"] = value
        self.dirty = True

    @property
    def saved_loops(self) -> list[dict[str, Any]]:
        return self.recording_state.get("loops", [])

    def save_loop(self, name: str) -> None:
        if not self.loop:
            return
        self.recording_state.setdefault("loops", []).append(
            {"name": name.strip() or "Loop", "a": self.loop[0], "b": self.loop[1]}
        )
        self.dirty = True
        self.emit("loop")

    def use_saved_loop(self, saved: dict[str, Any]) -> None:
        self.set_loop(saved["a"], saved["b"])
        self.seek(saved["a"])

    def delete_saved_loop(self, saved: dict[str, Any]) -> None:
        self.recording_state.get("loops", []).remove(saved)
        self.dirty = True
        self.emit("loop")

    # ------------------------------------------------------------ step-up trainer

    def toggle_trainer(self, on: bool) -> None:
        self.trainer["on"] = on
        self.engine.reset_repeats()
        self.emit("trainer")

    def set_trainer(self, key: str, value: float) -> None:
        if self.trainer[key] == value:  # also when a part shows the restored values
            return
        self.trainer[key] = value
        if self.audio:
            self.remember(trainer={k: self.trainer[k] for k in TRAINER})
        self.emit("trainer")

    def restore_trainer(self) -> None:
        self.trainer.update({**TRAINER, **self.song_state.get("trainer", {})})
        self.emit("trainer")

    # ------------------------------------------------------------ every 0.1 s

    def tick(self) -> None:
        engine, t = self.engine, self.trainer
        if (
            self.audio
            and t["on"]
            and self.loop
            and self.looping
            and engine.repeats >= t["every"]
            and engine.speed < t["target"] - 1e-6
        ):
            engine.reset_repeats()
            self.set_speed(min(engine.speed + t["step"], t["target"]))
            ui.notify(
                f"Tempo {round(engine.speed * 100)} %", position="top", timeout=1500
            )
        self.emit("tick")
        self._ticks += 1
        if self._ticks >= SAVE_EVERY:
            self._ticks = 0
            self.save_position()
            if self.dirty:
                save_state(self.state)
                self.dirty = False
