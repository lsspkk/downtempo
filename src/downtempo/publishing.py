"""Making `songs.json` from the sorting, keeping the "new" marks, and previewing a listing.

`rebuild` is what runs after a download and by `downtempo catalog`; `publish` writes a grouping
that is already made (after every sorting operation). The Library calls these."""

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from downtempo.catalog import (
    Song,
    build_catalog,
    file_id,
    read_catalog,
    song_paths,
    write_catalog,
)
from downtempo.config import MEDIA_EXTENSIONS
from downtempo.downloaders.remote import RemoteFile
from downtempo.grouping import group
from downtempo.newmarks import add_marks, clear_marks, keep_marks, read_marks
from downtempo.shapes import FileRef, Grouping
from downtempo.sources import is_skipped

if TYPE_CHECKING:
    from downtempo.library import Library


@dataclass(frozen=True)
class CatalogDiff:
    """What a rebuild changed, for "5 new files: 4 joined songs, 1 to sort"."""

    songs: int
    new_songs: list[str]
    gone_songs: list[str]
    joined: dict[str, int]  # song title → files that joined it in this run
    to_sort: int  # files in To sort now (suggested songs and loose files)

    def news(self) -> str:
        """`4 joined songs, 1 to sort`: files that joined a song now, files waiting in To sort."""
        joined = sum(self.joined.values())
        parts = [
            f"{len(self.new_songs)} new song{'s' * (len(self.new_songs) != 1)}"
            if self.new_songs
            else "",
            f"{joined} joined songs" if joined else "",
            f"{self.to_sort} unknown" if self.to_sort else "",
        ]
        return ", ".join(p for p in parts if p)


def publish(library: "Library", result: Grouping) -> list[Song]:
    songs = build_catalog(result)
    write_catalog(library.songs_file, songs)
    return songs


def rebuild(library: "Library", mark_new: bool = False) -> CatalogDiff:
    """Group the files again, save the matches that were made, write `songs.json`. With
    `mark_new` the files that joined a song now get a "new" mark. Files with no song wait in To
    sort (the project screen's Unknown files, or `downtempo songs --create`)."""
    sorting = library.sorting
    old = read_catalog(library.songs_file)
    files = library.files()
    _, result = sorting.settle(sorting.read(), files)
    songs = publish(library, result)
    if mark_new and result.joined:
        add_marks(library.new_file, result.joined)
    keep_marks(library.new_file, {f.id for f in files})
    titles = {s.id: s.title for s in result.songs}
    old_titles = {s["title"] for s in old}
    new_titles = {s["title"] for s in songs}
    return CatalogDiff(
        len(songs),
        sorted(new_titles - old_titles),
        sorted(old_titles - new_titles),
        dict(Counter(titles[song] for song in result.joined.values())),
        sum(len(s.files) for s in result.suggestions) + len(result.loose),
    )


def preview(library: "Library", listing: dict[str, list[RemoteFile]]) -> Grouping:
    """How a remote listing (source name → files) would be sorted now: for "about 12 songs from 31
    files" before anything is downloaded. Changes nothing."""
    skip = {s.name: s.skip for s in library.sources()}
    refs = [
        FileRef.from_id(f"{source}:{file.path}", file.size, file.modified)
        for source, files in listing.items()
        for file in files
        if file.path.suffix.lower() in MEDIA_EXTENSIONS
        and not is_skipped(file.path.parts, skip.get(source, ()))
    ]
    memory = library.sorting.read()
    return group(refs, memory, library.sorting.words(memory))


def songs_with_new(library: "Library") -> set[str]:
    """Ids of the songs that have a file with a "new" mark."""
    marks = read_marks(library.new_file)
    return {
        song["id"]
        for song in library.songs()
        if any(file_id(path) in marks for path in song_paths(song))
    }


def mark_seen(library: "Library", song_id: str) -> None:
    """The user opened the song: its files are no longer new."""
    for song in library.songs():
        if song.get("id") == song_id:
            clear_marks(library.new_file, [file_id(p) for p in song_paths(song)])
