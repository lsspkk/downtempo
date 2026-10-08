# Downtempo

Practice songs at a slower tempo.

- Now: a Python downloader for song files (mp3, pdf) in a shared OneDrive folder.
- Planned: a Python user interface that plays the songs slower, with pitch kept.


Needs [uv](https://docs.astral.sh/uv/).


# OneDrive Downloader

```sh
cp .env.example .env                            # set ONEDRIVE_CLIENT_ID, see docs/onedrive.md
cp data/sources.example.toml data/sources.toml  # add the shared folder link
uv run downtempo download
```



# License

MIT, see [LICENSE](LICENSE). Song material is not included: it stays local in `data/` (git-ignored).
