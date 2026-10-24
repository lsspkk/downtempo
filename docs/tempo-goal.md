# Tempo in BPM and the optimal tempo

**Summary**: built in both apps (T231 Python player, T232 browser app, 2026-10-24) from the design revised with the user (T230), which replaced the first design (T223–T226); tried by the user (T219, T231.1, T232.7). Every recording has a **recording tempo** (BPM at 100 %), found by the player on first load and just a number the user can change (no "estimated" state). A song can have an **optimal tempo** in BPM (from the sheet, a teacher or the band). The always-visible tempo row shows **BPM now** ("75 BPM"), a round **TAP** button that sets the speed like a DAW's tap tempo, a round **metronome** button that ticks steadily at the BPM now, and a **Play at 100** switch: on, every recording of the song plays at the optimal tempo (remembered per song, T237, T238). The rest sits in a **BPM tab**: the recording tempo and the optimal tempo. In the Python player Full controls become one tight surface with folder tabs **Pitch · Trainer · Loop · BPM** on a full-height slot below, and the recordings are a labelled dropdown. No dialog.

## What other apps do (principles, not layouts)

- **Anytune** estimates a song's BPM on import, shows it in the song info and changes the shown value as the tempo changes; the user can override it, and it is saved with the song's other settings ([anytune-basics](web/anytune-basics.txt)). → Estimate once, show BPM × speed, let the user override, save it.
- **Capo** says its detected tempo is an average and may not match a tap over a few bars; its click plays the detected beats, not a steady timer, because a steady click drifts against a live recording ([capo-beat-tracking](web/capo-beat-tracking.txt)). Users count at different pulses (eighths, quarters, half-time) ([capo-beat-grid-edit](web/capo-beat-grid-edit.txt)), and not being able to double or halve the detected pulse was a known gap ([capo-music-analysis-ios](web/capo-music-analysis-ios.txt)). → (T230 lined the click up with the music and kept ½ · 2×; the user found neither useful in practice and T239 dropped both: the metronome is a steady tick to hear a tempo by itself.)
- **Amazing Slow Downer** and **Transcribe!** work only in % speed ([amazing-slow-downer](web/amazing-slow-downer.txt), [design-transcribe-overview](web/design-transcribe-overview.txt)). → Keep % as the control; BPM is shown beside it, not instead of it.

## Decisions (T230, with the user)

1. **The optimal tempo is in BPM**: it comes from the sheet's marking or from a teacher or the band, so it needs the recording's BPM in the same pulse.
2. **The estimate is usually right**, so fixing it gets a small place: −/+, a typed number (½ · 2× dropped by T239). **No "estimated" state**, no "≈", no "That's right", no "Find it": the label is always "Recording tempo"; its value says "finding…" on first load, then the number; "none found" when there is none.
3. **One metronome button, a steady tick** (T239, T240, the user's calls: a click lined up with the playing music "just won't work", and buttons for the BPM tab's two rows were useless): round like TAP, it starts or stops the tick at once at the BPM now (so ←/→, Play at and Tap move it), playing or not. Off it is outlined with a metronome; ticking it is filled blue with a white ■ (a click stops it). A new recording starts quiet.
4. **The Play at switch stays on** (T237, T238; it first showed only whether BPM now = the optimal tempo, so a new recording turned it off): remembered per song, every recording plays at the optimal tempo by its own BPM. On sets the speed (as far as 50–130 % allows, with a note when it can't reach); off goes back to the speed before, until the user changes the tempo by hand (then the switch just turns off and the speed stays). Without an optimal tempo it is grey; its tooltip says to set one in the BPM tab, and a click opens that tab. No Clear: an empty field means no optimal tempo.
5. **Tap is a DAW tap tempo**: the user taps along another version (YouTube) and the recording plays that fast. After 4 taps the speed follows (BPM now = tapped), every tap refines it, a 2 s pause starts over. It is a try, not a setting: nothing is saved but the speed, as with ←/→. It needs the recording tempo (disabled without it).
6. **Tabs, not cards** (Python Full controls): **Pitch · Trainer · Loop · BPM**, the most used at the right; one tab is always open, remembered. "Trainer" is the step-up trainer moved out of its expansion.
7. **One surface with thin dividers** instead of a stack of cards: padding 8 px, gaps 4–8 px. Below it, after a gap, the tabs as **folder tabs on a slot** that fills the pane's height: the open tab has the slot's tint and joins it, the others are plain labels (the user's call, T236: underlined labels didn't read as tabs). Full fits 1280×720.
8. **The recordings are a dropdown with a visible label**, two clicks are fine: `Recording [ live 2025 ▾ ] 2 of 3`; with one recording plain text without ▾ and count. Its menu rows: ✓ on the current one, the name in full, its recording tempo. Keys in the menu: ↑/↓, Enter, Esc; T still steps through them.
9. **Simple** keeps only the tempo row (no slider, no tabs, no Tap button). **Sheet-only**'s bar gets nothing new; X and G there show a short toast ("Playing at 100 BPM (114 %)", "Back to 85 %", "Tapped: 108 BPM (123 %)").

## Concepts in plain words

| Word on screen | Meaning | Belongs to | Saved |
|---|---|---|---|
| **Recording tempo** | the BPM of the audio as recorded, at 100 % | a recording (two takes differ) | `practice.json` → `recordings[path].bpm` (the old `bpm_estimate` flag is dropped) |
| **Optimal tempo** | how fast the song should go; optional | the song | `practice.json` → `songs[id].goal_bpm` (the key stays) |
| **BPM now** | what you hear: recording tempo × the speed % | nothing, computed | not saved |

The speed % stays the player's one tempo control (slider, ←/→, trainer). BPM numbers move it only by the user's action: the Play at switch and Tap.

## Python player: Full controls (T231)

```
┌──────────────────────────────────────────────────────────────┐
│ Recording [ live 2025                  ▾ ]  2 of 3           │
│ ▁▂▅▇▅▃▂▁▂▃▅▇█▇▅▃▂▁▂▃▅▇▅▃▂▁  (waveform)                       │
│ 1:12 / 4:12          ⏮  ↺5  ▶  5↻  🔁                        │
│──────────────────────────────────────────────────────────────│
│ Tempo  [−] 85 % [+]  75 BPM  (TAP) (♩)   ○ Play at 100       │
│ ═══════════════●══════════════════════════                   │
│  50   60   70   80   90  100  110  120  130                  │
│──────────────────────────────────────────────────────────────│
│  Pitch   Trainer   Loop   BPM                                │
│                           ‾‾‾                                │
│ Recording tempo [−] [ 88 ] [+] BPM                           │
│ Optimal tempo   [−] [100 ] [+] BPM                           │
│                 → 114 % of this recording                    │
└──────────────────────────────────────────────────────────────┘
```

- **Tempo row**: "75 BPM" ("finding…", "–" without a tempo; "now" dropped by T239); the round TAP shows the tapped BPM for a moment; (♩) is the metronome button (filled, with ■, while it ticks); TAP and it share a soft grey outline; "Play at 100" next to the switch ("Play at –" without one; the user's name, T238: "Optimal" read as a rating, not a switch).
- **BPM tab**: the steppers' typed values count on Enter or leaving the field; the first −/+ of an empty optimal tempo starts from the recording tempo; "→ 114 %" is only shown with both numbers.
- **Loop tab**: redrawn by T241 ([loop-editor.md](loop-editor.md#the-loop-tab-t241)).
- **Trainer tab**: the switch and the step / every / up to row, the status line.
- **Pitch tab**: semitones −/+ and Reset, the volume row.
- **Simple**: `Tempo [−] 85 % [+]  75 BPM  (♩)  ○ Play at 100` and the transport; no tabs.
- Code (built): `tempo_goal.py` the state (no widgets), `tempo_row.py` the tempo row, `bpm_tab.py` / `loop_tab.py` / `trainer_tab.py` / `pitch_tab.py` one module per tab, `recordings.py` the dropdown, `mini_bar.py` the sheet-only bar; `controls.py` only puts the surface together. The Tempo view and the BPM box are gone.
- As built: in a narrow pane the tempo row wraps after `[+]` (BPM now, TAP, the metronome and Play at on a second line). ↑ / ↓ move in an open menu (a small page script), Enter picks, Esc closes.

## Browser app (T232)

- **Bar**, after the tempo slider: `75 BPM  (TAP) (♩)  ○ Play at 100`; TAP hides first on a narrow desktop (G still taps).
- The **BPM** button opens a thin strip under the bar (where the loop editor opens), one or two rows, replacing today's three-card panel: `Recording tempo [−][88][+] BPM   Optimal tempo [−][100][+] BPM   ✕`, "→ 114 %" under the optimal tempo. Esc closes it.
- **Phone**: the position line keeps "75 BPM"; the strip is its page (Back closes it) and holds the Play at switch, TAP and the metronome.
- The **recording menu** gets "Recording" on it and the same rows (✓, name, BPM).
- Memory: `tempos[project/recording]` keeps `bpm` (the `estimate` flag goes), `goal` per song stays.
- As built: `ui/tempo/useTempoGoal.ts` (state), `TempoBar.tsx` (`BpmButton`, `TapButton`, `MetronomeButton`, `OptimalSwitch`), `click.ts` (the tick), `BpmStrip.tsx` (the strip, the phone page), `ui/kit/Switch.tsx`. Tap hides below 1536 px wide (the bar is full at 1280 with the song list open). Finnish: "Optimitempo", the switch "Soita 100", "Metronomi"; TAP stays "TAP" (round).

## Keys

| Key | Where | Does |
|---|---|---|
| G | everywhere (not in the loop editor) | tap the beat: after 4 taps the speed follows; the view stays as it is |
| X | everywhere | Play at switch on / off |
| T | everywhere | next recording |
| Space | everywhere | play / pause |
