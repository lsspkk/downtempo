"""The Metronome, mixed into the engine's output: a steady tick at one BPM (the BPM now), playing
or not. docs/tempo-goal.md."""

from dataclasses import dataclass, field

import numpy as np

LEVEL = 0.5
SOUND_SECONDS = 0.03
PITCH = 1800  # Hz


def click_sound(rate: int) -> np.ndarray:
    t = np.arange(int(SOUND_SECONDS * rate)) / rate
    return (np.sin(2 * np.pi * PITCH * t) * np.exp(-t * 180)).astype(np.float32)


@dataclass
class Click:
    bpm: float = 0.0  # 0: quiet
    _tail: np.ndarray = field(default_factory=lambda: np.zeros(0, np.float32))
    _next: float = 0.0  # output frames to the next tick
    _sound: np.ndarray = field(default_factory=lambda: np.zeros(0, np.float32))

    def add(self, out: np.ndarray, rate: int, volume: float) -> None:
        """Called by the audio callback after the music is in `out`."""
        if len(self._sound) != int(SOUND_SECONDS * rate):
            self._sound = click_sound(rate)
        level = LEVEL * volume
        tail, self._tail = self._tail, np.zeros(0, np.float32)
        if len(tail):
            n = min(len(tail), len(out))
            out[:n] += tail[:n, None] * level
        if self.bpm <= 0:
            self._next = 0.0  # switched on, it ticks at once
            return
        i = self._next
        while i < len(out):
            self._place(out, int(i), level)
            i += 60 / self.bpm * rate
        self._next = i - len(out)

    def _place(self, out: np.ndarray, i: int, level: float) -> None:
        n = max(min(len(self._sound), len(out) - i), 0)
        out[i : i + n] += self._sound[:n, None] * level
        if n < len(self._sound):
            self._tail = self._sound[n:]
