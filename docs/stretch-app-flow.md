# Stretch app flow: from mp3 to speaker

**Summary**: Built. How the player streams: blocks through Rubber Band into a small queue (≈ 0.14–0.28 s delay), seeks tagged by generation, short fades at the loop seam and on pause.

What the Python player does, step by step, while you play and move the tempo slider. Code: [frontends/nicegui/engine.py](../frontends/nicegui/engine.py). Previous: [stretch-theory.md](stretch-theory.md). Next: [stretch-rubberband.md](stretch-rubberband.md).

## The picture

```
 song.mp3 --soundfile--> numbers in memory (2 × 4 200 000 for a 95 s stereo song)
                                  |
            worker thread         v
   +--------------------------------------------------------------+
   | read 1024 samples from the play position (wrap at loop B)    |
   | set time_ratio = 1 / speed, pitch_scale = 2^(semitones/12)   |
   | Rubber Band: process(block) -> retrieve() stretched audio    |
   | tag it: Chunk(generation, song position, speed, samples)     |
   +--------------------------------------------------------------+
                                  |  queue: at most 6 chunks
                                  v
            audio callback (sounddevice, its own thread, one buffer at a time)
   copy chunks into the speaker buffer, ramp the volume, note the position
                                  |
                                  v
                               speaker

   UI thread (NiceGUI): slider, keys, waveform clicks
   -> only sets engine.speed / semitones / loop, or calls seek(), play(), pause()
   <- reads engine.position 10 times a second for the clock and playhead
```

The callback must never wait or compute much: if it is late, you hear a click or a gap. So the heavy work (Rubber Band) runs in the worker, and the callback only copies.

- **In math:** at 0.5x each 1024-sample input block becomes about 2048 output samples (`out ≈ in × time_ratio`).

## Blocks and the queue: why a change takes a moment

The worker stays ahead of the speaker by the queue (6 chunks). A new tempo applies to the *next* block the worker reads, so you hear it after the queued audio has played.

```
 queue  [c1][c2][c3][c4][c5][c6] -> speaker     new speed starts at c7
```

- **In math:** delay ≈ `6 × 1024 × time_ratio / 44 100`: 0.14 s at 1.0x, 0.28 s at 0.5x. Rubber Band adds its own start delay of 2048 samples (46 ms), see [stretch-rubberband.md](stretch-rubberband.md).
- **You hear when it fails:** a bigger queue = sluggish slider. A smaller queue = dropouts when the computer is busy.

## Seek: generations

Clicking the waveform must stop the old audio at once, even though old chunks are still in the queue. Every `seek()` raises a *generation* number. The worker restarts Rubber Band at the new place (`reset()`, silence pad, drop the start delay) and tags new chunks with the new generation. The callback throws away chunks with an old generation.

```
 queue  [g4][g4][g5][g5]   callback on generation 5: skips both g4 chunks
```

## Loop seam: a short fade

At B the worker jumps back to A and keeps feeding the same stretcher, so the loop has no gap. The last 256 samples before B fade out and the first 256 after A fade in (5.8 ms each), so the jump doesn't click. An optional pause between repeats is a chunk of silence. The worker marks the first chunk after a jump, and the callback counts repeats when it plays that chunk; the step-up trainer uses the count.

```
 ... B]  fade \   (optional silence)   / fade  [A ...
```

## Pause: a volume ramp

Stopping in the middle of a wave makes a click. On pause the callback lowers the volume to 0 over one callback buffer (its size is chosen by the sound system: a few ms to a few tens of ms), then stops taking chunks, so the queue stays exactly where you paused. Play ramps the volume back up.

- **In math:** `out[n] = sample[n] × g[n]`, with `g` going linearly from the current volume to 0.
- **You hear when it fails:** a click at pause or play.

## Position on screen

Each chunk knows the song position of its first sample and its speed (`step`). The callback sets `position = start + samples_played × step`, so the playhead follows what you *hear*, not what the worker has read ahead. During the pause between repeats `step = 0`, so the playhead waits at A.

- Checked (T12.1): the output lines up with the original audio within one callback buffer.

## Loading a song

`load()` decodes the whole mp3 into memory (about 0.1 s, about 30–50 MB for a 4-minute song), computes 1000 waveform peaks, starts a paused stream at the file's sample rate and a new worker. Loads run one at a time (a lock). Two at once once dropped a running stream without closing it, and the process aborted (T13.4).
