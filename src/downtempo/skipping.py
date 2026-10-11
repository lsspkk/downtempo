"""Skipped folders: folders of a source that are not downloaded (the list is the source's `skip` in
`project.toml`), and giving back the space their old downloads use. Plan: docs/song-grouping.md."""

import unicodedata
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from downtempo.config import MEDIA_EXTENSIONS
from downtempo.errors import UserError
from downtempo.sources import is_skipped

if TYPE_CHECKING:
    from downtempo.library import Library

MAX_FOLDER = 500


def check_folder(folder: str) -> str:
    """A folder path inside a source, trimmed: `a/b`."""
    folder = unicodedata.normalize("NFC", folder.strip().strip("/"))
    parts = folder.split("/") if folder else []
    if (
        not parts
        or len(folder) > MAX_FOLDER
        or any(p in ("", ".", "..") or not p.isprintable() or "\\" in p for p in parts)
    ):
        raise UserError(f"'{folder[:80]}' isn't a folder path inside the source.")
    return folder


def skip_folder(library: "Library", source: str, folder: str) -> None:
    """From now on the folder isn't downloaded; files already here stay until `free_space`."""
    found = library.source(source)
    folder = check_folder(folder)
    if folder.casefold() not in {s.casefold() for s in found.skip}:
        library.replace_source(found.name, replace(found, skip=(*found.skip, folder)))


def unskip_folder(library: "Library", source: str, folder: str) -> None:
    found = library.source(source)
    kept = tuple(s for s in found.skip if s.casefold() != folder.strip("/").casefold())
    library.replace_source(found.name, replace(found, skip=kept))


def skipped_files(library: "Library", source: str) -> list[Path]:
    """Downloaded media files of the source that lie in skipped folders."""
    found = library.source(source)
    target = library.target(found)
    if not found.skip or not target.is_dir():
        return []
    return sorted(
        p
        for p in target.rglob("*")
        if p.is_file()
        and p.suffix.lower() in MEDIA_EXTENSIONS
        and is_skipped(p.relative_to(target).parts, found.skip)
    )


def skipped_size(library: "Library", source: str) -> int:
    return sum(p.stat().st_size for p in skipped_files(library, source))


def free_space(library: "Library", source: str) -> int:
    """Delete exactly the files `skipped_files` lists (ask the user first); returns the bytes
    freed. Folders left empty go too."""
    target = library.target(library.source(source)).resolve()
    freed = 0
    folders: set[Path] = set()
    for path in skipped_files(library, source):
        if not path.resolve().is_relative_to(target):
            continue
        freed += path.stat().st_size
        path.unlink()
        folders.add(path.parent)
    for folder in sorted(folders, key=lambda p: len(p.parts), reverse=True):
        while folder != target and folder.is_relative_to(target):
            try:
                folder.rmdir()
            except OSError:
                break
            folder = folder.parent
    return freed
