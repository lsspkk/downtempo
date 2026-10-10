# Loop editor

**Summary**: Built (T40–T43), pitfalls checked (T39: one fix, the view no longer follows the playhead while a loop edge is in view); the user's test T44 remains. A full-window waveform: click start, click end (or drag), ⠿ handles, zoom by pinch / wheel / ruler drag, Hear end, Undo; `E` opens, Esc leaves.

Plan for the loop editor (T39–T44). **Status: implemented (T40–T43, 2026-10-09), pitfalls checked (T39, 2026-10-10)**; the user's test T44 remains. Code: [loop_editor.js](../frontends/nicegui/loop_editor.js) (drawing, gestures), [loop_editor.py](../frontends/nicegui/loop_editor.py) (dialog, loop, undo). Follows [ux.md](ux.md).

## What the user wants (2026-10-09)

- The current waveform in the controls pane is good and stays. The editor is for **setting loop start and end quickly and exactly**.
- Typical way: open the editor, zoom in once, maybe once or twice more, set the loop. Sometimes just select on the whole song, full screen, without zooming.
- A **very quick way back** to the main screen with all its areas.
- A possible flow: zoom in (or click near) the loop start and set it, then zoom in (or click near) the loop end and set it, then **OK** or **redo**.
- Drag is good too; maybe the default, or both. When zoomed in, a drag past the view's edge could scroll, slowly first, then faster.
- **Trackpad must work without holding a drag**: click to start the selection, scroll with a two-finger swipe (the selection follows the pointer), click again to set the end.

## Sketch (1280×720)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Loop · Song title     [Rec 1][Rec 2]                       [↶ Undo] [Done E] │ header
│ [−] 4× [+] [Whole song] [Zoom to loop] │ [▶ Play loop] [Hear end] │ − 80 % + │ toolbar
│ ▁▂▅▇▅▃▂▁▂▃[▅▇▆▅▃]▂▁▂▃▅▆▅▃▂▁▂▃▅▇▆▅▃▂▁▂▃▅▆▅▃▂▁▂▃▅▇▆▅▃▂▁▂▃▅▆▅▃▂▁▂▃▅▇▆▅▃▂▁       │ overview
│ 1:10        1:12        1:14        1:16        1:18        1:20             │ ruler
│        A▼                                          B▼                        │
│ ▂▃▅▇▆▅▃▂▃│▅▇▇▆▅▃▂▁▂▃▅▆▇▆▅▃▂▃▅▆▇▇▆▅▃▂▁▂▃▅▆▇▆▅▃▂▃▅▆▇│▆▅▃▂▃▅▇▆▅▃▂▁▂▃▅▆▇▆▅▃▂     │ waveform
│ ▂▃▅▇▆▅▃▂▃│▅▇▇▆▅▃▂▁▂▃▅▆▇▆▅▃▂▃▅▆▇▇▆▅▃▂▁▂▃▅▆▇▆▅▃▂▃▅▆▇│▆▅▃▂▃▅▇▆▅▃▂▁▂▃▅▆▇▆▅▃▂     │ (the rest
│ ▂▃▅▇▆▅▃▂▃│▅▇▇▆▅▃▂▁▂▃▅▆▇▆▅▃▂▃▅▆▇▇▆▅▃▂▁▂▃▅▆▇▆▅▃▂▃▅▆▇│▆▅▃▂▃▅▇▆▅▃▂▁▂▃▅▆▇▆▅▃▂     │  of the
│ Start [1:11.2] ‹ ›                                      End [1:18.7] ‹ ›     │  height)
│ Drag or click to select · pinch or ⌃ wheel to zoom · Esc back                │ hint line
└──────────────────────────────────────────────────────────────────────────────┘
```

## Decisions

### Open and leave

- **Open**: `E` (Edit loop) anywhere, or its button: "Edit" in the Loop card (Full), an icon next to the loop button (Simple), an icon in the header bar (Sheet only). It fills the whole window, with no header, list or sheet; the main layout isn't changed.
- **Leave**: `E` again, **Done**, or Esc. Esc first cancels a started selection, a second Esc leaves. The loop as pit is now is kept: no OK step.
- It opens at the zoom it had last time for this recording; the first time, at the loop with a margin, or the whole song if there is no loop.

### Select

- **Both ways always work, told apart by the gesture** (pointer moves less than 4 px between press and release = click):
  - **Drag**: press, move, release sets start and end. Holding the pointer in the edge zone (the outer 24 px of the waveform, tinted while dragging) scrolls: slowly at first (0.15 views/s), faster the longer it's held (+0.6 views/s each second, up to 2). Time, not distance: in full screen the pointer can't go past the screen's edge (user, 2026-10-09). The slow start keeps a short touch from overshooting; leaving the zone stops at once.
  - **Click, move, click**: the first click sets the start and starts a selection whose end follows the pointer. Two-finger swipe, pinch and the zoom buttons keep working meanwhile. The second click sets the end.
- **A started selection shows it**: the start edge is solid, the end edge is dashed and follows the pointer, the area between is lightly shaded, and the hint line says "Click to set the end · Esc cancels". The cursor is a crosshair.
- **Refine**: each edge has a drag handle on top: a square with the standard grip dots (⠿), centred on the line, its letter A / B beside it. The cursor shows grab / grabbing. The line itself also grabs (±5 px). Dragging a handle moves only that edge, also with edge scrolling. (User, 2026-10-09: clicking sets the points; the handles are what you drag.) Dragging inside the loop, away from the handles, starts a new selection: a new loop is more common than moving one.
- Start and end are also typed values (`1:11.2`) with ‹ › nudges of 0.1 s, as in the main pane. A / B (at the play position) and the nudge keys work unchanged.
- **Undo**: Ctrl+Z or the Undo button brings back the previous loop, step by step, during this visit. Making a new selection is the redo.

### Seek

- In the editor a click on the waveform selects, so **seeking is a click on the time ruler** (a drag on it zooms) (as in most audio editors). The playhead line is drawn across the ruler and the waveform.
- Keys keep seeking: `0` to the start (loop start when looping), `,` `.` `J` `L`, digits.

### Zoom and scroll

- **Pinch** (or Ctrl + wheel) zooms at the pointer: the time under the pointer stays put.
- **Drag the time ruler** (as in Cubase, user 2026-10-09): down zooms in, up zooms out (100 px = 3.3×); the grabbed time stays under the pointer, so moving sideways scrolls at the same time. A click without moving seeks (on release).
- **Buttons and `+` / `−`** zoom by 2× around the loop edge being set during a started selection; otherwise around the playhead if it's in view, else around the middle. In the editor `+` / `−` zoom the waveform (the sheet isn't visible).
- **Whole song** and **Zoom to loop** (the loop plus 10 % on each side) are labelled buttons. The zoom shows as `4×`.
- Zoom range: from the whole song down to 1 s across the view.
- **Scroll**: two-finger swipe sideways (wheel `deltaX`, or Shift + wheel), dragging the window in the **overview strip** (the whole song, with the visible part as a box: it is the slider), or a click in the overview to jump there.
- While playing, the view follows the playhead only when it would leave the view, by turning a page, and never during a selection or drag, nor while a playing loop has an edge in view: the jump back to the loop start would pull the view away from the edge being fixed on every pass (T39).

### Hear the edges

- **Space** plays and pauses; with the loop on it plays the loop from its start.
- **Hear end** (button, Shift+Space) plays from 2 s before the end, so the seam back to the start is heard right after. That is the edge that most often needs a fix.
- Nothing plays by itself after an edit ([ux.md](ux.md) #7).

### Rendering

- The editor's waveform, ruler and overview are drawn **in the page on a canvas**, and select, zoom and scroll are handled there with no server round trip, like the sheet's scroll keys. The server gets only the results (loop set, seek, play).
- Peaks go to the page once per recording, at a few resolutions (a pyramid down to about 5 ms per bin). A finer range is fetched from the server on request when zoomed in further.
- The small waveform in the controls pane stays as it is.

## To check during the work

- The native window (Qt WebEngine on Linux) must pass pinch as Ctrl + wheel and two-finger sideways as `deltaX`, as Chrome and Firefox do. If pinch doesn't arrive, the zoom buttons and keys are enough.
- The loop editor fits 1280×720 with the hint line visible.

## Pitfall check (T39, 2026-10-10)

Compared with a DAW ([audacity-selecting-audio](web/audacity-selecting-audio.txt), [audacity-zooming](web/audacity-zooming.txt), [audacity-timeline](web/audacity-timeline.txt)), waveform libraries ([peaksjs-readme](web/peaksjs-readme.txt), [wavesurfer-regions-example](web/wavesurfer-regions-example.txt)) and practice apps ([design-transcribe-overview](web/design-transcribe-overview.txt), [anytune-basics](web/anytune-basics.txt)).

- **Changed**: the view following the playhead while a loop plays. Audacity says to turn following off "when using Quick-Play to adjust the start and end of loops", so the edges don't move away. Here, zoomed in on the end with Hear end, each pass jumped the view to the start. Now the view stays while a loop edge is in it.
- **Already right**: Esc during a drag cancels it and keeps the old loop (as Audacity); dragging past the edge scrolls; edges are grabbed by hovering near them; a too-short loop is refused (0.2 s; wavesurfer has `minLength`); typed start / end with nudges (Audacity's Selection Toolbar); overview + zoomed view (peaks.js, Anytune's double waveform); zoom at the pointer, buttons at the edge being set; hearing the end of the selection (Audacity has keys for the selection's start and end).
- **Different on purpose, kept**: a ruler drag zooms (Cubase, user's choice) where Audacity makes a loop region; a drag inside the loop makes a new loop where Audacity and wavesurfer move the whole region (a new loop is more common). No Shift-click to extend the nearest edge: click–move–click and the handles cover setting an edge that is off screen.
