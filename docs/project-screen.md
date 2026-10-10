# Project screen: sources and songs (UX plan)

A full-screen view of the current project: where its files come from, and which files make up each song. It's the downloader UI and the song-grouping UI in one place, because the user's question is "are my group's songs here and right?", not "what did the downloader do". Purpose: [purpose.md](purpose.md); logic and words (magnet, To sort, offers): [song-grouping.md](song-grouping.md); principles: [ux.md](ux.md). Decisions from the T100 interview. Replaces the planned Sources dialog (T46).

## User picture

The [practising musician](ux.md#the-user), at the desk now, not with the instrument: setting up the project the first time, or after an update that brought new files. Mouse or trackpad, small laptop (1280×720). Not technical: knows the songs by name, not the folder layout. Visits rarely and briefly, so everything must be visible without learning (heuristics #6, recognition over recall).

## Frame

```
┌─ ← Practice │ My band ▾ │ Band share · OneDrive · 2 h ago │ Choir sheets · Google Drive │ + Add folder │ ⟳ Update │ ↶ ↷ ─┐
│  [ To sort (14) ]  [ Songs (32) ]                                                                                   │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  (the tab's content)                                                                                                │
```

- **Header**: back to practice (Esc), the project name with its menu (switch, new, rename, export, delete; [projects.md](projects.md)), one chip per source with its state (updated 2 h ago / downloading 45 % / ⚠ sign in again) and its menu, + Add folder, ⟳ Update, Undo / Redo.
- **Two tabs**: **To sort** (deciding what's new) and **Songs** (keeping existing songs right). The screen opens on To sort when it isn't empty, else on Songs.

## To sort tab

```
│ ☑ Select all   [ Create selected (12) ]                                     │ Your songs          │
│ ☑ Night Ferry ✎      ♪ Night Ferry   📄 chords            Band share / Night Ferry │ Balkan Reel        │
│ ☑ Old Mill Reel ✎    📄 Old Mill Reel                     Band share /             │ Harbour Waltz      │
│ ☐ Intro ✎            ♪ intro   ♪ Intro 2                  Band share / Demos       │ Night Ferry (…)    │
│ … 9 more                                                                             │ …                  │
│ Loose files (2)                                                                      │                    │
│ ♪ HW_take3.wav ▶  Harbour Waltz?    📄 scan7.pdf 👁                                   │ (drop targets)     │
│ Not song files (1) ▸                                                                 │                    │
```

- **Suggested songs**, one row each: ☑, the title (edit in place), file chips, and the source folder (📁 when Create will link it). Rows are A–Z; all are ticked on the first visit, and later ones are ticked by default too.
- **Create selected (n)** creates the ticked rows. New magnets pull matching loose files at once ("+2 files").
- Drag a row onto another row to **merge suggestions**; drag a chip out of a row to make it a suggestion of its own.
- **Loose files**: no suggestion of their own. A fuzzy match is shown as a one-click suggestion ("Harbour Waltz?").
- **Your songs** (right, about 220 px): existing songs by title only, with search. Drop a row or chips onto a title to add them to that song.
- **Not song files**, folded: files set aside, each with "Back to To sort".

## Songs tab

```
│ [Search songs…]   [All] [New (4)] [Needs a look (1)]                                                            │
│ Harbour Waltz ✎   📄 Harbour Waltz · 2 versions   📄 chords   ♪ Harbour Waltz   ♪ Rehearsal 9.10 · 1 •   ♪ Ending ✋ │
│   ↳ Also collect files named "hw …"? 2 more in To sort match   [Yes] [No]                                       │
│ Night Ferry ✎     ♪ Night Ferry   ♪ Rehearsal 9.10 · 2                                    no sheet              │
│ Old Mill Reel ✎   📄 Old Mill Reel   📄 Songbook ×2                                        no recording          │
```

- One row per song, A–Z: title, sheet chips, recording chips. "no sheet" / "no recording" in grey where a kind is missing; it's normal, not an error. Chips wrap; long names end in "…" with the full name in the tooltip.
- **Filters**: All, **New (n)** (songs with files that joined since the last look), **Needs a look** (songs with a pending offer or a file "removed on server").
- **Offers** appear as one line under their song (gather after a drag, better match after Create / Rename / new alias), with Yes and No; No is the default and they go away on their own when the screen closes.

## File chip

📄 or ♪, the label, and marks: **•** new, **✋** placed by hand, **×2** in two songs, **2 versions** (sheets), **removed on server**. Tooltip: source and full path (`Band share / Rehearsal 9.10.2026 / HW_take3.wav`) and why it's here ("name contains *harbour waltz*", "in the linked folder *Harbour Waltz*", "you placed it"). ▶ plays the first 15 s (a plain audio element, no tempo engine); 👁 shows the PDF's first page. The chip's menu: Move to…, Also add to…, Not a song file, Back to To sort, Rename label, Make first, Older versions (sheets), Skip folder *X*.

## Song edit box

Opens from ✎ or `F2` on a title:

```
Title     [ Satamavalssi                  ]
          ☑ Keep "Harbour Waltz" as also called          (only after a rename)
Also called   ( Harbour Waltz × ) ( HW Satama × )  + name      matches 6 files
Folders       ( 📁 Band share / Harbour Waltz × )  + folder
              [ Merge into… ]   [ Delete song ]                       [ Done ]
```

The count next to the names shows what the magnets reach, live, as you type. Removing a name or folder never moves files already in the song.

## Actions

Every drag has a click and key alternative (ux #6); every change can be undone (ux #8). Nothing asks "are you sure" except deleting downloaded files ("Free space").

| Do | Mouse | Keyboard / click |
|---|---|---|
| create suggested songs | — | tick rows, **Create selected** |
| move files to a song | drag chips onto a song row or a title in Your songs | select (click, Ctrl/Shift+click), `M` or **Move to…** → type the song, Enter |
| add to a second song | Ctrl+drag | **Also add to…** |
| new song from files | drag onto ＋ New song | `N` with files selected |
| set aside | drag to Not song files | `Delete` |
| back to To sort | drag to the To sort tab | chip menu |
| rename song, aliases, folders | ✎ | `F2` |
| merge songs | drag a song title onto another | edit box → Merge into… |
| delete a song | — | edit box → Delete song (Undo) |
| choose the default file | drag the chip to the first place | chip menu → Make first |
| skip a folder | — | chip menu → Skip folder *X*, or the folder picker |
| accept an offer | Yes | `Enter` while it's focused |
| undo / redo | ↶ ↷ in the header | Ctrl+Z / Ctrl+Shift+Z |

Changes are saved at once (no Apply). The player's song list follows when the user returns to practise; the open song stays open unless its files moved away.

## Source menu

From a source chip in the header: rename, change folder (the picker), **Skipped folders** (list, each with ×), **Free space (1.2 GB)** when skipped folders still have local files, remove the source (keep or delete its files), signed-in account + Sign out.

## Getting there

- **First start** (no project): the player shows "Paste a link to your group's shared folder". Then: sign-in card if needed (code, Copy, Open page, time left, Cancel) → **folder picker** (the share's tree with ♪/📄 counts and a ☐ Skip per folder; the shared folder itself is preselected; the project name is prefilled from it) → "About 12 songs from 31 files, 180 MB" (grouping run on the listing) → Download. The project screen opens on To sort, filling in as files arrive; **Create selected** → Songs → ← Practice.
- **Later**: the Songs drawer gets a "Sort songs and sources" button at the bottom, with a badge while To sort isn't empty (state visible, ux #4). It's not a frequent action, so no single-letter key (ux #2).
- **Add folder** reuses link → sign-in → picker → preview; the new files meet the existing magnets, and only the rest lands in To sort.
- **Update** runs in the background; the source chip shows progress, also in the player's header while practising. Result: "5 new files: 4 joined songs, 1 to sort", clickable (opens New or To sort).

## Errors, in plain words with what to do

| Situation | Says |
|---|---|
| unknown link | "This isn't a OneDrive or Google Drive folder link. Copy the link from the Share button." |
| no access / removed | "The folder can't be opened: the link may have expired or you may lack access. Ask for a new link." |
| offline | "No internet connection. Your downloaded songs still work." + Retry |
| sign-in expired | the source chip says "Sign in again" and opens the sign-in card |
| file gone from the server | its chip says "removed on server"; the local copy stays until the user removes it |

## Player side

- **New marks**: a dot on songs in the song list that got new files, until the song is opened.
- **Sheet versions**: the player opens the newest version unless the user picked another one for this song.
- **A song without recordings**: the controls pane shrinks to the title and "No recording"; the sheet gets the space.
- **A song without sheets**: a large waveform instead of an empty "No sheet music" box.

## Checks (ux.md checklist)

- 1280×720: the Your songs column ≤ 220 px; rows wrap their chips; source chips collapse to "2 sources ▾" when they don't fit.
- Drag and drop runs in the page's own script (like `loop_editor.js`); the server only receives "these file ids → that song". T92 picks the method.
- Dark mode: chip kinds and marks differ by icon and outline, not only by colour.
