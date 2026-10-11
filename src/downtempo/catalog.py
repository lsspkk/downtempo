"""`songs.json`: what the players read, derived from the files and the sorting; format in
`docs/songs.md`. Paths in it are relative to the project folder (`downloads/<source>/…`).

Which songs there are and what is in them is decided by `grouping`; this module lists the files
that go in and writes the result down."""

import json
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from downtempo.config import AUDIO_EXTENSIONS, MEDIA_EXTENSIONS
from downtempo.jsonfile import write_json
from downtempo.shapes import FileRef, Grouping
from downtempo.sources import is_skipped

type Song = dict[str, Any]


def list_files(
    downloads: Path, skip: dict[str, tuple[str, ...]] | None = None
) -> list[FileRef]:
    """Every audio and sheet file under `downloads/<source>/`, except in skipped folders; the
    input of `grouping.group`. Sorted, so the same disk gives the same list."""
    found = []
    skip = skip or {}
    folders = (
        sorted(p for p in downloads.iterdir() if p.is_dir())
        if downloads.exists()
        else []
    )
    for folder in folders:
        for path in sorted(folder.rglob("*")):
            relative = path.relative_to(folder)
            if (
                not path.is_file()
                or path.suffix.lower() not in MEDIA_EXTENSIONS
                or is_skipped(relative.parts, skip.get(folder.name, ()))
            ):
                continue
            stat = path.stat()
            found.append(
                FileRef(
                    folder.name,
                    PurePosixPath(relative.as_posix()),
                    "audio" if path.suffix.lower() in AUDIO_EXTENSIONS else "sheet",
                    stat.st_size,
                    datetime.fromtimestamp(stat.st_mtime),
                )
            )
    return found


def catalog_path(file: FileRef) -> str:
    return f"downloads/{file.source}/{file.path}"


def file_id(path: str) -> str:
    """The file id (`source:path`) of a catalog path."""
    source, _, rest = path.removeprefix("downloads/").partition("/")
    return f"{source}:{rest}"


def build_catalog(result: Grouping) -> list[Song]:
    """The songs that have a file, as the players read them: recordings in display order (the
    default first), sheets newest first with older versions after."""
    songs = []
    for song in result.songs:
        audio = [{"label": m.label, "path": catalog_path(m.file)} for m in song.audio]
        pdf = [catalog_path(f) for m in song.sheets for f in (m.file, *m.older)]
        if audio or pdf:
            songs.append(
                {"id": song.id, "title": song.title, "audio": audio, "pdf": pdf}
            )
    return songs


def song_paths(song: Song) -> set[str]:
    return {audio["path"] for audio in song.get("audio", [])} | set(song.get("pdf", []))


def read_catalog(path: Path) -> list[Song]:
    """The songs in a `songs.json`, or none when it does not exist yet."""
    return (
        json.loads(path.read_text(encoding="utf-8"))["songs"] if path.exists() else []
    )


def write_catalog(path: Path, songs: list[Song]) -> None:
    write_json(path, {"songs": songs})
