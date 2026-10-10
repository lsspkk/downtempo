# Song grouping: files → songs (plan)

**Summary**: Plan (T86–T91). Hybrid: the program proposes songs, the user approves the list. Songs' titles, also-called names and 📁 folder links are magnets for files with no song; exact, whole-word and small-typo matches join, the rest waits in To sort. Placement is sticky; drags never make rules, only one-time offers.

The business logic behind [purpose.md](purpose.md): a project's files, from any folder layout and any number of sources, become songs. Decided with the user in T100 (questions 1–13); UI: [project-screen.md](project-screen.md). It replaces the folder-rules plan of T53.

## In short

- **Hybrid**: the program proposes songs, the user approves the list, and from then on files follow that list.
- Each song has **magnets**: its title, zero or more **Also called** names, and **📁 folder links**. A file with no song joins the song whose magnet it matches.
- **Placement is sticky**: once a file is in a song, it only moves when the user moves it. Magnets act only on files that have no song yet.
- No rule is ever learned behind the user's back. Every lasting choice (an alias, a folder link, a skipped folder) is made deliberately and shown where it can be removed. Convenience actions (gathering similar files, moving files to a better-matching new song) are **one-time offers**.

## Words

| Word | Meaning |
|---|---|
| song | a title, its magnets, and its files (sheets and recordings; either kind may be missing) |
| magnet | title, Also called name, or 📁 folder link of a song |
| To sort | files with no song: grouped into **suggested songs** where they share a name, else loose |
| suggested song | a proposed title + files, with ☑; nothing is created without a click |
| placed *auto* / *by hand* | how a file got into a song: by a magnet or Create, or by the user's drag |
| not a song file | a file the user set aside; hidden |
| skipped folder | a folder of a source that isn't downloaded |

## Inputs and outputs

```python
@dataclass(frozen=True)
class FileRef:              # one media file; id = f"{source}:{path}"
    source: str             # source name in the project
    path: PurePosixPath     # inside the source, as on the server
    kind: Literal["audio", "sheet"]
    size: int | None
    modified: datetime | None

def group(files: list[FileRef], memory: Memory, words: Words) -> Grouping   # pure: no disk, no network
```

- `files` come from disk after a download, **or from a remote listing** before it (the "about 12 songs" preview).
- `memory` = `grouping.json` (below); `words` = built-in noise words + the project's own.
- `Grouping` = songs (each file with its label, auto/by hand, version group), suggested songs, loose files, not song files, and **offers** (below).

## Cleaning a name

`clean("Harbour_Waltz - CHORDS 2026-01-15")` → key `harbour waltz`, extras `chords`, `2026-01-15`.

1. Unicode NFC, casefold; `_ . - + ,` become spaces; `&` and letters like ä, ö, å are kept.
2. Moved to extras: text in brackets, dates (`2026-01-15`, `9.10.2026`, `20260115`), versions and takes (`v2`, `ver 3`, `take 2`, `otto 2`, `final`, `uusi`, a trailing number), a trailing musical key (`E`, `Bb`, `F#m`, `in G`), and **noise words**.
3. Built-in noise words (English + Finnish; the project can add or keep some): chords, soinnut, sointu, lyrics, sanat, sheet, notes, nuotit, nuotti, score, partituuri, melody, melodia, demo, live, mix, master, rehearsal, harjoitus, harjoitukset, treeni, part, stemma, voice, ääni; bass, basso, guitar, kitara, fiddle, violin, viulu, accordion, harmonikka, piano, drums, rummut, vocals, laulu, soprano, sopraano, alto, altto, tenor, tenori.
4. Whole words only: *Vanhassa* is not *vanha*.

## Matching a file that has no song

Against every magnet of every song (all sources alike):

| Match | Result |
|---|---|
| the file is directly in a song's 📁 linked folder | joins that song, unless its own name matches **another** song's title or alias (then To sort) |
| key = a title or alias | joins |
| a title or alias is contained as whole words | joins |
| a title or alias within the **typo tolerance** | joins |
| only similar (fuzzy, beyond the tolerance) | To sort, the song shown as a one-click suggestion |
| nothing | To sort |

- **Typo tolerance**, letters different (edit distance) by the magnet's length: under 5 letters 0, from 5 letters 1, from 10 letters 2.
- **Longest magnet wins** (*Harbour Waltz Reprise* over *Harbour Waltz*). Two different songs matching equally, or a file containing two different titles → To sort.
- Files that join are marked **new** (see [New files](#new-files)).

## Suggested songs

Files left in To sort are grouped: the same cleaned key (within the typo tolerance) makes one **suggested song**, titled with the most common original spelling. A **song folder** (a folder holding media directly whose name isn't a date, noise or type word like *Audio*, *PDF*, *Old*) makes a suggestion from all its files, with the folder as its 📁 link-to-be. A song folder inside a song folder is its own suggestion (a medley).

On the first visit every file is in To sort, so the suggestions are the proposed song list ("Create selected (12)"). Later, only unmatched new files make suggestions; the song list never grows by itself.

## What the user's actions do

| Action | Effect |
|---|---|
| **Create** a suggestion | a song with that title; a song-folder suggestion also gets its 📁 link; then the new magnets pull matching To sort files at once; a **better-match offer** if it fits auto-placed files of other songs better |
| **Drag** files into a song | placed by hand (pinned); then a **gather offer** |
| **Ctrl+drag** / Also add to… | the file is in both songs (×2); sharing is always by hand |
| **New song** from files | title prefilled from the first file's cleaned name, editable |
| **Rename** | files stay; "Keep *old name* as also called" ☑ by default (untick to fix a wrong title) |
| **Also called** + / × | add or remove an alias; removing doesn't move files already placed |
| 📁 **link** + / × | link a folder by hand, or remove a link; files already placed stay |
| **Merge** A into B | B gets A's files, A's title and aliases as Also called, A's folder links |
| **Delete** a song | its aliases and folder links go; its files return to To sort as if new (they may join other songs or regroup into a suggestion); files shared with another song stay there; Undo, no confirm |
| **Not a song file** | hidden in the Not song files list; still downloaded |
| **Skip folder** | the folder isn't downloaded (now or later), listed in the source's menu; "Free space (1.2 GB)" there deletes its local files only when pressed |
| merge / split **suggestions** | drag a suggested row onto another, or a chip out to a new suggestion |

**Offers** are one-time lines under the song, default No, never stored as rules:

- **Gather** after a drag: when the dragged file's cleaned key has something meaningful left (≥ 2 letters, not only noise words, not another song's name): "Also collect files named ***hw …***? 2 more in To sort match → Yes". Only files in To sort; each becomes placed by hand.
- **Better match** after Create, Rename, or a new alias: "*Harbour Waltz Reprise* better matches 1 file in *Harbour Waltz* → Move it". Only files placed **auto**; files placed by hand are never offered.

## Versions of a sheet

Sheets in one song with the same cleaned key that differ only by a date or version word are **versions**: one chip showing the newest (by the date in the name, else the server's change time), "2 versions", older ones in the chip's menu. The player opens the newest; when a newer one arrives it switches to it and marks it new, unless the user deliberately picked an older version (that choice is remembered, as today). Recordings with dates are separate rehearsals, not versions.

## Labels and order

- Label of a file: its extras plus a container folder's name (`Rehearsal 9.10.2026 · 2`, `chords`, `Bass`); none left → the file name. Editable; an edited label is stored.
- Order: the main recording first (key = title, no extras), then by folder and date; sheets newest first. Dragging a chip to the first place makes it the default.

## New files

A file that joined a song since the user last looked carries a **new** mark: a dot on its chip in the project screen, the "New (n)" filter there, and a dot on the song in the player's song list until the song is opened. The marks belong to this computer (in the practice memory), not to the shared sorting.

## Memory: `grouping.json` in the project

```json
{
  "songs": {
    "harbour-waltz": {"title": "Harbour Waltz", "also": ["Satamavalssi"], "folders": ["band:Harbour Waltz"]}
  },
  "files": {
    "band:Harbour Waltz/Harbour Waltz.mp3": {"songs": ["harbour-waltz"], "by": "auto"},
    "band:Rehearsal 9.10/HW_take3.wav": {"songs": ["harbour-waltz"], "by": "hand", "label": "Ending"},
    "band:Songbook.pdf": {"songs": ["harbour-waltz", "night-ferry"], "by": "hand"},
    "band:invoice.pdf": {"songs": [], "by": "hand"}
  },
  "first": {"harbour-waltz": ["band:Harbour Waltz/Harbour Waltz.mp3"]}
}
```

- Every placed file is stored (sticky); `"songs": []` = not a song file. A file not in `files` has no song and goes through matching. Entries for files that disappeared stay, so they apply again if the file comes back; their chips show "removed on server".
- Song ids are stable (title slug, `-2` if taken), so renames keep the practice memory.
- Skipped folders live with the source (`skip = ["Old"]` in the project file), because the downloader uses them.
- `songs.json` is **derived** from the files and this memory, for the players; it's never edited by hand. Today's hand edits and `extra_folders` are moved in once.
- The settings file carries `grouping.json` and the skipped folders, so a bandmate gets the same songs.

## Operations (Library API)

`grouping()`, `create(suggestions)`, `move(files, song)`, `also_add(files, song)`, `new_song(files, title)`, `rename(song, title, keep_old)`, `alias(song, add | remove)`, `link_folder(song, folder)`, `unlink_folder(song, folder)`, `merge(a, into)`, `delete(song)`, `not_song(files)`, `skip_folder(source, folder)`, `free_space(source)`, `label(file, text)`, `make_first(file)`, `accept(offer)`, `undo()` / `redo()`. Each writes `grouping.json` atomically and rebuilds `songs.json`.

## Open (tasks)

- Edit distance and fuzzy similarity: `rapidfuzz` or the standard library (T87).
- Thresholds and noise words tried on the corpus (T86).
