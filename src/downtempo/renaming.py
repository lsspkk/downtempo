"""New names everywhere that keys by them: a source's (`rename`: `project.toml` and its
`downloads/<name>/` folder, the last checks) and a file's (`move_files`: a wav kept as mp3,
docs/compress.md). Both reach the sorting's file ids (`grouping.json`), the new marks and the
practice memory's file paths (`downloads/<name>/…`: the chosen recording and sheet, a recording's
position and loops). The Library calls these; a player with the practice memory open must save
it before a rename and load it again after, and apply `move_practice` to it after a download."""

import json
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from downtempo.bundle_grouping import rename_files, rename_sources
from downtempo.catalog import file_id
from downtempo.jsonfile import write_json
from downtempo.newmarks import read_marks
from downtempo.sources import Source

if TYPE_CHECKING:
    from downtempo.library import Library


def rename(library: "Library", old: Source, new: Source) -> None:
    # checks the name, moves the downloads folder and the last checks
    library.replace_source(old.name, new)
    renames = {old.name: new.name}
    library.sorting.save(rename_sources(library.sorting.read(), renames))
    before, after = f"downloads/{old.name}/", f"downloads/{new.name}/"
    rename_keys(
        library,
        lambda id: moved(id, renames),
        lambda path: (
            after + path.removeprefix(before) if path.startswith(before) else path
        ),
    )
    library.rebuild()


def move_files(library: "Library", moves: dict[str, str]) -> None:
    """Files now stored under another name: catalog path (`downloads/<source>/…`) → new one."""
    if not moves:
        return
    ids = {file_id(old): file_id(new) for old, new in moves.items()}
    library.sorting.save(rename_files(library.sorting.read(), ids))
    rename_keys(library, lambda id: ids.get(id, id), lambda path: moves.get(path, path))


def rename_keys(
    library: "Library", id: Callable[[str], str], path: Callable[[str], str]
) -> None:
    """The new marks' file ids and the practice memory's paths (the sorting is the caller's)."""
    sorting = library.sorting
    sorting.undo_stack, sorting.redo_stack, sorting.offers = [], [], []
    marks = read_marks(library.new_file)
    if marks:
        write_json(library.new_file, {id(k): v for k, v in marks.items()})
    try:
        practice = json.loads(library.practice_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        practice = None
    if isinstance(practice, dict):
        write_json(library.practice_file, rename_practice(practice, path))


def moved(file_id: str, renames: dict[str, str]) -> str:
    source, colon, path = file_id.partition(":")
    return f"{renames.get(source, source)}{colon}{path}"


def move_practice(practice: dict[str, Any], moves: dict[str, str]) -> dict[str, Any]:
    """The practice memory (or the player's state holding it) after `move_files`."""
    return rename_practice(practice, lambda path: moves.get(path, path))


def rename_practice(
    practice: dict[str, Any], renamed: Callable[[str], str]
) -> dict[str, Any]:
    """Catalog paths in `songs` values and the keys of `recordings`."""

    def path(value: Any) -> Any:
        return renamed(value) if isinstance(value, str) else value

    songs = {
        id: {k: path(v) for k, v in song.items()} if isinstance(song, dict) else song
        for id, song in practice.get("songs", {}).items()
    }
    recordings = {path(k): v for k, v in practice.get("recordings", {}).items()}
    return practice | {"songs": songs, "recordings": recordings}
