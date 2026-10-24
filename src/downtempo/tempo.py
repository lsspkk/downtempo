"""A recording's tempo: the estimate from the audio (Essentia, docs/tempo-detection.md).

`estimate` takes a second or two and holds the GIL: the player runs it as its own process,
`python -m downtempo.tempo <file>`, which prints the estimate as JSON (null when none).
"""

import json
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

RATE = 44100
PIECES = 10
PIECE_SECONDS = 10.0
MIN_BPM, MAX_BPM = 50, 210
SAME = 0.04  # within 4 % counts as the same tempo


@dataclass(frozen=True)
class Estimate:
    bpm: float
    sure: float  # share of pieces at that tempo, half and double counted as the same


def estimate(path: Path) -> Estimate | None:
    """The median of PercivalBpmEstimator over pieces spread over the song; None without a tempo."""
    import essentia
    import essentia.standard as es

    essentia.log.infoActive = essentia.log.warningActive = False
    audio = es.MonoLoader(filename=str(path), sampleRate=RATE)()
    percival = es.PercivalBpmEstimator(sampleRate=RATE, minBPM=MIN_BPM, maxBPM=MAX_BPM)
    found = []
    for piece in pieces(audio):
        percival.reset()  # it keeps state between calls
        if (bpm := float(percival(piece))) > 0:
            found.append(bpm)
    if not found:
        return None
    middle = statistics.median(found)
    folded = [fold(bpm, middle) for bpm in found]
    bpm = statistics.median(folded)
    same = sum(abs(b / bpm - 1) <= SAME for b in folded)
    return Estimate(round(bpm, 1), round(same / len(found), 2))


def pieces(audio: np.ndarray) -> list[np.ndarray]:
    size = int(PIECE_SECONDS * RATE)
    if len(audio) <= size:
        return [audio]
    count = min(PIECES, len(audio) // size)
    gap = (len(audio) - size) / max(count - 1, 1)
    return [audio[int(i * gap) : int(i * gap) + size] for i in range(count)]


def fold(bpm: float, middle: float) -> float:
    """Half or double of `middle` counts as `middle`'s octave."""
    for factor in (2.0, 0.5):
        if abs(bpm / (middle * factor) - 1) <= SAME:
            return bpm / factor
    return bpm


def main() -> None:
    found = estimate(Path(sys.argv[1]))
    print(json.dumps(found and {"bpm": found.bpm, "sure": found.sure}))


if __name__ == "__main__":
    main()
