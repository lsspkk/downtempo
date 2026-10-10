# data/

All local material. Git-ignored except this file and `*.example.*`.

| Path | What | Written by |
|---|---|---|
| `sources.toml` | shared folders to download (`[[source]]`: `name`, `type`, `url`, optional `subfolder`, `extra_folders`); format in `sources.example.toml` | you |
| `downloads/<name>/` | one collection per source: its mp3/wav/pdf files, original folder structure | `uv run downtempo download` |
| `songs.json` | song catalog the frontends read; format in `docs/songs.md` | `uv run downtempo catalog` + hand edits |
| `material.md` | notes for agents: sources, collections, songs, anything odd about the files | agents, you |
| `player-state.json` | what the Python player remembers (last song, tempo, loops, positions); [docs/player.md](../docs/player.md) | player |
| `cache/pages/` | PDF pages rendered to PNG for the player; safe to delete | player |
| `scratch/` | experiments and test renders, not songs | anyone |
| `.onedrive_token.json` | OneDrive sign-in cache (mode 600) | OneDrive downloader |
