# Browser app on a phone

**Summary**: Built (T174): the browser app on a large phone (a 6.9" Android, about 412–440 CSS px wide, held upright, used with one thumb). One top line of round 44 px icon buttons (☰, songs, ♪ recording, tempo, loop, loop editor, and at the right end the sheet's menu); the time, the position waveform and ▶ on a line under it; the song list as a full-screen page with ✕; tempo in a panel that drops under the top line; the sheet has no line of its own: its controls and the choice of PDF are in that menu, as wide as the screen. Applies below 640 px (Tailwind `sm`); wider screens keep the laptop layout ([browser-app.md](browser-app.md)). Built as `ui/song/PhoneSong.tsx`, which arranges the same parts as `DesktopSong.tsx`; every menu here is the kit's `DropDown`, which on a phone opens as a full-width sheet under the bar, headed by what opened it ("Äänitteet", "Tempo 80 %", "Nuotti"), since the round buttons have no text.

## Why it differs from the laptop

- **No keyboard.** Every key (tempo ← →, A / B, W / H, F, O) needs a tap target; exact values need − / + buttons, not only a slider ([ux.md](ux.md) #5).
- **Fingers, not a pointer.** Targets at least 44 × 44 px with room between them; nothing important at the screen's edges where the phone's own gestures are.
- **Little width.** One line of icons fits about eight 44 px buttons in 412 px; text labels don't fit, so every icon has a tooltip / `aria-label` and the panels it opens say in words what they are ([ux.md](ux.md) #3).
- **The sheet is the point.** While playing, the music should fill the screen: the top line and the position line are all the chrome there is.

## Top line (left to right)

| Button | Icon | Opens |
|---|---|---|
| Main menu | ☰ (`Menu`) | the ☰ menu as now (projects, Settings, theme, language) |
| Songs | `ListMusic` | the song list as a full-screen page: ← and its title, the Project panel, search, songs; picking a song closes it |
| Recording | ♪ (`Music`) | the recording menu (names and upload dates) across the full width under the top line |
| Tempo | `Gauge` over the current % in small type | a panel under the top line: − , the slider with its marks, +; closes on a tap outside |
| Loop | `Repeat`, amber when on | (turns the loop on / off; no loop yet → the loop editor) |
| Loop editor | `Maximize2` | the loop editor over the screen under the top line and the position line (▶ and the loop button stay at hand): a heading line with ← and its title and its buttons under it, Start and End on rows of their own, short labels ("Song", "Loop"; "Kappale", "Valinta"), Clear as text only |
| Sheet (right end) | `SlidersHorizontal` | a menu across the full width: zoom − / % / +, the song's PDFs (✓ on the one shown) when it has several, Fit width, Fit page, Sheet only ([sheet-only.md](sheet-only.md)), Trim margins (off / 0.5 / 1 / 2 cm from every side, so the notes fill the width), Rotate right, Rotate left, Open the PDF |

All the same: 44 px round, a 20 px icon with the same 2 px stroke, grey (`zinc-600`), the active state tinted (indigo, or amber for the loop), no text. The song's title is not in the top line: the song list shows which song is on, and the sheet menu names the PDFs.

## Under the top line

- **Position line**: the time, a full-width thin bar waveform (28 px; tap or drag seeks) and at the right end ▶ / ⏸, a filled indigo circle a little smaller than the top line's buttons (40 px).
- **The sheet** right under it, with no line of its own, filling the width: no grey margin or shadow, only a 2 px line between pages.

## Pages over the song

The song list, Settings and the loop editor fill the screen on a phone, so they behave as pages: a bar with ← at the top left and the title after it (as Android's and iOS's own pages), and the phone's Back button or gesture closes the one on top. Each adds a history step when it opens and takes it out again when closed some other way (`ui/kit/back.ts`).
