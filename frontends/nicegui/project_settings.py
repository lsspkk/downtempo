"""Project settings: one dialog for how the project is set up, from ☰ → Project settings… or a
folder chip's "Folder settings…" (docs/project-screen.md#project-settings). The project's name
(saved on Enter or Save); its shared folders, each with its link (Copy, Change link…), the folder
inside the share, skipped folders, Rename… and Remove…, and the last error with a way to fix it;
+ Add folder; the sign-ins. More settings of the project go here too."""

from collections.abc import Callable

from change_link import ChangeLink
from common import copy_text
from folder_actions import FolderActions
from nicegui import ui
from updates import Updates, ago

from downtempo.errors import UserError
from downtempo.events import size
from downtempo.library import Library
from downtempo.projects import Workspace
from downtempo.sources import Source

CSS = """
.folder-box { border: 1px solid rgba(128, 128, 128, 0.35); border-radius: 8px; padding: 10px 14px; }
.folder-box.here { border-color: #4f5bd5; box-shadow: 0 0 0 1px #4f5bd5; }
.folder-box.warn { border-color: #c62828; }
.folder-box .key { width: 84px; flex: none; }
"""


class ProjectSettings:
    def __init__(
        self,
        workspace: Workspace,
        library: Callable[[], Library],
        updates: Updates,
        actions: FolderActions,
        change_link: ChangeLink,
        add_folder: Callable[[], None],
        renamed: Callable[[], None],
    ) -> None:
        """`renamed` runs after the project got a new name (the page shows it in two places)."""
        self.workspace, self.library, self.updates = workspace, library, updates
        self.actions, self.change_link = actions, change_link
        self.add_folder, self.renamed = add_folder, renamed
        self.focus = ""  # the folder it was opened at
        ui.add_css(CSS)
        with (
            ui.dialog() as self.dialog,
            ui.card().classes("w-[720px] max-w-[95vw] max-h-[92vh] gap-0 p-0 no-wrap"),
        ):
            with ui.row().classes("items-center w-full no-wrap px-5 pt-4 pb-2"):
                ui.label("Project settings").classes("text-h6")
                ui.space()
                ui.button(icon="close", on_click=self.dialog.close).props(
                    "flat round dense"
                ).tooltip("Close (Esc)")
            self.body = ui.column().classes("w-full gap-4 px-5 pb-5 overflow-y-auto")
        updates.changed.append(lambda: self.show() if self.dialog.value else None)

    def open(self, folder: str = "") -> None:
        self.focus = folder
        self.show()
        self.dialog.open()

    def show(self) -> None:
        library = self.library()
        try:
            sources = library.sources()
        except UserError as error:
            sources = []
            ui.notify(error.message, type="negative")
        checked = library.checked()
        self.body.clear()
        with self.body:
            self.name_part(library)
            with ui.row().classes("items-center w-full mt-2"):
                ui.label("Shared folders").classes("text-subtitle1 font-medium")
                ui.space()
                ui.button("Add folder", icon="add", on_click=self.add).props(
                    "flat no-caps"
                ).tooltip("Add another shared folder to this project")
            if not sources:
                ui.label(
                    "No shared folders yet: add the link to your group's folder."
                ).classes("text-body2 text-grey")
            for source in sources:
                self.folder_box(library, source, checked.get(source.name, ""))
            self.sign_ins(library)

    # ------------------------------------------------------------ the name

    def name_part(self, library: Library) -> None:
        old = library.name()
        with ui.row().classes("items-center gap-2 w-full no-wrap"):
            name = (
                ui.input("Project name", value=old)
                .props("outlined dense")
                .classes("grow")
            )
            save = ui.button("Save", on_click=lambda: self.rename(name.value)).props(
                "flat no-caps"
            )
        save.bind_enabled_from(name, "value", lambda v: (v or "").strip() != old)
        name.on("keydown.enter", lambda: self.rename(name.value))

    def rename(self, text: str) -> None:
        id = self.workspace.current_id()
        if not id or not text.strip() or text.strip() == self.library().name():
            return
        try:
            self.workspace.rename(id, text)
        except UserError as error:
            ui.notify(f"{error.message} {error.hint}".strip(), type="negative")
            return
        self.renamed()
        self.show()
        ui.notify("Project renamed")

    # ------------------------------------------------------------ one shared folder

    def folder_box(self, library: Library, source: Source, checked: str) -> None:
        error = self.updates.errors.get(source.name)
        here = " here" * (source.name == self.focus)
        with ui.column().classes(
            f"folder-box w-full gap-1{here}" + " warn" * bool(error)
        ):
            with ui.row().classes("items-center gap-2 w-full no-wrap"):
                ui.icon("cloud", size="20px").classes("text-primary")
                ui.label(source.name).classes("text-subtitle1 font-medium truncate")
                ui.label(self.state(source, checked)).classes(
                    "text-caption text-grey whitespace-nowrap"
                )
                ui.space()
                ui.button(
                    "Rename…", on_click=lambda: self.actions.rename(source)
                ).props("flat dense no-caps").set_enabled(not self.updates.running)
                ui.button("Remove…", on_click=lambda: self.remove(source)).props(
                    "flat dense no-caps color=negative"
                )
            if error:
                with ui.row().classes("items-center gap-2 w-full no-wrap"):
                    ui.icon("warning", size="18px").classes("text-negative")
                    ui.label(f"{error.message} {error.hint}".strip()).classes(
                        "text-body2 text-negative grow"
                    )
                    ui.button(
                        "Try again",
                        on_click=lambda: self.updates.start([source.name]),
                    ).props("flat dense no-caps").set_enabled(not self.updates.running)
            with ui.row().classes("items-center gap-2 w-full no-wrap"):
                ui.label("Link").classes("key text-grey")
                ui.label(source.url).classes(
                    "text-body2 truncate min-w-0 grow"
                ).tooltip(source.url)
                ui.button(
                    icon="content_copy", on_click=lambda: self.copy(source)
                ).props("flat round dense").tooltip("Copy the link")
                change = ui.button(
                    "Change link…", on_click=lambda: self.change(source)
                ).props(("unelevated" if error else "outline") + " dense no-caps")
                change.classes("whitespace-nowrap flex-none px-2")
                change.tooltip("The folder was shared again or the link expired")
            with ui.row().classes("items-center gap-2 w-full no-wrap"):
                ui.label("Folder").classes("key text-grey")
                ui.label(source.folder or "The whole shared folder").classes(
                    "text-body2 truncate"
                )
                provider = {a.type: a.provider for a in library.accounts()}
                ui.label(f"in {provider.get(source.type, source.type)}").classes(
                    "text-caption text-grey"
                )
            with ui.row().classes("items-center gap-2 w-full no-wrap"):
                ui.label("Skipped").classes("key text-grey")
                ui.label(", ".join(source.skip) or "nothing").classes(
                    "text-body2 truncate min-w-0" + " text-grey" * (not source.skip)
                ).tooltip(", ".join(source.skip) or "Every folder is downloaded")
                ui.space()
                ui.button(
                    "Skipped folders…", on_click=lambda: self.actions.skipped(source)
                ).props("flat dense no-caps")
                if freeable := library.skipped_size(source.name):
                    ui.button(
                        f"Free {size(freeable)}",
                        on_click=lambda: self.free(source, freeable),
                    ).props("flat dense no-caps").tooltip(
                        "Delete the downloaded files in the skipped folders"
                    )

    def state(self, source: Source, checked: str) -> str:
        updates = self.updates
        if source.name in updates.running:
            return "downloading" if updates.source == source.name else "waiting"
        return ago(checked) if checked else "not downloaded yet"

    def copy(self, source: Source) -> None:
        copy_text(source.url)
        ui.notify("Link copied", timeout=1000)

    def change(self, source: Source) -> None:
        if self.updates.running:
            ui.notify("Wait for the download to finish, or stop it.")
            return
        self.dialog.close()
        self.change_link.open(source)

    def add(self) -> None:
        self.dialog.close()
        self.add_folder()

    async def remove(self, source: Source) -> None:
        await self.actions.remove(source)
        self.show()

    async def free(self, source: Source, freeable: int) -> None:
        await self.actions.free_space(source, freeable)
        self.show()

    # ------------------------------------------------------------ sign-ins

    def sign_ins(self, library: Library) -> None:
        types = {s.type for s in library.sources()}
        accounts = [a for a in library.accounts() if a.type in types]
        if not accounts:
            return
        ui.label("Sign-in").classes("text-subtitle1 font-medium mt-2")
        for account in accounts:
            with ui.row().classes("items-center gap-2 w-full no-wrap"):
                if account.user:
                    ui.label(f"{account.provider}: {account.user}").classes(
                        "text-body2 grow truncate"
                    )
                    ui.button(
                        "Sign out",
                        on_click=lambda a=account: self.sign_out(a.type, a.provider),
                    ).props("flat dense no-caps")
                else:
                    ui.label(
                        f"{account.provider}: not signed in on this computer; "
                        "asked at the next download"
                    ).classes("text-body2 text-grey")
        ui.label(
            "Sign-ins belong to this computer and work for every project."
        ).classes("text-caption text-grey")

    def sign_out(self, type: str, provider: str) -> None:
        self.library().sign_out(type)
        ui.notify(f"Signed out of {provider}")
        self.show()
