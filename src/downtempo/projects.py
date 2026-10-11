"""Many libraries ("projects") under `data/projects/<id>/`, which one is current (`data/app.json`),
and moving the data from before projects in once (`migrate`). Plan: docs/projects.md."""

import json
import os
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from downtempo.errors import UserError
from downtempo.jsonfile import write_json
from downtempo.library import Library
from downtempo.sources import MAX_NAME, free_id, load, read_sources, save
from downtempo.upgrade import upgrade_project

# Keys of the old player-state.json that belong to a project; the rest is the computer's layout.
PRACTICE_KEYS = ("songs", "recordings", "last_song")
DEFAULT_NAME = "My songs"


@dataclass(frozen=True)
class ProjectInfo:
    id: str  # its folder name under projects/
    name: str
    sources: int
    songs: int


class Workspace:
    """The data folder: projects, the current one, and `app.json` (the player's layout too)."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir.resolve()
        self.folder = self.data_dir / "projects"
        self.app_file = self.data_dir / "app.json"
        migrate(self.data_dir)
        for project in sorted(self.folder.glob("*/project.toml")):
            upgrade_project(project.parent)

    def projects(self) -> list[ProjectInfo]:
        found = []
        for folder in sorted(self.folder.glob("*/project.toml")):
            library = Library(folder.parent)
            found.append(
                ProjectInfo(
                    folder.parent.name,
                    library.name(),
                    len(library.sources()),
                    len(library.songs()),
                )
            )
        return sorted(found, key=lambda p: p.name.casefold())

    def current_id(self) -> str | None:
        """The current project's id; None when it's gone or not chosen. Changes nothing."""
        wanted = read_json(self.app_file).get("project")
        return wanted if wanted in [p.id for p in self.projects()] else None

    def current(self) -> Library:
        """The current project; the first one when it's gone, a new one when there are none."""
        if id := self.current_id():
            return self.library(id)
        if ids := [p.id for p in self.projects()]:
            return self.use(ids[0])
        return self.create(DEFAULT_NAME)

    def library(self, id: str) -> Library:
        return Library(self.folder / id)

    def find(self, name: str) -> str:
        """A project's id from its name or id, any case."""
        for project in self.projects():
            if name.casefold() in (project.name.casefold(), project.id.casefold()):
                return project.id
        known = ", ".join(p.name for p in self.projects())
        raise UserError(f"There is no project called '{name}'.", f"Projects: {known}.")

    def use(self, id: str) -> Library:
        library = self.library(id)
        if not library.sources_file.exists():
            raise UserError(f"There is no project '{id}'.")
        update_json(self.app_file, project=id)
        return library

    def create(self, name: str) -> Library:
        """A new empty project, made current."""
        name = self.check_name(name)
        id = free_id(
            name,
            {p.name for p in self.folder.iterdir()} if self.folder.exists() else set(),
        )
        library = self.library(id)
        library.root.mkdir(parents=True)
        write_name(library.sources_file, name)
        return self.use(id)

    def rename(self, id: str, name: str) -> None:
        """Only the name changes; the folder keeps its id, so nothing moves."""
        library = self.library(id)
        write_name(library.sources_file, self.check_name(name, id))

    def delete(self, id: str) -> None:
        """Removes the project's folder with its downloads; ask the user first."""
        library = self.library(id)
        if library.root.parent != self.folder or not library.sources_file.exists():
            raise UserError(f"There is no project '{id}'.")
        shutil.rmtree(library.root)

    def free_name(self, name: str) -> str:
        """`name`, or `name 2`, … when a project already has it."""
        taken = {p.name.casefold() for p in self.projects()}
        free, number = name, 2
        while free.casefold() in taken:
            free, number = f"{name} {number}", number + 1
        return free

    def check_name(self, name: str, id: str = "") -> str:
        name = unicodedata.normalize("NFC", name.strip())
        if not name:
            raise UserError("The project name is empty.")
        if len(name) > MAX_NAME or not name.isprintable():
            raise UserError(
                f"A project name is at most {MAX_NAME} printable characters."
            )
        for other in self.projects():
            if other.id != id and other.name.casefold() == name.casefold():
                raise UserError(
                    f"There is already a project called '{name}'.", "Pick another name."
                )
        return name


def write_name(path: Path, name: str) -> None:
    doc = load(path)
    doc["name"] = name
    save(path, doc)


# ---------------------------------------------------------------- moving old data in


def migrate(data_dir: Path) -> None:
    """Move a library from before projects (`data/sources.toml`, `downloads/`, `songs.json`,
    `player-state.json`) into a project. Each step checks whether it's done, so an interrupted
    run continues on the next start; old JSON and TOML files stay as `*.before-projects`."""
    old = {
        name: data_dir / name
        for name in ("sources.toml", "downloads", "songs.json", "player-state.json")
    }
    if not any(path.exists() for path in old.values()):
        return
    app_file = data_dir / "app.json"
    id = read_json(app_file).get("project")
    if not id:  # first run: pick the project and write it down before moving anything
        sources = read_sources(old["sources.toml"])
        name = sources[0].name if sources else DEFAULT_NAME
        projects = data_dir / "projects"
        taken = {p.name for p in projects.iterdir()} if projects.exists() else set()
        id = free_id(name, taken)
        update_json(app_file, project=id, migrating_name=name)
    root = data_dir / "projects" / id
    root.mkdir(parents=True, exist_ok=True)
    project_file = root / "project.toml"

    if old["sources.toml"].exists():
        if not project_file.exists():
            temporary = root / "project.toml.tmp"
            shutil.copyfile(old["sources.toml"], temporary)
            os.replace(temporary, project_file)
        set_aside(old["sources.toml"])
    if "name" not in load(project_file):
        name = read_json(app_file).get("migrating_name", DEFAULT_NAME)
        write_name(project_file, name)

    if old["downloads"].exists():
        (root / "downloads").mkdir(exist_ok=True)
        for child in sorted(old["downloads"].iterdir()):
            target = root / "downloads" / child.name
            if target.exists():
                raise UserError(
                    f"Can't move {child} into the project: {target} is already there.",
                    "Move or remove one of them by hand, then start again.",
                )
            child.rename(target)
        old["downloads"].rmdir()

    if old["songs.json"].exists():
        if not (root / "songs.json").exists():
            temporary = root / "songs.json.tmp"
            shutil.copyfile(old["songs.json"], temporary)
            os.replace(temporary, root / "songs.json")
        set_aside(old["songs.json"])

    if old["player-state.json"].exists():
        state = read_json(old["player-state.json"])
        practice = {k: state[k] for k in PRACTICE_KEYS if k in state}
        layout = {k: v for k, v in state.items() if k not in PRACTICE_KEYS}
        write_json(root / "practice.json", practice)
        update_json(app_file, **layout)
        set_aside(old["player-state.json"])

    app = read_json(app_file)
    app.pop("migrating_name", None)
    write_json(app_file, app)


def set_aside(path: Path) -> None:
    os.replace(path, path.with_name(path.name + ".before-projects"))


# ---------------------------------------------------------------- small JSON files


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def update_json(path: Path, **values: Any) -> None:
    write_json(path, read_json(path) | values)
