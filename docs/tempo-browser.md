# Tempo and loop in the browser: what to use instead of `playbackRate`

**Summary**: Researched (T4) from saved pages; built (T4.1–T4.5) and tried by the user: sounds great. Pick: **Signalsmith Stretch Web** (npm `signalsmith-stretch`, MIT, AudioWorklet) in place of the `<audio>` element's `playbackRate`. It also fixes the loop: the loop runs inside the audio, sample-accurate, instead of our `requestAnimationFrame` jump back. SoundTouchJS is the fallback. Status: built in the browser app; T31 / T8 compare it with Python.

## What is poor now

[audio.ts](../frontends/browser/src/ui/player/audio.ts) plays an `<audio>` element with `playbackRate` and `preservesPitch`:

- Quality: the browser's own stretch (Chrome WSOLA, Firefox SoundTouch; [stretch-research.md](stretch-research.md)), time-domain, so slow music gets an echoing, "warbling" sound. No setting to tune.
- Loop: the end is checked once per animation frame (about 16 ms, and not at all in a background tab), then `currentTime` is set to the start. That is an audible gap or click and an end that drifts by a frame at any speed.

## The better way

Signalsmith Stretch Web ([npm readme](web/signalsmith-stretch-npm-readme.txt), [product page](web/signalsmith-stretch-web-demo.txt), [package data](web/signalsmith-stretch-npm-package.txt)):

- `SignalsmithStretch(audioContext)` gives an `AudioNode` that you connect to `audioContext.destination`.
- Load the song once: decode the file to channel arrays (`decodeAudioData`) and `stretch.addBuffers([left, right])`.
- `stretch.schedule({ active: true, rate: 0.6, input: 12.3, loopStart: 10, loopEnd: 20 })`: rate changes live, `semitones` is there for a later pitch control, and `loopStart` / `loopEnd` loop inside the node (equal values = no loop). `stretch.inputTime` and `setUpdateInterval(seconds, callback)` give the position for the screen and the loop editor.
- MIT, official WASM release, npm 1.3.2 (June 2025, first release February 2025), so it is current but young.
- Cost: no `<audio>` element. The whole decoded song sits in memory (about 100 MB for a 5-minute stereo song at 44.1 kHz; fine on a laptop, to check on a phone) and `audio.ts`'s seek, play and time have to be rewritten against the node. wavesurfer.js can still draw the waveform from the same file with `peaks` or its own decode, without `media`.
- Its README says the stretch sounds best between 0.75x and 1.5x; 0.5x is the case to listen to.

## Alternatives

| Option | Why / why not |
|---|---|
| **Signalsmith Stretch Web** | Pick: best quality candidate that is MIT, live rate, built-in loop. |
| SoundTouchJS ([readme](web/soundtouchjs-readme.txt)) | Same WSOLA family as the browser's own stretch, so little better than now; fallback if Signalsmith fails on some browser. |
| rubberband-web ([readme](web/rubberband-web-readme.txt), [npm](web/rubberband-web-npm.txt)) | Rubber Band R2/R3 quality (what the Python player uses), but a small project, last npm release 0.2.0 in October 2024, GPL-2.0 (fine for a personal tool, blocks any closed use), and only pitch shift in its README. Not first choice. |
| Keep `playbackRate`, fix only the loop | Cheap: loop with a `timeupdate`-free scheduler or a decoded `AudioBufferSourceNode` loop. Does not touch the sound. |

## Open (for T31 / T8)

- Safari: `AudioWorklet` exists there, but whether Signalsmith's WASM worklet runs well on iOS was not verified; test on the user's iPhone.
- Memory on phones and start delay (decoding a whole song) against streaming with `addBuffers` in pieces.
- Blind listening at 0.5x / 0.75x / 1.3x, per [stretch-research.md](stretch-research.md#then-listening-test-t31).
