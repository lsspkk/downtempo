"""The folder picker: browse a shared folder's subfolders (♪ / 📄 counts at all levels below), go
in and out, tick ☐ Skip on folders not to download, and use one. Each step lists one level through
`library.folders` as a job (the sign-in card shows when needed). Used by Add folder and by a
source's Change link… and Skipped folders… (docs/project-screen.md#getting-there)."""

from collections.abc import Callable
from pathlib import PurePosixPath

from jobs import Jobs
from nicegui import ui

from downtempo.library import Library, RemoteFolderInfo


def counts(audio: int, sheets: int, folders: int = 0) -> str:
    parts = [f"♪ {audio}" if audio else "", f"📄 {sheets}" if sheets else ""]
    parts.append(f"{folders} folder{'s' * (folders != 1)}" if folders else "")
    return "  ".join(p for p in parts if p) or "no recordings or sheets"


class FolderPicker:
    """Draws into `box`; `use(folder, skip)` gets the chosen path inside the share and the skipped
    folders relative to it. With `base` it doesn't go above that folder, and with `skip_only` it
    only edits the skipped folders: `use(base, skip relative to base)`."""

    def __init__(
        self,
        box: ui.element,
        library: Library,
        jobs: Jobs,
        url: str,
        use: Callable[[str, tuple[str, ...]], None],
        start: str = "",
        skip: tuple[str, ...] = (),
        base: str = "",
        skip_only: bool = False,
    ) -> None:
        self.box, self.library, self.jobs, self.url = box, library, jobs, url
        self.use, self.skip_only = use, skip_only
        self.base = base.strip("/")
        self.path = start.strip("/") or self.base
        # paths inside the share; ticked folders anywhere below the chosen one
        self.skipped = {f"{self.path}/{s}".strip("/") for s in skip}
        self.found: list[RemoteFolderInfo] = []
        self.known: dict[str, RemoteFolderInfo] = {}  # counts of folders seen so far
        self.go(self.path)

    def go(self, path: str) -> None:
        library, url = self.library, self.url
        self.box.clear()
        if not self.jobs.start(
            "Open the folder",
            lambda report, cancel: library.folders(url, path, report, cancel),
            lambda found: self.listed(path, found),
        ):
            with self.box, ui.row().classes("items-center gap-2 p-2"):
                ui.label("A download is running; try when it has finished.").classes(
                    "text-grey"
                )
                ui.button("Try again", on_click=lambda: self.go(path)).props(
                    "flat dense no-caps"
                )
            return
        self.path = path
        with self.box, ui.row().classes("items-center gap-2 p-4 text-grey"):
            ui.spinner(size="sm")
            ui.label("Opening the folder…")
            ui.button("Cancel", on_click=self.jobs.stop).props("flat dense no-caps")

    def listed(self, path: str, found: list[RemoteFolderInfo] | None) -> None:
        self.box.clear()
        if found is None:  # failed or cancelled
            error = self.jobs.error
            why = f"{error.message} {error.hint}".strip() if error else ""
            with self.box, ui.row().classes("items-center gap-2 p-2"):
                ui.label(why or "The folder couldn't be opened.").classes("text-grey")
                ui.button("Try again", on_click=lambda: self.go(path)).props(
                    "flat dense no-caps"
                )
            return
        self.found = found
        self.known |= {f.path: f for f in found}
        self.show()

    def show(self) -> None:
        self.box.clear()
        base = PurePosixPath(self.base).parts if self.base else ()
        parts = PurePosixPath(self.path).parts[len(base) :] if self.path else ()
        with self.box:
            with ui.row().classes("items-center gap-0 w-full no-wrap"):
                ui.button(
                    base[-1] if base else "Shared folder",
                    icon="folder_shared",
                    on_click=lambda: self.go(self.base),
                ).props("flat dense no-caps")
                for i, part in enumerate(parts):
                    ui.icon("chevron_right").classes("text-grey")
                    target = "/".join((*base, *parts[: i + 1]))
                    ui.button(
                        part, on_click=lambda target=target: self.go(target)
                    ).props("flat dense no-caps").classes("truncate max-w-[200px]")
                ui.space()
                here = self.known.get(self.path)
                if here and not self.skip_only:
                    ui.label(counts(here.audio, here.sheets)).classes(
                        "text-caption text-grey whitespace-nowrap"
                    )
                label = "Save skipped folders" if self.skip_only else "Use this folder"
                ui.button(label, icon="check", on_click=self.choose).props(
                    "unelevated no-caps"
                )
            with ui.scroll_area().classes("w-full h-[300px] border rounded-borders"):
                if not self.found:
                    ui.label(
                        "No folders inside."
                        + ("" if self.skip_only else " Use this one.")
                    ).classes("text-grey p-4")
                for folder in self.found:
                    self.row(folder)
            ui.label(
                "Tick Skip for folders you don't need (old sets, other parts): they aren't downloaded."
            ).classes("text-caption text-grey")

    def row(self, folder: RemoteFolderInfo) -> None:
        skipped = folder.path in self.skipped
        with ui.row().classes("items-center gap-2 w-full no-wrap px-2 py-1 border-b"):
            ui.icon("folder", size="20px").classes(
                "text-grey" if skipped else "text-primary"
            )
            name = ui.label(folder.name).classes(
                "truncate grow" + (" line-through text-grey" * skipped)
            )
            name.tooltip(folder.path)
            ui.label(counts(folder.audio, folder.sheets, folder.folders)).classes(
                "text-caption text-grey whitespace-nowrap"
            )
            ui.checkbox(
                "Skip",
                value=skipped,
                on_change=lambda e, p=folder.path: self.set_skip(p, e.value),
            ).props("dense")
            open_button = ui.button(
                icon="chevron_right", on_click=lambda p=folder.path: self.go(p)
            ).props("flat round dense")
            open_button.set_enabled(bool(folder.folders) and not skipped)
            open_button.tooltip("Open")

    def set_skip(self, path: str, on: bool) -> None:
        (self.skipped.add if on else self.skipped.discard)(path)
        self.show()

    def choose(self) -> None:
        chosen = self.base if self.skip_only else self.path
        prefix = f"{chosen}/" if chosen else ""
        skip = tuple(
            sorted(s.removeprefix(prefix) for s in self.skipped if s.startswith(prefix))
        )
        self.use(chosen, skip)
