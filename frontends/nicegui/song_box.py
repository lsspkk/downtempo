"""The song edit box (✎ on a title, or `F2`): the title, the also-called names and the linked 📁
folders, which are the song's magnets, with a live "matches n files"; Merge into… and Delete song
(docs/project-screen.md#song-edit-box). Every change is one sorting operation, saved at once and
undoable; removing a name or folder never moves files already in the song."""

from typing import TYPE_CHECKING

from chips import pick_song
from nicegui import ui

from downtempo.shapes import GroupedSong

if TYPE_CHECKING:
    from project_screen import ProjectScreen


def folder_text(folder: str) -> str:
    """`Band share:Harbour Waltz` → `Band share / Harbour Waltz`."""
    source, _, path = folder.partition(":")
    return f"{source} / {path}" if path else f"{source} (top level)"


class SongBox:
    def __init__(self, screen: "ProjectScreen") -> None:
        self.screen = screen
        self.id = ""
        with (
            ui.dialog() as self.dialog,
            ui.card().classes("w-[640px] max-w-[95vw] gap-3"),
        ):
            self.body = ui.column().classes("w-full gap-3")
        self.dialog.on("hide", self.hidden)

    @property
    def sorting(self):
        return self.screen.library.sorting

    def song(self) -> GroupedSong | None:
        grouping = self.screen.grouping
        return next((s for s in grouping.songs if s.id == self.id), None)

    def open(self, song_id: str) -> None:
        self.id = song_id
        self.show()
        self.dialog.open()

    def hidden(self) -> None:
        self.id = ""

    def do(self, action, done: str = "") -> None:
        """One operation through the screen (refresh, errors), then this box again."""
        if self.screen.do(action, done) and self.id:
            self.show()

    def show(self) -> None:
        song = self.song()
        self.body.clear()
        if song is None:
            self.dialog.close()
            return
        with self.body:
            ui.label("Song").classes("text-h6")
            with ui.row().classes("w-full items-center gap-2 no-wrap"):
                ui.label("Title").classes("w-28 text-grey")
                title = (
                    ui.input(value=song.title)
                    .props("dense outlined autofocus")
                    .classes("grow")
                )
            with ui.row().classes("w-full items-center gap-2 no-wrap") as keep_row:
                ui.label("").classes("w-28")
                keep = ui.checkbox(f"Keep “{song.title}” as also called", value=True)
            keep_row.set_visibility(False)

            with ui.row().classes("w-full items-start gap-2 no-wrap"):
                ui.label("Also called").classes("w-28 text-grey pt-1")
                with ui.row().classes("grow gap-1 items-center"):
                    for name in song.also:
                        ui.chip(
                            name,
                            removable=True,
                            on_value_change=lambda e, n=name: self.do(
                                lambda: self.sorting.alias(song.id, remove=n)
                            ),
                        ).props("dense outline").tooltip(
                            "× forgets the name; its files stay in the song"
                        )
                    add = (
                        ui.input(placeholder="+ name")
                        .props("dense borderless")
                        .classes("w-40")
                    )
                    add.tooltip("Another name its files go by (Enter adds it)")
            with ui.row().classes("w-full items-center gap-2 no-wrap"):
                ui.label("").classes("w-28")
                reach = ui.label("").classes("text-caption text-grey")

            with ui.row().classes("w-full items-start gap-2 no-wrap"):
                ui.label("Folders").classes("w-28 text-grey pt-1")
                with ui.row().classes("grow gap-1 items-center"):
                    for folder in song.folders:
                        ui.chip(
                            "📁 " + folder_text(folder),
                            removable=True,
                            on_value_change=lambda e, f=folder: self.do(
                                lambda: self.sorting.unlink_folder(song.id, f)
                            ),
                        ).props("dense outline").tooltip(
                            "New files in this folder join the song; × unlinks it"
                        )
                    linked = {f.casefold() for f in song.folders}
                    choices = {
                        f: folder_text(f)
                        for f in self.sorting.folders()
                        if f.casefold() not in linked
                    }
                    ui.select(
                        choices,
                        label="+ folder",
                        with_input=True,
                        on_change=lambda e: (
                            e.value
                            and self.do(
                                lambda: self.sorting.link_folder(song.id, e.value)
                            )
                        ),
                    ).props("dense borderless options-dense").classes("w-56").tooltip(
                        "Link a folder: its files with no song join this one"
                    )

            with ui.row().classes("w-full items-center gap-2 pt-2"):
                ui.button(
                    "Merge into…", icon="call_merge", on_click=lambda: self.merge(song)
                ).props("flat no-caps")
                ui.button(
                    "Delete song",
                    icon="delete_outline",
                    on_click=lambda: self.delete(song),
                ).props("flat no-caps color=grey")
                ui.space()
                ui.button("Done", on_click=lambda: self.done(song, title, keep)).props(
                    "unelevated no-caps"
                )

        def count() -> None:
            names = [title.value or "", *song.also, add.value or ""]
            n = self.sorting.reach([x for x in names if x.strip()], list(song.folders))
            reach.text = f"These names and folders match {n} file{'s' * (n != 1)}"

        def title_changed() -> None:
            keep_row.set_visibility(
                (title.value or "").strip().casefold() != song.title.casefold()
            )
            count()

        def add_name() -> None:
            text = (add.value or "").strip()
            if text:
                self.do(lambda: self.sorting.alias(song.id, add=text))

        title.on_value_change(title_changed)
        title.on("keydown.enter", lambda: self.done(song, title, keep))
        add.on_value_change(count)
        add.on("keydown.enter", add_name)
        count()

    def done(self, song: GroupedSong, title: ui.input, keep: ui.checkbox) -> None:
        text = (title.value or "").strip()
        if text and text != song.title:
            self.do(
                lambda: self.sorting.rename(song.id, text, keep_old=bool(keep.value))
            )
        self.dialog.close()

    async def merge(self, song: GroupedSong) -> None:
        others = {id: t for id, t in self.screen.titles().items() if id != song.id}
        picked = await pick_song(others, f"Merge “{song.title}” into", allow_new=False)
        if picked and picked[0]:
            self.dialog.close()
            self.screen.do(
                lambda: self.sorting.merge(song.id, picked[0]),
                f"Merged into {others[picked[0]]} (Ctrl+Z undoes)",
            )

    def delete(self, song: GroupedSong) -> None:
        self.dialog.close()
        self.screen.do(
            lambda: self.sorting.delete(song.id),
            f"Deleted “{song.title}”: its files are back in Unknown files (Ctrl+Z undoes)",
        )
