"""`grouping.json`: the user's sorting of a project (songs, where each file is, the default order),
read into a `Memory` and written back. Keys this version doesn't know are kept, so a newer
version's file survives a save. Format: docs/song-grouping.md ("Memory")."""

import json
from pathlib import Path
from typing import Any

from downtempo.errors import UserError
from downtempo.jsonfile import write_json
from downtempo.shapes import Memory, Placement, SongMemory

HINT = "Fix the file, or move it away to start the sorting over."


def read_memory(path: Path) -> tuple[Memory, dict[str, Any]]:
    """The memory in `path` and its raw JSON (for `write_memory`); empty when there's no file."""
    if not path.exists():
        return Memory(), {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise TypeError("it isn't a JSON object")
        return parse(raw), raw
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise UserError(f"{path.name} can't be read: {error}", HINT) from error


def parse(raw: dict[str, Any]) -> Memory:
    songs = {
        id: SongMemory(
            id,
            str(entry["title"]),
            tuple(map(str, entry.get("also", ()))),
            tuple(map(str, entry.get("folders", ()))),
        )
        for id, entry in raw.get("songs", {}).items()
    }
    files = {}
    for id, entry in raw.get("files", {}).items():
        by = entry.get("by", "hand")
        if by not in ("auto", "hand"):
            raise ValueError(f"'{id}' has by = {by!r}")
        files[id] = Placement(
            tuple(map(str, entry.get("songs", ()))),
            by,
            str(entry.get("label", "")),
            bool(entry.get("to_sort", False)),
        )
    words = raw.get("words", {})
    return Memory(
        songs,
        files,
        {id: tuple(map(str, ids)) for id, ids in raw.get("first", {}).items()},
        tuple(map(str, words.get("add", ()))),
        tuple(map(str, words.get("keep", ()))),
    )


def write_memory(path: Path, memory: Memory, raw: dict[str, Any]) -> dict[str, Any]:
    """Save `memory` through a temporary file; returns the JSON written (the next `raw`)."""
    data = to_dict(memory, raw)
    write_json(path, data)
    return data


def to_dict(memory: Memory, raw: dict[str, Any]) -> dict[str, Any]:
    """`memory` as the JSON of `grouping.json`, laid over `raw` (so unknown keys stay)."""
    old_songs, old_files = raw.get("songs", {}), raw.get("files", {})
    data = dict(raw)
    data["songs"] = {
        id: merged(
            old_songs.get(id),
            {"title": s.title, "also": list(s.also), "folders": list(s.folders)},
        )
        for id, s in memory.songs.items()
    }
    data["files"] = {
        id: merged(
            old_files.get(id),
            {
                "songs": list(p.songs),
                "by": p.by,
                "label": p.label,
                "to_sort": p.to_sort,
            },
            optional=("label", "to_sort"),
        )
        for id, p in memory.files.items()
    }
    data["first"] = {id: list(ids) for id, ids in memory.first.items() if ids}
    data["words"] = merged(
        raw.get("words"),
        {"add": list(memory.words_add), "keep": list(memory.words_keep)},
    )
    return data


def merged(
    old: object, known: dict[str, Any], optional: tuple[str, ...] = ()
) -> dict[str, Any]:
    """`known` laid over the old entry, whose unknown keys stay; an empty optional key is left out."""
    out = dict(old) if isinstance(old, dict) else {}
    for key, value in known.items():
        if key in optional and not value:
            out.pop(key, None)
        else:
            out[key] = value
    return out
