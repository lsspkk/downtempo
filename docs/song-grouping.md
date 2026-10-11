# Song grouping: files → songs (plan)

**Summary**: Built (T86–T91, T98, T102, T112): the pure core (cleaning, matching, suggestions, labels, offers) passes its corpus; memory, operations with undo, the catalog and the player side are built; the screen for it is [project-screen.md](project-screen.md). Hybrid: the program proposes songs, the user approves the list. Songs' titles, also-called names and 📁 folder links are magnets for files with no song; exact, whole-word and small-typo matches join, the rest waits in To sort. Placement is sticky; drags never make rules, only one-time offers.

The business logic behind [purpose.md](purpose.md): a project's files, from any folder layout and any number of sources, become songs. Decided with the user in T100 (questions 1–13); UI: [project-screen.md](project-screen.md). It replaces the folder-rules plan of T53.

## In short

- **Hybrid**: the program proposes songs, the user approves the list, and from then on files follow that list.
- Each song has **magnets**: its title, zero or more **Also called** names, and **📁 folder links**. A file with no song joins the song whose magnet it matches.
- **Placement is sticky**: once a file is in a song, it only moves when the user moves it. Magnets act only on files that have no song yet.
- No rule is ever learned behind the user's back. Every lasting choice (an alias, a folder link, a skipped folder) is made deliberately and shown where it can be removed. Convenience actions (gathering similar files, moving files to a better-matching new song) are **one-time offers**.

## Words

| Word                      | Meaning                                                                                  |
| ------------------------- | ---------------------------------------------------------------------------------------- |
| song                      | a title, its magnets, and its files (sheets and recordings; either kind may be missing)  |
| magnet                    | title, Also called name, or 📁 folder link of a song                                     |
| To sort                   | files with no song: grouped into **suggested songs** where they share a name, else loose |
| suggested song            | a proposed title + files, with ☑; nothing is created without a click                     |
| placed _auto_ / _by hand_ | how a file got into a song: by a magnet or Create, or by the user's drag                 |
| not a song file           | a file the user set aside; hidden                                                        |
| skipped folder            | a folder of a source that isn't downloaded                                               |

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
4. Whole words only: _Vanhassa_ is not _vanha_.

## Matching a file that has no song

Against every magnet of every song (all sources alike):

| Match                                             | Result                                                                                        |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| the file is directly in a song's 📁 linked folder | joins that song, unless its own name matches **another** song's title or alias (then To sort) |
| key = a title or alias                            | joins                                                                                         |
| a title or alias is contained as whole words      | joins                                                                                         |
| a title or alias within the **typo tolerance**    | joins                                                                                         |
| only similar (fuzzy, beyond the tolerance)        | To sort, the song shown as a one-click suggestion                                             |
| nothing                                           | To sort                                                                                       |

- **Typo tolerance**, letters different (edit distance) by the magnet's length: under 5 letters 0, from 5 letters 1, from 10 letters 2.
- **Longest magnet wins** (_Harbour Waltz Reprise_ over _Harbour Waltz_). Two different songs matching equally, or a file containing two different titles → To sort.
- Files that join are marked **new** (see [New files](#new-files)).

## Suggested songs

Files left in To sort are grouped: the same cleaned key (within the typo tolerance) makes one **suggested song**, titled with the most common original spelling. A **song folder** (a folder holding media directly whose name isn't a date, noise or type word like _Audio_, _PDF_, _Old_) makes a suggestion from all its files, with the folder as its 📁 link-to-be. A song folder inside a song folder is its own suggestion (a medley).

On the first visit every file is in To sort, so the suggestions are the proposed song list ("Create selected (12)"). Later, only unmatched new files make suggestions; the song list never grows by itself.

## What the user's actions do

| Action                        | Effect                                                                                                                                                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Create** a suggestion       | a song with that title; a song-folder suggestion also gets its 📁 link; then the new magnets pull matching To sort files at once; a **better-match offer** if it fits auto-placed files of other songs better |
| **Drag** files into a song    | placed by hand (pinned); then a **gather offer**                                                                                                                                                              |
| **Ctrl+drag** / Also add to…  | the file is in both songs (×2); sharing is always by hand                                                                                                                                                     |
| **New song** from files       | title prefilled from the first file's cleaned name, editable                                                                                                                                                  |
| **Rename**                    | files stay; "Keep _old name_ as also called" ☑ by default (untick to fix a wrong title)                                                                                                                       |
| **Also called** + / ×         | add or remove an alias; removing doesn't move files already placed                                                                                                                                            |
| 📁 **link** + / ×             | link a folder by hand, or remove a link; files already placed stay                                                                                                                                            |
| **Merge** A into B            | B gets A's files, A's title and aliases as Also called, A's folder links                                                                                                                                      |
| **Delete** a song             | its aliases and folder links go; its files return to To sort as if new (they may join other songs or regroup into a suggestion); files shared with another song stay there; Undo, no confirm                  |
| **Not a song file**           | hidden in the Not song files list; still downloaded                                                                                                                                                           |
| **Skip folder**               | the folder isn't downloaded (now or later), listed in the source's menu; "Free space (1.2 GB)" there deletes its local files only when pressed                                                                |
| merge / split **suggestions** | drag a suggested row onto another, or a chip out to a new suggestion                                                                                                                                          |

**Offers** are one-time lines under the song, default No, never stored as rules:

- **Gather** after a drag: when the dragged file's cleaned key has something meaningful left (≥ 2 letters, not only noise words, not another song's name): "Also collect files named **_hw …_**? 2 more in To sort match → Yes". Only files in To sort; each becomes placed by hand.
- **Better match** after Create, Rename, or a new alias: "_Harbour Waltz Reprise_ better matches 1 file in _Harbour Waltz_ → Move it". Only files placed **auto**; files placed by hand are never offered.

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
    "harbour-waltz": { "title": "Harbour Waltz", "also": ["Satamavalssi"], "folders": ["band:Harbour Waltz"] }
  },
  "files": {
    "band:Harbour Waltz/Harbour Waltz.mp3": { "songs": ["harbour-waltz"], "by": "auto" },
    "band:Rehearsal 9.10/HW_take3.wav": { "songs": ["harbour-waltz"], "by": "hand", "label": "Ending" },
    "band:Songbook.pdf": { "songs": ["harbour-waltz", "night-ferry"], "by": "hand" },
    "band:invoice.pdf": { "songs": [], "by": "hand" }
  },
  "first": { "harbour-waltz": ["band:Harbour Waltz/Harbour Waltz.mp3"] }
}
```

- Every placed file is stored (sticky); `"songs": []` = not a song file. A file not in `files` has no song and goes through matching. Entries for files that disappeared stay, so they apply again if the file comes back; their chips show "removed on server".
- Song ids are stable (title slug, `-2` if taken), so renames keep the practice memory.
- Skipped folders live with the source (`skip = ["Old"]` in the project file), because the downloader uses them.
- `songs.json` is **derived** from the files and this memory, for the players; it's never edited by hand. Today's hand edits and `extra_folders` are moved in once.
- The settings file carries `grouping.json` and the skipped folders, so a bandmate gets the same songs.

## Operations (Library API)

`grouping()`, `create(suggestions)`, `move(files, song)`, `also_add(files, song)`, `new_song(files, title)`, `rename(song, title, keep_old)`, `alias(song, add | remove)`, `link_folder(song, folder)`, `unlink_folder(song, folder)`, `merge(a, into)`, `delete(song)`, `not_song(files)`, `skip_folder(source, folder)`, `free_space(source)`, `label(file, text)`, `make_first(file)`, `accept(offer)`, `undo()` / `redo()`. Each writes `grouping.json` atomically and rebuilds `songs.json`.

## Decided while building

One line per decision the plan didn't make: date, task, decision, reason (a corpus case or a saved page). How to decide, first rule that answers wins: (1) the plan decides (no learned rules, no settings to learn); (2) the grouping corpus (`data/scratch/grouping-corpus/`, run `data/scratch/grouping_run.py`) decides between options, ties go to the simpler one; (3) simplest that works, stdlib; (4) write the decision here; (5) ask the user only for what they would see or do differently. A planned rule that gives a bad result isn't quietly changed: the case goes to the corpus README's Doubts.

### Matcher research (T87)

**Pick: the standard library only, no `rapidfuzz`.**

- **Typo tolerance**: our own Levenshtein function (~15 lines, stops early when the distance passes the allowed 0 / 1 / 2). `difflib` has no edit distance: its docs describe `SequenceMatcher` (a matching-block ratio), not Levenshtein ([web/python-difflib.txt](web/python-difflib.txt)). `rapidfuzz.distance.Levenshtein.distance(…, score_cutoff=n)` does the same, returning `n + 1` when over ([web/rapidfuzz-levenshtein.txt](web/rapidfuzz-levenshtein.txt)), so it saves the 15 lines and nothing else.
- **rapidfuzz** passes the criteria (MIT; Python ≥ 3.11 with cp312 wheels for Linux, Windows and macOS (arm64 + x86_64); release 3.14.6 on 2026-08-30: [web/rapidfuzz-pypi.txt](web/rapidfuzz-pypi.txt)), but criterion (e) fails: no named corpus case needs it. Its `token_set_ratio` also returns 100 whenever one string's words are a subset of the other's ([web/rapidfuzz-fuzz.txt](web/rapidfuzz-fuzz.txt)); for us that case is already a whole-word match, so it would add false "similar" results.
- **Fuzzy similarity** (the one-click "Harbour Waltz?" suggestion, beyond the tolerance), on the accent-folded keys: the **same set of words** in any order (`waltz harbour`), or `difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() ≥ 0.8`. `autojunk=False` because the automatic junk heuristic is meant for long sequences ([web/python-difflib.txt](web/python-difflib.txt)); the docs call a ratio over 0.6 "close", so 0.8 is stricter on purpose: a wrong suggestion costs a click and trust. Start at 0.8; T88's corpus run must confirm `Waltz Harbour` and `Yo ja paiva` get a `maybe` and `Jug` vs `Jig` (ratio 0.67) doesn't.
- **Unicode**: file names are normalised to **NFC** (`unicodedata.normalize`, [web/python-unicodedata.txt](web/python-unicodedata.txt)): `ä` becomes one code point whether it arrived as NFC or NFD (macOS, some clouds), and stays a different letter from `a`. **Not NFKC**: it would fold compatibility characters such as ligatures (`ﬃ` → `ffi`, [web/unicode-uax15.txt](web/unicode-uax15.txt)), which doesn't help song names and can change a title the user sees. Picard does the same for file names: tries the NFC and NFD spellings of a path ([web/picard-util.txt](web/picard-util.txt)).
- **Accent-folded keys for fuzzy matching only**: NFKD, drop combining marks. So `Yo ja paiva` is _similar_ to `Yö ja päivä` (a `maybe`) while the tolerance rules still count `ä` ≠ `a` (a join needs the real letters).
- **beets** (`string_dist`, [web/beets-distance.txt](web/beets-distance.txt)): lower case, `&` → `and`, "something, the" = "the something", brackets, `feat.`, `part n` weigh little, then Levenshtein over letters and digits only, divided by the longer length. Taken as principles: brackets and "part n" are extras (already ours); `&` ≈ `and` (T88: treat `&` as the word `and` in keys; `Bread & Butter Reel` in the real data); distance counts letters only, spaces and punctuation don't (already ours: "spaces not counted"). Not taken: unidecode (it would make `ä` = `a`; we keep that only for fuzzy).
- **Picard** (`similarity2`, [web/picard-similarity.txt](web/picard-similarity.txt); GPL, so principles only): compare word by word, each word to its best match in the other string, penalise the unmatched rest. That is what the "same set of words" test does in its simplest form; if word order plus a typo (`Walz Harbour`) turns out to matter, T88 can take it per word.
- **What would change the decision**: a corpus case that `SequenceMatcher` + word set misses and a per-word typo compare can't catch → `uv add rapidfuzz` then.

### While building

- 2026-10-11 T86 Names the plan's lists lacked, added for the corpus: type words `recordings`, `äänitykset`, `tallenteet`; noise `part`, `parts`, `soprano`, `sopraano` (cases `finnish`, `flat`, `parts`).
- 2026-10-11 T86 A file with a name conflict (in one song's folder but named like another; or containing two songs' titles) goes to To sort as **loose** with a `why`, with `maybe` = the song its name points to; never a suggested song (cases `update`).
- 2026-10-11 T86 A fuzzy near-miss is loose with `maybe`, never a suggested song (cases `typos-order`, `finnish`).
- 2026-10-11 T88 Split by stage, not one file: `names.py` (clean, typo tolerance, similar), `shapes.py` (the dataclasses), `matching.py` (magnets, hits, longest wins), `suggesting.py` (song folders, grouping by key), `arranging.py` (labels, versions, order, why), `grouping.py` (`group`), `offers.py` (gather, better match). All pure.
- 2026-10-11 T88 `final`, `uusi`, `new` are version words only at the end of a name (`New Orleans Blues` keeps `New`); `v2`, `take 2` forms anywhere. `new` is also a junk word (case `clutter`: `New Recording 12`). A word like `scan7` or `IMG_2041` is junk once its digits are off.
- 2026-10-11 T88 `&` is the word `and` in a key; the title keeps `&` (e.g. `Bread & Butter Reel`).
- 2026-10-11 T88 A date like `3.10` (day.month, no year) is a date extra with no `date` value; an impossible one (`31.2.`) stays text.
- 2026-10-11 T88 Equal word spans from different songs: the smaller edit distance wins, equal distance is a tie (loose). Otherwise the longest wins as planned.
- 2026-10-11 T88 Sheet versions are decided by key + `Cleaned.tags` (extras that are not dates, numbers or versions: noise words, brackets, a musical key); `Song in G` is not a version of `Song`. Newest = date in the name, else the file's modified day (case `two-sources`: an undated copy changed later is the newer one).
- 2026-10-11 T88 Recording order adds "fewest extras" before the date: with no plain `Song.mp3`, `Song E.mp3` comes before `Song E - pohjat.mp3` (real data).
- 2026-10-11 T88 Fuzzy threshold stays 0.8 (corpus: `Waltz Harbour` and `Yo ja paiva` get their `maybe`; `Jug` vs `Jig`, 0.67, doesn't). The song-folder guard works as in the brief (cases `sets`, `two-sources`, `finnish`): `Set 1/`, `Spring Show/`, `Songs/` and `Äänitykset/` are not songs.
- 2026-10-11 T88 Corpus: 15 cases, 0 differences; the real project's suggestions equal today's 9 songs; "Create all, then group again" gives the same songs; the result is the same for any file order.
- 2026-10-11 T89 Parts: `memory_file.py` (the `grouping.json` format, unknown keys kept at every level), `sorting.py` (`Sorting`: operations, undo / redo, pending offers), `skipping.py` (skipped folders and freeing space); `Library` has `sorting`, `files()`, `skip_folder`, `unskip_folder`, `skipped_size`, `free_space`. `free_id` moved to `sources.py`, `write_json` to `jsonfile.py` (both re-imported where they were used).
- 2026-10-11 T89 `Sorting.grouping()` saves the matches it made as auto placements every time it runs, and every operation settles before it changes anything, so a placement is stored before a later change can move it.
- 2026-10-11 T89 Undo / redo are stacks of memory snapshots in the `Sorting` object (50 deep, not saved); skipping and un-skipping a folder are not in them (un-skip is the undo). Pending offers live in `Sorting.offers` until the next operation; `accept` and `dismiss` remove one.
- 2026-10-11 T90 `songs.json` is written by `publishing.py` (`rebuild`, `publish`, `preview`, new marks); `Sorting.run`, undo, redo and an import publish it after every change. `rebuild(mark_new=True)` (after a download and by `catalog`) marks the files that joined a song; sorting operations don't.
- 2026-10-11 T90 `CatalogDiff` is songs, new / gone song titles, files joined per song, and the To-sort count; the sentence is `5 new files: 4 joined songs, 1 to sort` (the count of files that joined a song).
- 2026-10-11 T90 / T96.1 A project's first rebuild no longer makes a song of every suggestion (it did until the To sort tab existed): new files wait in Unknown files, where all suggestions are ticked; the CLI has `downtempo songs --create`.
- 2026-10-11 T90 The upgrade of an old catalog links the folder of each old song's first own file, keeps labels edited by hand (not the generated rehearsal ones), skips a fallback song named after an extra folder, moves practice keys to ids, and runs in `Workspace.__init__` per project (`upgrade.py`).
- 2026-10-11 T89 `link_folder` refuses a folder another song already has; `delete` leaves a file with no song as if new, so it may join another song by name at once (the plan says so); `rename` without `keep_old` also drops an also-called name equal to the new title.
