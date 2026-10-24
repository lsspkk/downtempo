"""Dev tool for the blind listening test (T31, docs/stretch-research.md#then-listening-test-t31):
the same excerpt of each recording stretched by each candidate at each speed, saved under letters.

Usage: uv run python scripts/stretch_test.py <file> [<file> ...] [--start S] [--seconds 20]
       [--speeds 0.5,0.75,1.3] [--out data/scratch/tempo-tests]

Writes <out>/<n>-<file name>/<speed>x/<letter>.wav, the letters shuffled per speed, and the answers in
<out>/key.json (don't open it before listening). Candidates: Rubber Band R3 as the player runs it
(real-time, block by block), R3 with ChannelsTogether, R2 (the faster engine), and Signalsmith Stretch
(python-stretch: the library the browser app runs as WASM); and the original at 1.0x as `original.wav`.
"""

import argparse
import json
import random
import string
from collections.abc import Callable
from pathlib import Path

import numpy as np
import python_stretch as ps
import soundfile as sf
from pylibrb import Option, RubberBandStretcher

BLOCK = 1024  # as the player's engine
Stretcher = Callable[[np.ndarray, int, float], np.ndarray]


def rubber_band(options: int) -> Stretcher:
    def stretch(audio: np.ndarray, rate: int, speed: float) -> np.ndarray:
        """Real-time mode like engine.py: a silence pad in, the start delay dropped."""
        channels = audio.shape[0]
        rb = RubberBandStretcher(sample_rate=rate, channels=channels, options=options)
        rb.set_max_process_size(BLOCK)
        rb.time_ratio = 1 / speed
        pad = rb.get_preferred_start_pad()
        for k in range(0, pad, BLOCK):
            rb.process(np.zeros((channels, min(BLOCK, pad - k)), np.float32))
        drop = rb.get_start_delay()
        out = []
        for start in range(0, audio.shape[1], BLOCK):
            final = start + BLOCK >= audio.shape[1]
            rb.process(
                np.ascontiguousarray(audio[:, start : start + BLOCK]), final=final
            )
            while rb.available() > 0:
                out.append(rb.retrieve_available())
        while not rb.is_done():
            if rb.available() > 0:
                out.append(rb.retrieve_available())
            else:
                break
        return np.concatenate(out, axis=1)[:, drop:]

    return stretch


def signalsmith(audio: np.ndarray, rate: int, speed: float) -> np.ndarray:
    stretch = ps.Signalsmith.Stretch()
    stretch.preset(audio.shape[0], rate)
    stretch.timeFactor = speed  # > 1 plays faster (the output is shorter)
    return stretch.process(audio)


REALTIME = Option.PROCESS_REALTIME | Option.PitchHighConsistency
CANDIDATES: dict[str, Stretcher] = {
    "Rubber Band R3 (the player)": rubber_band(REALTIME | Option.ENGINE_FINER),
    "Rubber Band R3 + ChannelsTogether": rubber_band(
        REALTIME | Option.ENGINE_FINER | Option.CHANNELS_TOGETHER
    ),
    "Rubber Band R2": rubber_band(REALTIME | Option.ENGINE_FASTER),
    "Signalsmith Stretch (the browser app)": signalsmith,
}


def excerpt(path: Path, start: float | None, seconds: float) -> tuple[np.ndarray, int]:
    """(channels, frames) float32; from the middle of the song when no start is given."""
    info = sf.info(path)
    if start is None:
        start = max(info.duration / 2 - seconds / 2, 0)
    frames = int(seconds * info.samplerate)
    data, rate = sf.read(
        path,
        start=int(start * info.samplerate),
        frames=frames,
        dtype="float32",
        always_2d=True,
    )
    return np.ascontiguousarray(data.T), rate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--start", type=float, help="seconds; default the middle")
    parser.add_argument("--seconds", type=float, default=20.0)
    parser.add_argument("--speeds", default="0.5,0.75,1.3")
    parser.add_argument("--out", type=Path, default=Path("data/scratch/tempo-tests"))
    args = parser.parse_args()
    speeds = [float(s) for s in args.speeds.split(",")]
    key: dict[str, dict[str, str]] = {}
    for n, path in enumerate(args.files, 1):
        audio, rate = excerpt(path, args.start, args.seconds)
        folder = args.out / f"{n}-{path.stem}"
        folder.mkdir(parents=True, exist_ok=True)
        sf.write(folder / "original.wav", audio.T, rate)
        for speed in speeds:
            names = list(CANDIDATES)
            random.shuffle(names)
            answers = {}
            for letter, name in zip(string.ascii_uppercase, names):
                out = CANDIDATES[name](audio, rate, speed)
                peak = float(np.abs(out).max()) or 1.0
                target = folder / f"{speed}x" / f"{letter}.wav"
                target.parent.mkdir(exist_ok=True)
                sf.write(target, (out / max(peak, 1.0)).T, rate)  # no clipping
                answers[letter] = name
                print(f"{target}  {out.shape[1] / rate:.1f} s")
            key[f"{folder.name}/{speed}x"] = answers
    (args.out / "key.json").write_text(json.dumps(key, indent=2, ensure_ascii=False))
    print(f"Listen blind, then open {args.out / 'key.json'}")


if __name__ == "__main__":
    main()
