"""Dev tool: how steady Essentia's tempo detection is on the downloaded recordings (T221.2).

Takes FILES recordings from any downloads/ folder under DATA, cuts each into PIECES pieces of
PIECE_SECONDS spread over the song, and runs both detectors on every piece: PercivalBpmEstimator and RhythmExtractor2013
(which gives a confidence too). The same algorithms exist in essentia.js for the browser
(docs/tempo-detection.md). Prints a table per file and saves everything as JSON under OUT.

Usage: uv run python scripts/tempo_test.py   (change the settings below and run again)
"""

import json
import statistics
from datetime import datetime
from pathlib import Path

import essentia
import essentia.standard as es

DATA = Path("data")
FILES = 5  # recordings, spread over the sorted list
PIECES = 10
PIECE_SECONDS = 10.0
MIN_BPM, MAX_BPM = 50, 210
OUT = Path("data/scratch/tempo-detection")
RATE = 44100  # RhythmExtractor2013 needs 44.1 kHz
SAME = 0.04  # within 4 % counts as the same tempo


def recordings() -> list[Path]:
    found = sorted(
        p
        for p in DATA.rglob("*")
        if "downloads" in p.parts and p.suffix.lower() in (".mp3", ".wav")
    )
    if len(found) <= FILES:
        return found
    step = len(found) / FILES
    return [found[int(i * step)] for i in range(FILES)]


def pieces(audio, rate: int) -> list[tuple[float, object]]:
    """PIECES windows of PIECE_SECONDS, evenly spread (fewer when the song is short)."""
    size = int(PIECE_SECONDS * rate)
    if len(audio) <= size:
        return [(0.0, audio)]
    count = min(PIECES, len(audio) // size)
    gap = (len(audio) - size) / max(count - 1, 1)
    return [
        (int(i * gap) / rate, audio[int(i * gap) : int(i * gap) + size])
        for i in range(count)
    ]


def relation(bpm: float, median: float) -> str:
    """How a piece's BPM relates to the file's median: same, half, double, 3:2, 4:3 … or other."""
    if not bpm or not median:
        return "none"
    for name, factor in (
        ("same", 1),
        ("double", 2),
        ("half", 0.5),
        ("1.5x", 1.5),
        ("2/3", 2 / 3),
        ("4/3", 4 / 3),
        ("3/4", 3 / 4),
    ):
        if abs(bpm / (median * factor) - 1) <= SAME:
            return name
    return "other"


def summary(values: list[float]) -> dict:
    found = [v for v in values if v > 0]
    if not found:
        return {"median": 0.0, "min": 0.0, "max": 0.0, "kinds": {}}
    median = statistics.median(found)
    kinds: dict[str, int] = {}
    for v in values:
        kind = relation(v, median)
        kinds[kind] = kinds.get(kind, 0) + 1
    return {
        "median": round(median, 1),
        "min": round(min(found), 1),
        "max": round(max(found), 1),
        "kinds": kinds,
    }


def analyse(path: Path) -> dict:
    audio = es.MonoLoader(filename=str(path), sampleRate=RATE)()
    percival = es.PercivalBpmEstimator(sampleRate=RATE, minBPM=MIN_BPM, maxBPM=MAX_BPM)
    rhythm = es.RhythmExtractor2013(
        method="multifeature", minTempo=MIN_BPM, maxTempo=MAX_BPM
    )
    rows = []
    for start, piece in pieces(audio, RATE):
        # both keep state between calls (Percival returned the first piece's BPM for all)
        percival.reset()
        rhythm.reset()
        bpm, _, confidence, _, _ = rhythm(piece)
        rows.append(
            {
                "start": round(start, 1),
                "percival": round(float(percival(piece)), 1),
                "rhythm": round(float(bpm), 1),
                "confidence": round(float(confidence), 2),
            }
        )
    return {
        "file": str(path.relative_to(DATA)),
        "seconds": round(len(audio) / RATE, 1),
        "pieces": rows,
        "percival": summary([r["percival"] for r in rows]),
        "rhythm": summary([r["rhythm"] for r in rows]),
        "confidence": round(statistics.mean(r["confidence"] for r in rows), 2),
    }


def show(result: dict) -> None:
    minutes, seconds = divmod(int(result["seconds"]), 60)
    print(f"\n{result['file']}  ({minutes}:{seconds:02d})")
    print("   start   Percival   Rhythm   confidence")
    for r in result["pieces"]:
        m, s = divmod(int(r["start"]), 60)
        print(
            f"   {m:2d}:{s:02d}   {r['percival']:8.1f}   {r['rhythm']:6.1f}   {r['confidence']:10.2f}"
        )
    for name in ("percival", "rhythm"):
        s = result[name]
        kinds = ", ".join(f"{k} {n}" for k, n in s["kinds"].items())
        print(
            f"   {name.capitalize():9s} median {s['median']:6.1f}  range {s['min']:.0f}–{s['max']:.0f}  pieces: {kinds}"
        )
    agree = relation(result["percival"]["median"], result["rhythm"]["median"])
    print(
        f"   The two medians: {agree}; mean confidence {result['confidence']:.2f} (above ~3 is good)"
    )


def main() -> None:
    essentia.log.infoActive = essentia.log.warningActive = False
    settings = {
        "files": FILES,
        "pieces": PIECES,
        "piece_seconds": PIECE_SECONDS,
        "bpm": [MIN_BPM, MAX_BPM],
    }
    print(
        f"Tempo test: {FILES} files from {DATA}/**/downloads, {PIECES} pieces of {PIECE_SECONDS:g} s each"
    )
    results = []
    for path in recordings():
        result = analyse(path)
        show(result)
        results.append(result)
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"results-{datetime.now():%Y%m%d-%H%M%S}.json"
    out.write_text(
        json.dumps(
            {"settings": settings, "results": results}, indent=1, ensure_ascii=False
        ),
        encoding="utf-8",
    )
    steady = sum(
        1
        for r in results
        if r["rhythm"]["kinds"].get("same", 0) >= 0.8 * len(r["pieces"])
    )
    print(
        f"\n{steady} of {len(results)} files steady (8 of 10 pieces at the median, Rhythm). Saved {out}"
    )


if __name__ == "__main__":
    main()
