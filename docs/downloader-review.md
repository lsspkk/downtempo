# Review: downloader plans vs. the purpose (T84, 2026-10-10)

**Summary**: Done 2026-10-10 (T84). The T53 plans made users configure folder rules and had no place to fix songs; replaced by name-based grouping, a full-screen project screen and a first-run flow. Findings R1–R16 each point to their task.

The T53 plans ([blocks.md](blocks.md), the removed `folder-layouts.md`, [settings-file.md](settings-file.md), [projects.md](projects.md), tasks T46, T54–T83) and today's player, checked against [purpose.md](purpose.md). Each finding names the task that handles it.

## What holds

- Downloaders as transport only, behind a `Provider` with `open` / `files`; one `sync.py`; events instead of prints; cancellable background jobs; untrusted input checked at the edge (T54–T60).
- `Library(root)` as the one API for frontends, with paths relative to the library root, so Projects is cheap (T58, T78).
- Grouping on a listing before download was already possible in that design (`layouts` were pure); it now becomes a visible step (T97).

## Findings

| # | Finding | Change | Task |
|---|---|---|---|
| R1 | The plan made the **user configure folder rules** (`folder` / `by-name` / `join` …) in `sources.toml` and a rules editor. The purpose says names decide and the layout is only a hint; nobody wants to learn rules. | Rules dropped. A guesser scores name and folder signals ([song-grouping.md](song-grouping.md)); the user fixes results, not rules. T70–T72, T74–T76 replaced. | T86–T91 |
| R2 | Fixes lived as **hand edits in `songs.json`**: no UI, kept only while a file is shared with the old entry, and lost by bandmates. | `grouping.json` holds decisions and known songs; `songs.json` is derived. | T89, T90 |
| R3 | A song belonged to **one source** (`collection`), so a sheet from one place and a recording from another couldn't meet, and the player keys memory by `collection/title`. | Songs are per project, across sources; stable ids (T73 absorbed). | T90 |
| R4 | **No place to see and fix songs.** The plan had a small Sources dialog (T46, T61) about links and downloads only. | One full-screen project screen: sources in the header, songs as rows of file chips, a To sort tray, drag and drop ([project-screen.md](project-screen.md)). T46 done by this review. | T93–T96 |
| R5 | **Folder choice** was a typed top-level `subfolder` name. The user wants to point at "some folder there". | Folder picker over the share's tree with counts; a source stores a folder path of any depth. | T85, T97 |
| R6 | The **first run** went link → download everything → "4 new songs". The user never sees the grouping before 180 MB arrive, or after. | Link → sign-in → pick folder → "about 12 songs" preview → download → project screen. | T97 |
| R7 | **New files after an update** only got a count. | They join songs by the same guesser; unsure ones wait in To sort, with a badge on the Songs button. | T96 |
| R8 | **Files gone from the server** were counted, nothing more. | Their chips are marked "removed on server"; the local copy stays until the user removes it. | T96 |
| R9 | **Sheet-only / audio-only songs**: the catalog allows them, but the player keeps a full controls pane for a sheet-only song and a big "No sheet music" box for an audio-only one (`controls.py` `no_audio`, `sheet_pane.py` `message`). | Layout adapts to what the song has. | T98 |
| R10 | Vague names make sorting guesswork without **hearing or seeing a file**. | ▶ 15 s preview and 👁 first page on the chips. | T95 |
| R11 | The **settings file** carried sources and folder rules only; T69 asked whether song edits should go too. | The grouping memory is part of the project and always exported: sharing the sorting is the point. Only practice memory stays optional (T69). | T66, T69 |
| R12 | Matching words are language-bound (the real material is Finnish: *soinnut*, *harjoitukset*). | Built-in English + Finnish noise words, project-extendable; whole words only. | T88 |
| R13 | Building the T71 rules engine first would have been thrown away. | Order: core transport (T54–T60, T85) → grouping engine (T86–T91) → project screen (T92–T98). | todo order |
| R14 | No way to check grouping from the terminal while developing. | `downtempo songs --explain` shows songs, confidence and why. | T91 |
| R15 | The project's **switch / rename / export** had a planned menu in the song list (T81) apart from everything else about the project. | The project menu sits in the project screen header (and the song list shows the name). | T81 |
| R16 | The empty start shows terminal commands (`app.py` "No songs yet"). | Paste-a-link start, part of the first-run flow. | T97 (T64 absorbed) |
