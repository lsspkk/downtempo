# Browser app (MVP)

**Summary**: Built (T135–T146, folder choice T148, English / Finnish T149–T152, compact player and loop editor T153–T158). Downtempo as a web page on GitHub Pages: projects, a OneDrive shared folder per project with the folders to take ticked in its tree, download into the browser's private file system, songs grouped by name, a player in the top bar with tempo 50–130 % (pitch kept), a loop editor on the waveform (wavesurfer.js) with saved regions, and the PDF sheets. A proof that the whole app fits in a browser; not every control of the Python player. React 19 + TypeScript, built by Vite, styled with Tailwind 4, texts by Paraglide JS, tested with Vitest. Code: [frontends/browser/](../frontends/browser/). On a phone: [browser-mobile.md](browser-mobile.md).

## Run

```sh
cd frontends/browser
npm install        # Node 22.13 or newer; also copies pdf.js's font and decoder files to public/pdfjs/
npm run dev        # http://localhost:8000/ (the registered sign-in address; the port is fixed)
npm test           # unit tests + the Tailwind test (a real build)
npm run build      # dist/, for https://lsspkk.github.io/downtempo/
npm run preview    # the build at http://localhost:8001/downtempo/ (sign-in won't come back here)
npm run format     # prettier (not the generated src/paraglide/)
```

Published by [.github/workflows/pages.yml](../.github/workflows/pages.yml) on every push to `main` that changes `frontends/browser/` or `frontends/browser-tests/`: `npm ci`, test, build, the test page copied to `/downtempo/tests/` ([browser-tests.md](browser-tests.md)). Sign-in comes back to `https://lsspkk.github.io/downtempo/` and `http://localhost:8000/`, both already in the Entra registration, so the app needs no new setup.

## What it has, what it leaves out

| Has | Leaves out (Python player has it) |
|---|---|
| First start: one full page, not a wizard: the concept, how it works and what it doesn't do beside one form (the group's name, the link required, with a "why" box and Microsoft's sharing guide; no project without a folder link). Then Get the songs, a full page with a progress list (Link · Sign in · Folders · Download): sign in, tick the folders to take (the tree opens one level at a time, each folder with its item count and size; none ticked = all; inside a ticked folder a click leaves a folder out, crossed out), then "about 12 songs from 31 files, 180 MB", Download | skipped folders by rule |
| ☰ menu: projects, New project…, Settings…, the other theme in one item ("Dark theme" / "Light theme", moon or sun), the other language in one item ("Suomi" / "English", a small grey flag), About ("Tietoja": a demonstration, run your own copy for regular use; exactly what happens to the account and files; how to remove it) | export / import of the settings file |
| Settings as a full page (the top bar shows ☰, ← Back and "Settings" instead of the song and player; Esc), the important first: the project (name, shared folders with what they take, Folders…, Remove, Add folder, and at its end "Delete the files from this device" (frees the space, keeps the project and its memory) and "Delete the project" (link, folders, files, loops, regions, all remembered), each asking first), this device (what the browser holds and allows, Keep files and that only the browser's site settings undo it), OneDrive sign-in, keys; language and theme only in the ☰ menu | sign-in per provider, Change link |
| ⟳ Update: list, download what's new or changed, Stop; files gone from the server are only counted | Google Drive |
| Song list: search, ♪ / 𝄞 marks, N / P, a drawer on phones | new-file dots, Edit song list (sorting by hand, To sort) |
| Top bar as in the Python player: ☰ and the list toggle over the song list's column, the title, then "♪ Recording 1/2" in small type (a menu headed Recording: ✓, the name, its recording tempo and upload date; one recording is plain text), ▶ / ⏸, the time, the position as a small bar waveform (click or drag seeks, the loop as an amber band), tempo slider with its marks, repeat (amber when on), loop editor. The song list's top: Project ⟳, its name, one status line | step-up trainer, pitch, volume, view modes, the always-visible waveform |
| Loop editor (✎ or E, full width, not full height): laid out as the Python player's Loop tab (T242, [loop-editor.md](loop-editor.md#the-loop-tab-t241)): the loop's line (Loop switch, length, Whole song, Zoom to loop, Hear end, Clear), the waveform with ruler (click, click or drag selects, handles, wheel / pinch zoom), Start / End cards (amber) with Set here (A / B) and « ‹ › » (1 s, 0.1 s), Saved loops per recording under a line | full screen, undo, edge scrolling, ruler-drag zoom, overview strip, pause between repeats |
| Sheet as the Python player's: a tab per PDF, zoom − / % / +, fit width (W), fit page (H, kept on resize), Sheet only (F: no bars, side taps turn, a middle tap shows ←; Back or Esc leaves; [sheet-only.md](sheet-only.md)), trim margins (0.5 / 1 / 2 cm cut from every side of the pages, one setting for every song), ⋮ rotate right (O) / left (the whole view turns, so scrolling and keys follow the page; one rotation per device), open the PDF in a new tab; ↑ / ↓ a 20 % step, PgUp / PgDn a screen (a quick double tap goes two), Home / End | cropping, page-by-page PgDn, scroll settings |
| Tempo in BPM and the optimal tempo as the Python player's ([tempo-goal.md](tempo-goal.md), T232): `75 BPM  (TAP) (metronome)  ○ Play at 100` after the tempo slider (TAP from 1536 px; G taps anyway: from the 4th tap the speed follows; X switches). "75 BPM" opens the BPM strip under the bar (a page of its own on a phone, with the Play at switch, TAP and the metronome; ✕, Esc or Back closes it): the recording tempo (found by essentia.js in a worker on first load; −/+, typed) and the optimal tempo with "→ 114 %" under it; the metronome (Web Audio: a steady tick at the BPM now, T239, T240) is the bar's round button | trainer |
| Remembered per song: tempo, loop, recording, sheet, zoom or fit page; the optimal tempo; per recording its regions, its tempo in BPM and where it was left (on pause, on leaving it, when the page closes; T234); the last song | |
| In Sheet only a tempo change (← / →, X, G) shows for 1.5 s over the sheet: "Play at 100 · 114 % · 100 BPM" (T235) | |
| Wavs kept as mp3 ([compress.md](compress.md), T217): a new or changed wav is downloaded, encoded at 128 kbit/s (Mediabunny's WASM LAME, loaded with the first wav) and only the mp3 kept; wavs downloaded before are encoded on the next ⟳ without downloading them again, and the practice memory moves with them; "Compressing 2 of 7: take3.wav"; a wav that can't be encoded stays a wav | |

## Parts

`src/core/` has no React. `src/ui/` has a folder per part of the screen; the song's state lives in hooks (`usePlayer`, `useSheet`), the parts take what the hook returns, and the song page's two layouts only arrange the parts.

```
App ─ start/Welcome (no project yet)
    └ practice/Practice ─ GetSongs (nothing downloaded)          ┐ each page brings its own bar:
                        ├ song/SongPage ─ DesktopSong | PhoneSong ├ bar/Bar + bar/MainMenu (☰)
                        └ settings/SettingsPage (over all of it) ┘
SongPage = usePlayer + useSheet  →  player/*  and  sheet/*  parts
```

| Folder | Files: one job each |
|---|---|
| `core/` | `onedrive.ts` sign-in by hand-written PKCE (tokens in `localStorage`, refreshed; SPA refresh tokens last 24 h), share link → share id, one folder's subfolders, list the chosen folders at any depth (others never opened), a file's download URL · `files.ts` the private file system `projects/<project>/<source>/<path>`, save as it streams, open, remove, storage, Keep files · `projects.ts` projects, sources with chosen and left-out folders, what's on this device · `chosen.ts` pure: what the ticked folders take minus the left-out ones · `plan.ts` pure: listings vs. this device → fetch / compress (smallest first) / same / gone · `compress.ts` a server's wav stored as mp3 (`storedAs`), `toMp3` by Mediabunny · `download.ts` one run at a time (3 files at once in it), its status a store; encodes wavs and moves their memory · `grouping.ts` pure: songs by name · `practice.ts` per-song memory, regions, recording tempos, the last song, the sheet's rotation; `moveRecording` when a wav becomes an mp3 · `store.ts` a value React can watch · `format.ts` times, sizes, dates, "ago" in the app's language |
| `ui/` | `App.tsx` first start or practice, sign-in coming back · `signin.ts` what waits for the sign-in · `theme.ts` light / dark · `language.ts` English / Suomi |
| `ui/kit/` | the reusable pieces, nothing about Downtempo: `Button.tsx` (`Button`, round `IconButton`: 44 px on a phone, 36 px with a pointer) · `DropDown.tsx` (a trigger and its panel: under the trigger with a pointer, a full-width sheet under the bar on a phone, by CSS alone; `MenuItem`, `MenuLabel`, `MenuSeparator`) · `bits.tsx` (`Muted`, `Progress`, `Step`, `WaveBuilding`) · `keys.ts` keys per part · `phone.ts` `usePhone`, asked only by the song page |
| `ui/bar/` | `Bar.tsx` the top bar's frame (48 px) and its pieces: `BarStart` (as wide as the song list under it), `BarTitle`, `ListButton`, `BackTitle` · `MainMenu.tsx` the ☰ menu |
| `ui/start/` | `Welcome.tsx` the first start's one-page form (with "why a link" and a link to Microsoft's sharing guide) |
| `ui/practice/` | `Practice.tsx` songs, the chosen one, the list open; picks the page · `SongList.tsx` the list (a column, a drawer, or a phone's full page) · `ProjectPanel.tsx` its top: Project ⟳, name, status · `GetSongs.tsx` steps 3 sign in and 4 folders, preview → Download |
| `ui/folders/` | `FolderPicker.tsx` the shared folder's tree with ticks, left-out folders and sizes · `LinkInput.tsx` the link field and Add folder |
| `ui/song/` | `SongPage.tsx` the song's choices (recording, PDF, zoom), `usePlayer` and `useSheet`, then the layout · `DesktopSong.tsx` / `PhoneSong.tsx` where the parts go ([browser-mobile.md](browser-mobile.md)) |
| `ui/player/` | `usePlayer.ts` state, actions and keys · `audio.ts` the hook: state, actions, `peaks`, `onTime` · `stretch.ts` the recording decoded and played by Signalsmith Stretch (tempo, loop in the audio) · `followTime.ts` the waveforms' cursor · `controls.tsx` `PlayButton`, `PlayTime`, `LoopButton`, `EditorButton`, `PlayerError` · `Tempo.tsx` `TempoSlider`, `TempoButton` · `RecordingMenu.tsx` · `lazy.tsx` loads wavesurfer.js with `Position` / `LoopEditorPanel` · `PositionWave.tsx` · `LoopEditor.tsx` · `SavedLoops.tsx` |
| `ui/tempo/` | the tempo in BPM: `useTempoGoal.ts` state and actions (the recording tempo, the optimal tempo and its switch, Tap, the Metronome), made by `usePlayer` · `TempoBar.tsx` `BpmButton`, `TapButton`, `OptimalSwitch` · `BpmStrip.tsx` the strip · `estimate.ts` decode + pieces, `tempoWorker.ts` essentia.js's PercivalBpmEstimator (both loaded with the first estimate) · `click.ts` the click by Web Audio; the pure part (pieces, median, beat offset) in `core/tempo.ts` |
| `ui/sheet/` | `useSheet.ts` the PDF choice, size, zoom / fit, rotation, full screen, scroll keys (no pdf.js) · `SheetFrame.tsx` the turning scroll view · `SheetPages.tsx` pdf.js (loaded with the first sheet) · `SheetControls.tsx` `SheetToolbar` (a pointer), `SheetMenu` (a phone) |
| `ui/settings/` | `Settings.tsx` the settings page and its parts |
| `ui/about/` | `About.tsx` the About page |
| `messages/` | `en.json`, `fi.json` (with `project.inlang/`): every text, in English and Finnish (below) |

## Decisions

- **Tempo and loop by Signalsmith Stretch Web** (T4.1–T4.5, built and tried by the user 2026-10-14: sounds great): the recording is decoded whole into memory (`decodeAudioData`, then handed to the AudioWorklet node; its worklet and WASM are inlined in the npm package, so the build needs no extra file), `schedule({rate, loopStart, loopEnd})` changes tempo and loop live, the loop runs sample-accurate in the node. No `<audio>` element. Why and the alternatives: [tempo-browser.md](tempo-browser.md). The browser's own `playbackRate` build is in git history if the listening test says the old one was better.
- **Parts, hooks and layouts** (T177–T181, the user's review): a menu is always a `DropDown`, a round button always an `IconButton`; phone and pointer differences inside a part are CSS (`max-sm:` / `sm:`), and only `SongPage` picks a layout by `usePhone`. No portals: each page builds its own bar.
- **Look of the Python player**: indigo accent (`#4f5bd5`), amber loop (`#f59e0b`), cool greys (Tailwind zinc), its Material icons as [lucide-react](web/lucide-react-start.txt) (repeat, maximize, panel toggle, chevrons, refresh).
- **Loop editor by wavesurfer.js**, not our own drawing (the user's call, 2026-10-13): it draws from the peaks `stretch.ts` makes while decoding (one channel of ±maximum per 8 samples, `peaks` + `duration`, no `media`, no second decode); `followTime.ts` moves its cursor from the player's `onTime`, so playback, tempo and the loop stay in `stretch.ts`. `interact: false`: a click on the waveform selects (click, click), its drag selection makes a new loop, the loop region's handles resize it, a click on the ruler seeks. Docs: [readme](web/wavesurfer-readme.txt), [options](web/wavesurfer-options.txt), [methods](web/wavesurfer-methods.txt), [regions](web/wavesurfer-region-params.txt).
- **Grouping without the sorting screen**: every suggestion becomes a song. Song folders (a folder whose name its files mostly agree with), other files joining a song folder by name, the rest grouped by cleaned name within the typo tolerance; names that say nothing go to "Other files". Same cleaning, noise words and tolerance as [song-grouping.md](song-grouping.md); no `grouping.json`, no offers, nothing by hand.
- **pdf.js legacy build**: pdf.js 6 uses `Map.getOrInsertComputed` (2026 JavaScript) that older browsers lack. Its standard fonts, character maps and JBIG2 / JPEG 2000 decoders are served from `pdfjs/`, so scanned sheets draw too.
- **Web UI by [ux.md](ux.md#web-app-browser-app-t165)** (#12–16): settings a page not a modal, the first start one question per step, empty states that lead on, the important first, forms in one column.
- **Folders by ticks, not rules**: a source keeps `folders` (paths from the shared folder's top) and `skip` (folders left out inside them); missing `folders` means not chosen yet, so a new link always shows the tree before anything is listed. Listing walks only the folders on the way to a ticked one, so a big OneDrive tree costs a few calls.
- **No router**: the page address stays the sign-in redirect address; screens are state.
- **Tests**: unit tests for the pure parts (names, grouping, plan, share id, formats) and a Tailwind test that builds the app with Vite into a temp folder and checks the CSS (used utilities, theme colours, the `.dark` variant, breakpoints, the custom `range` utility, nothing unused). Test files are left out of Tailwind's sources, since they name classes too.

## Languages

English and Finnish, by [Paraglide JS](https://inlang.com/m/gerre34r/library-inlang-paraglideJs) (inlang). Every text lives in `messages/en.json` and `messages/fi.json` under the same key; its Vite plugin compiles them into `src/paraglide/` (generated, git-ignored), one typed function per text: `m.download()`, `m.n_songs({ count })`. A missing text or parameter is a type error, unused texts are left out of the build, and there is no provider. Code in `src/core/` uses the same functions for the texts it shows (download status, OneDrive and file errors, "Other files").

- **Which language**: the saved choice (`localStorage` `downtempo-language`), else the browser's language, else English. ☰ menu or Settings → Language switches it; the page reloads in the new language (Paraglide's way), so not while a download runs. `<html lang>` follows.
- **Add a text**: the same key in both files, then `m.<key>(…)` in the code. Parameters are `{name}`; a count with singular and plural is a variant on `count: plural` (see `n_songs`); `npm test` checks both files have the same keys and parameters and that no Finnish text is still the English one (except OK and Tempo). The loop is "valinta" in Finnish, saved loops "valinnat".
- **Numbers**: sizes ("1,2 Mt") and "3 t sitten" come from `Intl` in `core/format.ts`, not from the messages.
- **Add a language**: its code in `project.inlang/settings.json` `locales`, `messages/<code>.json`, and a name in `ui/language.ts`.
