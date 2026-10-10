"""The song list in the left drawer: search, the songs, next and previous song."""

from nicegui import ui
from player import Player

from downtempo.catalog import Song


class SongList:
    def __init__(self, drawer: ui.left_drawer, player: Player) -> None:
        self.player = player
        with drawer:
            self.search = (
                ui.input(placeholder="Search songs  ( / )", on_change=self.show)
                .props("dense outlined clearable")
                .classes("w-full")
            )
            self.list = ui.list().props("dense").classes("w-full")
        player.on("selection", lambda new_song: new_song and self.show())

    def filtered(self) -> list[Song]:
        text = (self.search.value or "").casefold()
        return [
            x
            for x in self.player.songs
            if text in f"{x['title']} {x['collection']}".casefold()
        ]

    async def step(self, offset: int) -> None:
        await self.player.step_song(self.filtered(), offset)

    def focus_search(self) -> None:
        self.search.run_method("focus")

    def show(self) -> None:
        songs, player = self.player.songs, self.player
        many_collections = len({x["collection"] for x in songs}) > 1
        self.list.clear()
        shown = self.filtered()
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
                    with ui.item_section():
                        ui.item_label(song["title"]).classes(
                            "font-medium" if current else ""
                        )
                        if many_collections:
                            ui.item_label(song["collection"]).props("caption")
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
