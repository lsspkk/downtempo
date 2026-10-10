# Player: switching songs, recordings and sheets

Study for the switching bug (T13.6 → T13.5): who switches, what they expect, what the code does, which design fits. **Status: C + D implemented (T13.5, 2026-10-08)**; "What the code does now" describes the code before the fix. One difference from the plan: the newest-wins check uses one ticket per part (audio, sheet) instead of `sel is s.selection`, so a sheet tab click doesn't cancel the song's audio load. Since T34 recordings switch with chips, a menu and `T` (option E: clicks only, nothing for code to set). Code: [frontends/nicegui/app.py](../frontends/nicegui/app.py).

## User picture

An amateur musician in a band (accordion and folk tunes) practises at home on a laptop before rehearsal. The band shares about ten songs, each with an mp3 and one or two sheets (melody, chords). A session goes: pick a song, look at the sheet, play the hard part slowly in a loop, raise the tempo, then go to the next song. The hands are often on the instrument, so switching must be one key or one click and must just work. Quickly switching songs and playing them at another tempo is the core of the app.

Comparable apps: Anytune "saves settings for each song … tempo, pitch, marks, loops" and moves through songs with next/previous ([anytune-basics](web/anytune-basics.txt)). DJ apps treat tempo as temporary, and users ask for it to be kept per song ([djay-tempo-per-song](web/djay-tempo-per-song.txt)).

## User stories and checks

| # | I do | I expect | Check |
|---|---|---|---|
| S1 | click a song, or N / P | the old song stops at once; title, list highlight, sheet, waveform, and that song's tempo, pitch, recording and loop appear together; Play works within a moment | no sound from the old song after the press; no mixed song/recording data |
| S2 | browse fast: N N N N | the highlight follows each press immediately; only the song I stop on is shown and ready | never stuck "loading"; nothing from skipped songs shows up later |
| S3 | pick another recording of the song | same song, same tempo; that recording's loops and position come back; the sheet stays | one load, no reload loop |
| S4 | pick another sheet tab | only the sheet changes; playback is not interrupted | audio continues |
| S5 | restart the app | the last song and its settings return | `data/player-state.json` holds only working choices |
| S6 | a file is missing or broken | a clear message; the rest keeps working; the bad choice is not remembered | next start isn't stuck on the broken file |
| S7 | a song without mp3 or without pdf | the part that exists works; the other part says "none" | no errors |

Open questions (my proposal in brackets):

1. Playing, then switching song: does the new song start by itself? **Decided (user, 2026-10-08): no autoplay.** It stops and waits for Play.
2. Do tempo and pitch belong to the song? [Yes, as Anytune does and as now.]
3. Where does a song start? [Its remembered position, which lies inside the loop when one is set.]

## What the code does now

| Path | What happens | Problem against the stories |
|---|---|---|
| list click / `step_song` → `open_song` | sets `s.song`, then `await load_recording`, then `await show_sheet` | sheet waits for the audio (fine, 0.1 s); OK otherwise |
| `load_recording` | `s.audio = ""`; awaits `engine.close`; then reads **`s.song`** to fill the recording select | after the await, `s.song` may already be the *next* song: mixed data (S1, S2) |
| `recordings.set_options(..., value=path)` | NiceGUI fires `on_change` whenever the value really changes, from code too; the handler is async, so it runs later as a task (source: `value_element.py`, `events.handle_event`). Switching first resets the value to `None` (old path not in new options), then to the new path: two events | `pick_recording` runs after `s.switching` is reset, sees `path != s.audio` (still `""` while loading), and loads again, which sets the value again: **endless reload (S2, S3)** |
| `sheet_tabs.set_options(...)` | same mechanism | double renders; same ping-pong risk |
| `remember(pdf=...)` | stored before the PDF rendered | a broken PDF is remembered (S6) |
| `s.opened` ticket, `_load_lock` | the newest load wins; loads never overlap | good; keep |
| one global `engine`, one `Session` per page | a second browser tab gets its own Session but shares the engine | only in `--browser` mode; out of scope, note it |

Root cause: **code changes a widget's value, and the widget's handler then behaves as if the user had picked it.** The flags (`s.switching`) try to tell these apart by timing, which async handlers break.

## Alternatives

| Option | Idea | Meets S1–S7? | Cost / risk |
|---|---|---|---|
| A. Compare with the requested value | handlers ignore `value == s.want_audio / s.pdf` | stops the loop (S3); still fires `None` events; mixed-data bug stays unless fixed separately | small; still two sources of truth |
| B. Listen to user input only | `.on('update:model-value')` instead of `on_change` | yes for the loop | the event carries NiceGUI's internal option *index*: depends on internals, fragile across versions |
| C. One selection owner, newest wins | a `Selection(song, audio, pdf)` set synchronously by user actions only; a single loader task works on a *copy* of it and gives up when a newer one exists; save choices after success | yes, all; fixes mixed data and S6 | medium refactor of ~4 functions |
| D. Rebuild the recording/sheet widgets per song | create them new with the right value; a value set at creation doesn't fire `on_change` (handlers are registered after `set_value`), so later events come only from the user | yes for the loop; no flags needed | small; widgets get recreated on each switch (cheap) |
| E. Plain buttons/chips instead of select and toggle | `on_click` comes only from the user | yes | UI change; a select scales better for many recordings |

## Pick: C + D

- **D removes the cause**: code never sets a widget's value after creation, so every `on_change` is a real user choice. No flags, no timing.
- **C makes switching correct under speed**: user actions update the selection at once (highlight, title). One loader task takes a snapshot (`song, audio, pdf`), checks after each await that it is still the newest, and only then touches the screen or `state`. Choices are remembered after they load (S6).
- Kept: `_load_lock` in the engine and the newest-wins ticket idea, now inside the loader.
- Not chosen: A treats a symptom, B relies on internals, E is a UI change not needed for the fix (could return in a UI pass).
- Optional, only if S2 still feels slow: skip loading a song whose request was overtaken before its decode started (no timer debounce needed).
