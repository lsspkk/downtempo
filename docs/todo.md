# Todo

Tasks grouped under the idea they belong to ([ideas.md](ideas.md)). `- [ ] T<n> task`. Top = next. Follow-up to `T<n>`: `T<n>.<k>`, e.g. T11.1.
When done: delete the line here and add it to `log.md`.

### Agent guide

- [ ] T104 Summaries retrofit per CLAUDE.md "Summaries first": a few lines (decisions + status) under the title of every doc in `docs/` (most have only an intro line; onedrive.md starts with "Answer"), plus README.md and data/README.md; `docs/README.md` lines say what each doc decides; `architecture.md` rewritten to open with the whole system on one screen (data flow, parts with one job, rules, planned parts from blocks.md marked as planned); first-line docstrings checked in `src/`, `frontends/`, `scripts/`
- [ ] T105 Split `frontends/nicegui/app.py` (1752 lines) by job per CLAUDE.md "Code: get the shape right": by part of the screen, e.g. library drawer, controls pane, sheet pane, loop editor dialog, keys/help, settings each in its own module, `app.py` only wiring; no behaviour change; smoke in `--browser` with screenshot.py (song switch, play, loop, sheet keys, loop editor), then a manual test for the user

### Python player

- [ ] T13.8 Manual test by the user in the native window (only `--browser` mode and a fake audio stream were tested): real sound at 0.5x / 1.0x / 1.3x, live slider, loop seam, pause click, trainer, pitch, sheet zoom; small-laptop layout on the real screen: Q, V, rotate with the laptop on its side, footswitch PgDn/PgUp, Settings; full screen F / Esc in the native window, fit page H, recording switch T (needs a song folder with 2 mp3s); findings become tasks
- [ ] T12.8 Loop seam, listen (user): `data/scratch/loop-seam/` has a 5.5 s loop of the first song at 0.75x, 4 repeats, rendered 3 ways: `1-current` (stretcher memory runs on: B's last ~46 ms after the wrap, A starts that late), `2-reset` (reset + pad at the wrap: A exact, B's last ~0.1 s cut), `3-flush-reset` (B complete, A exact, but a 95 ms silence at each seam). Pick by ear; if 2 or 3, add a task to put it in `Engine._work` (script: scratchpad `t128/seam.py`, not kept)

### Loop editor

- [ ] T39 Check the decisions in [loop-editor.md](loop-editor.md) against a few loop/zoom UIs (a DAW, a practice app, a waveform library) for pitfalls only (save the pages); principles that hold go into [ux.md](ux.md); change the plan only for a clear reason
- [ ] T44 Manual UX test by the user on the real laptop (mouse and trackpad): `E`, click start / end with a two-finger swipe between, pinch zoom in the native window (unknown whether Qt WebEngine passes it), ⠿ handles, Hear end, Undo, Esc back; findings become tasks

### Browser player

- [ ] T4 Browser research, the rest after [stretch-research.md](stretch-research.md): pick the worklet for T6 (Signalsmith Stretch Web vs SoundTouchJS vs plain `playbackRate`), check Safari and whether rubberband-web is maintained → short `docs/tempo-browser.md`
- [ ] T6 `frontends/browser/index.html` MVP: load `data/songs.json`, song dropdown, tempo slider 0.5–1.3x; served by `uv run downtempo serve`, which exposes only the page, the catalog and its files (not the project root: `.env`)
- [ ] T31 Listening test per [stretch-research.md](stretch-research.md#then-listening-test-t31): same 20 s excerpts (drums, solo melody) at 0.5x / 0.75x / 1.3x with R3, R3 + ChannelsTogether, R2, Signalsmith, browser `playbackRate` → `data/scratch/tempo-tests/`; blind listening by the user
- [ ] T8 Compare Python vs browser by ear (uses T31); write the pick and why into `docs/tempo-decision.md`

### Downloaders

- [ ] T14 Google Drive research: download all mp3/pdf from an "anyone with the link" folder (Drive API v3 + API key vs OAuth vs `gdown`); what credentials are needed, and whether it fits the `Provider` protocol in [blocks.md](blocks.md#apis) (listing with size and change time, download URL + headers) → `docs/gdrive.md`
- [ ] T17 `src/downtempo/downloaders/gdrive.py` per T14, after T56: a `Provider` (`owns`, `connect`, `open`, `files`), registered as `gdrive`; usage in `docs/gdrive.md`

### Downloader UI

Transport core first ([blocks.md](blocks.md)); the UI for it lives in the project screen below. Order ([downloader-review.md](downloader-review.md) R13): T54–T60 → Song grouping T86–T91 → Project screen.

- [ ] T54 Read the docs (save the pages) for the open points in [blocks.md](blocks.md#open-points-tasks): `tomlkit` (edit TOML keeping comments and order), MSAL device flow from a worker thread (`verification_uri`, `user_code`, `expires_in`; how to stop a waiting `acquire_token_by_device_flow`), Microsoft's word on shipping a public client ID with an app, NiceGUI background work (`run.io_bound`, `background_tasks`, updating widgets only from the UI side); decisions into blocks.md
- [ ] T55 `events.py` + `errors.py` per [blocks.md](blocks.md#apis): event dataclasses, `print_report` (the CLI's current lines), `UserError(message, hint)`; `save_url` and the OneDrive downloader report instead of `print`, HTTP and network errors become plain `UserError`s (offline, no access, link not found, not a folder); smoke: `uv run downtempo download` prints the same as before
- [ ] T56 Provider protocol + `sync.py`: OneDrive split into `connect` / `open` (a folder path of any depth) / `files` (no file saving), `provider_for(url)` with `owns()`; `sync.plan` (new / updated / same / gone vs local files) and `sync.run` (`.part`, server mtime, `Fetching` about every MB, cancel between chunks keeps finished files, a server name can't leave the source folder); `downtempo download --dry-run` prints the plan; smoke: local HTTP server as in T36 + one real run (all "same")
- [ ] T57 `sources.py`: `Source` + `check_name` / `check_url`, read and write `sources.toml` with `tomlkit` keeping comments (`uv add tomlkit`, per T54), atomic write; `Source.folder` = path inside the share (old `subfolder` read as it); CLI `downtempo add <link> [--name] [--folder <path>]` (provider from the link, name from the folder, made unique), `downtempo sources` (list), `downtempo remove <name> [--delete-files]`; README "Use"
- [ ] T58 `library.py` per [blocks.md](blocks.md#apis): `Library(root)` with sources, `inspect_link`, `sync` (downloads then `rebuild`), `rebuild` returning `CatalogDiff` (new / gone songs, new recordings, sheets), `path()`; `DOWNTEMPO_DATA` sets the data folder (scratch runs); CLI and player go through it, the player resolves files with `library.path()` instead of `DATA_DIR`; new rules into architecture.md (core never prints; frontends never import `downloaders/`)
- [ ] T59 Sign-in for a window: `SignIn` event with code, page and expiry; cancellable wait; token cache moved to `data/tokens/onedrive.json` (old file moved on first use); `account()` → "Signed in as …", `sign_out()`; built-in client ID if T54 allows (`.env` still overrides), [onedrive.md](onedrive.md) updated
- [ ] T85 Folder picker, core: `Connection.folders(folder)` lists subfolders with ♪/📄 counts (lazy, one level per call); `downtempo folders <link> [<path>]` prints them; smoke on the real share
- [ ] T60 Player job bridge `frontends/nicegui/jobs.py`: one background job at a time, events through a queue drained by a `ui.timer`, cancel; after a job the song list reloads without a restart, keeping the open song (or stopping cleanly if it's gone); smoke in `--browser` with a fake provider job

### Song grouping

Plan: [song-grouping.md](song-grouping.md); why: [purpose.md](purpose.md). Replaces the folder-rule tasks T70–T77 ([downloader-review.md](downloader-review.md) R1).

- [ ] T86 Grouping corpus in `data/scratch/grouping-corpus/`: made-up path lists (one file path per line, no audio) for folder per song, flat, by type, rehearsal dates, parts, sets, clutter, typos and word order, Finnish words, sheet-only and audio-only songs, two sources; plus the real `data/downloads` listing; the expected songs written beside each list; a README
- [ ] T87 Read the docs (save the pages): `rapidfuzz` (ratio, token_set_ratio, licence) vs `difflib`; `unicodedata` normalisation; how beets / MusicBrainz Picard match names; pick the matcher and first thresholds → [song-grouping.md](song-grouping.md#open-tasks)
- [ ] T88 `grouping.py` per [song-grouping.md](song-grouping.md): `clean`, matching of files with no song (📁 linked folder, exact, whole words, typo tolerance 0/1/2 by length, longest magnet wins, ties → To sort, fuzzy → suggestion only), suggested songs (same key, song folders), sheet versions, labels, order, offers (gather, better match); pure, takes `FileRef`s + memory; smoke: a scratch script runs the T86 corpus and prints differences from the expected songs; the real data's suggestions equal today's catalog without `extra_folders`
- [ ] T89 Grouping memory per [song-grouping.md](song-grouping.md#memory-groupingjson-in-the-project): sticky placements (`by` auto / hand), songs with title, also, folders; Library operations (create, move, also_add, new_song, rename with keep_old, alias, link / unlink folder, merge, delete → files back to To sort, not_song, skip_folder + free_space, label, make_first, accept offer) + undo/redo, atomic writes; `skip` per source honoured by `sync.plan`; smoke: each operation on a scratch copy, then a rebuild keeps it
- [ ] T90 Catalog from grouping: `songs.json` derived (song `id`, files from any source, shared files in several songs, newest sheet version first, no `collection`), hand edits and `extra_folders` moved into `grouping.json` once; the player keys its memory by song id (one-time move of `<collection>/<title>` keys); new marks kept in the practice memory; `library.preview(files)` for listings; songs.md, data/README updated; smoke: real catalog same songs, tempo and loops kept (absorbs T73)
- [ ] T91 CLI `downtempo songs [--explain] [--to-sort]` (songs, each file's label, confidence and why) and `downtempo move <file> <song>` for smoke runs; README "Use"
- [ ] T98 Player for sheet-only and audio-only songs per [project-screen.md](project-screen.md#player-side): no recording → controls pane shrinks to title + "No recording", the sheet gets the space; no sheet → a large waveform instead of the "No sheet music" box; smoke with a scratch catalog holding both kinds ([downloader-review.md](downloader-review.md) R9)
- [ ] T102 Player follows grouping per [project-screen.md](project-screen.md#player-side): a dot on songs with new files in the song list until opened; the newest sheet version opens unless the user picked another for this song (remember a deliberate pick apart from the default); smoke with a scratch catalog getting a newer dated PDF

### Project screen

Plan: [project-screen.md](project-screen.md). Replaces the Sources dialog (T46 done by T84, T61–T64 reworked).

- [ ] T92 Read the docs (save the pages): drag and drop in NiceGUI (its examples, HTML5 drag events vs SortableJS in the page's own script), serving only catalog files to the page for previews, the first PDF page from `sheets.py`; pick the method → [project-screen.md](project-screen.md#checks-uxmd-checklist)
- [ ] T93 Skeleton `frontends/nicegui/project_screen.py` + `project_screen.js` per [project-screen.md](project-screen.md): full-screen view from a "Sort songs and sources" button in the Songs drawer; header (back / Esc, project name, source chips, Update, Undo / Redo), tabs To sort / Songs (opens on To sort when not empty), rows of file chips with marks (• new, ✋ by hand, ×2, versions) and tooltips (path, why here), read-only; screenshot at 1280×720 light and dark
- [ ] T94 Moving files in the Songs tab: drag and drop onto rows, Ctrl+drag = also add (×2), selection (click, Ctrl/Shift), Move to… (`M`), Also add to…, `Delete` → Not song files, `N` new song, drag a title to merge, Make first, chip menu; the gather offer after a drag and the better-match offer as lines under the song (Yes / No); each one Library operation; the player's song list follows on return; smoke with synthetic events in `--browser`
- [ ] T101 Song edit box (✎ / `F2`) per [project-screen.md](project-screen.md#song-edit-box): title, "Keep *old* as also called" ☑ after a rename, Also called chips (+ / ×), 📁 folder chips (+ via the picker / ×), live "matches n files", Merge into…, Delete song (Undo, files back to To sort)
- [ ] T95 File previews: ▶ first 15 s in an audio element, 👁 first PDF page, tooltip with source path and why the file is here ([downloader-review.md](downloader-review.md) R10)
- [ ] T96 To sort tab per [project-screen.md](project-screen.md#to-sort-tab): suggested songs with ☑ and editable titles, Create selected (n) (with the "+2 files" pull), merge / split suggestions by dragging, loose files with one-click fuzzy suggestions, Your songs drop column (≤ 220 px, search), Not song files folded; Songs tab filters New (n) and Needs a look; "removed on server" marks; To sort badge on the Songs button
- [ ] T61 Sources in the header: chips with state (updated 2 h ago / 45 % / sign in again), source menu (rename, change folder via the picker, Skipped folders with ×, Free space (n GB), remove keeping or deleting files, signed-in account + Sign out), ⟳ Update in the background (T60) with progress in the chip and the player's header, clickable result "5 new files: 4 joined songs, 1 to sort"
- [ ] T62 Add folder: paste → Checking… → sign-in card (code, Copy, Open page, time left, Cancel) → folder picker (T85) with ☐ Skip per folder → "About 12 songs from 31 files, 180 MB" (`library.preview`) → Download; the screen opens on To sort and fills in as files arrive
- [ ] T63 Errors per [project-screen.md](project-screen.md#errors-in-plain-words-with-what-to-do): plain texts with what to do, Retry, Cancel keeps finished files, expired sign-in shown on the source chip
- [ ] T97 First start: the empty player shows "Paste a link to your group's shared folder" (no terminal commands) → the T62 flow → project named from the folder → project screen → Done → the first song (absorbs T64; [downloader-review.md](downloader-review.md) R6, R16)
- [ ] T65 Manual test by the user on a fresh data folder (`DOWNTEMPO_DATA`): first start with a real link, sign-in, folder picker, cancel midway, unplug the network, a changed file on the server, remove a source; findings become tasks
- [ ] T99 Manual test by the user of sorting: the real project plus a made-up messy folder (scratch source): drag, Move to…, merge, rename, undo, previews, an update bringing a new file; findings become tasks

### Settings file

Plan: [settings-file.md](settings-file.md).

- [ ] T66 `bundle.py` per [settings-file.md](settings-file.md#api): `export` (sources + `[grouping]`) / `read` (all [import rules](settings-file.md#import-rules)) / `preview` / `apply`; CLI `downtempo export <file>`, `downtempo import <file> [--yes]`; smoke: round trip into a scratch `DOWNTEMPO_DATA`, plus bad files (`../` name, `file://` link, 1 MB, newer version, unknown key, name taken: its `[grouping]` file keys renamed too)
- [ ] T67 Player: Export… / Copy as text and Import… / Paste in the project menu of the project screen (native save/open dialogs, download/upload in `--browser`); the preview list with what each source gets; after Apply, "Download now?" opens the T63 progress
- [ ] T68 Manual test by the user: export, email it to yourself, import on another computer (or a 2nd `DOWNTEMPO_DATA`), download; findings become tasks
- [ ] T69 Ask the user whether exports should optionally carry practice memory (tempo, loops: a teacher sending loops); the sorting is always included ([downloader-review.md](downloader-review.md) R11); if yes, plan it as new tasks

### Projects

Plan: [projects.md](projects.md).

- [ ] T78 `projects.py` per [projects.md](projects.md#api): `Workspace` (list, current, use, create, rename, delete) with `data/app.json`; one `Library` per `data/projects/<id>/` with `project.toml`, `grouping.json`, `songs.json`, `practice.json`; `migrate()` of today's `data/` (moves, resumable, keeps `*.before-projects`), `player-state.json` split into `app.json` + `practice.json`; smoke: migrate a copy of `data/` twice, songs and practice memory the same
- [ ] T79 CLI: global `--project`, `downtempo project list | new | use | rename | delete`; README "Use"
- [ ] T80 Settings file with projects: export = one project; import offers New project *name* or Add to the current one
- [ ] T81 UX plan for projects → section in [project-screen.md](project-screen.md): the project menu in the screen's header (switch, new, rename, export, delete), the name in the song list, what switching does, first start after the migration; follows [ux.md](ux.md) ([downloader-review.md](downloader-review.md) R15)
- [ ] T82 Implement T81: switching stops playback, swaps the `Library`, reloads songs and practice memory, opens that project's last song paused
- [ ] T83 Manual test by the user: two projects, switch while playing, export one and import it as a new project on a 2nd `DOWNTEMPO_DATA`; findings become tasks
