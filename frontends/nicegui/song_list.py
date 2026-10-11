"""The song list in the left drawer: search, the songs (the only part of the drawer that
scrolls), next and previous song."""

from nicegui import ui
from player import Player

from downtempo.catalog import Song

CSS = """
.new-dot { width: 8px; height: 8px; border-radius: 50%; background: #4f5bd5; flex: none; }
.body--dark .new-dot { background: #8f98ff; }
"""


class SongList:
    def __init__(self, drawer: ui.left_drawer, player: Player) -> None:
        self.player = player
        ui.add_css(CSS)
        with drawer:
            self.search = (
                ui.input(placeholder="Search songs  ( / )", on_change=self.show)
                .props("dense outlined clearable")
                .classes("w-full flex-none")
            )
            with ui.element("div").classes("w-full grow min-h-0 overflow-y-auto"):
                self.list = ui.list().props("dense").classes("w-full")
        player.on("selection", lambda new_song: new_song and self.show())

    def filtered(self) -> list[Song]:
        text = (self.search.value or "").casefold()
        return [x for x in self.player.songs if text in x["title"].casefold()]

    async def step(self, offset: int) -> None:
        await self.player.step_song(self.filtered(), offset)

    def focus_search(self) -> None:
        self.search.run_method("focus")

    def show(self) -> None:
        player = self.player
        self.list.clear()
        shown = self.filtered()
        new = player.library.songs_with_new()
        with self.list:
            if not shown:
                ui.label("No songs match").classes("p-4 text-grey")
            for song in shown:
                current = song is player.song
                with (
                    ui.item(on_click=lambda song=song: player.open_song(song))
                    .props("clickable")
                    .classes(
                        "rounded-borders"
                        + (" song-active text-primary" if current else "")
                    )
                ):
                    with (
                        ui.item_section(),
                        ui.row().classes("items-center gap-1 no-wrap"),
                    ):
                        ui.item_label(song["title"]).classes(
                            "font-medium" if current else ""
                        )
                        if song["id"] in new:
                            ui.element("span").classes("new-dot").tooltip(
                                "New files since you last opened it"
                            )
                    with (
                        ui.item_section().props("side"),
                        ui.row().classes("gap-1 items-center"),
                    ):
                        if len(song["audio"]) > 1:
                            ui.badge(str(len(song["audio"]))).props("outline").tooltip(
                                "recordings"
                            )
                        if song["pdf"]:
                            ui.icon("description", size="18px").classes("text-grey")
                        if not song["audio"]:
                            ui.icon("volume_off", size="18px").classes(
                                "text-grey"
                            ).tooltip("no recording")
