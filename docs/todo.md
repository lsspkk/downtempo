# Todo

Small tasks, each under an idea. `- [ ] T<n> (I<n>) task`. Top = next.
When done: delete the line here and add it to `log.md`.

- [ ] T9 (I2) Define the `data/songs.json` format (song: `title`, `collection`, `audio: [{label, path}]`, `pdf: [path]`, paths relative to `data/`) and document it in `docs/songs.md`; add a tracked `data/songs.example.json` with 1–2 made-up songs
- [ ] T10 (I2) `uv run downtempo catalog` (`src/downtempo/catalog.py`): scan `data/downloads/<collection>/` into `data/songs.json` (one song per folder, keeps hand-edited labels on re-run); quirks in `data/material.md`
- [ ] T11 (I3) `frontends/nicegui/app.py` step 1: NiceGUI window with Play/Stop; plays the first mp3 of the first song in `data/songs.json` from Python via `sounddevice` (no tempo yet)
- [ ] T12 (I3) `frontends/nicegui/app.py` step 2: NiceGUI tempo slider 0.5–1.3x (0.05 steps) feeding the T5 time-stretcher in the audio callback; pitch kept, changes while playing
- [ ] T13 (I3) `frontends/nicegui/app.py` step 3: NiceGUI song selector listing the songs from `data/songs.json`; picking one stops playback and loads its first audio
- [ ] T4 (I4) Browser research: `<audio>` `playbackRate` + `preservesPitch`, SoundTouchJS, Rubber Band WASM; quality at 0.5x, browser support → `docs/tempo-browser.md`
- [ ] T6 (I4) `frontends/browser/index.html` MVP: load `data/songs.json`, song dropdown, tempo slider 0.5–1.3x; served by `uv run downtempo serve`, which exposes only the page, the catalog and its files (not the project root: `.env`)
- [ ] T8 (I4) Compare Python vs browser by ear; write the pick and why into `docs/tempo-decision.md`
- [ ] T14 (I7) Google Drive research: download all mp3/pdf from an "anyone with the link" folder (Drive API v3 + API key vs OAuth vs `gdown`); what credentials are needed → `docs/gdrive.md`
- [ ] T17 (I7) `src/downtempo/downloaders/gdrive.py` per T14, registered as `gdrive` in `DOWNLOADERS`; follows the downloader contract in `docs/architecture.md`; usage in `docs/gdrive.md`
