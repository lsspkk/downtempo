# data/

All local material. Git-ignored except this file and `*.example.*`.

| Path | What | Written by |
|---|---|---|
| `sources.toml` | shared folders to download (`[[source]]`: `name`, `type`, `url`, optional `subfolder`); format in `sources.example.toml` | you |
| `downloads/<name>/` | one collection per source: its mp3/pdf files, original folder structure | `uv run downtempo download` |
| `songs.json` | song catalog the frontends read; format in `docs/songs.md` (T9) | catalog command (T10) + hand edits |
| `material.md` | notes for agents: sources, collections, songs, anything odd about the files | agents, you |
| `scratch/` | experiments and test renders, not songs | anyone |
| `.onedrive_token.json` | OneDrive sign-in cache (mode 600) | OneDrive downloader |
