"""What can be done to one shared folder of the project, each its own small dialog: rename it (its
paths move everywhere, then the page is built again), its skipped folders (the folder picker),
free the space of skipped folders, remove it (keep or delete its files). Project settings
(project_settings.py) shows them per folder; `changed` runs after the files changed."""

from collections.abc import Callable
from dataclasses import replace

from chips import ask_text, close
from folder_picker import FolderPicker
from jobs import Jobs
from main_menu import MainMenu
from nicegui import ui

from downtempo.errors import UserError
from downtempo.events import count, size
from downtempo.library import Library
from downtempo.sources import Source


class FolderActions:
    def __init__(
        self,
        library: Callable[[], Library],
        jobs: Jobs,
        menu: MainMenu,
        changed: Callable[[], None],
    ) -> None:
        """`menu`: renaming a folder saves and rebuilds the page like a project switch."""
        self.library, self.jobs, self.menu, self.changed = library, jobs, menu, changed

    async def rename(self, source: Source) -> None:
        answer = await ask_text(f"Rename “{source.name}”", source.name)
        if not answer or answer[0] == source.name:
            return
        menu = self.menu
        menu.leave()  # its practice memory is saved, then renamed on disk
        try:
            self.library().rename_source(source.name, answer[0])
        except UserError as error:
            menu.player.retired = False
            ui.notify(f"{error.message} {error.hint}".strip(), type="negative")
            return
        menu.rebuild(menu.from_screen())

    def skipped(self, source: Source) -> None:
        library = self.library()
        with (
            ui.dialog() as dialog,
            ui.card().classes("w-[720px] max-w-[95vw] gap-2"),
        ):
            ui.label(f"Skipped folders of “{source.name}”").classes("text-h6")
            ui.label(
                "Skipped folders aren't downloaded. Files already here stay until you free the space."
            ).classes("text-body2 text-grey")
            box = ui.column().classes("w-full gap-2")
            ui.button("Cancel", on_click=dialog.close).props("flat no-caps").classes(
                "self-end"
            )

        def save(_: str, skip: tuple[str, ...]) -> None:
            try:
                library.replace_source(source.name, replace(source, skip=skip))
            except UserError as error:
                ui.notify(error.message, type="negative")
                return
            dialog.close()
            library.rebuild()
            self.changed()
            ui.notify(
                f"{count(len(skip), 'folder')} skipped"
                if skip
                else "No folders skipped"
            )

        FolderPicker(
            box,
            library,
            self.jobs,
            source.url,
            save,
            start=source.folder,
            skip=source.skip,
            base=source.folder,
            skip_only=True,
        )
        dialog.on("hide", lambda: close(dialog))
        dialog.open()

    async def free_space(self, source: Source, freeable: int) -> None:
        library = self.library()
        with ui.dialog() as dialog, ui.card().classes("gap-3"):
            ui.label(
                f"Delete the {size(freeable)} of downloaded files in the skipped folders of “{source.name}”?"
            ).classes("text-body1")
            ui.label(
                "They are on the server still; un-skip a folder to get them back."
            ).classes("text-caption text-grey")
            with ui.row().classes("self-end"):
                ui.button("Cancel", on_click=lambda: dialog.submit(False)).props(
                    "flat no-caps autofocus"
                )
                ui.button("Delete", on_click=lambda: dialog.submit(True)).props(
                    "unelevated no-caps color=negative"
                )
        sure = await dialog
        close(dialog)
        if sure:
            freed = library.free_space(source.name)
            library.rebuild()
            self.changed()
            ui.notify(f"Freed {size(freed)}")

    async def remove(self, source: Source) -> None:
        library = self.library()
        target = library.target(source)
        files = [p for p in target.rglob("*") if p.is_file()] if target.exists() else []
        bytes = sum(p.stat().st_size for p in files)
        with ui.dialog() as dialog, ui.card().classes("gap-3 max-w-[520px]"):
            ui.label(f"Remove “{source.name}”?").classes("text-h6")
            ui.label(
                "Downtempo stops checking this folder. The folder on the server isn't touched."
            ).classes("text-body2")
            with ui.column().classes("w-full gap-1"):
                ui.button(
                    "Keep its files",
                    on_click=lambda: dialog.submit("keep"),
                ).props("outline no-caps").classes("w-full").tooltip(
                    "They stay in your songs, without updates"
                )
                ui.button(
                    f"Delete its {count(len(files), 'file')} ({size(bytes)})",
                    on_click=lambda: dialog.submit("delete"),
                ).props("outline no-caps color=negative").classes("w-full").tooltip(
                    "Their songs lose these files"
                )
                ui.button("Cancel", on_click=lambda: dialog.submit(None)).props(
                    "flat no-caps autofocus"
                ).classes("w-full")
        answer = await dialog
        close(dialog)
        if not answer:
            return
        try:
            library.remove_source(source.name, delete_files=answer == "delete")
        except UserError as error:
            ui.notify(error.message, type="negative")
            return
        library.rebuild()
        self.changed()
        ui.notify(f"Removed “{source.name}”")
