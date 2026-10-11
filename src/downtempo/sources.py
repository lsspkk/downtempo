"""The shared folders a library downloads: `Source`, checks on names and links, and reading and
writing them in the project's `project.toml` (comments kept, atomic writes)."""

import os
import tomllib
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import tomlkit

from downtempo.errors import UserError

HEADER = """\
A Downtempo project: its name and the shared folders it downloads. Written by
Downtempo (`downtempo add`, the player); editing by hand is fine.
Files land in downloads/<source name>/.
"""
MAX_NAME = 60


@dataclass(frozen=True)
class Source:
    """One shared folder: its link, and which folder inside it (`folder`, "" = all of it)."""

    name: str  # also the folder name under downloads/
    type: str  # provider type, "onedrive"
    url: str
    folder: str = ""
    # folders (inside the source) that are not downloaded
    skip: tuple[str, ...] = ()


def read_sources(path: Path) -> list[Source]:
    """The sources in `path`; none when the file doesn't exist yet."""
    if not path.exists():
        return []
    try:
        entries = tomllib.loads(path.read_text(encoding="utf-8")).get("source", [])
    except tomllib.TOMLDecodeError as error:
        raise UserError(
            f"{path.name} can't be read: {error}", "Fix the line it names."
        ) from error
    sources = [from_entry(entry, path) for entry in entries]
    names = [s.name.casefold() for s in sources]
    if len(names) != len(set(names)):
        raise UserError(
            f"Two sources in {path.name} have the same name.", "Rename one of them."
        )
    return sources


def from_entry(entry: dict, path: Path) -> Source:
    entry = dict(entry)
    if "subfolder" in entry:  # the name before folder paths of any depth
        entry.setdefault("folder", entry.pop("subfolder"))
    entry.pop("extra_folders", None)  # the name before song grouping
    entry["skip"] = tuple(entry.get("skip", ()))
    try:
        return Source(**entry)
    except TypeError as error:
        raise UserError(
            f"A source in {path.name} has a missing or unknown setting: {error}",
            "Each [[source]] needs name, type and url.",
        ) from error


def add_source(path: Path, source: Source) -> None:
    doc = load(path)
    doc.setdefault("source", tomlkit.aot()).append(to_table(source))
    save(path, doc)


def replace_source(path: Path, name: str, source: Source) -> None:
    doc = load(path)
    tables = doc.get("source", [])
    index = position(tables, name)
    table = tables[index]
    for key, value in to_table(source).items():
        table[key] = value
    for key in (
        "subfolder",
        "folder",
        "extra_folders",
        "skip",
    ):  # optional ones that went away
        if key in table and key not in to_table(source):
            del table[key]
    save(path, doc)


def remove_source(path: Path, name: str) -> None:
    doc = load(path)
    del doc["source"][position(doc.get("source", []), name)]
    save(path, doc)


def position(tables: list, name: str) -> int:
    for index, table in enumerate(tables):
        if str(table.get("name", "")).casefold() == name.casefold():
            return index
    raise UserError(f"There is no source called '{name}'.")


def to_table(source: Source) -> tomlkit.items.Table:
    table = tomlkit.table()
    table["name"] = source.name
    table["type"] = source.type
    table["url"] = source.url
    if source.folder:
        table["folder"] = source.folder
    if source.skip:
        table["skip"] = list(source.skip)
    return table


def load(path: Path) -> tomlkit.TOMLDocument:
    if not path.exists():
        doc = tomlkit.document()
        for line in HEADER.splitlines():
            doc.add(tomlkit.comment(line))
        return doc
    return tomlkit.parse(path.read_text(encoding="utf-8"))


def save(path: Path, doc: tomlkit.TOMLDocument) -> None:
    """Write through a temporary file, so a crash leaves the old file whole."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(tomlkit.dumps(doc), encoding="utf-8")
    os.replace(temporary, path)


def check_url(url: str) -> str:
    """A pasted link, trimmed; raises `UserError` when it can't be a share link."""
    url = url.strip()
    parts = urlparse(url)
    if not url or any(c.isspace() for c in url):
        raise UserError(
            "That isn't a link.", "Copy the shared folder's link and paste it whole."
        )
    if parts.scheme != "https" or not parts.netloc:
        raise UserError(
            "The link must start with https://",
            "Copy the shared folder's link from OneDrive's Share button.",
        )
    if len(url) > 2000:
        raise UserError("The link is too long to be a share link.")
    return url


def check_name(name: str, taken: list[str]) -> str:
    """A source name, trimmed; it becomes a folder name, so it must be one."""
    name = unicodedata.normalize("NFC", name.strip())
    if not name:
        raise UserError("The name is empty.")
    if len(name) > MAX_NAME:
        raise UserError(f"The name is longer than {MAX_NAME} characters.")
    if any(c in '/\\:*?"<>|' or not c.isprintable() for c in name) or name[0] == ".":
        raise UserError(
            f"'{name}' can't be a folder name.",
            "Use letters, numbers, spaces and - or _.",
        )
    if name.casefold() in {t.casefold() for t in taken}:
        raise UserError(
            f"There is already a source called '{name}'.", "Pick another name."
        )
    return name


def name_from(text: str, taken: list[str]) -> str:
    """A free, valid name made from a folder name: `Songs`, then `Songs 2`."""
    base = (
        "".join("-" if c in '/\\:*?"<>|' or not c.isprintable() else c for c in text)
        .strip(" .-")[:MAX_NAME]
        .strip()
        or "Shared folder"
    )
    lowered = {t.casefold() for t in taken}
    name, number = base, 2
    while name.casefold() in lowered:
        name, number = f"{base} {number}", number + 1
    return name


def free_id(name: str, taken: set[str], fallback: str = "project") -> str:
    """A safe id from a name: `My Band!` → `my-band`, then `my-band-2`. Used for project folders
    and song ids."""
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    words = "".join(c if c.isalnum() else " " for c in plain.casefold()).split()
    base = "-".join(words)[:40].strip("-") or fallback
    id, number = base, 2
    while id in taken:
        id, number = f"{base}-{number}", number + 1
    return id


def is_skipped(parts: tuple[str, ...], skip: tuple[str, ...]) -> bool:
    """Whether a path (its parts, inside a source) is under a skipped folder; whole parts, any case."""
    folded = tuple(unicodedata.normalize("NFC", p).casefold() for p in parts)
    for folder in skip:
        wanted = tuple(
            unicodedata.normalize("NFC", p).casefold() for p in folder.split("/") if p
        )
        if wanted and folded[: len(wanted)] == wanted:
            return True
    return False
