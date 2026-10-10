# UX principles

Every UI task follows these. They come from the saved articles (principles, not layouts to copy) and from decisions already made in this project. A task that learns a new principle adds it here, with its source.

## The user

An amateur musician practising alone on a small laptop (about 1280×720), instrument in hand. Changes come between run-throughs, or from one key or a USB footswitch while playing. Details: [practice-layout.md](practice-layout.md#user-picture), [player-switching.md](player-switching.md#user-picture).

## Principles

1. **Few things, clearly.** Show only what this moment needs; more lives one step away (Full / Simple / Sheet, ⋮ menus). Every extra element competes with the ones that matter ([design-nng-heuristics](web/design-nng-heuristics.txt) #8).
2. **One key or one click for each frequent action**; hands-busy actions get the big keys (Space, arrows, PgDn). Keys follow known players (YouTube: Space, F, J/L, digits) ([design-youtube-shortcuts](web/design-youtube-shortcuts.txt), heuristics #4, #7).
3. **Labels beat icons.** Only a few icons are universal; ambiguous ones get a visible label, or at least a tooltip that names the key. Don't reuse a well-known icon for something else (☰ means the app menu) ([nng-icon-usability](web/nng-icon-usability.txt), [nng-hamburger-menus](web/nng-hamburger-menus.txt)).
4. **State is always visible**: what plays, the tempo, loop on/off, which recording and sheet, which mode is active (tinted button, filled chip) (heuristics #1).
5. **Exact values don't come from sliders.** A slider is for a rough range; next to it go −/+ steps, presets or typed values ([design-nng-sliders](web/design-nng-sliders.txt)). The value label sits beside the control, not under the hand.
6. **Direct manipulation where it's natural**: click the waveform to seek, drag to loop, drag pages to scroll; every drag has a button or key alternative (heuristics #7).
7. **Nothing surprising happens by itself.** Switching songs stops and waits for Play; code never fires a user action (widgets set by code don't trigger their handlers) ([player-switching.md](player-switching.md)).
8. **Easy way back.** Esc, the same key again, or a visible button undoes a mode (full screen, sheet only); the remembered layout is untouched by temporary modes (heuristics #3).
9. **Remember the practice, not the accident.** Per song: tempo, pitch, recording, sheet; per recording: position and loops; the layout. Only choices that loaded are remembered (heuristics #6).
10. **Fit the small screen first.** Check every UI change at 1280×720 (`scripts/screenshot.py --size 1280x720`): no wrapping toolbars, long names shorten with "…" and show in full in a tooltip.

## Checklist for a UI task

- Which principle does the change rely on, and does it break one?
- Mouse, keyboard (and footswitch if it's about the sheet) all work.
- Screenshot at 1280×720 in light mode; dark mode readable.
- Keys added to the help dialog, [player.md](player.md) and [practice-layout.md](practice-layout.md#keys).
