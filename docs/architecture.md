# Architecture

Downloaders fill `data/downloads/`, a catalog describes the songs, frontends play them.

```
sources.toml ──downloaders──> data/downloads/<collection>/ ──catalog──> data/songs.json ──> frontends
```

## Layout

- `src/downtempo/`: shared package, installed by uv; command line `uv run downtempo <command>` (`cli.py`).
  - `config.py`: paths, `.env` loading, `Source` + `load_sources()` for `data/sources.toml`.
  - `catalog.py`: `uv run downtempo catalog` builds `data/songs.json` ([songs.md](songs.md)).
  - `downloaders/`: one module per source type, registered in `downloaders/__init__.py` (`DOWNLOADERS`). `files.py` has shared file saving.
- `frontends/`: players; may import `downtempo.config` and `downtempo.catalog`. `nicegui/` (Python player, [player.md](player.md)): `app.py` UI in a native window (pywebview, Qt on Linux), `engine.py` Rubber Band stretch + `sounddevice`, `loop_editor.js` the loop editor's canvas drawing and gestures, `sheets.py` PDF pages, `state.py` `data/player-state.json`. Browser player not started.
- `data/`: all local material, see [data/README.md](../data/README.md).
- `scripts/`: dev tools: `webfetch.py` (save web pages), `screenshot.py` (load a page, run JS steps such as key presses, save PNGs: repeatable UI checks of the player in `--browser` mode).

Planned next: the core split into blocks with one API for the CLI and players ([blocks.md](blocks.md)); its rules join the principles below as they are built.

## Principles

- **Provider code stays in its downloader.** Nothing outside `downloaders/<type>.py` knows about OneDrive or Google Drive. A new provider = one module + one registry line + one doc.
- **A downloader's contract**: `download(source: Source) -> None`. It writes only mp3/wav/pdf (`MEDIA_EXTENSIONS`, endings in any case) under `source.target` (`data/downloads/<name>/`), keeps the folder structure, never deletes. Through `files.save_url(url, path, size, modified)`: a saved file gets the server's change time as its mtime; a file is skipped when its size matches and its mtime isn't older than the server's, else downloaded again ("Updated:"). User-facing failures raise `RuntimeError`.
- **Frontends read only the catalog** (`data/songs.json`) and the files it points to. They never scan folders or import downloader code.
- **Config split**: `.env` = credentials only; `data/sources.toml` = what to download, and per source how the catalog reads it (`extra_folders`).
- **Private stays local**: real links, folder and song names live only in `data/` (git-ignored). Tracked files use made-up examples.
