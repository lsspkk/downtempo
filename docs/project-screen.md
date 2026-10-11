# Project screen: sources and songs (built)

**Summary**: Built (T93, T111, T61–T63, T97, T94, T95, T101, T82, T67, T96, T124): the screen opens from "Edit song list" in the song list, with both tabs, every sorting action by click, key and drag (Ctrl+drag = also add, a title onto a song = merge), Undo / Redo, the song edit box, ▶ / 👁 previews, the sources in the header (state, menu, + Add folder, ⟳ Update) and Add folder from a pasted link (also the first start); the ☰ main menu (T82, T67, T118, T120: projects, new, Project settings, Export / Import, delete, the player's settings), Project settings with Change link (T116), the To sort extras (T96: drag a suggestion onto another, "+n files joined", the Removed on server filter). Renaming a source is built (T114); a new link for a source is Change link… (T116), which also picks another folder when the new share lacks the old one. Plan: A full-screen view with the project menu (switch, new, rename, export, delete) and sources in the header and two tabs: To sort (☑ list of suggested songs, Create selected, drop on your songs) and Songs (rows of file chips, drag between songs, one-time offers). Every drag has a key / click alternative and Undo.

A full-screen view of the current project: where its files come from, and which files make up each song. It's the downloader UI and the song-grouping UI in one place, because the user's question is "are my group's songs here and right?", not "what did the downloader do". Purpose: [purpose.md](purpose.md); logic and words (magnet, To sort, offers): [song-grouping.md](song-grouping.md); principles: [ux.md](ux.md). Decisions from the T100 interview. Replaces the planned Sources dialog (T46).

## Built so far

**Names on screen** (the user's choice, T113): the button is **Edit song list**; the tabs are **Unknown files** (files in no song yet; called *To sort* in this plan and in the code) and **Song files**. "Back to To sort" reads **Back to unknown files** / **Not in this song**. New UI text uses these names.

| Part | File | Does |
|---|---|---|
| frame | `frontends/nicegui/project_screen.py` | maximized dialog from "Edit song list (n unknown)" in the song list; header: ← Practice (Esc), project name, the sources (`sources_bar.py`), Undo / Redo (Ctrl+Z, Ctrl+Shift+Z / Ctrl+Y); tabs Unknown files (n) / Song files (no count), opens on To sort when it isn't empty; `do(action)` runs one `library.sorting` operation, shows a `UserError`, refreshes both tabs; keys while open (the player's are off); playback pauses on open; songs reload on close |
| main menu | `main_menu.py`, `settings_file.py` | ☰ at the top left of the player (T120; not in this screen, where ← Practice is top left and the way out): the projects with song counts (✓ the current one, others greyed while a download runs, a search field from 9 on), New project…, Project settings… (a name; the welcome page follows), Export… / Import… (the settings file: text + Copy + Save as file…; paste or Open a file…, the preview as a new project or into this one, Import, then Download now?), Delete project… (the one question, with files and size), then the player's Player settings…, Keyboard shortcuts, Dark mode. Switching saves, stops, and builds the page again; from the screen, the screen opens again on the same tab |
| project settings | `project_settings.py`, `folder_actions.py`, `change_link.py` | [below](#project-settings): the name; per folder link, folder, skipped folders, Rename…, Remove…, the last error; + Add folder; the sign-in |
| sources | `sources_bar.py` | one chip per source, for watching: name + "checked 2 h ago" / "45 %" / "waiting" / "⚠ sign in again" (the last update's error, full text in the tooltip); its menu: Update this folder, Folder settings… (Project settings at that folder); then + Add folder, ⟳ Update (Cancel and % while one runs), the last result line |
| Add folder | `add_folder.py`, `folder_picker.py` | link (checked without network; plain error under the field) → sign-in card if asked → folder picker (breadcrumbs, ♪ / 📄 counts, ☐ Skip, ›) → "About 4 songs from 8 files, 32.7 MB" (`library.preview_folder`), the suggested titles, files joining your songs, the folder's name here, the project's name on the first start → Download: the source is saved, its download starts, the screen opens on Unknown files and fills in every 1.5 s as files arrive. Nothing is saved before Download |
| downloads | `updates.py`, `sign_in.py`, `welcome.py` | one download at a time for the whole page (song list button, ⟳ Update, Add folder); the sign-in card opens for any job; the empty page is the welcome ("Paste a link to your group's shared folder") or "Edit song list" / "Check for new files" when there are folders but no songs |
| To sort | `sort_tab.py` | the **Your songs** column (220 px, search): drop chips or a whole suggestion (its ⠿) on a title; drop a suggestion or chips onto another suggestion = one song of both (that one's title and folder); while dragging, zones New song / Not a song file (a chip out of a suggestion = split); Create selected says "and n more files joined them" when the new titles pull other unknown files; nothing is created by itself (T96.1: a fresh project's files wait here, all ticked); suggested songs with ☑ (all ticked), editable title, chips, 📁 folder; Select all; Create selected (n); row menu: Add to a song…, Not song files; loose files: the fuzzy "Title?" button, Move to…, Not a song file; Not song files folded, each with Back to To sort |
| Songs | `songs_tab.py` | search, filter chips shown only when they have songs: New files n, Suggestions n (a pending offer), Removed on server n (`checked.json` keeps what the last check found gone, `checks.py`); none selected = every song, click a selected one again to turn it off; one row per song (sheets, then recordings, "no sheet" / "no recording"; an empty song says so with Delete song); click chips to select (several songs at once, Shift+click a range); bar: Move to… (`M`), Also add to…, New song… (`N`), Not a song file (`Delete`), Not in this song; **drag** chips (a selected chip drags the selection) onto a song row (Ctrl = also add; onto another chip of its own song = make it the default) or onto the drop zones that appear while dragging (New song, Not a song file, Back to unknown files); drag a title onto another song = merge; a chip's **right-click menu**: Make it the default, Rename label…, Move to…, Not in this song, Not a song file, its older versions, Skip the folder; offers as lines under their song with Yes / No |
| song edit box | `song_box.py` | a click on a title (✎) or `F2` with a file of the song selected: title (☑ keep the old one as also called, shown once it changes), also-called chips (× / + name, Enter), 📁 folder chips (× / + folder from the project's folders), live "These names and folders match n files" (`Sorting.reach`), Merge into…, Delete song, Done (Enter); every change saved at once and undoable |
| dragging | `drag.js` | HTML5 drag events caught once on the document: chips `[data-file]` / `[data-from]`, titles `[data-title]`, targets `[data-drop]`; highlight in the page; one `screen_drop` event per drop, turned into one sorting call by `ProjectScreen.drop` |
| previews | `previews.py` | ▶ on a recording chip (on hover) plays its first 15 s in an audio element (again: stop; closing the screen stops it); 👁 on a sheet chip shows the first page; `/preview/<source>/<path>` serves only the current project's downloaded media (Range works) |
| pieces | `chips.py` | file chip (♪ solid / 📄 dashed outline, label, • new, ✋ by hand, ×2, n versions; tooltip: source / path + why), `pick_song` (type to search, or a new title → new song), `ask_text` |

**Rename…** in the source menu (T114) goes through `Library.rename_source` (`renaming.py`): the file ids (`source:path`) in the sorting, the new marks, the last checks and the practice memory's paths move with the name, the undo history is cleared, and the page is built again (like a project switch) so nothing holds old paths. **Change folder** on its own is not built: the local files would have to move or go depending on how the two folders nest. Change link… covers the real case (a re-shared folder): same folder found → only the link changes; otherwise the picked folder is downloaded into the same place and files it lacks show as removed on server.

How to add to it: a new action is one `screen.do(lambda: library.sorting.<op>(…))` call (the refresh and the error message come with it); widgets that start an action may be deleted by the refresh, so code after `do` runs in `with screen.dialog:` (done inside `do`). A multi-song move is one undo step (`Sorting.move_from`). Dragging (T94) should end in the same calls.

## User picture

The [practising musician](ux.md#the-user), at the desk now, not with the instrument: setting up the project the first time, or after an update that brought new files. Mouse or trackpad, small laptop (1280×720). Not technical: knows the songs by name, not the folder layout. Visits rarely and briefly, so everything must be visible without learning (heuristics #6, recognition over recall).

## Frame

```
┌─ ← Practice │ My band ⋮ │ Band share · OneDrive · 2 h ago │ Choir sheets · Google Drive │ + Add folder │ ⟳ Update │ ↶ ↷ ─┐
│  [ To sort (14) ]  [ Songs (32) ]                                                                                   │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  (the tab's content)                                                                                                │
```

- **Header**: back to practice (Esc), the project name with its menu ([below](#project-menu)), one chip per source with its state (updated 2 h ago / downloading 45 % / ⚠ sign in again) and its menu, + Add folder, ⟳ Update, Undo / Redo.
- **Two tabs**: **To sort** (deciding what's new) and **Songs** (keeping existing songs right). The screen opens on To sort when it isn't empty, else on Songs.

## To sort tab

```
│ ☑ Select all   [ Create selected (12) ]                                     │ Your songs          │
│ ☑ Night Ferry ✎      ♪ Night Ferry   📄 chords            Band share / Night Ferry │ Old Mill Reel        │
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
│ [Search songs…]   ( New files 4 )  ( Suggestions 1 )  ( Removed on server 1 )                                     │
│ Harbour Waltz ✎   📄 Harbour Waltz · 2 versions   📄 chords   ♪ Harbour Waltz   ♪ Rehearsal 9.10 · 1 •   ♪ Ending ✋ │
│   ↳ Also collect files named "hw …"? 2 more in To sort match   [Yes] [No]                                       │
│ Night Ferry ✎     ♪ Night Ferry   ♪ Rehearsal 9.10 · 2                                    no sheet              │
│ Old Mill Reel ✎   📄 Old Mill Reel   📄 Songbook ×2                                        no recording          │
```

- One row per song, A–Z: title, sheet chips, recording chips. "no sheet" / "no recording" in grey where a kind is missing; it's normal, not an error. Chips wrap; long names end in "…" with the full name in the tooltip.
- **Filters** (T124): filter chips, the usual control for optional filters above a list (Material 3 filter chips, Gmail's Unread): **New files n** (songs with files that joined since the last look), **Suggestions n** (an offer to answer), **Removed on server n** (a file gone from the shared folder; the same words as the chip's mark). A chip shows only while it has songs, so the row is empty on a quiet day; no "All": with none selected every song shows, and a selected chip is clicked again to turn it off. The old toggle (All / New / Needs a look) offered empty filters and a vague name.
- **Offers** appear as one line under their song (gather after a drag, better match after Create / Rename / new alias), with Yes and No; No is the default and they go away on their own when the screen closes.

## File chip

📄 or ♪, the label, and marks: **•** new, **✋** placed by hand, **×2** in two songs, **2 versions** (sheets), **removed on server**. Tooltip: source and full path (`Band share / Rehearsal 9.10.2026 / HW_take3.wav`) and why it's here ("name contains *harbour waltz*", "in the linked folder *Harbour Waltz*", "you placed it"). ▶ plays the first 15 s (a plain audio element, no tempo engine); 👁 shows the PDF's first page. The chip's menu: Move to…, Also add to…, Not a song file, Back to To sort, Rename label, Make first, Older versions (sheets), Skip folder *X*.

## Project menu

T81, from [downloader-review.md](downloader-review.md) R15; built by T82 (switching), T67 (export / import), T118, T120 (☰, the user's call: "this is the main menu of the application"). Core: [projects.md](projects.md).

```
☰ ┌──────────────────────────────┐
  │ Projects                     │
  │ [Search projects]            │   from 9 projects on
  │ ✓ My band        41 songs  │
  │   Choir             9 songs  │
  │ New project…                 │
  │ ──────────────────────────── │
  │ Project settings…            │
  │ Export… / Import…            │
  │ Delete project…              │
  │ ──────────────────────────── │
  │ Player settings…             │
  │ Keyboard shortcuts         ? │
  │ Dark mode                 ⏽ │
  └──────────────────────────────┘
```

- **Where**: ☰ at the top left, the app's main menu as the icon promises ([nng-hamburger-menus](web/nng-hamburger-menus.txt): hidden behind ☰ is fine for rare things, and all of this is rare). The project screen has no ☰ (the user's call): ← Practice is its top-left way out, and the menu is one click away after it. No single-letter key (ux #2); Tab reaches it, Esc closes it.
- **Projects first**: "which group am I practising" is the menu's main job; the current one has ✓, even when it's the only one.
- **Switch** (click another project): the practice memory is saved, playback stops (ux #7), the `Library` is swapped, songs and practice memory reload. From the song list, the player then opens that project's last song, paused; from the project screen, the screen shows the other project and ← Practice opens its last song, paused. The layout (dark mode, view, settings) belongs to the computer and stays.
- **While an update downloads**, the other projects are greyed with the tooltip "Wait for the download to finish, or cancel it": a job belongs to one project, and one job runs at a time.
- **New project…**: a small dialog with one name field (Enter creates, Esc cancels). The new project becomes current and the screen shows the first-start flow (paste a link, T97).
- **Renaming** is in Project settings (the name field; Enter or Save). Only the name changes; the folder doesn't move; the page shows the new name without reloading.
- **Delete project…**: the one question asked, since downloaded files go (ux #8): "Delete *Choir* with its 312 downloaded files (1.2 GB)? Its tempo and loops go too." Cancel is the default button. Deleting the current project switches to the first remaining one (A–Z); deleting the last one ends at the first start.
- **Long names** end in "…" with the full name in the tooltip (ux #10).
- **First start after the move into projects**: nothing to do and no message (ux #7): the project carries the first source's name, the player opens the last song as before, and the name above the song list shows that projects exist. The old files stay as `*.before-projects` in `data/`.

## Project settings

T116 (the user's idea, T115–T119): one place for how the project is set up, with room for more settings. Opened from ☰ → Project settings…, a folder chip's Folder settings…, or the red status line (at that folder, outlined).

```
Project settings                                                    ✕
[ Project name: My band                         ]  Save
Shared folders                                         + Add folder
┌──────────────────────────────────────────────────────────────────┐
│ ☁ My band  checked 2 h ago                   Rename…  Remove…  │
│ ⚠ The folder can't be opened … Ask for a new link.    Try again  │   only after an error
│ Link     https://1drv.ms/f/…                  ⧉  [Change link…]  │
│ Folder   My band  in OneDrive                                  │
│ Skipped  Old sets                   Skipped folders…  Free 1.2 GB│
└──────────────────────────────────────────────────────────────────┘
Sign-in
OneDrive: me@example.com                                  Sign out
```

- **Visible, not in menus**: a settings page is visited on purpose, so every setting shows with its value; the actions sit beside what they change.
- **Change link…** (`change_link.py`): paste the new link (the current one is shown) → sign in if asked → `Library.has_folder` looks for the same folder in the new share. Found: "The new link has the same folder; your songs, sorting, tempo and loops stay." Not found: the folder picker, then "Files already downloaded stay; the ones the new folder doesn't have show as removed on server." Then **Save and check for new files** (`Library.change_link`, then a download of that folder). Nothing is saved before that button. After an error the button is filled, so the fix is the obvious next step.
- **Rename… / Skipped folders… / Free / Remove…** (`folder_actions.py`): the dialogs that were in the chip menu before T116; renaming a folder rebuilds the page (paths move, T114).
- **Sign-in**: per provider the folders use, with Sign out; sign-ins belong to the computer, not the project.

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

From a source chip in the header: **Update this folder** and **Folder settings…**, which opens [Project settings](#project-settings) at that folder; everything that changes a folder lives there (one home), the chips are for watching.

## Getting there

- **First start** (no project): the player shows "Paste a link to your group's shared folder". Then: sign-in card if needed (code, Copy, Open page, time left, Cancel) → **folder picker** (the share's tree with ♪/📄 counts and a ☐ Skip per folder; the shared folder itself is preselected; the project name is prefilled from it) → "About 12 songs from 31 files, 180 MB" (grouping run on the listing) → Download. The project screen opens on To sort, filling in as files arrive; **Create selected** → Songs → ← Practice.
- **Later**: **Edit song list (n unknown)** pinned at the bottom of the song list, the count while To sort isn't empty (state visible, ux #4). It's not a frequent action, so no single-letter key (ux #2). Setup (links, names, folders) is in ☰ → Project settings.
- **Add folder** reuses link → sign-in → picker → preview; the new files meet the existing magnets, and only the rest lands in To sort.
- **Update** runs in the background; the source chip shows progress, and the status line under the project's name in the song list while practising. Result: "5 new files: 4 joined songs, 1 to sort", clickable (opens New or To sort).

## Errors, in plain words with what to do

| Situation | Says |
|---|---|
| unknown link | "This isn't a OneDrive or Google Drive folder link. Copy the link from the Share button." |
| no access / removed | "The folder can't be opened: the link may have expired or you may lack access. Ask for a new link." In red on the status line and the folder's box in Project settings, where Change link… is the filled button |
| offline | "No internet connection. Your downloaded songs still work." + Retry |
| sign-in expired | the source chip says "Sign in again" and opens the sign-in card |
| file gone from the server | its chip says "removed on server"; the local copy stays until the user removes it |

## Player side

Built (T98, T102, 2026-10-11): `waveform.py`, the narrow pane in `layout.py` / `controls.py`, the dots in `song_list.py`, `pdf_picked` in `player.py`.

- **New marks**: a dot on songs in the song list that got new files, until the song is opened.
- **Sheet versions**: the player opens the newest version unless the user picked another one for this song.
- **A song without recordings**: the controls pane shrinks to the title and "No recording"; the sheet gets the space.
- **A song without sheets**: a large waveform instead of an empty "No sheet music" box.

## Checks (ux.md checklist)

- 1280×720: the Your songs column ≤ 220 px; rows wrap their chips; source chips collapse to "2 sources ▾" when they don't fit.
- Drag and drop runs in the page's own script (like `loop_editor.js`); the server only receives "these file ids → that song". **Picked (T92)**: HTML5 drag events (`draggable`, `dragover` + `preventDefault` makes a drop target, `drop` with `ctrlKey` for Also add) caught by one delegated listener in a page script, not NiceGUI's per-element `.on("dragstart")` as in its Trello example: highlighting stays in the page, and the server gets one event per drop ([web/nicegui-trello-dnd.txt](web/nicegui-trello-dnd.txt), [web/mdn-html-drag-drop.txt](web/mdn-html-drag-drop.txt)). Previews: a route that serves only files under the current project's `downloads/` with media endings; Starlette's `FileResponse` answers Range requests, so an audio element can seek ([web/nicegui-pages-routing.txt](web/nicegui-pages-routing.txt) for `add_media_files`, which would serve a fixed folder and so not follow a project switch). The PDF preview is `sheets.page_images()[0]` (cached PNGs under `/pages`). Unknown: whether Qt WebEngine in the native window passes HTML5 drags like Chromium does (manual test T99).
- Dark mode: chip kinds and marks differ by icon and outline, not only by colour.
