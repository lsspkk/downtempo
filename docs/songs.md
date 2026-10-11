# Song catalog: `projects/<id>/songs.json`

**Summary**: Built (T90). `songs.json` is the only file the players read: songs with recordings and sheets, paths relative to the project folder. It is **derived** from the downloaded files and the project's sorting (`grouping.json`, [song-grouping.md](song-grouping.md)); it is never edited by hand. Rebuilt after every download, after every sorting change, and by `uv run downtempo catalog`.

Example: [data/songs.example.json](../data/songs.example.json).

```json
{
  "songs": [
    {
      "id": "harbour-waltz",
      "title": "Harbour Waltz",
      "audio": [{ "label": "Harbour Waltz", "path": "downloads/my-band/Harbour Waltz/Harbour Waltz.mp3" }],
      "pdf": ["downloads/my-band/Harbour Waltz/Harbour Waltz-2026-01-15.pdf"]
    }
  ]
}
```

| Field   | What                                                                                                                                                |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`    | the song's id (a slug of its first title, `-2` when taken); never changes on a rename. The player's memory (tempo, loops, last song) is keyed by it |
| `title` | shown in the players                                                                                                                                |
| `audio` | recordings in display order, the default first; `label` tells them apart                                                                            |
| `pdf`   | sheets, the newest version first, older versions after                                                                                              |

- Paths are relative to the project folder, with `/`: `downloads/<source>/<path as on the server>`.
- Songs are in title order; a song with no file isn't listed. A file can be in several songs.
- A song's recordings and sheets come from any of the project's sources.

## How it is built

`Library.rebuild()` (after a download and by `catalog`; `catalog.build_catalog` is the last step):

1. `catalog.list_files` lists the audio and sheet files under `downloads/<source>/` (endings in any case), leaving out skipped folders.
2. `grouping.group` puts every file in a song, To sort or the not-song list, using `grouping.json`; the matches it made now are saved there as automatic placements.
3. The songs are written to `songs.json` (whole or not at all). Files that joined a song in this run get a mark in `new.json`.

Nothing is read from folder names alone: how files become songs is [song-grouping.md](song-grouping.md). A project that has never been sorted gets a song of every suggestion on its first rebuild (temporary until the To sort screen, T96).

## `new.json`: this computer's

`projects/<id>/new.json`: `{file id: date}` of files that joined a song since the song was last opened. Written only by the Library (the player's periodic state save never touches it); `library.new_marks()`, `songs_with_new()`, `mark_seen(song id)`. Not exported in the settings file.

## From before song grouping

Projects whose `songs.json` has no `id` (folder = song, with `collection` and the source's `extra_folders`) are moved once, when the data folder is opened (`upgrade.py`): each old song becomes a song with its folder linked and its files placed, labels that were edited by hand are kept, the practice memory (`<collection>/<title>` keys) moves to the ids, `extra_folders` leaves `project.toml`, and the old catalog stays as `songs.json.before-grouping`.
