# Python time-stretch (T5)

**Summary**: Decided (T5). pylibrb (Rubber Band, real-time) + sounddevice + soundfile: tempo changes live while playing. Fallback: pedalboard, which can only re-render.

Goal: play an mp3 at 0.5x–1.3x with pitch kept, tempo changeable **while playing**, sound from Python (`sounddevice`).

## Plan

1. **Dependencies**: T11 added `nicegui sounddevice soundfile numpy`; T12 adds `pylibrb`.
2. **T11, plain playback:**
   - `soundfile` reads the mp3 into numpy.
   - A worker thread feeds blocks to a queue.
   - A `sounddevice` callback plays from the queue.
   - NiceGUI has Play/Stop buttons. No stretching yet.
3. **T12, tempo:**
   - Put a `pylibrb` stretcher (real-time mode, R3 engine) in the worker thread.
   - The NiceGUI slider sets `speed`, and the worker sets `time_ratio = 1 / speed` before each block.
   - Built as described in [stretch-app-flow.md](stretch-app-flow.md).
4. **Listen at 0.5x.** If it sounds bad or uses too much CPU, try R2 (`ENGINE_FASTER`). If that doesn't help, go to the alternatives below.
5. **T13, song selector:** on song change, stop, reset the stretcher, and load the new file.

## Alternatives (in order, if the plan fails)

| # | Option | Switch to it when | Cost |
|---|---|---|---|
| 1 | `pylibrb` R2 engine (`ENGINE_FASTER`) | R3 uses too much CPU or the delay is too long | One option flag; slightly lower quality |
| 2 | `pedalboard.time_stretch`: re-render the whole song when the slider is released | `pylibrb` fails to install, crashes, or real-time quality is bad | Tempo isn't live; a wait on each change (a few seconds per song). Very well maintained |
| 3 | `python-stretch` (Signalsmith), whole-buffer render | A non-GPL (MIT) license is needed | Same as #2, plus weaker below 0.75x by its own docs |
| 4 | Browser `playbackRate` + `preservesPitch` (the browser player idea) | Python audio output is unreliable on some machine | Gives up "sound from Python" |

Ruled out:
- pyrubberband: runs a command-line tool through temp files.
- audiotsm: dead since 2017.
- librosa: offline only, and it sounds smeared on music.
- pytsmod: offline, and requires Python < 3.13.
- pytimestretch: not on PyPI.

## Pick

**`pylibrb` (Rubber Band, real-time mode) + `sounddevice` for output + `soundfile` for mp3 decoding.**

- Rubber Band's real-time mode streams: you `process()` blocks in and `retrieve()` blocks out, and you can change the time ratio at any time. Sources: [rubberband-stretcher-class](web/rubberband-stretcher-class.txt), [pylibrb-readme](web/pylibrb-readme.txt)
- R3 (`ENGINE_FINER`) is the high-quality engine and R2 (`ENGINE_FASTER`) the cheaper one: details, start delay and limits in [stretch-rubberband.md](stretch-rubberband.md).
- `pylibrb` is a thin nanobind binding with a numpy API, no CLI or temp files. It has `cp312-abi3` wheels for Linux and Windows x86_64. Source: [pypi-pylibrb-json](web/pypi-pylibrb-json.txt)
- Risks:
  - The last `pylibrb` release was 0.1.2 in Dec 2023. It's a thin wrapper and the abi3 wheel covers newer Pythons, so this is acceptable.
  - The license is GPL (Rubber Band is GPL or commercial). That's fine for a personal tool.

**Fallback: `pedalboard.time_stretch`** (also Rubber Band, very actively maintained, GPLv3). It only works on whole buffers, so changing tempo would mean re-rendering the song, not a live change. Sources: [pedalboard-api-reference](web/pedalboard-api-reference.txt), [pedalboard-readme](web/pedalboard-readme.txt)

## Candidates

| Library | Live tempo change | 0.5x quality (from docs) | Maintained | Linux + Windows wheels | License |
|---|---|---|---|---|---|
| **pylibrb** (Rubber Band) | **Yes**, real-time mode, ratio changeable at any time | Rubber Band R3 is the reference-quality engine | Last release 2023 | Yes, cp312-abi3 | GPLv2 |
| python-stretch (Signalsmith) | The C++ library can; the Python wrapper only documents whole-buffer `process()` | Upstream: "sounds best for more modest changes (0.75x–1.5x)" | 0.3.1, Feb 2025 | Yes, cp312-abi3 | MIT |
| pedalboard | No, offline buffers. `stretch_factor` can be an array that varies over the file | Rubber Band | Very active, 0.9.26 Oct 2026 | Yes | GPLv3 |
| pyrubberband | No, runs the `rubberband` CLI through temp files | Rubber Band | 0.4.0, 2024 | Pure Python + system binary | ISC |
| audiotsm | Streaming WSOLA / phase vocoder | Lower than Rubber Band | **Dead**, last release 2017 | Pure Python | MIT |
| librosa `effects.time_stretch` | No, offline phase vocoder | Phasey on music | Active, 1.0.0 Aug 2026 | Pure Python | ISC |
| pytsmod | No, offline | Research algorithms | 2023; requires Python < 3.13 | Pure Python | GPLv3 |
| pytimestretch | No, offline whole buffers | Rubber Band / Signalsmith | Not on PyPI | Build from source | GPLv2 |

Sources:
- Signalsmith: [python-stretch-readme](web/python-stretch-readme.txt), [signalsmith-stretch-readme](web/signalsmith-stretch-readme.txt)
- pyrubberband: [pyrubberband-docs](web/pyrubberband-docs.txt)
- pytimestretch: [pytimestretch-readme](web/pytimestretch-readme.txt)
- PyPI metadata for each package: `web/pypi-<name>-json.txt`

### Signalsmith wrapper (python-stretch): not for small blocks

Fed in 1024-sample blocks, the Python wrapper's output had level dips and an off pitch. When it was given the whole buffer at once, the output was clean. Treat it as an offline tool, like pedalboard.

## Supporting pieces

- **`sounddevice`**: `OutputStream(callback=...)` plays numpy blocks. Active, MIT, wheels include PortAudio on Windows. [pypi-sounddevice-json](web/pypi-sounddevice-json.txt)
- **`soundfile`**: reads mp3 into numpy (libsndfile ≥ 1.1 is bundled in the wheels). BSD license. [pypi-soundfile-json](web/pypi-soundfile-json.txt)
- **`nicegui`**: UI, 3.18.0 (Oct 2026), MIT. [pypi-nicegui-json](web/pypi-nicegui-json.txt)

## How it was built

The design sketch that was here is superseded by `frontends/nicegui/engine.py`. The flow is explained in [stretch-app-flow.md](stretch-app-flow.md), and the library details in [stretch-rubberband.md](stretch-rubberband.md).
