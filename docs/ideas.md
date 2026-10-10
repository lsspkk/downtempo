# Ideas

The big things, one line each. Tasks for them are grouped under the same names in [todo.md](todo.md).

## Not done

- **Agent guide**: CLAUDE.md rules that keep a growing codebase readable: summaries first in every doc, small clean parts without enterprise overhead
- **Browser player**: same in a web page, to compare with the Python player
- **Downloaders**: one per source type; OneDrive done, Google Drive next
- **Downloader UI**: in the Python player: add a shared folder by pasting its link, sign in, download with progress, songs appear; no terminal or config files ([blocks.md](blocks.md))
- **Song grouping**: files from any folder layout and any source become songs by their names; the user approves the song list (titles, also-called names, linked folders are the magnets), unsure files wait in To sort, the user drags files between songs in a full-screen project screen; sheet-only and audio-only songs are fine ([purpose.md](purpose.md), [song-grouping.md](song-grouping.md), [project-screen.md](project-screen.md))
- **Project screen**: a full-screen view of the project: its sources (add a folder, update, sign in) and its songs as rows of files to drag between songs; the downloader UI and the sorting UI in one ([project-screen.md](project-screen.md))
- **Parts of a file**: a song uses pages 4–5 of a songbook PDF or 12:30–16:10 of a long rehearsal recording (after Song grouping, which lets one file be in several songs)
- **Settings file**: export the download settings to one file to email, import it on another computer ([settings-file.md](settings-file.md))
- **Projects**: several music projects, each with its own sources and songs ([projects.md](projects.md))

## Done

- **Python player**: tempo 50–130 % with pitch kept, loops, trainer ([player.md](player.md))
- **Loop editor**: a full-screen view of the waveform to zoom, scroll and select a loop, like a DAW but simple
- **Small-laptop practice**: hideable panes, simple controls, rotated sheet, footswitch keys ([practice-layout.md](practice-layout.md))
- **Recording choice**: pick among a song's recordings
- **Sheet music**: the song's PDFs beside the player
- **Song catalog**: `data/songs.json`, the only thing players read
- **OneDrive downloader**
