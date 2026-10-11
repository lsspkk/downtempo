"""Python player: NiceGUI in a native window (pywebview), sound stretched and played in Python.
This file only puts the page together; each part is its own module (docs/architecture.md).

Run: `uv run python frontends/nicegui/app.py`. Features and shortcuts: docs/player.md.
"""

import sys
from typing import Any

import keys
import previews
from add_folder import AddFolder
from change_link import ChangeLink
from common import BLUR_AFTER_CLICK, CSS, LOOP_COLOR
from controls import Controls
from engine import Engine
from folder_actions import FolderActions
from jobs import Jobs
from layout import Shell
from loop_editor import LoopEditor
from main_menu import MainMenu
from nicegui import app, ui
from player import Player, song_key
from project_panel import ProjectPanel
from project_screen import ProjectScreen
from project_settings import ProjectSettings
from settings_file import SettingsFile
from sheet_pane import SheetPane
from sheets import CACHE_DIR
from sign_in import SignInCard
from song_list import SongList
from state import load_state, save_state
from updates import Updates
from welcome import welcome

from downtempo.config import DATA_DIR
from downtempo.library import Library, UpdateResult
from downtempo.projects import Workspace

# Module level, not under the main guard: the native window runs in its own process (NiceGUI docs).
# Qt comes as wheels (pyproject); GTK would need the system's PyGObject.
if sys.platform == "linux":
    app.native.start_args["gui"] = "qt"

engine = Engine()
# One engine, so one page drives it: the newest (a reload is a new page while the old one lingers).
owner = {"client": ""}
workspace = Workspace(DATA_DIR)  # moves data from before projects in, once
# The current project's Library and remembered state; a project switch builds the page again and
# `current()` loads the other one. "screen": the project screen's tab to open after a rebuild.
session: dict[str, Any] = {"screen": ""}


def current() -> tuple[Library, dict[str, Any]]:
    library = workspace.current()
    if session.get("library") is None or session["library"].root != library.root:
        session["library"] = library
        session["state"] = load_state(workspace.app_file, library.practice_file)
    return session["library"], session["state"]


current()
CACHE_DIR.mkdir(parents=True, exist_ok=True)
app.add_static_files("/pages", CACHE_DIR)
previews.serve(workspace.current)  # the current project's files only, for ▶ and 👁


def root() -> None:
    ui.add_head_html(BLUR_AFTER_CLICK)
    ui.add_css(CSS)
    ui.colors(primary="#4f5bd5", accent=LOOP_COLOR)
    ui.query(".nicegui-content").classes("p-0 gap-0")
    library, state = current()
    player = Player(engine, state, library)
    me = owner["client"] = ui.context.client.id

    shell = Shell(player)
    jobs = Jobs()

    def rebuild(screen_tab: str) -> None:
        """The page again, with the project read from disk (it was just saved, then maybe
        switched or renamed: the memory here may hold old paths)."""
        session["screen"] = screen_tab
        session["library"] = None
        ui.navigate.reload()

    def imported(new_project: bool, download: bool) -> None:
        if new_project:  # it's the current project now
            menu.leave()
            session["download"] = download
            rebuild("")
        elif download:
            updates.start()

    settings_file = SettingsFile(workspace, lambda: player.library, imported)
    menu = MainMenu(workspace, player, jobs, rebuild, settings_file.open)
    menu.player_items = shell.menu_items
    with shell.menu_slot:
        menu.button()
    updates = Updates(player, jobs)
    with shell.drawer:
        panel = ProjectPanel(
            lambda: player.library, updates, lambda f: project_settings.open(f)
        )
    songs = SongList(shell.drawer, player)
    SignInCard(jobs)
    had_songs = bool(player.songs)

    async def refresh_songs() -> None:
        if not had_songs and player.library.songs():
            ui.navigate.reload()  # the first songs: build the whole page
            return
        await player.reload_songs()
        songs.show()
        show_waiting()

    async def after_download(result: UpdateResult) -> None:
        if (
            not screen.is_open
        ):  # else when the screen closes (sorting goes on meanwhile)
            await refresh_songs()

    def name_project(name: str) -> None:
        if id := workspace.current_id():
            workspace.rename(id, name)
            panel.show_name()

    screen = ProjectScreen(
        player,
        refresh_songs,
        updates,
        lambda: adder.open(),
        menu,
        lambda f: project_settings.open(f),
    )
    adder = AddFolder(
        player, jobs, updates, lambda _: screen.open("sort"), name_project
    )
    updates.add_folder = adder.open
    updates.finished.append(after_download)

    def files_changed() -> None:
        """A folder was removed, skipped, freed or got a new link."""
        if project_settings.dialog.value:
            project_settings.show()
        panel.show()
        if screen.is_open:
            screen.refresh()
        else:
            ui.timer(0, refresh_songs, once=True)

    def renamed() -> None:
        panel.show_name()
        if screen.is_open:
            screen.refresh()

    project_settings = ProjectSettings(
        workspace,
        lambda: player.library,
        updates,
        FolderActions(lambda: player.library, jobs, menu, files_changed),
        ChangeLink(player, jobs, updates, files_changed),
        adder.open,
        renamed,
    )
    menu.project_settings = project_settings.open
    with shell.drawer:
        sort_button = (
            ui.button(
                "Edit song list", icon="edit_note", on_click=lambda: screen.open()
            )
            .props("flat no-caps align=left")
            .classes("w-full flex-none border-t")
        )
        sort_button.tooltip(
            "Which files make up each song, the files not in any song yet, and your shared folders"
        )

    def show_waiting() -> None:
        screen.grouping = player.library.sorting.grouping()
        waiting = screen.waiting()
        sort_button.text = (
            f"Edit song list ({waiting} unknown)" if waiting else "Edit song list"
        )

    show_waiting()
    if tab := session["screen"]:  # rebuilt for another project from the screen
        session["screen"] = ""
        ui.timer(0.2, lambda: screen.open(tab), once=True)
    if session.pop("download", False):  # a settings file was imported as a new project
        ui.timer(0.5, lambda: updates.start(), once=True)
    if not player.songs:
        welcome(player.library, adder.open, screen.open, updates.start)
        return

    editor = LoopEditor(player)
    sheet_column = shell.build_grid()
    controls = Controls(shell, player, editor.open)
    sheet = SheetPane(sheet_column, shell, player, editor.open)
    keys.install(
        lambda: owner["client"] == me,
        player,
        shell,
        songs,
        controls,
        sheet,
        editor,
        screen,
    )
    shell.set_controls(shell.view["controls"])
    songs.show()

    def tick() -> None:
        if owner["client"] != me:
            taken_over()
            return
        player.tick()

    def taken_over() -> None:
        ticker.cancel()
        player.audio = ""  # nothing here touches the engine any more
        with ui.dialog().props("persistent") as dialog, ui.card():
            ui.label("The player was opened in another tab or window.")
            ui.label("Reload this page to use it here.").classes("text-grey")
        dialog.open()

    ticker = ui.timer(0.1, tick)
    by_key = {song_key(x): x for x in player.songs}
    first = by_key.get(state.get("last_song", ""), player.songs[0])

    async def start() -> None:
        sheet.watch()
        await player.open_song(first)

    ui.timer(0, start, once=True)


def shutdown() -> None:
    engine.close()
    save_state(session["state"])


def main() -> None:
    app.on_shutdown(shutdown)
    if "--browser" in sys.argv:  # a normal browser tab instead of the native window
        ui.run(root, title="Downtempo", reload=False, show=False, port=8765)
    else:
        ui.run(
            root, title="Downtempo", reload=False, native=True, window_size=(1400, 900)
        )


if __name__ in {"__main__", "__mp_main__"}:
    main()
