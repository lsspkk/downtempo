# Compression

**Summary**: requirements for keeping downloaded wavs as mp3, for both apps. Status: built in the Python app (T215, T216) and in the browser app (T217.1–T217.3, mp3 by Mediabunny's LAME extension chosen in T233); the browser's manual test T217.4 is next.

## Why

Practice needs no hi-fi, and a wav takes about 10x the space of a 128 kbit/s mp3.

## Requirements

1. **Every wav is kept as an mp3** with the same name: the server's `Song.wav` is `Song.mp3` on disk, at about 128 kbit/s.
2. **Except when the server has both**: if `Song.mp3` sits next to `Song.wav`, the wav stays a wav, so the two never clash.
3. **New and changed wavs** are downloaded, encoded, and only the mp3 is kept. The mp3 gets the server's change time and counts as up to date by that time alone, because its size can't match the wav's.
4. **Wavs already downloaded** are encoded on the next fetch, without downloading them again, and the wav is then deleted. This is the only file a fetch ever deletes.
5. **Everything that names the file follows it** in the same step: the sorting, the new marks and the practice memory (chosen recording, position, loops). Nothing looks new or unsorted because of compression.
6. **The file id is the stored name** (`band:Rehearsal/take3.mp3`), so a project and its settings file look the same on every computer and in both apps.
7. **Written whole or not at all**: the mp3 goes through `.part`. A cancel leaves the wav or nothing. A wav that can't be encoded stays a wav and is tried again on the next fetch.
8. **Left alone**: wavs in skipped folders and wavs the server no longer has.
9. **Shown like a download**: "Compressing 2 of 7: take3.wav"; the browser says it before the first download too ("Then the 7 wav files are compressed to mp3 on this device", T243).

## Python app

`src/downtempo/compress.py` (`stored_as`, `to_mp3` through soundfile, no ffmpeg) is used by `sync.py`. `renaming.py` moves the file ids. `COMPRESS_WAV` and `MP3_QUALITY` live in `config.py`. Turning compression off is only for testing, because ids then differ from computers that compress.

## Browser app (built, T217)

`core/compress.ts` (`storedAs`, `toMp3`), `core/plan.ts` (a wav's stored key, `compress` for wavs already here, an mp3 made from a wav current by its time), `core/download.ts` (encode after the download, wavs on the device first, the result line "2 wavs made into mp3"), `core/practice.ts` `moveRecording`. Checked: `npm run build`, the tests (plan and `storedAs`), and a 3 s wav encoded in a Chromium page (48.6 kB, about 130 kbit/s, 0.3 s with loading). Not yet tried with OneDrive: T217.4.

As built: a downloaded wav is held in memory whole while it is encoded (Mediabunny reads a Blob); `files.save` writes through the browser's own swap file (`createWritable`), so the mp3 is written whole or not at all, as `.part` does in Python; the wav is removed only after the mp3 and the project's list are written; what was planned follows.

**Encoder (T233)**: **mp3**, by [Mediabunny](web/mediabunny-formats.txt) with its [`@mediabunny/mp3-encoder`](web/mediabunny-mp3-encoder.txt) extension: a SIMD build of LAME 3.100 in WASM, worker and WASM bundled in one file (no paths to set up), about 130 kB gzipped, about 55× real time, MPL-2.0. Mediabunny reads WAVE and writes MP3 (`Conversion` from a `BlobSource` to `Mp3OutputFormat`); the encoder is registered only when the browser can't encode mp3 itself (`canEncodeAudio('mp3')`, which browsers' WebCodecs usually can't).

Why mp3 and not Opus or AAC: requirement 6, the file id is the stored name (`take3.mp3`) in both apps, so another format would make the projects and settings files differ from the Python app's (which writes mp3 through soundfile). Opus would also be smaller, but WebCodecs' encoders depend on the browser (Firefox has Opus only, no AAC; Safari unclear) ([mediabunny-formats](web/mediabunny-formats.txt)), and the WASM LAME works the same everywhere. Not chosen: ffmpeg.wasm (tens of MB for one codec), old lamejs ports (unmaintained, slower than SIMD LAME).

**Plan**, the requirements above in `core/`:
- **T217.1** `core/compress.ts`, pure: `storedAs(path, siblings)` like the Python `stored_as` (wav → mp3 unless the server has the mp3 too); `ui`-free `toMp3(wav: Blob, signal): Promise<Blob>` at about 128 kbit/s, Mediabunny and the encoder loaded with the first wav only (dynamic import, like essentia.js).
- **T217.2** Download: `plan.ts` maps a server wav to its stored key and counts a compressed copy as current by the change time alone; `download.ts` fetches a wav, encodes it, saves only the mp3 through `.part` (a stop leaves the old file or nothing); a wav that can't be encoded is kept as a wav and tried again next time; the status says "Compressing 2 of 7: take3.wav"; English and Finnish.
- **T217.3** Wavs already on the device: on the next download they are encoded from the device (not downloaded again), the mp3 saved, the wav removed, and everything that names the file moves with it in the same step: the project's `files`, the practice memory (chosen recording, position, regions, tempos) and the last song. Wavs in skipped folders and wavs the server no longer has stay.
- **T217.4** The user's manual test: a project with wavs downloaded before (they turn into mp3s on ⟳, loops and tempo kept), a new wav on the server, Stop midway, the storage shown before and after.
