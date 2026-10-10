# Practice layout on a small laptop

**Summary**: Built (T24–T35). The window has three regions with simple states: song list (shown / hidden), controls (Full / Simple / Sheet), sheet (fit width / page, rotation, full screen); big keys for hands-busy actions, settings for scroll and tempo steps.

Design for the small-laptop tasks (T24–T29, T33–T35): how the window is shared between song list, controls and sheet, and which keys do what. Code: [frontends/nicegui/layout.py](../frontends/nicegui/layout.py), keys in [keys.py](../frontends/nicegui/keys.py). User guide: [player.md](player.md).

## User picture

A 13" laptop (about 1280×720 usable) on a music stand or a chair, the accordion on the lap. While playing, the **sheet** is what matters and the hands are busy: changes come from one key, or from a **USB footswitch** (these send PgDn/PgUp, sometimes arrows). Between run-throughs the player adjusts tempo and loop, then plays again. Some turn the laptop **on its side** (like a book) to get a tall page.

## Three regions, each with a simple state

| Region | States | Switch | Default |
|---|---|---|---|
| Song list (left drawer) | shown / hidden | **Songs** button, `Q` | shown; remembered |
| Controls (middle pane) | **Full** / **Simple** / **Hidden** | header toggle; `V` cycles | Full; remembered |
| Sheet (right, takes the rest) | zoom, fit width / fit page, rotation 0° / 90° / 180° / 270° | toolbar; `+` / `−`, `W` / `H`; ⋮ menu, `O` | fit width, 0°; remembered |
| Full screen | on / off | toolbar button, `F`; Esc or the corner button back | off; not remembered |

- **Simple** keeps what is needed between run-throughs: waveform (seek, drag a loop), time, to start, play, loop on/off, tempo − value +. Trainer, A/B nudging, saved loops, pitch and volume are only in Full. Same widgets, hidden, so nothing is duplicated or out of sync.
- **Hidden** gives the sheet the whole width. A small bar in the header (play, time, tempo − value +, loop, recording) stays visible, so the basics are always one click away.
- **Full screen** hides everything but the sheet (header, song list, controls, sheet toolbar) and makes the window full screen. Keys keep working; a faint button in the corner and Esc lead back. The remembered layout is untouched.
- **Fit width** (100 %) and **fit page** (the whole page at the top of the view, height and width) are separate buttons, icons ↔ and ↕, next to the zoom; the active one is tinted. Fit page follows rotation, window size, song list, controls and full screen, and turns off with `+` / `−`. With PgDn set to "to next page" it turns whole pages, like a reader. The old "fit width" used the `fit_screen` icon, which looks like full screen.
- Rotate and "open in PDF viewer" sit in the toolbar's ⋮ menu: rotation is set once for how the laptop stands, and `O` does it too. This leaves room for the sheet tabs, which shorten with "…" (full names in the tooltip).
- **Rotation** turns the sheet *viewport*, not just the pages: the scrollbar, the wheel and ↑/↓ follow the page. With the laptop on its side and the sheet at 90° or 270°, the page reads upright and fills the tall screen. It is global (it describes how the laptop stands, not the PDF). 180° is there for completeness.

## Keys

Chosen so that the hands-busy actions are the big keys and the footswitch keys only scroll.

| Keys | Action | Why |
|---|---|---|
| Space / K | play / pause | biggest key |
| ↑ / ↓ | scroll the sheet one step | read on |
| PgUp / PgDn | scroll a screen (or a page, setting) | footswitch |
| Home / End | sheet top / bottom | reader convention |
| ← / → | tempo − / + one step | the most changed setting |
| + / − | sheet zoom | |
| `,` / `.` | back / forward 5 s | `<` `>` as arrows |
| J / L | back / forward 10 s | YouTube |
| 0 | to start (loop start when looping) | |
| 1 … 9 | jump to 10 … 90 % | YouTube |
| A / B / R / C / S | loop start / end / on-off / clear / save | |
| N / P | next / previous song | |
| T / Shift+T | next / previous recording | Track |
| Q | song list | left edge, like the drawer |
| V | controls: Full → Simple → none | View |
| F | full screen (Esc back) | YouTube |
| W / H | fit width / fit page | Width, Height |
| O | rotate the sheet 90° | Orientation |
| E | loop editor ([loop-editor.md](loop-editor.md)) | Edit |
| M, /, ? | mute, search, help | |

Scroll keys run in the page's own script (no server round trip), call `preventDefault` so the browser doesn't scroll twice, and scroll smoothly. Pressing again during the animation continues from the target, so a quick double tap on the footswitch moves two steps.

## Song list button

Study (T35). The song list was opened by ☰, which reads as the app's main menu. [nng-icon-usability](web/nng-icon-usability.txt): the 3-line icon mostly means the navigation menu, and "a text label must be present alongside an icon … visible at all times". [nng-hamburger-menus](web/nng-hamburger-menus.txt): hidden navigation behind an icon is found less often, worst on desktops ("low information scent"). forScore, a sheet-music reader, opens its library from named toolbar items (scores, bookmarks, setlists) on the left, and on desktop shows menus as a sidebar beside the music ([forscore-basics](web/forscore-basics.txt), [forscore-menus](web/forscore-menus.txt)).

- **Pick**: a labelled **Songs** button with a music-list icon, at the left where the drawer opens, tinted while the list is shown. The tooltip names the key (`Q`).
- **Recordings stay with the player, not in the list.** forScore links audio tracks to the score and shows them in its media panel ([forscore-audio](web/forscore-audio.txt)). The list is hidden most of the practice time anyway. So the list only shows a count badge, and the switch (T34) is where playback is: chips in the controls pane (Full and Simple), a "♪ 1/2" menu in the sheet-only bar, and `T` everywhere.

## Settings (gear button)

| Setting | Options | Default |
|---|---|---|
| ↑ / ↓ scroll step | 10 / 20 / 33 / 50 % of the view | 20 % |
| PgUp / PgDn | a screen (85 %, keeps the last line visible) / to the next page | a screen |
| ← / → tempo step | 1 / 2 / 5 / 10 % | 5 % |
| Smooth scrolling | on / off | on |
