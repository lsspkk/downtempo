# Python player

**Summary**: Built; user-tested 2026-10-10. User guide of the Python player: how to run it, features, keys, what it remembers, files.

The Python player: NiceGUI page in its own window, sound decoded, time-stretched and played in Python. Code: [frontends/nicegui/](../frontends/nicegui/).

```sh
uv run python frontends/nicegui/app.py              # native window (pywebview, Qt on Linux)
uv run python frontends/nicegui/app.py --browser    # normal browser tab: http://127.0.0.1:8765
```

It reads only `data/songs.json` ([songs.md](songs.md)). Use `--browser` for development and UI checks ([scripts/screenshot.py](../scripts/screenshot.py)). There is one audio engine, so the newest tab or window takes over; older ones show a notice (reload to take back).

## Features

- **Song list** (left drawer, the sidebar icon next to ☰ or `Q` to hide, `/` to search, N / P for next and previous). Switching stops the song and waits for Play ([player-switching.md](player-switching.md)). Its top is the project: a **Project** caption with ⟳, the name, and a status line; only the songs scroll, **Edit song list** stays at the bottom ([practice-layout.md](practice-layout.md#song-list)).
- **⟳ Check for new files**: downloads what's new in the shared folders while you keep playing; shows the sign-in code when OneDrive asks for it; ⟳ again stops (finished files are kept). The status line shows "Checked 2 h ago", the progress, the result, or "⚠ folder: what went wrong" (click: Project settings at that folder).
- **☰ Main menu** (top left): the projects (click one to switch; a search field when there are many), New project…, Project settings…, Export… / Import…, Delete project…, Player settings…, Keyboard shortcuts, Dark mode.
- **Project settings**: the project's name; per shared folder its link (Copy, **Change link…**), the folder inside the share, skipped folders, Rename…, Remove…, the last error with Try again; + Add folder; the sign-in ([project-screen.md](project-screen.md#project-settings)).
- **Adding a shared folder**: on the first start the page asks for the link; later + Add folder in Project settings or Edit song list. Sign in if asked, pick the folder (tick Skip on folders you don't need), see "About 12 songs from 31 files, 180 MB", Download.
- **Recordings**: `Recording [ live 2025 ▾ ] 2 of 3` above the waveform when a song has several (the menu: ✓ on the current one, the name, its recording tempo; ↑ / ↓, Enter, Esc), a "♪ 1/2" menu in the sheet-only header, and `T` / Shift+T for next / previous. One recording: its name as plain text (nothing when it is named after the song).
- **Controls: Full / Simple / Sheet** (header toggle, `V` cycles). Full is one surface: the recording, the waveform and transport, the tempo row, and the tabs **Pitch · Trainer · Loop · BPM** (the open tab is remembered). Simple keeps waveform, play, loop on/off and the tempo row (`Tempo − 85 % +  75 BPM  ○ Play at 100`); Sheet hides the controls and puts play, time, tempo, loop and recording in the header. Made for small laptops: [practice-layout.md](practice-layout.md).
- **Waveform**: click plays from there, drag sets a loop (drag out the left or right side: the loop runs to the song's start or end). Shows the play position and the loop.
- **Songs with only a sheet or only a recording**: no recording → the controls pane narrows to the title and "No recording", the sheet gets the room, the audio keys do nothing; no sheet → a large waveform (click, drag, Loop editor) in the sheet's place. Per song: the remembered layout stays.
- **New files**: a dot after a song's title in the song list when files joined it since you last opened it; opening the song clears it.
- **Loop editor** (`E`, "Edit" in the Loop card, or the ⤢ icon next to the loop button in Simple and in the sheet-only bar): the waveform over the whole window to set a loop exactly. Click the start, then the end (scroll and zoom in between); drag the ⠿ handles on the edges; pinch, Ctrl+wheel or dragging the time ruler up / down zooms, two-finger swipe or the overview strip scrolls; Whole song / Zoom to loop; click the time ruler to seek; Hear end (Shift+Space) plays the last 2 s and the jump back; Undo (Ctrl+Z); typed start/end times. `E`, Done or Esc goes back ([loop-editor.md](loop-editor.md)).
- **Tempo** 50–130 % with the pitch kept: the tempo row's −/+ and ←/→ (step in Settings), and in Full the slider with clickable 50 … 130 under it (the current one highlighted). The time's tooltip says how long the song takes at this tempo.
- **Tempo in BPM and the optimal tempo** ([tempo-goal.md](tempo-goal.md)): a recording's tempo is found in the background when it first loads ("finding…", then the number). The tempo row shows **BPM now** (recording tempo × speed), a round **TAP** (G: tap along another version; from the 4th tap the recording plays that fast, every tap refines it, a 2 s pause starts over), a round **metronome** button (a steady tick at the BPM now, on / off) and the **Play at 100** switch (X): on, every recording of the song plays at its optimal tempo (remembered per song); off goes back to the speed before, a change by hand just turns it off. Without an optimal tempo the switch is grey and a click opens the BPM tab. In Sheet only, X and G show a short toast.
- **BPM tab**: the recording tempo and the optimal tempo (−/+, typed), and under them the speed the optimal tempo needs ("→ 114 % of this recording"); an empty field means none.
- **Trainer tab** (step-up trainer): raises the tempo by a step every N loop repeats, up to a target.
- **Loop tab** ([loop-editor.md](loop-editor.md#the-loop-tab-t241)): the loop's line (on / off, its length, the pause between repeats, Clear, **Loop editor**); Start and End as cards, each with **Set here** (A / B) and nudges by 0.1 s (‹ ›) or 1 s (« »); Save loop; the saved loops as one scrolling row of chips. Loops are set at the play position with A / B or by dragging the waveform.
- **Pitch tab**: ±12 semitones, Reset, **volume** and mute.
- **Sheet music** (right): the song's PDFs as cropped pages, one tab per PDF (the newest version opens unless you picked another one for this song), zoom, **fit width** / **fit page** (`W` / `H`; fit page keeps the whole page in view and follows window and layout changes). ↑/↓ scroll, PgUp/PgDn (a USB footswitch) scroll a screen or jump to the next page. **Full screen** (`F`, Esc back) shows only the sheet. In the ⋮ menu: **rotate** (`O`) turns the whole sheet view, scrollbar included, for a laptop standing on its side; open in the PDF viewer.
- **Player settings** (☰): ↑/↓ scroll step, PgUp/PgDn screen or page, ←/→ tempo step, smooth scrolling.
- **Dark mode** (header button).

## Keyboard

Press `?` in the player for this list. Why these keys: [practice-layout.md](practice-layout.md#keys).

| Playing | | Sheet and view | |
|---|---|---|---|
| Space / K | play / pause | ↑ / ↓ | scroll the sheet |
| ← / → | tempo slower / faster | PgUp / PgDn | a screen or page (footswitch) |
| G | tap the beat: from the 4th tap the speed follows | | |
| X | optimal tempo on / off | | |
| , / . | back / forward 5 s | Home / End | sheet top / bottom |
| J / L | back / forward 10 s | + / − | sheet zoom |
| 0 | to start (loop start when looping) | W / H | fit width / fit page |
| 1 … 9 | jump to 10 … 90 % | O | rotate the sheet |
| A / B | loop start / end here | F | full screen (Esc back) |
| R | loop on / off | V | controls: full, simple, none |
| C | clear loop | Q | song list |
| S | save loop | N / P | next / previous song |
| T / Shift+T | next / previous recording | / | search songs |
| M | mute | ? | help |
| E | loop editor | Shift+Space | hear the loop end (editor) |

## What it remembers

The project's `practice.json` and `data/app.json` ([state.py](../frontends/nicegui/state.py)); practice memory in the project: per song the chosen recording and the sheet you picked (otherwise the newest opens), tempo, pitch and step-up trainer settings; per song the optimal tempo (`goal_bpm`); per recording the position, the active loop, saved loops, the loop editor's zoom and the recording tempo in BPM; the last song. The Metronome and taps are not remembered. On the computer (`app.json`): volume, zoom and fit, dark mode, loop pause; the layout (song list shown, controls mode, the open tab of Full controls, rotation) and the settings. A recording or sheet is remembered only after it loaded.

## Files

| File | What |
|---|---|
| `app.py` | puts the page together: builds the parts and wires them (only wiring) |
| `player.py` | what plays and what's remembered: song, recording loading, tempo, pitch, volume, loop, trainer, autosave; no widgets |
| `layout.py` | the window's frame: header (☰ slot, song list toggle, title, Full / Simple / Sheet), song-list drawer, controls / sheet grid, full screen; the player's ☰ items (settings, shortcuts, dark mode) |
| `song_list.py` | the song list in the drawer: search, next / previous song |
| `tempo_goal.py` | the tempo in BPM, no widgets: the recording tempo (found in a process of its own, `python -m downtempo.tempo`), the optimal tempo, the Play at switch, Tap, the Metronome |
| `tempo_row.py` | the tempo row: −/+, %, BPM now, TAP, the metronome button (`MetronomeButton`), the Play at switch; the slider and its marks in Full |
| `bpm_tab.py`, `loop_tab.py`, `trainer_tab.py`, `pitch_tab.py` | Full controls' tabs, one module each (the Save loop dialog lives in `loop_tab.py`) |
| `recordings.py` | the recording dropdown, the menu rows (✓, name, BPM) and the loop editor's chips |
| `mini_bar.py` | the controls' short form in the header while the pane is hidden (Sheet) |
| `metronome.py` | the Metronome mixed into the engine's output: a steady tick at one BPM |
| `tap_tempo.py` | the taps' BPM |
| `controls.py` | the controls pane as one surface: the recording, the waveform and transport, the tempo row, the tabs; the loading card; "No recording" for sheet-only songs |
| `waveform.py` | the waveform with play position and loop, click to seek, drag to loop; one in the controls, a large one for songs without sheets |
| `sheet_pane.py` + `sheet_pane.js` | the sheet: PDF pages, tabs, zoom, fit, rotation; scrolling and fitting in the page; the large waveform when a song has no sheet |
| `loop_editor.py` | the loop editor dialog: loop, undo, seek, talks to `loop_editor.js` |
| `keys.py` | keyboard shortcuts: the key handler and the help table |
| `common.py` | small shared helpers: tooltips, times, page events, CSS |
| `engine.py` | Rubber Band real-time stretch in a worker thread → queue → `sounddevice` callback ([stretch-app-flow.md](stretch-app-flow.md)) |
| `loop_editor.js` | loop editor in the page: canvases, select, zoom, scroll ([loop-editor.md](loop-editor.md)) |
| `sheets.py` | PDF pages → cropped PNGs in `data/cache/pages/` (pypdfium2) |
| `state.py` | load and save `data/app.json` (layout) + the project's `practice.json` as one dict |
| `jobs.py` | background jobs, one at a time: core work in a worker thread, its events to the page through a queue a timer drains, Cancel |
| `project_screen.py` | the project screen ("Edit song list" in the song list): header, tabs, Undo / Redo, drops, its keys (`M` move, `N` new song, `Delete` not a song file, `F2` edit the song, Ctrl+Z / Ctrl+Shift+Z); [project-screen.md](project-screen.md#built-so-far) |
| `sort_tab.py`, `songs_tab.py`, `chips.py` | its To sort and Songs tabs, file chips (draggable, right-click menu, ▶ / 👁) and the song picker |
| `song_box.py`, `drag.js`, `previews.py` | the song edit box; dragging in the page; ▶ / 👁 previews and the `/preview/` route |
| `updates.py` | downloading for the whole page (⟳ in the song list, ⟳ Update in the project screen, after Add folder or Change link): the state only (progress, result, errors per folder), shown by whoever listens; the song list updates without a restart and the playing song goes on |
| `project_panel.py` | the top of the song list: Project caption, ⟳, the name, the status line |
| `sign_in.py` | the sign-in card (code, Copy, Open the page, time left, Cancel) for any job |
| `add_folder.py`, `folder_picker.py` | Add folder: link → sign-in → folder picker with Skip → what it brings → Download |
| `sources_bar.py` | the project screen's folder chips with state (menu: Update this folder, Folder settings…), + Add folder, ⟳ Update |
| `main_menu.py`, `settings_file.py` | the ☰ main menu (player and project screen): projects and switching, new, Project settings…, delete, Export / Import of the settings file; the player's items come from `layout.py` |
| `project_settings.py`, `folder_actions.py`, `change_link.py` | Project settings: the name, the shared folders and the sign-in; one folder's rename, skipped folders, free space, remove; Change link… (paste, the same folder found or picked, save and download) |
| `welcome.py` | the page before there are songs: paste a link (first start), or the way to the unknown files |
