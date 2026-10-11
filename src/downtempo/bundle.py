"""The settings file: one project's sources as TOML text to email (`export`), and importing one
from someone else (`read` checks it all, `preview` says what would change, `apply` writes).
Nothing is written before `apply`. Format and rules: docs/settings-file.md."""

import datetime
import tomllib
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

import tomlkit

from downtempo.bundle_grouping import Merged, check_grouping, merge, rename_sources
from downtempo.downloaders import provider_for
from downtempo.errors import UserError
from downtempo.library import Library
from downtempo.memory_file import to_dict
from downtempo.shapes import Memory
from downtempo.skipping import check_folder
from downtempo.sources import Source, check_name, check_url, name_from, to_table

VERSION = 1
MAX_BYTES = 512 * 1024  # a sorting of about 1,000 files is ~150 KB
MAX_FOLDER = 500
MAX_REPORTED = 5  # lines of one kind shown in the preview
NOT_SETTINGS = "This isn't a Downtempo settings file."
HEADER = (
    "Downtempo settings. Import: the project menu → Export… / Import…, "
    "or uv run downtempo import <this file>"
)
TOO_BIG = f"{MAX_BYTES // 1024} KB at most"


@dataclass(frozen=True)
class Bundle:
    project: str
    sources: list[Source]
    refused: list[str]  # "source 'x': why", shown in the preview
    ignored: list[str]  # unknown keys, listed, never guessed
    grouping: Memory = field(default_factory=Memory)  # the sorting, checked


@dataclass(frozen=True)
class Change:
    kind: Literal["add", "rename", "same", "update"]
    source: Source  # as it will be saved
    old: str = ""  # rename: the name in the file; update: the name here

    def describe(self) -> str:
        match self.kind:
            case "add":
                return f"Add '{self.source.name}' ({self.source.type})"
            case "rename":
                return f"Add '{self.old}' as '{self.source.name}' (the name is taken)"
            case "same":
                return f"'{self.source.name}': already here"
            case "update":
                return f"'{self.old}': skipped folders {list(self.source.skip)}"


@dataclass(frozen=True)
class SortingChange:
    """The file's sorting merged into the project's (ours win where both decided)."""

    kind: Literal["sorting", "same"]
    merged: Merged
    first_time: bool  # the project had no sorting

    def describe(self) -> str:
        m = self.merged
        if self.kind == "same":
            if m.differing:
                return (
                    f"The sorting: nothing new (yours kept where {m.differing} differ)"
                )
            return "The sorting: already here"
        if self.first_time:
            return f"Add the sorting ({m.songs_added} songs, {m.files_added} files)"
        parts = [
            (f"{m.differing} songs differ" if m.differing != 1 else "1 song differs")
            if m.differing
            else "",
            f"{m.songs_added} songs and {m.files_added} files added"
            if m.songs_added or m.files_added
            else "",
        ]
        lines = [f"Update the sorting: {', '.join(p for p in parts if p)}"]
        lines += [f"    {line}" for line in m.kept[:MAX_REPORTED]]
        if len(m.kept) > MAX_REPORTED:
            lines.append(f"    …and {len(m.kept) - MAX_REPORTED} more kept as yours")
        return "\n".join(lines)


def export(library: Library) -> str:
    """The project's settings file. Never tokens or paths of this computer."""
    doc = tomlkit.document()
    doc.add(tomlkit.comment(HEADER))
    doc["downtempo"] = VERSION
    doc["project"] = library.name()
    doc["exported"] = datetime.date.today()
    sources = tomlkit.aot()
    for source in library.sources():
        sources.append(to_table(source))
    doc["source"] = sources
    memory = library.sorting.read()
    if memory.songs or memory.files:
        doc["grouping"] = to_dict(memory, {})
    return tomlkit.dumps(doc)


def read_file(path: Path) -> Bundle:
    try:
        if path.stat().st_size > MAX_BYTES:
            raise UserError(f"{path.name} is too big for a settings file ({TOO_BIG}).")
        return read(path.read_bytes().decode("utf-8"))
    except UnicodeDecodeError as error:
        raise UserError(NOT_SETTINGS, "It isn't plain text.") from error
    except OSError as error:
        raise UserError(f"Can't read {path}: {error.strerror}.") from error


def read(text: str) -> Bundle:
    """Check a settings file from someone else; raises `UserError` when it can't be used at all."""
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise UserError(f"This is too big for a settings file ({TOO_BIG}).")
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise UserError(NOT_SETTINGS, str(error)) from error
    version = data.get("downtempo")
    if not isinstance(version, int) or isinstance(version, bool):
        raise UserError(NOT_SETTINGS, "Its first line should be: downtempo = 1")
    if version > VERSION:
        raise UserError("Made by a newer Downtempo.", "Update Downtempo first.")
    ignored = [
        k
        for k in data
        if k not in ("downtempo", "project", "exported", "source", "grouping")
    ]
    project = data.get("project")
    project = (
        project.strip()[:60]
        if isinstance(project, str) and project.isprintable()
        else ""
    )
    entries = data.get("source", [])
    if not isinstance(entries, list):
        raise UserError(NOT_SETTINGS, "'source' should be [[source]] tables.")
    sources: list[Source] = []
    refused: list[str] = []
    for number, entry in enumerate(entries, 1):
        try:
            source, unknown = check_source(entry, [s.name for s in sources])
            sources.append(source)
            ignored += [f"source '{source.name}': {k}" for k in unknown]
        except UserError as error:
            name = entry.get("name") if isinstance(entry, dict) else None
            label = f"'{name}'" if isinstance(name, str) else f"number {number}"
            refused.append(f"source {label[:70]}: {error.message}")
    memory = Memory()
    if "grouping" in data:
        memory, dropped, unknown = check_grouping(
            data["grouping"], {s.name for s in sources}
        )
        refused += dropped[:MAX_REPORTED]
        if len(dropped) > MAX_REPORTED:
            refused.append(f"grouping: …and {len(dropped) - MAX_REPORTED} more dropped")
        ignored += unknown
    return Bundle(project or "Imported", sources, refused, ignored, memory)


def check_source(entry: object, taken: list[str]) -> tuple[Source, list[str]]:
    """One `[[source]]` from the file, checked like a pasted link; also its unknown keys."""
    if not isinstance(entry, dict):
        raise UserError("it isn't a table.")
    text = {k: v for k, v in entry.items() if k in ("name", "type", "url", "folder")}
    if not all(isinstance(v, str) for v in text.values()):
        raise UserError("name, type, url and folder must be text.")
    if "name" not in text or "url" not in text:
        raise UserError("it needs a name and a url.")
    url = check_url(text["url"])
    found = provider_for(url)
    if found is None:
        raise UserError("the link isn't a OneDrive folder link.")
    if text.get("type", found.type) != found.type:
        raise UserError(f"the link is {found.label}, not '{text['type']}'.")
    folder = text.get("folder", "").strip("/")
    parts = folder.split("/") if folder else []
    if len(folder) > MAX_FOLDER or any(
        p in ("", ".", "..") or not p.isprintable() for p in parts
    ):
        raise UserError(
            f"the folder '{folder[:80]}' isn't a folder path inside the share."
        )
    skip = entry.get("skip", [])
    if not isinstance(skip, list) or not all(isinstance(p, str) for p in skip):
        raise UserError("skip must be a list of folder paths.")
    skipped = tuple(check_skip(p) for p in skip)
    source = Source(check_name(text["name"], taken), found.type, url, folder, skipped)
    known = (
        "name",
        "type",
        "url",
        "folder",
        "skip",
        "extra_folders",
    )  # the last: old files
    return source, [k for k in entry if k not in known]


def check_skip(folder: str) -> str:
    try:
        return check_folder(folder)
    except UserError as error:
        raise UserError(f"skip: {error.message}") from error


def preview(library: Library | None, bundle: Bundle) -> list[Change | SortingChange]:
    """What `apply` would do to `library` (None: a new, empty project). Writes nothing."""
    here = library.sources() if library else []
    taken = [s.name for s in here]
    changes: list[Change | SortingChange] = []
    # the file's source name → the name it gets here
    renames: dict[str, str] = {}
    for source in bundle.sources:
        same = next(
            (
                s
                for s in here
                if (s.url, s.folder.casefold())
                == (source.url, source.folder.casefold())
            ),
            None,
        )
        if same:
            # Both decided: ours stay, the file's skipped folders are added.
            skip = same.skip + tuple(
                p
                for p in source.skip
                if p.casefold() not in {s.casefold() for s in same.skip}
            )
            if skip == same.skip:
                changes.append(Change("same", same))
            else:
                changes.append(Change("update", replace(same, skip=skip), same.name))
            renames[source.name] = same.name
        elif source.name.casefold() in {t.casefold() for t in taken}:
            renamed = replace(source, name=name_from(source.name, taken))
            changes.append(Change("rename", renamed, source.name))
            taken.append(renamed.name)
            renames[source.name] = renamed.name
        else:
            changes.append(Change("add", source))
            taken.append(source.name)
            renames[source.name] = source.name
    theirs = rename_sources(
        bundle.grouping, {k: v for k, v in renames.items() if k != v}
    )
    if theirs.songs or theirs.files:
        ours = library.sorting.read() if library else Memory()
        merged = merge(ours, theirs)
        nothing = not (merged.songs_added or merged.files_added)
        changes.append(
            SortingChange(
                "same" if nothing else "sorting",
                merged,
                not (ours.songs or ours.files),
            )
        )
    return changes


def apply(library: Library, changes: list[Change | SortingChange]) -> None:
    """Sources first, then the sorting (a taken name was renamed, so the keys already fit)."""
    for change in changes:
        match change:
            case Change(kind="add" | "rename"):
                library.add_source(change.source)
            case Change(kind="update"):
                library.replace_source(change.old, change.source)
            case SortingChange(kind="sorting"):
                library.sorting.replace_memory(change.merged.memory)
