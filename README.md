# Downtempo

Practise your group's songs at your own speed. For musicians in a band, a choir or a course whose sheets and recordings live in a shared OneDrive folder.

- **Songs, not files.** Downtempo downloads the shared folder and groups the files into songs by their names: each song's recordings and sheets together, whatever the folder layout.
- **Slower, same pitch.** Tempo 50–130 % with the pitch unchanged; an A–B loop set exactly on the waveform, saved loops for the hard bars.
- **The sheet beside the recording.** Zoom, fit width or page, trim wide margins, rotate for a laptop on the music stand; page turns from the keyboard or a footswitch.
- **Easy to browse and practise.** A searchable song list, the next song with one key or tap, and each song remembers its tempo, loop, recording and zoom.
- **Always up to date.** ⟳ fetches what's new or changed in the shared folder; nothing on your side is ever deleted by it.

## Two versions

- **The player** (this repository; Windows, macOS, Linux) sounds best: the tempo is changed by [Rubber Band](https://breakfastquay.com/rubberband/), the time-stretcher of professional audio software, so slowed-down music stays clean. It has everything: waveform, loop editor, tempo trainer, pitch, the project screen for sorting songs. Install below.
- **The browser version**, <https://lsspkk.github.io/downtempo/>, needs nothing installed and works on a laptop or a phone, in English and Finnish. It is a demonstration: the tempo uses the browser's own stretch, fine for moderate slowing but not as clean as the player's, and for regular use you should run your own copy ([docs/browser-app.md](docs/browser-app.md)).

## Where the songs come from: OneDrive

Downtempo reads a group's material from a **OneDrive shared folder**; other services aren't supported yet. Whoever leads the group shares the folder in OneDrive (Share → Copy link) and sends the link around. Each musician pastes it into Downtempo, signs in once with any Microsoft account (Microsoft needs that to open a shared link), and ticks the folders to download. Downtempo only reads the shared folder; the files are copied to your own computer or browser and play without a network afterwards. A **project** is one group, with its own shared folders and songs; you can have several.

Why it exists: [docs/purpose.md](docs/purpose.md). What's built and what's next: [docs/ideas.md](docs/ideas.md).


# Install and start

The player runs with [uv](https://docs.astral.sh/uv/), which fetches the right Python and every library by itself on the first start (a few minutes, once).

## Linux and macOS

```sh
# 1. Install uv (in a terminal), then open a new terminal:
curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Start python app from the Downtempo folder:
uv run python frontends/nicegui/app.py
```

No sound on Linux? `sudo apt install libportaudio2` (Debian, Ubuntu).

## Windows

Windows 10 or 11, 64-bit. Open **PowerShell** (Start menu → *PowerShell*), paste this block and press Enter:

```powershell
# 1. Install uv, and let this window find it:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
$env:Path = "$HOME\.local\bin;$env:Path"
# 2. Get Downtempo into Documents\downtempo:
Invoke-WebRequest https://github.com/lsspkk/downtempo/archive/refs/heads/main.zip -OutFile "$HOME\Documents\downtempo.zip"
Expand-Archive "$HOME\Documents\downtempo.zip" -DestinationPath "$HOME\Documents" -Force
Rename-Item "$HOME\Documents\downtempo-main" downtempo
Remove-Item "$HOME\Documents\downtempo.zip"
# 3. Start the player:
cd "$HOME\Documents\downtempo"
uv run python frontends\nicegui\app.py
```

Later starts take a few seconds: run only the last two lines in a new PowerShell (if `uv` isn't found, `winget install --id=astral-sh.uv -e` once). To update, repeat the block into a fresh folder and copy the old `data` folder over, or use [Git](https://git-scm.com/download/win) (`git clone https://github.com/lsspkk/downtempo.git`, then `git pull`). An empty window means the *Evergreen WebView2 Runtime* from Microsoft is missing. Your songs, settings and sign-in stay in the `data` folder.

# Use the player

1. **Start**: paste your group's OneDrive folder link (Share → Copy link), sign in, pick the folder, Download.
2. **Songs**: **Edit song list** → **Create selected**.
3. **New files**: ⟳ at the top of the song list.
4. **Settings, other groups, sharing**: the ☰ menu.

More: [docs/player.md](docs/player.md).

# Command line

The same without the player, for scripts and testing:

```sh
uv run downtempo add '<link>'                  # add a shared folder (signs in the first time)
uv run downtempo download                      # download what's new, then update the song list
```

## Use

| Command | Does |
|---|---|
| `uv run downtempo add '<link>' [--folder a/b] [--name N]` | add a shared folder (or one folder inside it); shows what's there |
| `uv run downtempo folders '<link>' [a/b]` | list the folders inside a share, with recordings and sheets counted |
| `uv run downtempo sources` | the shared folders, their files here, who is signed in |
| `uv run downtempo download [name …] [--dry-run]` | download what's new or changed (Ctrl+C stops, keeping finished files), then rebuild the song list |
| `uv run downtempo remove <name> [--delete-files]` | forget a shared folder; its files stay unless `--delete-files` |
| `uv run downtempo catalog` | rebuild the song list from the downloaded files |
| `uv run downtempo sign-out` | forget the OneDrive sign-in on this computer |
| `uv run downtempo export <file>` | save the project's settings file (its shared folders) to email; `-` prints it |
| `uv run downtempo import <file> [--new \| --add] [--yes]` | add shared folders from a settings file, as a new project or into the current one; shows what changes and asks |
| `uv run downtempo songs [--explain \| --to-sort \| --create]` | the songs, each file with its label and why it's there, and what waits in To sort; `--create` makes a song of every suggested song first |
| `uv run downtempo move <file> <song>` | put a file into a song by hand (file: its id or a unique end of it) |
| `uv run downtempo project [list]` | the projects (a band, a choir, a course), `*` = current |
| `uv run downtempo project new <name>` / `use <name>` | make a project and switch to it / switch |
| `uv run downtempo project rename <name> <new>` / `delete <name> [--yes]` | rename (nothing moves) / delete with its downloads (asks) |

`--project <name>` before a command works on that project instead of the current one (`uv run downtempo --project choir download`). `DOWNTEMPO_DATA=<folder>` in front of any command (or the player) uses another data folder, e.g. a throwaway one for tests. Data from before projects is moved into a project on the first run.

# License

Copyright (C) 2026 Lasse Pekkarinen

Downtempo is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. It is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See [LICENSE](LICENSE) (AGPL-3.0).

In short: use, copy and change it freely; if you give a changed version to others, or run it as a web page others use, offer them its source under the same license. Both apps link to this repository. Song material is not included: it stays local in `data/` (git-ignored).
