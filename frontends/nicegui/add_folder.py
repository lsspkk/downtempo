"""Add folder: paste a share link → (sign in) → pick the folder, tick Skip on folders not needed →
"About 12 songs from 31 files, 180 MB" → Download. Nothing is saved before Download; then the
source is added, its download starts (updates.py) and the project screen opens on the unknown
files (docs/project-screen.md#getting-there). Also the first start: the project takes the folder's
name."""

from collections.abc import Callable

from folder_picker import FolderPicker
from jobs import Jobs
from nicegui import ui
from player import Player
from updates import Updates

from downtempo.errors import UserError
from downtempo.events import count, size
from downtempo.library import FolderPreview
from downtempo.sources import Source

SHOWN_TITLES = 14


class AddFolder:
    def __init__(
        self,
        player: Player,
        jobs: Jobs,
        updates: Updates,
        added: Callable[[str], None],
        rename_project: Callable[[str], None],
    ) -> None:
        """`added(source name)` runs after Download started; `rename_project` names a project
        that had no folders yet."""
        self.player, self.jobs, self.updates = player, jobs, updates
        self.added, self.rename_project = added, rename_project
        self.url = self.provider = self.type = ""
        with (
            ui.dialog().props("persistent") as self.dialog,
            ui.card().classes("w-[760px] max-w-[95vw] gap-3"),
        ):
            with ui.row().classes("items-center w-full no-wrap"):
                self.heading = ui.label("").classes("text-h6")
                ui.space()
                ui.button(icon="close", on_click=self.close).props(
                    "flat round dense"
                ).tooltip("Cancel (Esc)")
            self.body = ui.column().classes("w-full gap-3")
        self.dialog.on("keydown.esc", self.close)

    @property
    def library(self):
        return self.player.library

    def open(self, url: str = "") -> None:
        self.link_step(url)
        self.dialog.open()
        if url.strip():  # pasted on the welcome page: go on at once
            self.next_step()

    def close(self) -> None:
        if self.jobs.running and not self.updates.running:
            self.jobs.stop()  # a listing of ours; a download goes on
        self.dialog.close()

    # ------------------------------------------------------------ 1. the link

    def link_step(self, url: str = "") -> None:
        self.heading.text = "Add a shared folder"
        self.body.clear()
        with self.body:
            ui.label(
                "Paste the link to the folder where your group keeps its songs. "
                "In OneDrive: open the folder, press Share, then Copy link."
            ).classes("text-body2")
            self.link = (
                ui.input("Link", value=url, placeholder="https://1drv.ms/f/…")
                .props("autofocus outlined clearable")
                .classes("w-full")
            )
            self.link_error = ui.label("").classes("text-negative text-body2")
            self.link_error.set_visibility(False)
            self.link.on("keydown.enter", self.next_step)
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=self.close).props("flat no-caps")
                ui.button("Next", icon="arrow_forward", on_click=self.next_step).props(
                    "unelevated no-caps"
                )

    def next_step(self) -> None:
        text = (self.link.value or "").strip()
        try:
            self.provider, self.type = self.library.link_provider(text)
        except UserError as problem:
            self.link_error.text = f"{problem.message} {problem.hint}".strip()
            self.link_error.set_visibility(True)
            return
        self.url = text
        self.pick_step()

    # ------------------------------------------------------------ 2. the folder

    def pick_step(self, start: str = "", skip: tuple[str, ...] = ()) -> None:
        self.heading.text = f"Which {self.provider} folder holds the songs?"
        self.body.clear()
        with self.body:
            box = ui.column().classes("w-full gap-2")
            with ui.row().classes("w-full gap-2"):
                ui.button("Back", icon="arrow_back", on_click=self.back_to_link).props(
                    "flat no-caps"
                )
        FolderPicker(
            box, self.library, self.jobs, self.url, self.preview_step, start, skip
        )

    def back_to_link(self) -> None:
        if self.jobs.running and not self.updates.running:
            self.jobs.stop()
        self.link_step(self.url)

    # ------------------------------------------------------------ 3. what it brings

    def preview_step(self, folder: str, skip: tuple[str, ...]) -> None:
        try:
            self.library.check_new(self.url, folder)
        except UserError as problem:
            ui.notify(problem.message, type="warning")
            return
        library, url = self.library, self.url
        if not self.jobs.start(
            "Look at the folder",
            lambda report, cancel: library.preview_folder(
                url, folder, skip, report, cancel
            ),
            lambda found: self.show_preview(folder, skip, found),
        ):
            return
        self.heading.text = "Looking at what's there…"
        self.body.clear()
        with self.body, ui.row().classes("items-center gap-2 p-4 text-grey"):
            ui.spinner(size="md")
            ui.label("Listing the files and sorting them into songs…")
            ui.button("Cancel", on_click=lambda: self.stop_preview(folder, skip)).props(
                "flat dense no-caps"
            )

    def stop_preview(self, folder: str, skip: tuple[str, ...]) -> None:
        self.jobs.stop()
        self.pick_step(folder, skip)

    def show_preview(
        self, folder: str, skip: tuple[str, ...], found: FolderPreview | None
    ) -> None:
        if not self.dialog.value:
            return
        if found is None:  # the error was shown, or it was cancelled
            self.pick_step(folder, skip)
            return
        grouping = found.grouping
        joining = found.joining()
        songs = len(grouping.suggestions) + len(joining)
        unknown = len(grouping.loose)
        self.heading.text = f"Add “{found.folder_name}”"
        self.body.clear()
        with self.body:
            if not found.files:
                ui.label(
                    "There are no recordings or sheets here (mp3, wav and pdf count)."
                ).classes("text-body1")
                ui.button(
                    "Pick another folder",
                    icon="arrow_back",
                    on_click=lambda: self.pick_step(folder, skip),
                ).props("flat no-caps")
                return
            ui.label(
                f"About {count(songs, 'song')} from {count(found.files, 'file')}, "
                f"{size(found.bytes)}"
            ).classes("text-h5")
            with ui.row().classes("gap-1 w-full"):
                titles = [s.title for s in grouping.suggestions]
                for title in titles[:SHOWN_TITLES]:
                    ui.chip(title, icon="music_note").props("dense outline")
                if len(titles) > SHOWN_TITLES:
                    ui.chip(f"+ {len(titles) - SHOWN_TITLES} more").props("dense flat")
            notes = [
                f"{sum(joining.values())} files join your songs: {', '.join(joining)}"
                if joining
                else "",
                f"{count(unknown, 'file')} with no song yet: you sort them after the download"
                if unknown
                else "",
                f"Skipped: {', '.join(skip)}" if skip else "",
            ]
            for note in filter(None, notes):
                ui.label(note).classes("text-body2 text-grey")
            first = not self.library.sources()
            with ui.row().classes("w-full gap-4 no-wrap"):
                name = ui.input("Name of this folder here", value=found.name).props(
                    "outlined dense"
                )
                name.classes("grow").tooltip(
                    "How the folder is called in Downtempo; files go to downloads/<name>"
                )
                project = ui.input("Project name", value=found.folder_name).props(
                    "outlined dense"
                )
                project.classes("grow").set_visibility(first)
                project.tooltip("A project is one group you practise with")
            with ui.row().classes("w-full items-center gap-2"):
                ui.button(
                    "Back",
                    icon="arrow_back",
                    on_click=lambda: self.pick_step(folder, skip),
                ).props("flat no-caps")
                ui.space()
                ui.label("The songs are yours to fix after the download.").classes(
                    "text-caption text-grey"
                )
                ui.button(
                    "Download",
                    icon="download",
                    on_click=lambda: self.download(
                        name.value, folder, skip, project.value if first else ""
                    ),
                ).props("unelevated no-caps")

    # ------------------------------------------------------------ 4. download

    def download(
        self, name: str, folder: str, skip: tuple[str, ...], project: str
    ) -> None:
        try:
            source = self.library.add_source(
                Source(name.strip(), self.type, self.url, folder, skip)
            )
            if project.strip():
                self.rename_project(project.strip())
        except UserError as problem:
            ui.notify(f"{problem.message} {problem.hint}".strip(), type="negative")
            return
        self.dialog.close()
        self.updates.start([source.name])
        self.added(source.name)
