"""The project screen: a full-screen view of the current project's song files and the unknown files
(in no song yet; "To sort" in the plan and the code), opened from "Edit song list" in the song
list (docs/project-screen.md). This file is the frame: header
(back, project name, sources, Undo / Redo; no ☰: ← Practice is the way out), the two tabs, its keys, and running one sorting
operation; the tabs are `sort_tab.py` and `songs_tab.py`, the sources `sources_bar.py`. While a
download runs, the tabs fill in as files arrive.

Every change is a `library.sorting` operation, saved at once; `songs.json` follows, and the player's
song list reloads when the screen closes.
"""

import time
from collections.abc import Callable
from pathlib import PurePosixPath
from typing import Any

from chips import CSS, DRAG_JS, ask_text
from common import event_arg
from main_menu import MainMenu, short
from nicegui import events, ui
from player import Player
from previews import PREVIEW_JS, show_sheet
from song_box import SongBox
from songs_tab import SongsTab
from sort_tab import SortTab
from sources_bar import SourcesBar
from updates import Updates

from downtempo.errors import UserError
from downtempo.shapes import FileRef, Grouping

REFILL_EVERY = 1.5  # seconds between refreshes while files arrive


class ProjectScreen:
    def __init__(
        self,
        player: Player,
        closed: Callable[[], Any],
        updates: Updates,
        add_folder: Callable[[], None],
        menu: MainMenu,
        settings: Callable[[str], None],
    ) -> None:
        """`settings(folder)` opens Project settings (at a folder, or at the top for "")."""
        self.player = player
        self.closed = closed  # the player reloads its songs
        self.grouping: Grouping | None = None
        self.new_files: set[str] = set()
        self.gone: set[str] = set()  # file ids the last check didn't find on the server
        self.refilled = 0.0  # when the tabs were last refreshed for arriving files
        ui.add_css(CSS)
        ui.add_head_html(f"<script>{DRAG_JS}</script>")
        ui.add_head_html(PREVIEW_JS)
        ui.on("screen_drop", self.drop)
        with (
            ui.dialog().props(
                "maximized transition-show=none transition-hide=none"
            ) as self.dialog,
            ui.card().classes("w-full h-full p-0 gap-0 no-wrap"),
        ):
            with ui.row().classes(
                "app-header w-full items-center gap-2 px-3 py-1 min-h-[52px] no-wrap"
            ):
                ui.button(
                    "Practice", icon="arrow_back", on_click=self.dialog.close
                ).props("flat no-caps").tooltip("Back to practising (Esc)")
                self.name = ui.label("").classes("text-h6 whitespace-nowrap pl-2")
                with self.name:
                    self.name_tip = ui.tooltip("")
                menu.from_screen = lambda: self.tabs.value if self.is_open else ""
                self.sources = ui.row().classes(
                    "gap-1 items-center no-wrap min-w-0 overflow-hidden"
                )
                ui.space()
                self.undo_button = ui.button(
                    "Undo", icon="undo", on_click=self.undo
                ).props("flat no-caps")
                self.undo_button.tooltip("Undo (Ctrl+Z)")
                self.redo_button = ui.button(
                    "Redo", icon="redo", on_click=self.redo
                ).props("flat no-caps")
                self.redo_button.tooltip("Redo (Ctrl+Shift+Z)")
            with (
                ui.tabs()
                .props("dense no-caps align=left")
                .classes("w-full px-3") as self.tabs
            ):
                self.sort_label = ui.tab("sort", "Unknown files")
                ui.tab("songs", "Song files")
            with ui.tab_panels(self.tabs, value="sort").classes("w-full grow min-h-0"):
                with ui.tab_panel("sort").classes("p-0 h-full"):
                    self.sort_tab = SortTab(self)
                with ui.tab_panel("songs").classes("p-0 h-full"):
                    self.songs_tab = SongsTab(self)
        self.dialog.on_value_change(self.on_open_close)
        self.song_box = SongBox(self)
        self.sources_bar = SourcesBar(
            self.sources,
            lambda: self.library,
            updates,
            add_folder,
            settings,
            lambda: self.is_open,
        )
        updates.arrived.append(self.refill)
        updates.finished.append(lambda result: self.refresh() if self.is_open else None)

    @property
    def library(self):
        return self.player.library

    @property
    def is_open(self) -> bool:
        return self.dialog.value

    def open(self, tab: str = "") -> None:
        self.player.engine.pause()  # sorting is desk work; nothing plays on by surprise later
        self.refresh()
        self.tabs.value = tab or ("sort" if self.waiting() else "songs")
        self.dialog.open()

    def refill(self) -> None:
        """A file arrived: show it, at most every REFILL_EVERY seconds."""
        if self.is_open and time.monotonic() - self.refilled > REFILL_EVERY:
            self.refilled = time.monotonic()
            self.refresh()

    async def on_open_close(self, e: events.ValueChangeEventArguments) -> None:
        if not e.value:
            ui.run_javascript("dtPreview.stop()")
            self.songs_tab.selected.clear()
            await self.closed()

    def waiting(self) -> int:
        """Files in To sort (suggested songs and loose files)."""
        g = self.grouping
        return sum(len(s.files) for s in g.suggestions) + len(g.loose) if g else 0

    # ------------------------------------------------------------ showing

    def refresh(self) -> None:
        self.grouping = self.library.sorting.grouping()
        self.new_files = set(self.library.new_marks())
        self.gone = self.library.gone()
        self.name.text = short(self.library.name())
        self.name_tip.text = self.library.name()
        self.sources_bar.show()
        waiting = self.waiting()
        self.sort_label.props(
            f'label="Unknown files ({waiting})"' if waiting else 'label="Unknown files"'
        )
        self.undo_button.set_enabled(bool(self.library.sorting.undo_stack))
        self.redo_button.set_enabled(bool(self.library.sorting.redo_stack))
        self.sort_tab.show()
        self.songs_tab.show()

    def titles(self) -> dict[str, str]:
        return {s.id: s.title for s in self.grouping.songs} if self.grouping else {}

    # ------------------------------------------------------------ changing

    def do(self, action: Callable[[], Any], done: str = "") -> bool:
        """Run one sorting operation; a `UserError` is shown, not raised. The refresh deletes the
        clicked widget, so what follows runs in the dialog's context."""
        with self.dialog:
            try:
                action()
            except UserError as error:
                ui.notify(f"{error.message} {error.hint}".strip(), type="negative")
                return False
            self.songs_tab.selected.clear()
            self.refresh()
            if done:
                ui.notify(done)
            offers = self.library.sorting.offers
            if offers and self.tabs.value != "songs":
                ui.notify(f"{offers[0].text} (see Song files)", multi_line=True)
        return True

    async def drop(self, e: events.GenericEventArguments) -> None:
        """A drop from drag.js: files or a song title, onto a song or a drop zone."""
        if not self.is_open:
            return
        d, sorting = event_arg(e), self.library.sorting
        titles = self.titles()
        to = str(d.get("to", ""))
        song = to.removeprefix("song:") if to.startswith("song:") else ""
        if d.get("kind") == "song":
            gone = str(d.get("song", ""))
            if song and gone in titles and song in titles:
                self.do(
                    lambda: sorting.merge(gone, song),
                    f"Merged “{titles[gone]}” into “{titles[song]}” (Ctrl+Z undoes)",
                )
            return
        pairs = [(str(f), str(file)) for f, file in d.get("files", [])]
        files = sorted({file for _, file in pairs})
        if not files:
            return
        n = f"{len(files)} file{'s' * (len(files) != 1)}"
        match to:
            case "new":
                stem = PurePosixPath(files[0].partition(":")[2]).stem
                answer = await ask_text("New song", stem)
                if answer:
                    self.do(lambda: sorting.new_song(files, answer[0]))
            case "notsong":
                self.do(lambda: sorting.not_song(files), f"{n} set aside")
            case "tosort":
                self.do(
                    lambda: sorting.back_to_sort(files), f"{n} back to unknown files"
                )
            case _ if to.startswith("sugg:") and to[5:].isdigit():
                self.sort_tab.merge(int(to[5:]), files)
            case _ if song not in titles:
                return
            case _ if d.get("copy"):
                self.do(
                    lambda: sorting.also_add(files, song),
                    f"{n} also in “{titles[song]}”",
                )
            case _ if all(f == song for f, _ in pairs):
                # inside its own song: onto another chip makes it the default
                onto = str(d.get("onto", ""))
                if len(files) == 1 and onto and onto != files[0]:
                    self.do(lambda: sorting.make_first(song, files[0]))
            case _:
                moved = [(f, file) for f, file in pairs if f != song]
                self.do(
                    lambda: sorting.move_from(moved, song),
                    f"Moved {n} to “{titles[song]}”",
                )

    async def show_sheet(self, file: FileRef) -> None:
        with self.dialog:
            await show_sheet(self.library, file)

    def skip_folder(self, source: str, folder: str) -> None:
        """Its files hide and aren't downloaded any more; the source's Skipped folders undo it."""
        try:
            self.library.skip_folder(source, folder)
        except UserError as error:
            ui.notify(error.message, type="negative")
            return
        self.library.rebuild()
        self.refresh()
        ui.notify(
            f"Skipped “{PurePosixPath(folder).name}”: hidden and not downloaded "
            f"(Project settings → Skipped folders… brings it back)",
            multi_line=True,
        )

    def undo(self) -> None:
        if not self.library.sorting.undo():
            ui.notify("Nothing to undo")
        self.refresh()

    def redo(self) -> None:
        if not self.library.sorting.redo():
            ui.notify("Nothing to redo")
        self.refresh()

    async def on_key(self, e: events.KeyEventArguments) -> None:
        """Keys while the screen is open (the player's own keys are off)."""
        if not e.action.keydown or e.action.repeat:
            return
        key = e.key.name.lower() if len(e.key.name) == 1 else e.key.name
        ctrl = e.modifiers.ctrl or e.modifiers.meta
        match key:
            case "z" if ctrl and e.modifiers.shift:
                self.redo()
            case "z" if ctrl:
                self.undo()
            case "y" if ctrl:
                self.redo()
            case _ if ctrl or e.modifiers.alt:
                return
            case "m" if self.tabs.value == "songs":
                await self.songs_tab.move_selected()
            case "n" if self.tabs.value == "songs":
                await self.songs_tab.new_song_from_selected()
            case "Delete" if self.tabs.value == "songs":
                self.songs_tab.not_song_selected()
            case "F2" if self.tabs.value == "songs":
                songs = {song for song, _ in self.songs_tab.selected}
                if len(songs) == 1:
                    self.song_box.open(songs.pop())
                else:
                    ui.notify("Select a file of the song first, or click its title")
