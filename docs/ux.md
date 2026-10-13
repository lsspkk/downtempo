# UX principles

**Summary**: Every UI task follows these 11 principles and the checklist: few things clearly, one key per frequent action, labels over icons, visible state, easy way back, 1280×720 first, don't move what the user is editing. The browser app adds 5 web-app principles (12–16): pages not modals for settings, one step at a time for the first start, empty states that lead on, the important first and the rest one step away, forms in one plain column.

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
8. **Easy way back.** Esc, the same key again, or a visible button undoes a mode (full screen, sheet only); the remembered layout is untouched by temporary modes (heuristics #3). Esc also aborts a drag or selection in progress and keeps what was there before ([audacity-selecting-audio](web/audacity-selecting-audio.txt)).
9. **Remember the practice, not the accident.** Per song: tempo, pitch, recording, sheet; per recording: position and loops; the layout. Only choices that loaded are remembered (heuristics #6).
10. **Fit the small screen first.** Check every UI change at 1280×720 (`scripts/screenshot.py --size 1280x720`): no wrapping toolbars, long names shorten with "…" and show in full in a tooltip.
11. **Don't move what the user is working on.** A view that follows playback stops following while the user is editing in it (a loop edge in view); when zoomed, an overview always shows where the view is in the whole song ([audacity-timeline](web/audacity-timeline.txt), [peaksjs-readme](web/peaksjs-readme.txt), [anytune-basics](web/anytune-basics.txt)).

## Web app (browser app, T165)

12. **Pages, not modals, for anything to read or set up.** A modal blocks the page and makes the user drop what they were doing; it is for a short, critical question (a destructive step, information the current action can't go on without), not for browsing or long content. Settings are a full page with a clear way back (a ← link at the top, Esc), and only a confirmation or a quick choice stays a small dialog ([nng-modal-dialogs](web/nng-modal-dialogs.txt)).
13. **One step at a time only where steps depend on each other.** (Revised 2026-10-14: the first start's name + optional link is one page, a wizard for two fields was heavy on a desktop; sign in and folders stay separate screens with a visible progress list. Never a centred card that looks like a modal.) Original rule: A task in distinct steps (name, link, sign in, folders) goes one step per screen, each with a heading that says what this step asks, the progress ("Step 2 of 4"), Back and one main button; low-confidence users and phones do better this way ([govuk-one-thing-per-page](web/govuk-one-thing-per-page.txt), [govuk-question-pages](web/govuk-question-pages.txt), staged disclosure in [nng-progressive-disclosure](web/nng-progressive-disclosure.txt)).
14. **Empty states lead on.** An empty place says what will be there, why it's empty, and holds the button that fills it; while something loads it shows progress, never a premature "nothing here" ([nng-empty-states](web/nng-empty-states.txt)).
15. **The important first, the rest one step away.** On a page with many parts, the frequent ones come first and the rare or advanced ones (delete, keys, storage details) last or behind a clearly labelled link; more than two levels means the design is too complex ([nng-progressive-disclosure](web/nng-progressive-disclosure.txt)).
16. **Forms in one plain column.** Labels above their fields, fields as wide as their content, no placeholder as the only label, hints stated before the error, errors next to the field and kept, no Reset or Clear beside the main button ([nng-web-forms](web/nng-web-forms.txt)).

Plan from these (T166): Settings becomes a page in the practice view's place (top bar keeps ☰ and the song list toggle; a "← Back to the songs" link and Esc); parts in this order: the project (name, shared folders with Folders… and Add folder), this device (storage, Keep files), OneDrive sign-in, language and theme, keys, and last the danger zone (Delete project). The first start becomes steps: 1 name, 2 link, 3 sign in (skipped when signed in), 4 folders, then the preview and Download; each with Back, and the step count on top.

## Checklist for a UI task

- Which principle does the change rely on, and does it break one?
- Mouse, keyboard (and footswitch if it's about the sheet) all work.
- Screenshot at 1280×720 in light mode; dark mode readable.
- Keys added to the help dialog, [player.md](player.md) and [practice-layout.md](practice-layout.md#keys).
