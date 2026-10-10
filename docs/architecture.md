# Architecture

**Summary**: Downloaders copy a shared folder's media into `data/downloads/`, the catalog turns those files into `data/songs.json`, and the players read only that catalog. Built: OneDrive downloader, catalog, Python player. Planned: the core split into blocks behind one `Library` API, name-based song grouping, the project screen and projects ([blocks.md](blocks.md), [purpose.md](purpose.md)).

```
sources.toml ──downloaders──> data/downloads/<collection>/ ──catalog──> data/songs.json ──> frontends
```

| Part | One job | Status |
|---|---|---|
| `src/downtempo/config.py` | paths, `.env`, `Source` list from `sources.toml` | built |
| `src/downtempo/events.py`, `errors.py` | what long work reports (events + `print_report`), failures in plain words (`UserError`) | built (T55) |
| `src/downtempo/downloaders/` | one module per provider: copy media files, keep mtimes | built (OneDrive) |
| `src/downtempo/catalog.py` | files → `songs.json` | built; becomes grouping (T88–T90) |
| `src/downtempo/cli.py` | `uv run downtempo download / catalog` | built |
| `frontends/nicegui/` | the Python player: UI, audio engine, sheets, remembered state | built |
| `scripts/` | dev tools: save web pages, screenshots of the player | built |
| `library`, `sync`, `grouping`, `bundle`, `projects` | the planned core ([blocks.md](blocks.md#blocks)) | plan |

## Layout

- `src/downtempo/`: shared package, installed by uv; command line `uv run downtempo <command>` (`cli.py`).
  - `config.py`: paths, `.env` loading, `Source` + `load_sources()` for `data/sources.toml`.
  - `catalog.py`: `uv run downtempo catalog` builds `data/songs.json` ([songs.md](songs.md)).
  - `events.py`: event dataclasses (`SignIn`, `Same`, `Fetching`, `Saved`, `Skipped`) and `print_report`, the CLI's lines. `errors.py`: `UserError(message, hint)`.
  - `downloaders/`: one module per source type, registered in `downloaders/__init__.py` (`DOWNLOADERS`). `files.py` has shared file saving and `request_error` (a failed request → `UserError`).
- `frontends/`: players; may import `downtempo.config` and `downtempo.catalog`. `nicegui/` (Python player, [player.md](player.md)): `app.py` wires the page in a native window (pywebview, Qt on Linux) from one module per part of the screen (`layout.py` frame, `song_list.py`, `controls.py`, `sheet_pane.py` + `.js`, `loop_editor.py`, `keys.py`) and `player.py` (what plays, no widgets), `engine.py` Rubber Band stretch + `sounddevice`, `loop_editor.js` the loop editor's canvas drawing and gestures, `sheets.py` PDF pages, `state.py` `data/player-state.json`. Browser player not started.
- `data/`: all local material, see [data/README.md](../data/README.md).
- `scripts/`: dev tools: `webfetch.py` (save web pages), `screenshot.py` (load a page, run JS steps such as key presses, save PNGs: repeatable UI checks of the player in `--browser` mode).

The planned core's rules ([blocks.md](blocks.md#rules)) join the principles below as they are built.

## Principles

- **Provider code stays in its downloader.** Nothing outside `downloaders/<type>.py` knows about OneDrive or Google Drive. A new provider = one module + one registry line + one doc.
- **A downloader's contract**: `download(source: Source, report: Report) -> None`. It writes only mp3/wav/pdf (`MEDIA_EXTENSIONS`, endings in any case) under `source.target` (`data/downloads/<name>/`), keeps the folder structure, never deletes. Through `files.save_url(url, path, source, report, size, modified)`: a saved file gets the server's change time as its mtime; a file is skipped when its size matches and its mtime isn't older than the server's, else downloaded again ("Updated:"). It never prints: progress goes to `report` as events, and every failure the user should read is a `UserError` (network and HTTP errors through `request_error`). The CLI passes `print_report` and prints `UserError`s with their hint.
- **Frontends read only the catalog** (`data/songs.json`) and the files it points to. They never scan folders or import downloader code.
- **Config split**: `.env` = credentials only; `data/sources.toml` = what to download, and per source how the catalog reads it (`extra_folders`).
- **Private stays local**: real links, folder and song names live only in `data/` (git-ignored). Tracked files use made-up examples.
