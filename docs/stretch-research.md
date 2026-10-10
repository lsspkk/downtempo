# Stretch research: what would make the best stretch

**Summary**: Researched (T12.6). Keep Rubber Band R3 in Python; for a browser player Signalsmith Stretch Web is the best candidate, with plain `playbackRate` as the baseline. A blind listening test (T31) decides.

**Status: researched 2026-10-08 (T12.6)** from docs, READMEs and source comments only; nothing installed or benchmarked. Previous: [stretch-rubberband.md](stretch-rubberband.md). Theory terms: [stretch-theory.md](stretch-theory.md).

## Question

Which algorithm and implementation give the best practice sound for this app?

- Clean at **0.5x** (the hard case) and good up to **1.3x**.
- **Live** tempo and pitch changes without gaps.
- Low enough latency for a responsive slider.
- Runs in Python, and ideally also in the browser.
- Has a usable licence and active maintenance.

## Short answer

- **Keep Rubber Band R3 in Python.** Its maker calls R3 "substantially higher-quality" than R2 ([rubberband-v3-announcement](web/rubberband-v3-announcement.txt)), it changes tempo live, and pylibrb already works here. Licence GPL: fine for a personal tool.
- **For the browser, Signalsmith Stretch Web is the strongest candidate**: official WASM/AudioWorklet release, MIT, live `rate`/`semitones`, and built-in `loopStart`/`loopEnd` ([signalsmith-stretch-npm-readme](web/signalsmith-stretch-npm-readme.txt)). Its README warns that time-stretch "sounds best" between 0.75x and 1.5x ([signalsmith-stretch-readme](web/signalsmith-stretch-readme.txt)), so 0.5x has to be checked by ear.
- **Browser built-in `playbackRate`** is the zero-code baseline: Chrome uses WSOLA, Firefox uses SoundTouch (also WSOLA-type). Expect the "echoing" that time-domain methods have when slowing down.
- Nobody publishes a written verdict for 0.5x on real music. The only comparison with numbers (Bungee's page) uses steady sine tones, which favour time-domain methods. **The listening test decides** (task at the end).

## Candidates

| Candidate | Family | Slow-down notes | Live | Latency | Licence | Maintained | Python | Browser |
|---|---|---|---|---|---|---|---|---|
| Rubber Band R3 (ours) | frequency domain, new engine (method not published) | "substantially higher-quality" than R2, more CPU | yes | 2048 frames (46 ms) default, 1280 short | GPL / commercial | v4.0 Oct 2024 | pylibrb | rubberband-web (WASM worklet, small project) |
| Rubber Band R2 | phase vocoder + phase reset at transients + "lamination" | the older default | yes | 1024 (512–2048) | same | same | pylibrb | same |
| Signalsmith Stretch | frequency domain | "best for 0.75x–1.5x" | yes | ~120 ms blocks (configurable) | MIT | active, official web release | python-stretch (whole buffer only) | official npm `signalsmith-stretch` |
| SoundTouch / SoundTouchJS | WSOLA (SoundTouchJS adds an optional phase vocoder worklet) | "echoing" when slowing; longer sequences help slowing but hurt speeding | yes | ~100 ms | LGPL / SoundTouchJS MPL-2.0 | SoundTouchJS active (11 packages) | none maintained | `@soundtouchjs/audio-worklet` |
| Bungee | phase vocoder on grains (~100/s) | open version "good quality"; Pro claims crisper transients | yes, per grain; reverse and zero speed too | ? (grains every ~10 ms) | MPL-2.0 (Pro commercial) | active | none | only Bungee Pro (commercial WASM) |
| Browser `playbackRate` + `preservesPitch` | Chrome WSOLA, Firefox SoundTouch | time-domain echo; Firefox mutes outside 0.25–4 | yes | browser internal | — | built in | — | all browsers (`preservesPitch` baseline since Dec 2023) |
| élastique, Serato, Superpowered | commercial | in Bungee's comparison as references | ? | ? | commercial | — | — | not checked |
| PaulStretch | extreme stretch | not for practice | — | — | GPL | — | — | — |

Sources: [rubberband-technical](web/rubberband-technical.txt), [rubberband-integration](web/rubberband-integration.txt), [rubberband-home](web/rubberband-home.txt), [rubberband-v4-announcement](web/rubberband-v4-announcement.txt), [rubberband-web-readme](web/rubberband-web-readme.txt), [soundtouch-readme](web/soundtouch-readme.txt), [soundtouchjs-readme](web/soundtouchjs-readme.txt), [bungee-readme](web/bungee-readme.txt), [mdn-playbackrate](web/mdn-playbackrate.txt), [mdn-preservespitch](web/mdn-preservespitch.txt), [chromium-audio-renderer-algorithm](web/chromium-audio-renderer-algorithm.txt), [gecko-audiostream](web/gecko-audiostream.txt). Python packages (pedalboard, pyrubberband, librosa, audiotsm, pytsmod): [tempo-python.md](tempo-python.md).

## Bungee's tonal test, read with care

[bungee-compare](web/bungee-compare.txt) stretches synthetic tones and reports pitch error, level and noise. At 0.56x on a 1637 Hz sine the noise is: SoundTouch −98 dB, Bungee −52, Signalsmith −47, Rubber Band −39, élastique −35 (lower is better). On a 227 Hz sine: SoundTouch −98, Rubber Band −70, Bungee −55, Signalsmith −51. Rubber Band's level is always −2.5 dB, which is a gain offset, not distortion.

Why this doesn't decide: a steady sine repeats exactly, which is the ideal case for WSOLA (it can always find a perfectly matching piece). Music has attacks, chords and voices, where WSOLA's weakness (echo, doubled attacks) shows. The page also has listening samples (drums, jazz, pop, voice) for every library at 0.56x. Listening to those is a cheap first check before our own test.

## Open questions, answered

- **What is R3's method?** Not published. The technical notes cover R2 only ("R3 has some technical differences"), and the v3.0 announcement says only "an entirely new processing engine". The GPL source is the only full description.
- **What do browsers use under `playbackRate`?** Chrome: WSOLA (`AudioRendererAlgorithm`). Firefox: SoundTouch through `RLBoxSoundTouch` (sandboxed), with sequence, seek-window and overlap times as prefs. Safari: not checked (AVFoundation, closed).
- **Is there a maintained WASM build?** Signalsmith Stretch (official, MIT), SoundTouchJS (active, MPL-2.0), rubberband-web (small third-party project, GPL via Rubber Band, last activity not checked), Bungee Pro (commercial only).
- **Does `OptionChannelsTogether` help?** Rubber Band's own advice: "If CPU power is not a major limitation, add OptionEngineFiner | OptionChannelsTogether". It keeps the stereo image steadier. We don't set it yet: a one-line change to try by ear.
- **Published listening comparisons at 0.5x?** Only Bungee's page (samples at 0.56x, no scores). The TSM review paper (Driedger & Müller 2016, MDPI) returned 403 to both `webfetch.py` and WebFetch; not read.

## Then: listening test (T31)

Render the same 20 s excerpt (one with drums, one solo melody) at 0.5x, 0.75x and 1.3x into `data/scratch/tempo-tests/`, with Rubber Band R3, R3 + ChannelsTogether, R2, Signalsmith (python-stretch) and the browser's `playbackRate` (recorded from a test page). Listen blind, note echo, smear, warble and stereo width, and write the result into T8's `docs/tempo-decision.md`.
