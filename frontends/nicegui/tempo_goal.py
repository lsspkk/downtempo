"""The tempo in BPM, no widgets (docs/tempo-goal.md): the recording tempo (found by itself on first
load, then just a number the user may change), the song's optimal tempo, the Play at switch, Tap
(sets the speed like a DAW's tap tempo) and the Metronome (a steady tick at the BPM now). Tells the parts through the "bpm" topic.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

from nicegui import background_tasks, ui
from player import SPEEDS, Player
from tap_tempo import Taps

ESTIMATE_SECONDS = 120  # give up on a stuck estimate
TAPS_TO_FOLLOW = 4  # the speed follows the taps from this many on
SHOW_TAPPED = 2.0  # seconds "tapped 108" stays in the tempo row


async def estimate(path: Path) -> dict | None:
    """`python -m downtempo.tempo` on the file: {"bpm", "sure"} or None."""
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "downtempo.tempo",
        str(path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(process.communicate(), ESTIMATE_SECONDS)
    except TimeoutError:
        process.kill()
        raise
    if process.returncode:
        raise OSError(
            err.decode(errors="replace").strip().splitlines()[-1:] or "failed"
        )
    return json.loads(
        out.decode().strip().splitlines()[-1]
    )  # Essentia may print before it


def clamp(value: float) -> float:
    return round(min(max(value, 20.0), 400.0), 1)


class TempoGoal:
    def __init__(self, player: Player) -> None:
        self.player, self.engine = player, player.engine
        self.finding = ""  # the recording being analysed
        self.not_found = ""  # the recording whose estimate found no tempo
        self.restoring = (
            False  # a recording loads: its remembered speed isn't a change by hand
        )
        self.taps = Taps()
        self.metronome = False  # ticking at the BPM now
        player.on("audio", self.on_audio)
        player.on("tempo", self.on_tempo)

    # ------------------------------------------------------------ the numbers

    @property
    def bpm(self) -> float | None:
        """The recording tempo: its BPM at 100 %."""
        return self.player.recording_state.get("bpm")

    @property
    def optimal(self) -> float | None:
        return self.player.song_state.get("goal_bpm")

    @property
    def now(self) -> float | None:
        return self.bpm * self.engine.speed if self.bpm else None

    @property
    def optimal_speed(self) -> float | None:
        """The speed that plays the optimal tempo, as far as the player goes (None without both)."""
        if not (self.optimal and self.bpm):
            return None
        return round(min(max(self.optimal / self.bpm, SPEEDS[0]), SPEEDS[1]), 2)

    @property
    def at_optimal(self) -> bool:
        """The Play at switch, remembered per song: on, every recording of the song plays at the
        optimal tempo (by its own BPM) until the speed is changed by hand."""
        return self.back is not None and bool(self.optimal)

    @property
    def back(self) -> float | None:
        """The speed to go back to when the switch goes off; kept only while it is on."""
        return self.player.song_state.get("at_optimal")

    @property
    def tapped(self) -> float | None:
        """The tapped BPM while "tapped 108" is shown."""
        times = self.taps.times
        if self.taps.bpm and time.monotonic() - times[-1] < SHOW_TAPPED:
            return self.taps.bpm
        return None

    def state_text(self) -> str:
        """The recording tempo's value when there is no number."""
        if self.finding:
            return "finding…"
        return "none found" if self.not_found == self.player.audio else "–"

    # ------------------------------------------------------------ changes

    def set_bpm(self, value: float | None) -> None:
        if not self.player.audio:
            return
        state = self.player.recording_state
        if value:
            state["bpm"] = clamp(value)
        else:
            state.pop("bpm", None)
        state.pop("bpm_estimate", None)  # from the first design: no estimated state now
        self.changed()

    def set_optimal(self, value: float | None) -> None:
        """An empty field means no optimal tempo."""
        if not self.player.audio:
            return
        if value:
            self.player.song_state["goal_bpm"] = clamp(value)
        else:
            self.player.song_state.pop("goal_bpm", None)
            self.player.song_state.pop("at_optimal", None)
        self.changed()

    def changed(self) -> None:
        self.player.dirty = True
        self.follow_optimal()
        self.click_tempo()
        self.player.emit("bpm")

    def follow_optimal(self) -> None:
        """While the switch is on: play the optimal tempo (after a new recording, its BPM or the
        optimal tempo changed)."""
        speed = self.optimal_speed
        if self.at_optimal and speed and abs(self.engine.speed - speed) >= 0.005:
            self.player.set_speed(speed)

    def toggle_optimal(self) -> str:
        """The Play at switch (X): on plays the optimal tempo, off goes back to the speed before.
        Returns what happened, for a toast where the switch isn't seen (sheet only)."""
        player = self.player
        if not player.audio:
            return ""
        if self.at_optimal:
            back = player.song_state.pop("at_optimal")
            player.dirty = True
            player.set_speed(back)
            player.emit("bpm")
            return f"Back to {back * 100:.0f} %"
        if not self.optimal_speed:
            ui.notify(
                "Set the recording tempo first (BPM tab)"
                if self.optimal
                else "No optimal tempo for this song yet: set one in the BPM tab"
            )
            return ""
        wanted = self.optimal / self.bpm
        player.song_state["at_optimal"] = self.engine.speed
        player.dirty = True
        player.set_speed(wanted)
        player.emit("bpm")
        if abs(self.engine.speed - wanted) > 0.005:
            ui.notify(
                f"The optimal tempo needs {wanted * 100:.0f} %; the player goes "
                f"{SPEEDS[0] * 100:.0f}–{SPEEDS[1] * 100:.0f} %",
                type="warning",
            )
        return f"Playing at {self.optimal:.0f} BPM ({self.engine.speed * 100:.0f} %)"

    def tap(self) -> str:
        """Tap (G): from the 4th tap on, the speed follows (BPM now = tapped); a 2 s pause starts
        over. Only the speed is kept. Returns the toast for sheet only."""
        if not self.player.audio:
            return ""
        if not self.bpm:
            ui.notify("Tap needs the recording tempo (BPM tab)")
            return ""
        self.taps.tap(time.monotonic())
        tapped = self.taps.bpm
        follows = len(self.taps.times) >= TAPS_TO_FOLLOW and tapped
        if follows:
            self.player.set_speed(tapped / self.bpm)
        self.player.emit("bpm")
        if not follows:
            return f"Tap {len(self.taps.times)}…"
        return f"Tapped: {tapped:.0f} BPM ({self.engine.speed * 100:.0f} %)"

    # ------------------------------------------------------------ the Metronome

    def toggle_metronome(self) -> None:
        self.metronome = not self.metronome
        self.click_tempo()
        self.player.emit("bpm")

    def click_tempo(self) -> None:
        if not self.now:
            self.metronome = False
        self.engine.click.bpm = self.now if self.metronome else 0.0

    # ------------------------------------------------------------ the player's news

    def on_tempo(self) -> None:
        """A tempo change by hand turns the Play at switch off and keeps the speed."""
        speed = self.optimal_speed
        if (
            self.at_optimal
            and not self.restoring
            and speed
            and abs(self.engine.speed - speed) >= 0.005
        ):
            self.player.song_state.pop("at_optimal")
            self.player.dirty = True
        self.click_tempo()
        self.player.emit("bpm")

    def on_audio(self) -> None:
        player = self.player
        # "audio" comes as the load starts and again when it's done (after the remembered speed)
        self.restoring = player.loading
        if not player.loading:
            self.follow_optimal()
        self.metronome = False  # a new recording starts quiet
        if player.audio and not player.loading and not self.bpm:
            # in the background: the song's sheet loads after the "audio" listeners
            background_tasks.create(self.find())
        self.click_tempo()
        player.emit("bpm")

    async def find(self) -> None:
        """Estimate the loaded recording's tempo in a process of its own (Essentia holds the GIL;
        a fork of the player, with its audio threads, could hang)."""
        audio, player = self.player.audio, self.player
        if not audio or self.finding == audio:
            return
        self.finding = audio
        player.emit("bpm")
        try:
            found = await estimate(player.library.path(audio))
        except (
            OSError,
            ValueError,
            TimeoutError,
        ) as error:  # the user can still set it
            found = None
            ui.notify(f"Couldn't find the tempo: {error}", type="warning")
        self.finding = ""
        state = player.state["recordings"].setdefault(audio, {})
        if found and "bpm" not in state:
            state["bpm"] = found["bpm"]
            player.dirty = True
            if audio == player.audio:
                self.follow_optimal()
        elif not found:
            self.not_found = audio
        self.click_tempo()
        player.emit("bpm")
