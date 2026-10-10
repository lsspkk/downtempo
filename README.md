# Downtempo

Practice songs at a slower tempo.

- Now: a Python downloader for song files (mp3, wav, pdf) in a shared OneDrive folder.
- Now: a song catalog (`data/songs.json`) and a Python player: tempo 50–130 % with pitch kept, A–B loops, sheet music ([docs/player.md](docs/player.md)).
- Next: a browser player to compare with, Google Drive downloads.


Needs [uv](https://docs.astral.sh/uv/).


# OneDrive Downloader

```sh
cp .env.example .env                            # set ONEDRIVE_CLIENT_ID, see docs/onedrive.md
cp data/sources.example.toml data/sources.toml  # add the shared folder link
uv run downtempo download
```

# Player

```sh
uv run downtempo catalog                  # scan data/downloads/ into data/songs.json, see docs/songs.md
uv run python frontends/nicegui/app.py    # opens the player in its own window
```

Features, keyboard shortcuts and `--browser` mode: [docs/player.md](docs/player.md).

The window is a webview ([pywebview](https://pywebview.flowrl.com/)): Qt on Linux (installed by uv, no system packages needed), Edge WebView2 on Windows. Closing the window quits the player.



# License

MIT, see [LICENSE](LICENSE). Song material is not included: it stays local in `data/` (git-ignored).
