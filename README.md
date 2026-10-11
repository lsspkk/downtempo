# Downtempo

A practice tool for musicians in a band, choir or course. Paste the link to your group's shared OneDrive folder; Downtempo downloads the sheets and recordings, sorts them into songs, and keeps them up to date. Then practise: slower tempo with the pitch kept, loops, the sheet music beside the player.

Why it exists: [docs/purpose.md](docs/purpose.md). What's built and what's next: [docs/ideas.md](docs/ideas.md).


# Install and start

Downtempo runs with [uv](https://docs.astral.sh/uv/), which fetches the right Python and every library by itself on the first start (a few minutes, once). Install commands: [uv docs](https://docs.astral.sh/uv/getting-started/installation/).

## Linux and macOS

```sh
# 1. Install uv (in a terminal), then open a new terminal:
curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Start python app from the Downtempo folder:
uv run python frontends/nicegui/app.py
```

Linux: the window uses Qt, which uv installs. If there's no sound, install PortAudio from the system: `sudo apt install libportaudio2` (Debian, Ubuntu). macOS has everything built in.

## Windows

Windows 10 or 11, 64-bit.

Open **PowerShell** (Start menu → type *PowerShell*), paste this whole block and press Enter:

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

The first start downloads Python and the libraries; later starts take a few seconds. The player opens in its own window; closing the window quits it. To start it again later, run only the last two lines (the `cd` and `uv run`) in a new PowerShell. If `uv` is not found there, run `winget install --id=astral-sh.uv -e` once. To update, repeat the block after deleting the old folder (keep its `data` folder: copy it into the new one), or use [Git for Windows](https://git-scm.com/download/win) and `git clone https://github.com/lsspkk/downtempo.git` instead of step 2, then `git pull` to update.

The window uses Microsoft Edge WebView2, which Windows 10 and 11 already have; if the window stays empty, install the *Evergreen WebView2 Runtime* from Microsoft. Your songs, settings and sign-in stay in the `data` folder inside Downtempo's folder.

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

MIT, see [LICENSE](LICENSE). Song material is not included: it stays local in `data/` (git-ignored).
