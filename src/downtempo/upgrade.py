"""Moving a project from the folder-per-song catalog (before song grouping) to the sorting, once:
each old song becomes a song with its files placed, `extra_folders` goes away, and the player's
remembered tempo and loops follow their songs to the new ids. Runs where `migrate` runs
(`Workspace.__init__`), per project; `songs.json.before-grouping` is kept.

Plan: docs/song-grouping.md."""

import json
import shutil
import tomllib
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath

from downtempo.catalog import file_id, read_catalog
from downtempo.jsonfile import write_json
from downtempo.library import Library
from downtempo.memory_file import write_memory
from downtempo.shapes import Memory, Placement, SongMemory
from downtempo.sources import free_id, load, save


def upgrade_project(root: Path) -> None:
    songs_file, grouping_file = root / "songs.json", root / "grouping.json"
    if songs_file.exists() and not grouping_file.exists():
        old = read_catalog(songs_file)
        if old and any("id" not in song for song in old):
            memory, ids = memory_from_old(old, extra_patterns(root / "project.toml"))
            shutil.copyfile(songs_file, root / "songs.json.before-grouping")
            write_memory(grouping_file, memory, {})
            move_practice_keys(root / "practice.json", ids)
            Library(root).rebuild()
    drop_extra_folders(root / "project.toml")


def extra_patterns(project_file: Path) -> dict[str, list[str]]:
    """Each source's old `extra_folders` patterns (the folders that were not songs)."""
    try:
        entries = tomllib.loads(project_file.read_text(encoding="utf-8")).get(
            "source", []
        )
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return {str(e.get("name")): list(e.get("extra_folders", [])) for e in entries}


def extra_folder(path: str, patterns: dict[str, list[str]]) -> str | None:
    """Name of the outermost folder of a catalog path that matched an extra pattern, any case."""
    source, _, rest = path.removeprefix("downloads/").partition("/")
    for name in PurePosixPath(rest).parts[:-1]:
        if any(
            fnmatch(name.casefold(), p.casefold()) for p in patterns.get(source, [])
        ):
            return name
    return None


def memory_from_old(
    old: list[dict], patterns: dict[str, list[str]]
) -> tuple[Memory, dict[str, str]]:
    """The sorting that gives the old songs again, and old practice key → song id. A song only
    named after an extra folder (its files matched no song) isn't made: its files go to To sort."""
    songs: dict[str, SongMemory] = {}
    files: dict[str, Placement] = {}
    ids: dict[str, str] = {}
    for song in old:
        title = song["title"]
        labels = {a["path"]: a["label"] for a in song.get("audio", [])}
        paths = [*labels, *song.get("pdf", [])]
        in_extra = {p for p in paths if extra_folder(p, patterns)}
        own = [p for p in paths if p not in in_extra]
        if not own and {extra_folder(p, patterns) for p in paths} == {title}:
            continue
        id = free_id(title, set(songs), "song")
        folder = ""
        if own:
            source, _, rest = own[0].removeprefix("downloads/").partition("/")
            parent = str(PurePosixPath(rest).parent)
            folder = f"{source}:{parent}" if parent != "." else ""
        songs[id] = SongMemory(id, title, (), (folder,) if folder else ())
        for path in paths:
            label = labels.get(path, "")
            custom = label if path in own and label != PurePosixPath(path).stem else ""
            files[file_id(path)] = Placement((id,), "auto", custom)
        ids[f"{song.get('collection', '')}/{title}"] = id
    return Memory(songs, files), ids


def move_practice_keys(path: Path, ids: dict[str, str]) -> None:
    """`songs["<collection>/<title>"]` and `last_song` follow the song to its id."""
    try:
        practice = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    practice["songs"] = {ids.get(k, k): v for k, v in practice.get("songs", {}).items()}
    if "last_song" in practice:
        practice["last_song"] = ids.get(practice["last_song"], practice["last_song"])
    write_json(path, practice)


def drop_extra_folders(project_file: Path) -> None:
    if not project_file.exists() or "extra_folders" not in project_file.read_text(
        encoding="utf-8"
    ):
        return
    doc = load(project_file)
    for table in doc.get("source", []):
        table.pop("extra_folders", None)
    save(project_file, doc)
