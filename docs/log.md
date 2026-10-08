# Log

Finished tasks, newest first. `- YYYY-MM-DD T<n> (I<n>) what was done: note`

- 2026-10-08 T22 (I7) Commit safety check: no song/source names, share IDs or secrets in tracked files; `license = "MIT"` in pyproject, License section in README
- 2026-10-08 T21 (I7) README simplified: what it does now (OneDrive downloader) and next (Python player), three-line Use
- 2026-10-08 T20 (I7) CLAUDE.md shortened to 31 lines; details left to docs/architecture.md and data/README.md
- 2026-10-08 T19 (I7) Restructure: all local material in `data/` (downloads, sources, catalog, notes, scratch, OneDrive token); `docs/architecture.md` + `data/README.md`; CLAUDE.md principle: direct requests are done now
- 2026-10-08 T18 (I7) Docs: README, docs/README, `authentication.md` → `onedrive.md`, stale paths fixed
- 2026-10-08 T16 (I7) `download.py` → package `src/downtempo` with `uv run downtempo download [name]`; OneDrive in `downloaders/onedrive.py`, registry `DOWNLOADERS`; smoke run skipped all 19 existing files
- 2026-10-08 T15 (I7) `data/sources.toml` (+ tracked example) replaces `ONEDRIVE_SHARE_URL`/`ONEDRIVE_SUBFOLDER`/`DOWNLOADS_DIR`; `.env` = credentials only
- 2026-10-08 T3 (I1) dropped: superseded by I7 (`sources.toml` replaces `ONEDRIVE_SUBFOLDER`)
- 2026-10-08 T5 (I3) Python time-stretch research → `docs/tempo-python.md`: pick pylibrb (Rubber Band realtime) + sounddevice + soundfile; fallback pedalboard offline
- 2026-10-08 T2 (I1) Download only one top-level folder (`ONEDRIVE_SUBFOLDER`): 28 files, 65 MB
- 2026-10-08 T1 (I1) Switch auth to Entra app + MSAL device code + Graph; token cached in `.token_cache.json`
