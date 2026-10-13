# Sheet only

**Summary**: Built (T190), after a quick look (T189): for a musician who only reads the score, a "Sheet only" view where the page has the whole screen. It replaces the old full screen: the app's bars and menus go (no browser full screen, which an iPhone can't do reliably), the screen stays on, a tap on the left or right side turns a screen, a tap in the middle shows a small bar with ← to leave, and the phone's Back leaves too. Found by a quick look at two leading score readers, not a full study.

## What the leading readers do

- **forScore** (iPad / iPhone): the controls are hidden by default "to help you get the best view of your music"; a single tap in the middle of the page shows the control bar, another hides it; taps on the sides or swipes turn pages ([forscore-control-bar](web/forscore-control-bar.txt), [forscore-basics](web/forscore-basics.txt)).
- **MobileSheets** (Android): a Fullscreen Mode setting that also hides the phone's navigation bar; a tap in the centre brings the bar back and dismisses it; the left and right sides turn pages ([mobilesheets-fullscreen-forum](web/mobilesheets-fullscreen-forum.txt)).
- Both: no exit button on the page at all. The way out is the middle tap, which nobody does by accident because the side taps are where the page turns are.

## What a web page can do

- **Full screen of the browser** (`requestFullscreen`) needs a tap to start it; Android's Chrome allows it, and its Back gesture leaves it. On an iPhone Safari's support for anything but video has come and gone between versions, so the view must work without it: hiding the app's own bars is most of the gain anyway ([mdn-request-fullscreen](web/mdn-request-fullscreen.txt)).
- **Keeping the screen on** (Screen Wake Lock) while reading, so a long piece doesn't go dark between page turns ([mdn-wake-lock](web/mdn-wake-lock.txt)).
- **Back**: the phone's Back already closes pages over the song (T188); Sheet only is one more.

## The pick for Downtempo

- **One mode, called "Full screen"** ("Koko näyttö", the user's call), instead of the browser's full screen: from the sheet's menu or toolbar, or F.
- **Nothing on the page but the music**: the app hides all its bars and menus; no exit button; the screen kept on. No browser full screen (the user's call, 2026-10-14): an iPhone can't be relied on for it, and hiding the app's own bars is the same on every phone.
- **Taps**: the left third of the screen a screen back, the right third a screen on (the same smooth step as PgDn, so a quick double tap moves two); the middle shows a slim bar with ← and the mode's name, a second middle tap hides it. Swiping scrolls as always; zoom, trim and rotation stay as they were.
- **Leaving**: ← in that bar, the phone's or browser's Back, Esc or F.
- **Learning it**: on entering, the slim bar shows for a moment with one line, "Tap the sides to turn, the middle for the bar", then hides; the same line stays in the bar whenever it is shown.
