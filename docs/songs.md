# Song catalog: `data/songs.json`

The one file the players read. Written by `uv run downtempo catalog`, then edited by hand if needed. Example: [data/songs.example.json](../data/songs.example.json).

```json
{
  "songs": [
    {
      "title": "Harbour Waltz",
      "collection": "my-band",
      "audio": [{"label": "Harbour Waltz", "path": "downloads/my-band/Harbour Waltz/Harbour Waltz.mp3"}],
      "pdf": ["downloads/my-band/Harbour Waltz/Harbour Waltz-2026-01-15.pdf"]
    }
  ]
}
```

| Field | What |
|---|---|
| `title` | shown in the players; default: the song's folder name |
| `collection` | the source name = folder in `data/downloads/` |
| `audio` | recordings, first = default; `label` tells them apart (default: file name without the ending) |
| `pdf` | sheet music, chords etc., sorted by name |

- Paths are relative to `data/`, with `/`.
- Songs are in title order. Players play `audio[0]` unless the user picks another.

## How `catalog` builds it

- Every folder under `data/downloads/<collection>/` with audio (mp3, wav) or pdf files directly in it is one song (endings in any case, `.WAV` too), also nested ones (a nested folder is its own song).
- **Extra folders**: a folder whose name matches a pattern in the source's `extra_folders` (`data/sources.toml`, e.g. `["Rehearsal *"]`, any case, also nested) is not a song. It holds recordings of several songs, e.g. a rehearsal. Each of its files joins the song whose title the file name starts with, as whole words, any case; the longest title wins. Recordings are added after the song's own, labelled `<folder> · <rest of the name>` (`Rehearsal 3.10 · 2`); pdfs join the song's sheets. Files that match no song stay together as a song named after the folder.
- Re-run keeps hand edits: a scanned song that shares a file with an old entry keeps its `title`, the `label` of each recording still there, and any extra keys. Songs whose files are all gone are dropped.
