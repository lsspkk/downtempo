"""The sorting inside a settings file: checking it (it comes from someone else), renaming its source
prefixes when a source got another name, and merging it into a project that already has a sorting.

Rules: docs/settings-file.md ("Import rules"). The importer's own decisions win wherever both
decided. Pure: no disk."""

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, replace

from downtempo.shapes import Memory, Placement, SongMemory
from downtempo.sources import free_id

MAX_SONGS = 5000
MAX_FILES = 50000
MAX_TEXT = 120
MAX_PATH = 500
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
KNOWN = ("songs", "files", "first", "words")


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def check_text(text: object, limit: int = MAX_TEXT) -> str | None:
    return (
        text.strip()
        if isinstance(text, str)
        and text.strip()
        and text.isprintable()
        and len(text) <= limit
        else None
    )


def check_key(key: str, sources: set[str]) -> str | None:
    """Why `source:path` can't be a file or folder of this file's sources; None when it can."""
    source, colon, path = key.partition(":")
    if not colon or source not in sources:
        return "not in a source of this file"
    parts = path.split("/")
    if (
        len(path) > MAX_PATH
        or any(p in ("", ".", "..") for p in parts)
        or not path.isprintable()
    ):
        return "not a path inside the source"
    return None


def check_grouping(
    raw: object, sources: set[str]
) -> tuple[Memory, list[str], list[str]]:
    """The memory in a file's `[grouping]`, what was dropped and why, and unknown keys. A bad entry
    is dropped with a line, never guessed; a table that isn't one gives an empty memory."""
    dropped: list[str] = []
    if not isinstance(raw, dict):
        return Memory(), ["grouping: it isn't a table"], []
    ignored = [f"grouping: {k}" for k in raw if k not in KNOWN]
    songs_raw, files_raw = raw.get("songs", {}), raw.get("files", {})
    if not isinstance(songs_raw, dict) or not isinstance(files_raw, dict):
        return Memory(), ["grouping: songs and files must be tables"], ignored
    if len(songs_raw) > MAX_SONGS or len(files_raw) > MAX_FILES:
        return Memory(), ["grouping: too many songs or files"], ignored

    songs: dict[str, SongMemory] = {}
    for id, entry in songs_raw.items():
        title = check_text(entry.get("title")) if isinstance(entry, dict) else None
        if not SLUG.fullmatch(str(id)) or len(str(id)) > 80 or not title:
            dropped.append(f"song '{str(id)[:40]}': not a valid id and title")
            continue
        also = [a for a in map(check_text, as_list(entry.get("also"))) if a]
        folders = []
        for folder in as_list(entry.get("folders")):
            why = check_key(folder, sources) if isinstance(folder, str) else "not text"
            if why:
                dropped.append(f"song '{title}': folder '{str(folder)[:60]}' {why}")
            else:
                folders.append(folder)
        songs[id] = SongMemory(id, title, tuple(dict.fromkeys(also)), tuple(folders))

    files: dict[str, Placement] = {}
    for key, entry in files_raw.items():
        why = check_key(key, sources)
        if (
            why
            or not isinstance(entry, dict)
            or entry.get("by") not in ("auto", "hand")
        ):
            dropped.append(f"file '{key[:60]}': {why or 'not a valid placement'}")
            continue
        wanted = [s for s in as_list(entry.get("songs")) if isinstance(s, str)]
        known = tuple(dict.fromkeys(s for s in wanted if s in songs))
        for unknown in sorted({s for s in wanted if s not in songs}):
            dropped.append(
                f"file '{key[:60]}': song '{unknown[:40]}' isn't in the file"
            )
        if wanted and not known:
            continue
        label = check_text(entry.get("label", "")) or ""
        files[key] = Placement(known, entry["by"], label, entry.get("to_sort") is True)

    first = {}
    for id, keys in as_dict(raw.get("first")).items():
        if id in songs:
            first[id] = tuple(
                k for k in as_list(keys) if isinstance(k, str) and k in files
            )

    words = as_dict(raw.get("words"))
    add, keep = (
        tuple(w for w in map(check_text, as_list(words.get(name))[:100]) if w)
        for name in ("add", "keep")
    )
    return Memory(songs, files, first, add, keep), dropped, ignored


def rename_sources(memory: Memory, renames: dict[str, str]) -> Memory:
    """Source names that changed on import (`band` → `band 2`), in file keys and folder links."""

    def renamed(key: str) -> str:
        source, colon, path = key.partition(":")
        return f"{renames.get(source, source)}{colon}{path}"

    if not renames:
        return memory
    return rekeyed(memory, renamed, renamed)


def rename_files(memory: Memory, ids: dict[str, str]) -> Memory:
    """Files stored under a new name (a wav kept as mp3): old file id → new, in file keys."""
    if not ids:
        return memory
    return rekeyed(memory, lambda key: ids.get(key, key), lambda key: key)


def rekeyed(
    memory: Memory, file: Callable[[str], str], folder: Callable[[str], str]
) -> Memory:
    return Memory(
        {
            id: replace(s, folders=tuple(map(folder, s.folders)))
            for id, s in memory.songs.items()
        },
        {file(k): p for k, p in memory.files.items()},
        {id: tuple(map(file, keys)) for id, keys in memory.first.items()},
        memory.words_add,
        memory.words_keep,
    )


@dataclass(frozen=True)
class Merged:
    memory: Memory
    songs_added: int
    files_added: int
    differing: int  # songs of ours that the file decided differently
    kept: tuple[str, ...]  # what stayed ours, for the preview


def folded(items: tuple[str, ...]) -> set[str]:
    return {unicodedata.normalize("NFC", x).casefold() for x in items}


def same_names(a: SongMemory, b: SongMemory) -> bool:
    return (
        a.title.casefold() == b.title.casefold()
        and folded(a.also) == folded(b.also)
        and folded(a.folders) == folded(b.folders)
    )


def merge(ours: Memory, theirs: Memory) -> Merged:
    """`theirs` added to `ours`: a song of the same id or title (any case) is ours with ours kept;
    new songs and files with no place here are added."""
    by_title = {s.title.casefold(): id for id, s in ours.songs.items()}
    songs = dict(ours.songs)
    mapping: dict[str, str] = {}
    new_ids: set[str] = set()
    differ: set[str] = set()
    kept: list[str] = []
    for id, song in sorted(theirs.songs.items()):
        match = id if id in ours.songs else by_title.get(song.title.casefold())
        if match:
            mapping[id] = match
            if not same_names(ours.songs[match], song):
                differ.add(match)
                kept.append(
                    f"“{ours.songs[match].title}”: kept your title, names and folders"
                )
            continue
        new = id if id not in songs else free_id(song.title, set(songs), "song")
        songs[new] = replace(song, id=new)
        mapping[id] = new
        new_ids.add(new)
    files = dict(ours.files)
    added = 0
    for key, placement in theirs.files.items():
        mapped = tuple(dict.fromkeys(mapping[s] for s in placement.songs))
        if key in files:
            if set(files[key].songs) != set(mapped):
                differ |= set(files[key].songs)
                kept.append(f"{key}: kept where you put it")
            continue
        files[key] = replace(placement, songs=mapped)
        added += 1
    first = dict(ours.first)
    for id, keys in theirs.first.items():
        if mapping.get(id) in new_ids:
            first[mapping[id]] = keys
    memory = Memory(
        songs,
        files,
        first,
        tuple(dict.fromkeys((*ours.words_add, *theirs.words_add))),
        tuple(dict.fromkeys((*ours.words_keep, *theirs.words_keep))),
    )
    return Merged(memory, len(new_ids), added, len(differ), tuple(kept))
