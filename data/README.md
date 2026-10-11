# data/

All local material. Git-ignored except this file and `*.example.*`.

| Path | What | Written by |
|---|---|---|
| `app.json` | the current project and the player's layout (dark mode, view, settings, volume, zoom) | player, `downtempo project use` |
| `projects/<id>/project.toml` | written by the player (Project settings, Add folder) and the CLI; edit by hand only as a last resort. The project's `name` and shared folders (`[[source]]`: `name`, `type`, `url`, optional `folder` (a path inside the share; old name `subfolder`), optional `skip` (folders not downloaded)); format in `sources.example.toml` | `uv run downtempo add` / `project new`, or you |
| `projects/<id>/downloads/<name>/` | one collection per source: its mp3/wav/pdf files, original folder structure | `uv run downtempo download`, the player's "Check for new files" |
| `projects/<id>/songs.json` | song catalog the frontends read; format in `docs/songs.md` | derived from the files and `grouping.json`: rebuilt after every download, every sorting change and by `uv run downtempo catalog`; never edit by hand |
| `projects/<id>/grouping.json` | the sorting: songs (title, also-called names, linked folders), where each file is (`auto` / `hand`), default order; [docs/song-grouping.md](../docs/song-grouping.md) | the sorting operations (`Library.sorting`), the settings file import |
| `projects/<id>/new.json` | files that joined a song since it was opened (`{file id: date}`); this computer's, not exported | the Library |
| `projects/<id>/practice.json` | what the player remembers per song and recording (last song, tempo, loops, positions); [docs/player.md](../docs/player.md) | player |
| `projects/<id>/songs.json.before-grouping` | the old folder-per-song catalog, kept by the one-time upgrade; safe to delete | first run after song grouping |
| `*.before-projects` | the old `sources.toml`, `songs.json`, `player-state.json`, kept after the move into a project ([docs/projects.md](../docs/projects.md)); safe to delete | first run after projects |
| `material.md` | notes for agents: sources, collections, songs, anything odd about the files | agents, you |
| `cache/pages/` | PDF pages rendered to PNG for the player; safe to delete | player |
| `scratch/` | experiments and test renders, not songs | anyone |
| `tokens/onedrive.json` | OneDrive sign-in cache (mode 600); `uv run downtempo sign-out` removes it | OneDrive provider |
