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

### Loop editor

- [ ] T44 Manual UX test by the user on the real laptop (mouse and trackpad): `E`, click start / end with a two-finger swipe between, pinch zoom in the native window (unknown whether Qt WebEngine passes it), ⠿ handles, Hear end, Undo, Esc back; findings become tasks

### Browser player

The user's call (2026-10-11): find out first whether a browser version can sign in and get the files at all, by research, then small test pages on GitHub Pages that the user tries. Each test page says clearly that it is only for testing a browser version of Downtempo. No real links, names or files in the repo: the user pastes a link in the page.

- [ ] T133 Manual test by the user of the OneDrive page per [browser-tests.md](browser-tests.md) (setup there first): sign in, a real share link, download and play, reload and play again, Ask to keep; Chrome and Firefox (and a phone if handy); findings → tasks, and the decision whether the browser player goes on (then T4, T31, T8, T6)
- [ ] T4 Browser research, the rest after [stretch-research.md](stretch-research.md): pick the worklet for T6 (Signalsmith Stretch Web vs SoundTouchJS vs plain `playbackRate`), check Safari and whether rubberband-web is maintained → short `docs/tempo-browser.md`
- [ ] T6 `frontends/browser/index.html` MVP: load `data/songs.json`, song dropdown, tempo slider 0.5–1.3x; served by `uv run downtempo serve`, which exposes only the page, the catalog and its files (not the project root: `.env`)
- [ ] T31 Listening test per [stretch-research.md](stretch-research.md#then-listening-test-t31): same 20 s excerpts (drums, solo melody) at 0.5x / 0.75x / 1.3x with R3, R3 + ChannelsTogether, R2, Signalsmith, browser `playbackRate` → `data/scratch/tempo-tests/`; blind listening by the user
- [ ] T8 Compare Python vs browser by ear (uses T31); write the pick and why into `docs/tempo-decision.md`

## Later

Not now (the user's call, 2026-10-11).

### Downloaders

- [ ] T132.1 Google Drive test pages: tests 3–5 of [browser-research.md](browser-research.md#what-t132-tests) on the same page, after the user's Google Cloud setup there (skipped for now, the user's call 2026-10-13)

- [ ] T14 Google Drive research: download all mp3/pdf from an "anyone with the link" folder (Drive API v3 + API key vs OAuth vs `gdown`); what credentials are needed, and whether it fits the `Provider` protocol in [blocks.md](blocks.md#apis) (listing with size and change time, download URL + headers) → `docs/gdrive.md`
- [ ] T17 `src/downtempo/downloaders/gdrive.py` per T14, after T56: a `Provider` (`owns`, `connect`, `open`, `files`), registered as `gdrive`; usage in `docs/gdrive.md`
