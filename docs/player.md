# Python player

**Summary**: Built; user-tested 2026-10-10. User guide of the Python player: how to run it, features, keys, what it remembers, files.

The Python player: NiceGUI page in its own window, sound decoded, time-stretched and played in Python. Code: [frontends/nicegui/](../frontends/nicegui/).

```sh
uv run python frontends/nicegui/app.py              # native window (pywebview, Qt on Linux)
uv run python frontends/nicegui/app.py --browser    # normal browser tab: http://127.0.0.1:8765
```

It reads only `data/songs.json` ([songs.md](songs.md)). Use `--browser` for development and UI checks ([scripts/screenshot.py](../scripts/screenshot.py)). There is one audio engine, so the newest tab or window takes over; older ones show a notice (reload to take back).

## Features

- **Song list** (left drawer, **Songs** button or `Q` to hide, `/` to search, N / P for next and previous). Switching stops the song and waits for Play ([player-switching.md](player-switching.md)).
- **Recordings**: a song folder with several mp3s gets one chip per recording above the waveform, a "♪ 1/2" menu in the sheet-only header, and `T` / Shift+T for next / previous.
- **Controls: Full / Simple / Sheet** (header toggle, `V` cycles). Simple keeps waveform, play, loop on/off and tempo −/+; Sheet hides the controls and puts play, time, tempo, loop and recording in the header. Made for small laptops: [practice-layout.md](practice-layout.md).
- **Waveform**: click plays from there, drag sets a loop. Shows the play position and the loop.
- **Loop editor** (`E`, "Edit" in the Loop card, or the ⤢ icon next to the loop button in Simple and in the sheet-only bar): the waveform over the whole window to set a loop exactly. Click the start, then the end (scroll and zoom in between); drag the ⠿ handles on the edges; pinch, Ctrl+wheel or dragging the time ruler up / down zooms, two-finger swipe or the overview strip scrolls; Whole song / Zoom to loop; click the time ruler to seek; Hear end (Shift+Space) plays the last 2 s and the jump back; Undo (Ctrl+Z); typed start/end times. `E`, Done or Esc goes back ([loop-editor.md](loop-editor.md)).
- **Tempo** 50–130 % with the pitch kept: slider, preset chips, −/+ buttons and ←/→ (step in Settings). "Song takes m:ss" shows the length at this tempo.
- **Step-up trainer**: raises the tempo by a step every N loop repeats, up to a target.
- **Loop A–B**: set at the play position, nudge each edge by 0.1 s, save named loops per recording, optional pause between repeats.
- **Pitch** ±12 semitones, **volume** and mute.
- **Sheet music** (right): the song's PDFs as cropped pages, one tab per PDF, zoom, **fit width** / **fit page** (`W` / `H`; fit page keeps the whole page in view and follows window and layout changes). ↑/↓ scroll, PgUp/PgDn (a USB footswitch) scroll a screen or jump to the next page. **Full screen** (`F`, Esc back) shows only the sheet. In the ⋮ menu: **rotate** (`O`) turns the whole sheet view, scrollbar included, for a laptop standing on its side; open in the PDF viewer.
- **Settings** (gear): ↑/↓ scroll step, PgUp/PgDn screen or page, ←/→ tempo step, smooth scrolling.
- **Dark mode** (header button).

## Keyboard

Press `?` in the player for this list. Why these keys: [practice-layout.md](practice-layout.md#keys).

| Playing | | Sheet and view | |
|---|---|---|---|
| Space / K | play / pause | ↑ / ↓ | scroll the sheet |
| ← / → | tempo slower / faster | PgUp / PgDn | a screen or page (footswitch) |
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

`data/player-state.json` ([state.py](../frontends/nicegui/state.py)): per song the chosen recording and sheet, tempo, pitch and step-up trainer settings; per recording the position, the active loop, saved loops and the loop editor's zoom; the last song, volume, zoom and fit, dark mode, loop pause; the layout (song list shown, controls mode, rotation) and the settings. A recording or sheet is remembered only after it loaded.

## Files

| File | What |
|---|---|
| `app.py` | puts the page together: builds the parts and wires them (only wiring) |
| `player.py` | what plays and what's remembered: song, recording loading, tempo, pitch, volume, loop, trainer, autosave; no widgets |
| `layout.py` | the window's frame: header, song-list drawer, controls / sheet grid, Full / Simple / Sheet, full screen, settings, dark mode |
| `song_list.py` | the song list in the drawer: search, next / previous song |
| `controls.py` | the controls pane (recordings, waveform, transport, tempo, trainer, loop, pitch, volume) and its short form in the header |
| `sheet_pane.py` + `sheet_pane.js` | the sheet: PDF pages, tabs, zoom, fit, rotation; scrolling and fitting in the page |
| `loop_editor.py` | the loop editor dialog: loop, undo, seek, talks to `loop_editor.js` |
| `keys.py` | keyboard shortcuts: the key handler and the help table |
| `common.py` | small shared helpers: tooltips, times, page events, CSS |
| `engine.py` | Rubber Band real-time stretch in a worker thread → queue → `sounddevice` callback ([stretch-app-flow.md](stretch-app-flow.md)) |
| `loop_editor.js` | loop editor in the page: canvases, select, zoom, scroll ([loop-editor.md](loop-editor.md)) |
| `sheets.py` | PDF pages → cropped PNGs in `data/cache/pages/` (pypdfium2) |
| `state.py` | load and save `data/player-state.json` |
