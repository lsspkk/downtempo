"""Python player: NiceGUI in a native window (pywebview), sound stretched and played in Python.
This file only puts the page together; each part is its own module (docs/architecture.md).

Run: `uv run python frontends/nicegui/app.py`. Features and shortcuts: docs/player.md.
"""

import sys

import keys
from common import BLUR_AFTER_CLICK, CSS, LOOP_COLOR
from controls import Controls
from engine import Engine
from layout import Shell
from loop_editor import LoopEditor
from nicegui import app, ui
from player import Player, song_key
from sheet_pane import SheetPane
from sheets import CACHE_DIR
from song_list import SongList
from state import load_state, save_state

from downtempo.catalog import read_catalog

# Module level, not under the main guard: the native window runs in its own process (NiceGUI docs).
# Qt comes as wheels (pyproject); GTK would need the system's PyGObject.
if sys.platform == "linux":
    app.native.start_args["gui"] = "qt"

engine = Engine()
# One engine, so one page drives it: the newest (a reload is a new page while the old one lingers).
owner = {"client": ""}
state = load_state()
CACHE_DIR.mkdir(parents=True, exist_ok=True)
app.add_static_files("/pages", CACHE_DIR)


def root() -> None:
    ui.add_head_html(BLUR_AFTER_CLICK)
    ui.add_css(CSS)
    ui.colors(primary="#4f5bd5", accent=LOOP_COLOR)
    ui.query(".nicegui-content").classes("p-0 gap-0")
    player = Player(engine, state, read_catalog())
    me = owner["client"] = ui.context.client.id

    shell = Shell(player)
    songs = SongList(shell.drawer, player)
    if not player.songs:
        with ui.column().classes("w-full items-center mt-24 gap-2"):
            ui.icon("library_music", size="64px").classes("text-grey")
            ui.label("No songs yet").classes("text-h6")
            ui.label("Download and build the song list, then restart the player:")
            ui.code("uv run downtempo download\nuv run downtempo catalog").classes(
                "w-96"
            )
        return

    editor = LoopEditor(player)
    sheet_column = shell.build_grid()
    controls = Controls(shell, player, editor.open)
    sheet = SheetPane(sheet_column, shell, player)
    keys.install(
        lambda: owner["client"] == me, player, shell, songs, controls, sheet, editor
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
    save_state(state)


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
