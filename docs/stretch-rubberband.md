# Stretch library: Rubber Band (via pylibrb)

What the library does for us, the settings we use, and where its limits are. Previous: [stretch-app-flow.md](stretch-app-flow.md). Next: [stretch-research.md](stretch-research.md). Why we picked it: [tempo-python.md](tempo-python.md).

## What it is

[Rubber Band Library](web/rubberband-home.txt) is a C++ library for changing tempo and pitch independently, "dynamically" while audio streams. We call it from Python through **pylibrb**, a thin numpy binding ([pylibrb-readme](web/pylibrb-readme.txt)). We hand it blocks of samples and read back stretched samples. Everything in [stretch-theory.md](stretch-theory.md) from "phase vocoder" on happens inside it.

```
 our code:  process(1024 samples) ... retrieve_available() -> about 1024 × time_ratio samples
 inside:    FFT frames -> phase advance + locking + transient resets -> inverse FFT -> overlap-add
```

## Two engines

| | R2 "faster" | R3 "finer" (ours) |
|---|---|---|
| Method | phase vocoder + phase resets at hits + "lamination" for vertical phase coherence ([rubberband-technical](web/rubberband-technical.txt)) | newer design, "some technical differences" (not documented in our saved pages) |
| Vendor advice | limited CPU, percussive material | "if CPU power is not a major limitation" ([rubberband-integration](web/rubberband-integration.txt)) |
| Start delay (44.1/48 kHz) | 1024 samples (23 ms) | 2048 samples (46 ms) |

Our T5 renders compare R2 and R3 at 0.5x and a 0.5→1.3x sweep: `data/scratch/tempo-tests/rubberband_R2_*.wav`, `rubberband_R3_*.wav`.

## Real-time vs offline

- **Offline** sees the whole file first (two passes: `study()` then `process()`), gets exact length and alignment, but the ratio is fixed or pre-planned ([rubberband-stretcher-class](web/rubberband-stretcher-class.txt)).
- **Real-time** (ours) streams block by block, and `time_ratio` and `pitch_scale` can change between any two `process()` calls. That is what makes the live slider and trainer possible.

## Our settings

```python
RubberBandStretcher(rate, channels,
    options=Option.PROCESS_REALTIME | Option.ENGINE_FINER | Option.PitchHighConsistency)
rb.set_max_process_size(1024)
rb.time_ratio  = 1 / speed                 # duration ratio: 2.0 = half speed
rb.pitch_scale = 2 ** (semitones / 12)
```

- `PitchHighConsistency` is the vendor's choice for "pitch-shifting with dynamically-changing ratios" ([rubberband-integration](web/rubberband-integration.txt)), because our pitch buttons change it while playing.
- `time_ratio` is a *duration* ratio, the inverse of our speed.

## Start pad and start delay

Real-time output lags its input. The vendor's recipe: feed `get_preferred_start_pad()` samples of silence first, then drop the first `get_start_delay()` output samples. "Offline mode does this for you, but real-time mode doesn't" ([rubberband-integration](web/rubberband-integration.txt)). We do it after every `reset()` (load, seek).

- **In math:** with R3, pad = 2048 and delay = 2048 at 44 100 Hz (measured). Input sample 22 050 came out at 24 098 = 22 050 + 2048 before the drop: exactly aligned after it.
- A ratio change takes effect after the same delay. The vendor suggests scheduling changes "a little early" if timing matters. For us, the queue delay (0.14–0.28 s, [stretch-app-flow.md](stretch-app-flow.md)) is larger anyway.

## Costs and licence

- **CPU**: R3 is the heavier engine. It ran without dropouts in T5 and T12 on this machine; there's no measurement on a slower one.
- **Licence**: GPL, or a paid commercial licence ([rubberband-home](web/rubberband-home.txt)). That's fine for a personal open-source tool, but it would matter for a closed app.
- **pylibrb**: version 0.1.2, Dec 2023; wheels `cp312-abi3` for Linux and Windows ([pypi-pylibrb-json](web/pypi-pylibrb-json.txt)). It bundles a Rubber Band 3.x with R3 (exact version not exposed; Rubber Band 4.0 came out Oct 2024). At exit it prints harmless "nanobind: leaked" warnings if a stretcher is still alive; the engine joins its worker to avoid that.

## Limits we know of

- **Stereo**: the vendor advises `OptionChannelsTogether` with R3 for the best stereo image; we don't set it yet. It's a candidate for the listening test.
- **No end alignment in real-time mode**: the last block is "rounded up" with extra zeros. That's harmless for us (end of song = stop).
- **Loop seam**: Rubber Band sees a hard jump B→A. Our 5.8 ms fades hide the click, but the first ~46 ms after A still carry some of the audio before B, through the stretcher's memory.
- **Extremes**: 0.5x is the hardest case we use (every frame spread twice as wide). Any remaining artifact (a soft echo on hits) should show first there. Not yet judged by ear (T8).
- **No browser build here**: the browser player can't use this library without a WASM build ([stretch-research.md](stretch-research.md)).
