# Todo

Tasks grouped under the idea they belong to ([ideas.md](ideas.md)). `- [ ] T<n> task`. Top = next. Follow-up to `T<n>`: `T<n>.<k>`, e.g. T11.1.
When done: delete the line here and add it to `log.md`.

Order (the user's call, 2026-10-11): cores for downloading (done), projects and the settings file first; then song grouping; then the project screen, where all of them get their UI (sources first, sorting after). Browser player and Google Drive wait under **Later**.

### Tempo detection

- [ ] T221.3 Iterate `scripts/tempo_test.py` with the user: more files, piece length, BPM range, folding half / double; then pick the method for the player (and essentia.js for the browser) per [tempo-detection.md](tempo-detection.md)

### Browser player

Earlier (2026-10-11): find out first whether a browser version can sign in and get the files at all, by research, then small test pages on GitHub Pages that the user tries. Each test page says clearly that it is only for testing a browser version of Downtempo. No real links, names or files in the repo: the user pastes a link in the page.

MVP (the user's call, 2026-10-13, after T133 passed): a React + TypeScript app built by Vite with Tailwind, published by the Pages workflow; proof that the whole app fits in a browser. Has: projects, settings, download, song list, player with slow-down (plain `playbackRate`, pitch kept), PDF viewer. Not: loop editor, view modes, most of the Python player's controls. Built (T135–T146), grown and tried by the user (T147–T194): [browser-app.md](browser-app.md). Tempo by Signalsmith Stretch: built and tried (T4).

- [ ] T31.1 Blind listening by the user per [stretch-research.md](stretch-research.md#then-listening-test-t31): `data/scratch/tempo-tests/` (made by `uv run python scripts/stretch_test.py <files>`: pick one with drums and one solo melody), note echo, smear, warble and stereo width per letter, then open `key.json`
- [ ] T8 Compare Python vs browser by ear (uses T31); write the pick and why into `docs/tempo-decision.md`

## Later

Not now (the user's call, 2026-10-11).

### Downloaders

- [ ] T132.1 Google Drive test pages: tests 3–5 of [browser-research.md](browser-research.md#what-t132-tests) on the same page, after the user's Google Cloud setup there (skipped for now, the user's call 2026-10-13)

- [ ] T14 Google Drive research: download all mp3/pdf from an "anyone with the link" folder (Drive API v3 + API key vs OAuth vs `gdown`); what credentials are needed, and whether it fits the `Provider` protocol in [blocks.md](blocks.md#apis) (listing with size and change time, download URL + headers) → `docs/gdrive.md`
- [ ] T17 `src/downtempo/downloaders/gdrive.py` per T14, after T56: a `Provider` (`owns`, `connect`, `open`, `files`), registered as `gdrive`; usage in `docs/gdrive.md`
