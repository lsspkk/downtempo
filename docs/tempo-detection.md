# Tempo detection

**Summary**: research T220, T221.1; test tool T221.2; a first method in the Python player (T225: Percival's median over the pieces, half and double folded, shown as an estimate the user settles; `src/downtempo/tempo.py`). The player could find a recording's BPM by itself and show it next to tap tempo. **Pick: Essentia**, because the same C++ algorithms run in Python (`essentia`) and in the browser (`essentia.js`, WebAssembly), so both apps get the same numbers. **Principle: detect once on the original file, in pieces, and show the BPM × speed**; the slowed or sped-up sound is never analysed. The first run on 5 real recordings found the tempo, but often at half or double. That is the part to solve next with the test tool (`scripts/tempo_test.py`).

## The principle

- **The original, never the stretched sound.** Rubber Band changes the time scale exactly, so a recording at 120 BPM played at 75 % is at exactly 90 BPM. The player detects once per recording, in a background job, remembers the result with the recording, and shows original × speed. The number updates instantly with ←/→, the slider and the step-up trainer. Tap tempo already does the reverse (tapped ÷ speed = "N at 100 %").
- **In pieces, then a vote.** The recording is cut into pieces (now 10 × 10 s spread over the song). Each piece gets a BPM, and the median is the answer. Pieces that come out at half, double, 3:2 or 4:3 of it show how sure the answer is, and a drifting rehearsal take shows as a range.
- **The user settles half or double.** No detector knows whether a 2/4 tune "is" 80 or 160. ×2 / ÷2 next to the number, and the user's tap, decide. The choice is remembered with the recording.

## Why Essentia (T221.1)

| | Python | Browser | Notes |
|---|---|---|---|
| **Essentia** | `essentia` ([pypi-essentia-json](web/pypi-essentia-json.txt)): [RhythmExtractor2013](web/essentia-rhythm-extractor.txt) (BPM, beats, confidence), [PercivalBpmEstimator](web/essentia-percival-bpm.txt) (BPM by autocorrelation) | `essentia.js` 0.1.3 ([npm-essentia-js](web/npm-essentia-js.txt)) has both, plus `LoopBpmEstimator` ([essentiajs-api](web/essentiajs-api.txt)) | **pick**: the same code on both sides. AGPL-3.0, like the repo since T222. Python wheels are dev builds (`2.1b6.dev…`); the last one for Python 3.12 on Linux is `dev1389` (2025-07), which is pinned |
| librosa | `feature.tempo`, `beat.track` ([librosa-feature-tempo](web/librosa-feature-tempo.txt)) | none | Python only |
| web-audio-beat-detector | none | `guess` / `analyze` on an AudioBuffer, MIT ([npm-web-audio-beat-detector](web/npm-web-audio-beat-detector.txt)) | browser only; a port to Python would be possible but means two codes to keep alike |
| aubio | not for current Python versions ([pypi-aubio-json](web/pypi-aubio-json.txt)) | none | dead since 2019 |

## The test tool (T221.2)

`uv run python scripts/tempo_test.py`. Its settings are constants at the top: `DOWNLOADS`, `FILES`, `PIECES`, `PIECE_SECONDS` and the BPM range. It prints a table per file (each piece's BPM from both detectors, Rhythm's confidence, the medians, and how many pieces are the same, half, double and so on). Everything is saved as JSON in `data/scratch/tempo-detection/`. 5 files take about 10 s.

Note: both algorithms keep state between calls in Essentia's Python API, so the tool calls `reset()` before each piece. Without it, Percival returned the first piece's BPM for every piece.

## First run (2026-10-24, 5 recordings, 10 × 10 s)

- **Same tempo, different octave**: on 2 of 5 files Percival said about 80 and Rhythm said about 161 (half and double). On the other 3 they agreed within 2 BPM.
- **Rhythm flips between octaves within a song**: 4 of 10 pieces at 80 and 6 at 161 in one reel, 4 at 178 and 6 at 90 in another.
- **Percival is steadier but jumps 4:3** (90 → 120 in 3 pieces of one song).
- **Rehearsal takes drift**: one take went from 88 to 100 over the song, and both detectors saw it.
- Mean confidence was 2.6–3.0, just under Essentia's "good" level of about 3.

So the median of pieces with the octave folded (half and double counted as the same) gives a steady answer. Which octave to show is the open question for the next round.

## Next

T221.3 in [todo.md](todo.md#tempo-detection): iterate with the user on the settings (more files, piece length, BPM range, octave folding). Then decide the method for the player, and give the browser app the same through essentia.js.
