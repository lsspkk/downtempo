"""Build `data/songs.json` from `data/downloads/<collection>/`; format in `docs/songs.md`."""

import json
from collections.abc import Sequence
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from downtempo.config import (
    AUDIO_EXTENSIONS,
    DATA_DIR,
    DOWNLOADS_DIR,
    PROJECT_DIR,
    SHEET_EXTENSIONS,
    SONGS_FILE,
    SOURCES_FILE,
    load_sources,
)

type Song = dict[str, Any]


def scan_collection(collection: Path, extra_folders: Sequence[str] = ()) -> list[Song]:
    """One song per folder that holds audio/pdf files directly, nested folders included.

    Folders whose name matches a pattern in `extra_folders` (e.g. `Rehearsal *`) are not songs:
    each of their files is linked to the song whose title its name starts with.
    """
    songs: list[Song] = []
    extras: list[tuple[Path, Path]] = []  # (extra folder, file)
    for folder in sorted(
        [collection, *(p for p in collection.rglob("*") if p.is_dir())]
    ):
        files = sorted(p for p in folder.iterdir() if p.is_file())
        audios = [p for p in files if p.suffix.lower() in AUDIO_EXTENSIONS]
        pdfs = [p for p in files if p.suffix.lower() in SHEET_EXTENSIONS]
        if not audios and not pdfs:
            continue
        if extra := extra_folder(collection, folder, extra_folders):
            extras += [(extra, p) for p in audios + pdfs]
            continue
        songs.append(
            {
                "title": folder.name,
                "collection": collection.name,
                "audio": [{"label": p.stem, "path": data_path(p)} for p in audios],
                "pdf": [data_path(p) for p in pdfs],
            }
        )
    unmatched: dict[Path, list[Path]] = {}
    for extra, file in extras:
        if song := song_for(file.stem, songs):
            rest = file.stem[len(song["title"]) :].strip(" -_")
            if file.suffix.lower() in SHEET_EXTENSIONS:
                song["pdf"].append(data_path(file))
            else:
                label = f"{extra.name} · {rest}" if rest else extra.name
                song["audio"].append({"label": label, "path": data_path(file)})
        else:
            unmatched.setdefault(extra, []).append(file)
    for (
        extra,
        files,
    ) in unmatched.items():  # nothing gets lost: a song named after the folder
        songs.append(
            {
                "title": extra.name,
                "collection": collection.name,
                "audio": [
                    {"label": p.stem, "path": data_path(p)}
                    for p in files
                    if p.suffix.lower() in AUDIO_EXTENSIONS
                ],
                "pdf": [
                    data_path(p) for p in files if p.suffix.lower() in SHEET_EXTENSIONS
                ],
            }
        )
    return songs


def extra_folder(
    collection: Path, folder: Path, patterns: Sequence[str]
) -> Path | None:
    """The folder itself or the outermost folder above it that matches a pattern (any case)."""
    if folder == collection:
        return None
    parts = folder.relative_to(collection).parts
    for depth in range(1, len(parts) + 1):
        name = parts[depth - 1].casefold()
        if any(fnmatch(name, pattern.casefold()) for pattern in patterns):
            return collection.joinpath(*parts[:depth])
    return None


def song_for(name: str, songs: list[Song]) -> Song | None:
    """The song with the longest title that `name` starts with as whole words, any case."""
    name = name.casefold()
    matches = [
        song
        for song in songs
        if name.startswith(title := song["title"].casefold())
        and not name[len(title) : len(title) + 1].isalnum()
    ]
    return max(matches, key=lambda song: len(song["title"]), default=None)


def data_path(path: Path) -> str:
    return path.relative_to(DATA_DIR).as_posix()


def song_paths(song: Song) -> set[str]:
    return {audio["path"] for audio in song.get("audio", [])} | set(song.get("pdf", []))


def keep_hand_edits(song: Song, old_songs: list[Song]) -> Song:
    """Take title, labels and extra keys from the old entry that shares a file with `song`."""
    old = next((o for o in old_songs if song_paths(o) & song_paths(song)), None)
    if old is None:
        return song
    labels = {audio["path"]: audio["label"] for audio in old.get("audio", [])}
    for audio in song["audio"]:
        audio["label"] = labels.get(audio["path"], audio["label"])
    return old | {**song, "title": old.get("title", song["title"])}


def read_catalog(path: Path = SONGS_FILE) -> list[Song]:
    """The songs in `data/songs.json`, or none when it does not exist yet."""
    return (
        json.loads(path.read_text(encoding="utf-8"))["songs"] if path.exists() else []
    )


def extra_patterns(path: Path = SOURCES_FILE) -> dict[str, Sequence[str]]:
    """`extra_folders` patterns per source name; none without `data/sources.toml`."""
    return (
        {s.name: s.extra_folders for s in load_sources(path)} if path.exists() else {}
    )


def build_catalog(path: Path = SONGS_FILE) -> list[Song]:
    old_songs = read_catalog(path)
    collections = (
        sorted(p for p in DOWNLOADS_DIR.iterdir() if p.is_dir())
        if DOWNLOADS_DIR.exists()
        else []
    )
    extra = extra_patterns()
    songs = [
        keep_hand_edits(song, old_songs)
        for c in collections
        for song in scan_collection(c, extra.get(c.name, ()))
    ]
    songs.sort(key=lambda song: (song["title"].casefold(), song["collection"]))
    path.write_text(
        json.dumps({"songs": songs}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {path.relative_to(PROJECT_DIR)}: {len(songs)} songs from {len(collections)} collections"
    )
    return songs
