# Architecture

Downloaders fill `data/downloads/`, a catalog describes the songs, frontends play them.

```
sources.toml ──downloaders──> data/downloads/<collection>/ ──catalog──> data/songs.json ──> frontends
```

## Layout

- `src/downtempo/`: shared package, installed by uv; command line `uv run downtempo <command>` (`cli.py`).
  - `config.py`: paths, `.env` loading, `Source` + `load_sources()` for `data/sources.toml`.
  - `downloaders/`: one module per source type, registered in `downloaders/__init__.py` (`DOWNLOADERS`). `files.py` has shared file saving.
- `frontends/`: players (I3 NiceGUI in Python, I4 browser page). Not started.
- `data/`: all local material, see [data/README.md](../data/README.md).
- `scripts/`: dev tools (`webfetch.py`).

## Principles

- **Provider code stays in its downloader.** Nothing outside `downloaders/<type>.py` knows about OneDrive or Google Drive. A new provider = one module + one registry line + one doc.
- **A downloader's contract**: `download(source: Source) -> None`. It writes only mp3/pdf (`MEDIA_EXTENSIONS`) under `source.target` (`data/downloads/<name>/`), keeps the folder structure, skips files that already exist with the right size, never deletes. User-facing failures raise `RuntimeError`.
- **Frontends read only the catalog** (`data/songs.json`) and the files it points to. They never scan folders or import downloader code.
- **Config split**: `.env` = credentials only; `data/sources.toml` = what to download.
- **Private stays local**: real links, folder and song names live only in `data/` (git-ignored). Tracked files use made-up examples.
