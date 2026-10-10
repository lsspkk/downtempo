# Stretch theory: slower without lower

**Summary**: Background, no decisions. Slower without lower: resampling lowers pitch; OLA, WSOLA and the phase vocoder keep it, each with its typical artefact.

How a recording can play at 0.5x and keep its pitch, explained with high-school math. Next: [stretch-app-flow.md](stretch-app-flow.md).

Running example in all `stretch-*` files: 44 100 samples/s, a 440 Hz sine (the note A), speed 0.5x.

## Sound as numbers

A microphone measures air pressure. The computer stores it as a number, 44 100 times a second (the *sample rate*). A pure tone is a sine wave: it repeats every *period* `T`.

```
 +1 |   .-.       .-.          one period T = 100.2 samples
    |  /   \     /   \         (440 Hz at 44 100 samples/s)
  0 |-/-----\---/-----\---
    |/       \_/       \_
 -1 |
```

Music is many sines at once (notes, overtones) plus noise and short clicks (drum hits, plucks).

- **In math:** `f = 1 / T`; `T = 44 100 / 440 = 100.2 samples`.

## Slower = lower (resampling)

The simplest slow-down plays the samples more slowly: every sample lasts twice as long. That makes every period twice as long, so the pitch halves (one octave down). This is a tape or record played at the wrong speed.

```
original  /\/\/\/\     4 periods in 1 s   -> 440 Hz
0.5x      /  \  /  \   2 periods in 1 s   -> 220 Hz (an octave lower)
```

Time and pitch are tied together here. Every method below exists to untie them.

- **In math:** `new_f = f × speed`, so 440 Hz × 0.5 = 220 Hz.
- **You hear when it fails:** the "chipmunk" (fast) or "giant" (slow) voice. This is exactly the method's effect, not a bug.

## Cut, spread, glue (OLA)

Idea: don't slow down the wave itself. Cut the recording into short overlapping pieces (*frames*, about 20–100 ms), and lay them down further apart than they were taken. Each piece keeps its own periods, so it keeps its pitch. There are just more pieces per second of output.

```
input   [1111][2222][3333]          taken every Ha samples (analysis hop)
output  [1111]    [2222]    [3333]  placed every Hs samples (synthesis hop)
        overlaps are faded (window) and added: Overlap-Add
```

- **In math:** `stretch α = Hs / Ha`. At 0.5x, `α = 2`, for example `Ha = 512`, `Hs = 1024`.
- **You hear when it fails:** warble and roughness. Where two pieces overlap, their waves are out of step and partly cancel (picture below).

```
piece 1 ends  ...\/\/\/          piece 2 starts  /\/\/\...
added:  peaks meet troughs -> volume dips, a "flutter" many times a second
```

## Match before gluing (WSOLA)

WSOLA (Waveform Similarity OLA) fixes the out-of-step overlap in the time domain. Before placing the next piece, it slides the piece a little (within a *seek window* of a few ms) to the spot where it looks most like what is already there, then glues it. The waves now line up.

```
already out: ...\/\/\/
try offsets:      /\/\  /\/\  \/\/   <- pick the best match (highest similarity)
```

This is cheap and very clean for one voice or one instrument. In full music, the best spot for the bass is not the best spot for the hi-hat. SoundTouch works this way (Chrome's `playbackRate` is believed to as well; T4 checks); SoundTouch's README notes an "echoing" artifact when slowing down, tuned by its sequence and seek-window lengths ([soundtouch-readme](web/soundtouch-readme.txt)).

- **In math:** pick the offset `k` that maximizes the similarity `Σ old[n] × new[n + k]` (the sum of products, called cross-correlation).
- **You hear when it fails:** echo or doubling at 0.5x, a "drifting" tone, stutter on dense mixes.

## Work on frequencies (phase vocoder)

The phase vocoder works in the frequency domain. A *Fourier transform* (FFT) takes one frame and answers: which sines are in here, how strong, and at which point of their cycle (the *phase*). Treat it as a black box that turns a frame into a list of `(frequency, strength, phase)`.

```
frame --FFT--> 220 Hz strong, phase 30°  |  440 Hz medium, phase 200°  | ...
```

To stretch, the frames are placed further apart (like OLA). Each sine's phase is then *advanced* by exactly how far that sine would have turned in the new, longer gap. So every sine continues smoothly from frame to frame. Then the inverse FFT turns the lists back into sound.

- **In math:** `new_phase = old_phase + 2π × f × Hs / 44 100`. Example: a 440 Hz sine over `Hs = 1024` samples turns `440 × 1024 / 44 100 = 10.2` cycles; keep the `0.2`.
- **You hear when it fails:** "phasiness": a washed, distant sound like a room or a chorus, and soft, smeared attacks. Each frequency stays in step with itself *over time* (horizontal coherence), but neighbouring frequencies of one note drift apart (vertical coherence) ([wiki-phase-vocoder](web/wiki-phase-vocoder.txt)).

## Keep notes and drums sharp (phase locking, transients)

Two classic repairs:

- **Phase locking** (Laroche & Dolson, 1999): the FFT bins around one peak belong to one sine, so their phases are locked to the peak's phase. This brings back vertical coherence and clarity.
- **Transient handling**: a drum hit is a short click, not a sine. Spreading it over a long frame smears it into a "fwump". Detectors find hits, and at a hit the phases are *reset* to the original ones, so the attack stays crisp. Rubber Band's R2 engine does exactly this: "a phase vocoder with phase resets on percussive transients … and a 'lamination' method to improve vertical phase coherence" ([rubberband-technical](web/rubberband-technical.txt)).

```
input  ____|\____        |  = drum hit
plain  ___/‾‾\___        smeared over a frame
reset  ____|\____        phases reset at the hit: sharp again
```

- **In math:** at a detected hit, `new_phase = original_phase` instead of the advanced one.
- **You hear when it fails:** flams (doubled hits) or soft, "underwater" drums.

## Big and small windows at once (multi-resolution)

One frame size can't suit everything. Long frames (about 90 ms) separate low notes well but smear hits. Short frames (about 10 ms) keep hits sharp but blur pitch. Newer engines analyse with several sizes and use, per frequency region and moment, the one that fits. Rubber Band's R3 ("finer") engine is the newer, higher-quality design; its notes only say R3 "has some technical differences" from R2, so how multi-resolution it is is a question for [stretch-research.md](stretch-research.md). Bungee and Signalsmith Stretch are other modern frequency-domain designs ([bungee-readme](web/bungee-readme.txt), [signalsmith-stretch-readme](web/signalsmith-stretch-readme.txt)).

- **In math:** frequency resolution `≈ 44 100 / window_size`: 2048 samples gives 21.5 Hz steps but a 46 ms blur in time; 512 gives 86 Hz steps but only a 12 ms blur.
- **You hear when it fails:** much less often. Typically a slight graininess at extreme ratios, at a higher CPU cost.

## Pitch shift = stretch + resample

To change pitch but keep the tempo, stretch time by `r` and then resample by `r`. Resampling changes speed and pitch together, so the duration comes back to the original and only the pitch moved. Rubber Band and SoundTouch both do this ([rubberband-technical](web/rubberband-technical.txt), [soundtouch-readme](web/soundtouch-readme.txt)).

- **In math:** one semitone is `r = 2^(1/12) ≈ 1.059`; +3 semitones is `r ≈ 1.19`.

## Summary

| Method | Idea | Good at | Typical artifact | Used by |
|---|---|---|---|---|
| Resampling | play samples slower or faster | exact, free | pitch moves with speed | tape, `preservesPitch = false` |
| OLA | cut, spread, glue | trivial code | warble, flutter | teaching only |
| WSOLA | slide each piece to the best match first | speech, solo instruments, low CPU | echo at 0.5x, drift on dense mixes | SoundTouch (Chrome? T4) |
| Phase vocoder | stretch in frequency domain, advance phases | sustained tones, polyphony | phasiness, smeared hits | classic tools |
| + phase locking, transients | lock bins to peaks, reset at hits | music with drums | flams when a detector misses | Rubber Band R2 |
| Modern frequency-domain (multi-resolution and similar) | several window sizes, smarter phases | everything, 0.5x included | rare graininess; CPU | Rubber Band R3, Bungee, Signalsmith (details: research) |

Sources: [wiki-audio-time-stretching](web/wiki-audio-time-stretching.txt), [wiki-phase-vocoder](web/wiki-phase-vocoder.txt), [rubberband-technical](web/rubberband-technical.txt), [soundtouch-readme](web/soundtouch-readme.txt).
