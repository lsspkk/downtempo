"""`new.json`: files that joined a song since the user last looked (this computer's, not exported).
`{file id: date}`. Written by the Library only; the player reads it through the Library."""

import json
from collections.abc import Iterable
from datetime import date
from pathlib import Path

from downtempo.jsonfile import write_json


def read_marks(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return (
        {k: v for k, v in data.items() if isinstance(v, str)}
        if isinstance(data, dict)
        else {}
    )


def add_marks(path: Path, ids: Iterable[str]) -> None:
    marks = read_marks(path)
    today = date.today().isoformat()
    marks |= {id: marks.get(id, today) for id in ids}
    write_json(path, marks)


def clear_marks(path: Path, ids: Iterable[str]) -> None:
    marks = read_marks(path)
    left = {k: v for k, v in marks.items() if k not in set(ids)}
    if left != marks:
        write_json(path, left)


def keep_marks(path: Path, existing: set[str]) -> None:
    """Forget marks of files that are no longer there."""
    marks = read_marks(path)
    left = {k: v for k, v in marks.items() if k in existing}
    if left != marks:
        write_json(path, left)
