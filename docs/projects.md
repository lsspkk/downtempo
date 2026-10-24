# Projects: several music projects (built)

**Summary**: Built: core and CLI (T78, T79), the player's ☰ main menu (T82, T120: top left in the player and the project screen; switch, new, Project settings, delete) and Project settings (T116: name, links, folders); tried by the user (T83). A project = one group's sources, songs, sorting and practice memory in `data/projects/<id>/`; sign-ins and layout stay global. Today's `data/` is moved in once, resumably; switching saves, stops playback and builds the page again for the other project (`app.py` `current()` loads the current project per page; the old page's player is `retired` so it can't write into the new one).

Idea **Projects**; part of [blocks.md](blocks.md); tasks in [todo.md](todo.md).

## What a project is

A band, a choir, a course: its own sources, downloaded files, songs (with the user's sorting), and practice memory (tempo, loops, positions). Why: [purpose.md](purpose.md). One project is current; the player and the CLI work on it. Sign-ins and the player's layout belong to the computer, not a project.

## On disk

```
data/app.json                          current project; dark mode, view, settings (from player-state.json)
data/tokens/onedrive.json              sign-ins, shared by all projects
data/projects/<id>/project.toml        name + [[source]] (replaces sources.toml; the settings file's format)
data/projects/<id>/downloads/<source>/
data/projects/<id>/grouping.json       the user's sorting and song ids (song-grouping.md)
data/projects/<id>/songs.json          derived from files + grouping.json; paths relative to the project folder
data/projects/<id>/practice.json       per song and recording (from player-state.json)
```

`<id>` is a safe folder name made from the project name; the name itself can change without moving folders.

Each project folder is one `Library` ([blocks.md](blocks.md#apis)): code built before Projects already works on a library root, so Projects adds the list and the switch, not a rewrite.

## Moving today's data in

`migrate` runs whenever a `Workspace` is made (CLI, player) and does something only while any of `data/sources.toml`, `downloads/`, `songs.json`, `player-state.json` exists:

1. Create a project named after the first source (the user can rename it); its id goes into `app.json` before anything moves, so a rerun finds it.
2. Copy `sources.toml` → `project.toml` (+ `name`) and `songs.json` in; move `downloads/` one source folder at a time (no copies: hundreds of MB).
3. Split `player-state.json`: the layout keys to `app.json`, `songs` and `recordings` to `practice.json`.
4. Keep the old `sources.toml` and JSON files as `*.before-projects` until the user deletes them.

Each step checks whether it's already done, so an interrupted move continues on the next start. `songs.json` paths don't change because they are relative to the library root.

## API

```python
class Workspace:                                  # data/
    def projects(self) -> list[ProjectInfo]       # id, name, sources, songs
    def current(self) -> Library
    def use(self, id: str) -> Library
    def create(self, name: str) -> Library
    def rename(self, id: str, name: str) -> None
    def delete(self, id: str) -> None             # after the UI asked; removes its downloads
def migrate(data_dir: Path) -> None               # the move above, safe to re-run
```

Built in `src/downtempo/projects.py`; `current()` falls back to the first project, or makes "My songs" when there are none. `find(name)` takes a name or id, any case. Names: at most 60 printable characters, unique (any case).

CLI: a global `--project <name>`; `downtempo project list | new <name> | use <name> | rename <name> <new> | delete <name> [--yes]`.

## Player

- The current project's name is in the [project screen](project-screen.md)'s header, with a menu: switch to another project, New project, Rename, Export (the settings file), Delete. The song list shows the name and opens the same menu.
- Switching stops playback (ux.md #7), swaps the `Library`, reloads the songs and practice memory, and opens that project's last song paused.
- With one project the menu still shows, so the feature can be found, but nothing else changes.
- UX plan (T81): [project-screen.md](project-screen.md#project-menu).

## Not planned

- One download shared by two projects with the same link: each downloads its own copy. Simple, and links rarely overlap.
- Songs from several projects in one list.
