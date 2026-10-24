# Todo

Tasks grouped under the idea they belong to ([ideas.md](ideas.md)). `- [ ] T<n> task`. Top = next. Follow-up to `T<n>`: `T<n>.<k>`, e.g. T11.1.
When done: delete the line here and add it to `log.md`.

Order (the user's call, 2026-10-11): cores for downloading (done), projects and the settings file first; then song grouping; then the project screen, where all of them get their UI (sources first, sorting after). Browser player and Google Drive wait under **Later**.

### Project screen

Plan: [project-screen.md](project-screen.md). Replaces the Sources dialog (T46 done by T84, T61–T64 reworked).
**State (2026-10-11)**: built: sorting by click, key and drag, the song edit box, previews, the sources with Add folder from a pasted link (also the first start), the ☰ main menu with Export / Import, Project settings with Change link, the song list's Project ⟳ top (T111, T61–T63, T97, T94–T96, T101, T82, T67, T114, T116, T118, T120). What it is and how to add to it: [project-screen.md](project-screen.md#built-so-far). Next: the user's try-outs below (all can start now).


- [ ] T65 Manual test by the user on a fresh data folder (`DOWNTEMPO_DATA`): first start with a real link, sign-in, folder picker, cancel midway, unplug the network, a changed file on the server, remove a source; findings become tasks
- [ ] T99 Manual test by the user of sorting: the real project plus a made-up messy folder (scratch source): drag, Move to…, merge, rename, undo, previews, an update bringing a new file; findings become tasks
- [ ] T83 Manual test by the user: two projects, switch while playing, export one and import it as a new project on a 2nd `DOWNTEMPO_DATA`; findings become tasks
- [ ] T68 Manual test by the user: export, email it to yourself, import on another computer (or a 2nd `DOWNTEMPO_DATA`), download; findings become tasks

### Tap tempo

- [ ] T219 Manual test by the user: tap along a recording at 100 % and at a slower tempo (G or Tap in the tempo row: from the 4th tap the speed follows), compare with a metronome app; is the average steady enough; findings become tasks

### Tempo detection

- [ ] T231.1 Manual test by the user of the Python player's tempo (T231): Full controls' tabs at 1280×720, the recording dropdown (↑/↓, Enter, Esc), Tap along another version (G, 4 taps), Play at and X (stays on across recordings), the metronome button (■ while it ticks), Simple and Sheet only (the toasts); findings become tasks
- [ ] T232.7 Manual test by the user of T232.1–T232.6 (`npm run dev`, desktop and phone width): `75 BPM (TAP) (metronome) ○ Play at 100`, the BPM strip, the phone's BPM page, G and X, the recording menu; findings become tasks
- [ ] T221.3 Iterate `scripts/tempo_test.py` with the user: more files, piece length, BPM range, folding half / double; then pick the method for the player (and essentia.js for the browser) per [tempo-detection.md](tempo-detection.md)

### Loop editor

- [ ] T44 Manual UX test by the user on the real laptop (mouse and trackpad): `E`, click start / end with a two-finger swipe between, pinch zoom in the native window (unknown whether Qt WebEngine passes it), ⠿ handles, Hear end, Undo, Esc back; findings become tasks

### Browser player

Earlier (2026-10-11): find out first whether a browser version can sign in and get the files at all, by research, then small test pages on GitHub Pages that the user tries. Each test page says clearly that it is only for testing a browser version of Downtempo. No real links, names or files in the repo: the user pastes a link in the page.

MVP (the user's call, 2026-10-13, after T133 passed): a React + TypeScript app built by Vite with Tailwind, published by the Pages workflow; proof that the whole app fits in a browser. Has: projects, settings, download, song list, player with slow-down (plain `playbackRate`, pitch kept), PDF viewer. Not: loop editor, view modes, most of the Python player's controls. Built (T135–T146), grown and tried by the user (T147–T194): [browser-app.md](browser-app.md). Tempo by Signalsmith Stretch: built and tried (T4).

- [ ] T217.4 Manual test by the user of browser compression per [compress.md](compress.md#browser-app-built-t217): a project with wavs downloaded before (they turn into mp3s on ⟳, loops and tempo kept), a new wav on the server, Stop midway, the storage before and after; findings become tasks
- [ ] T31.1 Blind listening by the user per [stretch-research.md](stretch-research.md#then-listening-test-t31): `data/scratch/tempo-tests/` (made by `uv run python scripts/stretch_test.py <files>`: pick one with drums and one solo melody), note echo, smear, warble and stereo width per letter, then open `key.json`
- [ ] T8 Compare Python vs browser by ear (uses T31); write the pick and why into `docs/tempo-decision.md`

## Later

Not now (the user's call, 2026-10-11).

### Downloaders

- [ ] T132.1 Google Drive test pages: tests 3–5 of [browser-research.md](browser-research.md#what-t132-tests) on the same page, after the user's Google Cloud setup there (skipped for now, the user's call 2026-10-13)

- [ ] T14 Google Drive research: download all mp3/pdf from an "anyone with the link" folder (Drive API v3 + API key vs OAuth vs `gdown`); what credentials are needed, and whether it fits the `Provider` protocol in [blocks.md](blocks.md#apis) (listing with size and change time, download URL + headers) → `docs/gdrive.md`
- [ ] T17 `src/downtempo/downloaders/gdrive.py` per T14, after T56: a `Provider` (`owns`, `connect`, `open`, `files`), registered as `gdrive`; usage in `docs/gdrive.md`
