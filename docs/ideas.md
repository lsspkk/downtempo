# Ideas

Epics, one bullet each: `- I<n> title: goal`. Move to Done when no tasks are left.

## Not done

- I2 Song set: one file, `data/songs.json`, lists the songs the players use (title, audio files, pdfs); both players read only this file, never scan folders themselves
- I3 Python player MVP: `frontends/nicegui/`, NiceGUI UI, sound played and time-stretched in Python (`sounddevice`, not the browser), 0.5x–1.3x tempo with pitch kept
- I4 Browser player MVP: local web page plays a song from the song set at 0.5x–1.3x tempo with pitch kept; compare with I3
- I5 Sheet music view: show the song's PDF in the same program as the audio player
- I6 Audio choice: UI to pick which audio file to play when a song has several recordings
- I7 Multi-source downloader: `uv run downtempo download` fetches every source in `data/sources.toml` into `data/downloads/<name>/`; OneDrive done, Google Drive next

## Done

- I1 OneDrive downloader: fetch `.mp3`/`.pdf` from the shared folder (Entra + MSAL + Graph)
