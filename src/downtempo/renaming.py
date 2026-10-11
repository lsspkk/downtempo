"""A source's new name everywhere that keys by it: `project.toml` and its `downloads/<name>/`
folder, the sorting's file ids and folder links (`grouping.json`), the new marks, the last checks,
and the practice memory's file paths (`downloads/<name>/…`: the chosen recording and sheet, a
recording's position and loops). The Library calls it; a player with the practice memory open
must save it before and load it again after."""

import json
from typing import TYPE_CHECKING, Any

from downtempo.bundle_grouping import rename_sources
from downtempo.jsonfile import write_json
from downtempo.newmarks import read_marks
from downtempo.sources import Source

if TYPE_CHECKING:
    from downtempo.library import Library


def rename(library: "Library", old: Source, new: Source) -> None:
    # checks the name, moves the downloads folder and the last checks
    library.replace_source(old.name, new)
    renames = {old.name: new.name}
    sorting = library.sorting
    sorting.save(rename_sources(sorting.read(), renames))
    sorting.undo_stack, sorting.redo_stack, sorting.offers = [], [], []
    marks = read_marks(library.new_file)
    if marks:
        write_json(library.new_file, {moved(k, renames): v for k, v in marks.items()})
    try:
        practice = json.loads(library.practice_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        practice = None
    if isinstance(practice, dict):
        write_json(library.practice_file, rename_practice(practice, old.name, new.name))
    library.rebuild()


def moved(file_id: str, renames: dict[str, str]) -> str:
    source, colon, path = file_id.partition(":")
    return f"{renames.get(source, source)}{colon}{path}"


def rename_practice(practice: dict[str, Any], old: str, new: str) -> dict[str, Any]:
    """Catalog paths `downloads/<old>/…` → `downloads/<new>/…` in `songs` values and the keys of
    `recordings`."""
    before, after = f"downloads/{old}/", f"downloads/{new}/"

    def path(value: Any) -> Any:
        if isinstance(value, str) and value.startswith(before):
            return after + value.removeprefix(before)
        return value

    songs = {
        id: {k: path(v) for k, v in song.items()} if isinstance(song, dict) else song
        for id, song in practice.get("songs", {}).items()
    }
    recordings = {path(k): v for k, v in practice.get("recordings", {}).items()}
    return practice | {"songs": songs, "recordings": recordings}
