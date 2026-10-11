"""The main menu behind ☰, at the top left of the player and of the project screen
(docs/project-screen.md#project-menu): the projects with their song counts (✓ the current one,
click another to switch; a search field when there are many), New project…; Project settings…,
Export… / Import…, Delete project…; then the player's own items (Player settings…, Keyboard
shortcuts, Dark mode), drawn by the window's frame (layout.py).

Switching saves the practice memory, stops playback, makes the other project current and builds
the page again (app.py loads the current project per page); the player opens that project's last
song, paused, and the project screen opens again if the switch came from there."""

from collections.abc import Callable
from typing import Any

from chips import ask_text, close
from jobs import Jobs
from nicegui import ui
from player import Player
from state import save_state

from downtempo.errors import UserError
from downtempo.events import count, size
from downtempo.projects import ProjectInfo, Workspace

MAX_SHOWN = 24  # characters of a name in the header; the full name in the tooltip
SEARCH_FROM = 9  # projects; from this many on the menu has a search field


def short(name: str) -> str:
    return name if len(name) <= MAX_SHOWN else name[: MAX_SHOWN - 1] + "…"


def show_matching(items: dict[str, ui.menu_item], text: str) -> None:
    for name, item in items.items():
        item.set_visibility(text.casefold() in name.casefold())


class MainMenu:
    def __init__(
        self,
        workspace: Workspace,
        player: Player,
        jobs: Jobs,
        rebuild: Callable[[str], None],
        settings_file: Callable[[], Any] | None = None,
    ) -> None:
        """`rebuild(screen_tab)` builds the page again for the current project ("" = practice);
        `settings_file` opens the settings file's Export / Import (T67), when there is one."""
        self.workspace, self.player, self.jobs = workspace, player, jobs
        self.rebuild, self.settings_file = rebuild, settings_file
        self.project_settings: Callable[[], Any] = lambda: None  # set by the page
        self.player_items: Callable[[], None] = lambda: (
            None
        )  # set by the page (layout.py)
        self.from_screen: Callable[[], str] = lambda: (
            ""
        )  # the open tab, set by the screen

    def button(self) -> ui.button:
        """☰ with the menu under it, filled when it opens (it reads every project's folder)."""
        button = ui.button(icon="menu").props("flat round")
        button.tooltip("Menu: projects, settings, shortcuts")
        with button, ui.menu() as menu:
            pass
        menu.on_value_change(lambda e: self.fill(menu) if e.value else None)
        return button

    def fill(self, menu: ui.menu) -> None:
        menu.clear()
        current = self.workspace.current_id()
        busy = self.jobs.running
        projects = self.workspace.projects()
        with menu, ui.column().classes("gap-0 min-w-[280px]"):
            ui.label("Projects").classes("text-caption text-grey px-4 pt-2")
            search = None
            if len(projects) >= SEARCH_FROM:
                search = (
                    ui.input(placeholder="Search projects")
                    .props("dense outlined autofocus clearable")
                    .classes("px-4 pb-1 w-full")
                )
            items = {
                p.name: self.project_item(p, p.id == current, busy) for p in projects
            }
            if search:
                search.on_value_change(lambda e: show_matching(items, e.value or ""))
            ui.menu_item("New project…", on_click=self.new)
            ui.separator()
            ui.menu_item("Project settings…", on_click=self.project_settings)
            if self.settings_file:
                ui.menu_item("Export… / Import…", on_click=self.settings_file)
            delete = ui.menu_item("Delete project…", on_click=self.delete)
            if busy:
                delete.disable()
            ui.separator()
            self.player_items()

    def project_item(
        self, project: ProjectInfo, mine: bool, busy: bool
    ) -> ui.menu_item:
        item = ui.menu_item(on_click=lambda: self.switch(project.id))
        with item, ui.row().classes("w-full items-center gap-2 no-wrap"):
            ui.icon("check" if mine else "", size="18px").classes("text-primary w-5")
            ui.label(project.name).classes("grow truncate" + (" font-medium" * mine))
            ui.label(count(project.songs, "song")).classes("text-caption text-grey")
        if not mine and busy:
            item.disable()
            item.tooltip("Wait for the download to finish, or cancel it")
        return item

    # ------------------------------------------------------------ switching

    def leave(self) -> None:
        """The page is about to be built again: save, stop, and keep this page's player from
        writing the practice memory afterwards (it would go to the other project)."""
        self.player.engine.pause()
        self.player.save_position()
        save_state(self.player.state)
        self.player.retired = True

    def switch(self, id: str) -> None:
        if id == self.workspace.current_id():
            return
        if self.jobs.running:
            ui.notify("Wait for the download to finish, or cancel it.")
            return
        self.leave()
        self.workspace.use(id)
        self.rebuild(self.from_screen())

    async def new(self) -> None:
        answer = await ask_text("New project", self.workspace.free_name("New project"))
        if not answer:
            return
        self.leave()
        try:
            self.workspace.create(answer[0])
        except UserError as error:
            self.player.retired = False
            ui.notify(f"{error.message} {error.hint}".strip(), type="negative")
            return
        self.rebuild("")  # the first start: paste a link

    async def delete(self) -> None:
        id = self.workspace.current_id()
        if not id:
            return
        library = self.workspace.library(id)
        files = [p for p in library.downloads.rglob("*") if p.is_file()]
        bytes = sum(p.stat().st_size for p in files)
        with ui.dialog() as dialog, ui.card().classes("gap-3 max-w-[520px]"):
            ui.label(f"Delete “{library.name()}”?").classes("text-h6")
            ui.label(
                f"Its {count(len(files), 'downloaded file')} ({size(bytes)}) go, and its "
                "tempo and loops too. The shared folders on the server aren't touched."
            ).classes("text-body2")
            with ui.row().classes("self-end"):
                ui.button("Cancel", on_click=lambda: dialog.submit(False)).props(
                    "flat no-caps autofocus"
                )
                ui.button("Delete", on_click=lambda: dialog.submit(True)).props(
                    "unelevated no-caps color=negative"
                )
        sure = await dialog
        close(dialog)
        if not sure:
            return
        self.player.engine.pause()
        self.player.retired = True  # its practice memory goes with the project
        try:
            self.workspace.delete(id)
        except UserError as error:
            self.player.retired = False
            ui.notify(error.message, type="negative")
            return
        self.workspace.current()  # the first one left, or a new empty one
        self.rebuild("")
