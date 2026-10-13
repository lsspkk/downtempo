# Ideas

The big things, one line each. Tasks for them are grouped under the same names in [todo.md](todo.md).

## Not done

- **Project screen**: a full-screen view of the project: its sources (add a folder, update, sign in) and its songs as rows of files to drag between songs; the downloader UI and the sorting UI in one ([project-screen.md](project-screen.md))
- **Browser player**: the player as a web page; built and tried by the user (T135–T194: projects, download, songs, tempo, loop editor, sheets, phone layout, English and Finnish: [browser-app.md](browser-app.md)); left: a better tempo stretch than the browser's own (T4, T31, T8 in [todo.md](todo.md#browser-player))
- **Parts of a file**: a song uses pages 4–5 of a songbook PDF or 12:30–16:10 of a long rehearsal recording (after Song grouping, which lets one file be in several songs)

## Later

Not now (the user's call, 2026-10-11).

- **Downloaders**: one per source type; OneDrive done, Google Drive next

## Done

- **Languages**: the browser app in English and Finnish, from the browser's language or the ☰ menu; texts as typed message functions (Paraglide JS); built T149–T152 ([browser-app.md](browser-app.md#languages))
- **Settings file**: export the download settings to one file to email, import it on another computer; built, the user's try-out T68 in todo ([settings-file.md](settings-file.md))
- **Projects**: several music projects, each with its own sources and songs; built, the user's try-out T83 in todo ([projects.md](projects.md))
- **Song grouping**: files from any folder layout and any source become songs by their names; the user approves the song list (titles, also-called names, linked folders are the magnets), unsure files wait in To sort, the user drags files between songs in a full-screen project screen; sheet-only and audio-only songs are fine; built T86–T91, T98, T102, T112 ([purpose.md](purpose.md), [song-grouping.md](song-grouping.md), [project-screen.md](project-screen.md))
- **Downloader UI**: in the Python player: add a shared folder by pasting its link, sign in, download with progress, songs appear; no terminal or config files ([blocks.md](blocks.md)); core and "Check for new files" built (T56–T60, T85), pasting a link in the player comes with the project screen (T62)
- **Agent guide**: CLAUDE.md rules that keep a growing codebase readable: summaries first in every doc, small clean parts without enterprise overhead
- **Python player**: tempo 50–130 % with pitch kept, loops, trainer ([player.md](player.md))
- **Loop editor**: a full-screen view of the waveform to zoom, scroll and select a loop, like a DAW but simple
- **Small-laptop practice**: hideable panes, simple controls, rotated sheet, footswitch keys ([practice-layout.md](practice-layout.md))
- **Recording choice**: pick among a song's recordings
- **Sheet music**: the song's PDFs beside the player
- **Song catalog**: `data/songs.json`, the only thing players read
- **OneDrive downloader**
