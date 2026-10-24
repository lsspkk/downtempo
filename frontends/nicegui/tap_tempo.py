"""Tap tempo: the BPM of the last taps (G or Tap in the tempo row, tempo_goal.py)."""

from dataclasses import dataclass, field

RESET = 2.0  # seconds without a tap start a new count
KEEP = 8  # the BPM is the average over the last taps


@dataclass
class Taps:
    times: list[float] = field(default_factory=list)

    def tap(self, now: float) -> None:
        if self.times and now - self.times[-1] > RESET:
            self.times = []
        self.times = [*self.times, now][-KEEP:]

    @property
    def bpm(self) -> float | None:
        if len(self.times) < 2:
            return None
        return 60 * (len(self.times) - 1) / (self.times[-1] - self.times[0])
