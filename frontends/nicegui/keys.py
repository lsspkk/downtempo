"""Keyboard shortcuts: the help dialog's table and the key handler that calls the page's parts.

↑/↓, PgUp/PgDn and Home/End scroll the sheet in the page itself (sheet_pane.js), not here.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from nicegui import events, ui

if TYPE_CHECKING:  # the parts import this module for help_dialog
    from controls import Controls
    from layout import Shell
    from loop_editor import LoopEditor
    from player import Player
    from sheet_pane import SheetPane
    from song_list import SongList

SHORTCUTS = {
    "Playing": [
        ("Space / K", "Play / pause"),
        ("← / →", "Tempo slower / faster"),
        (", / .", "Back / forward 5 s"),
        ("J / L", "Back / forward 10 s"),
        ("0", "To start (loop start when looping)"),
        ("1 … 9", "Jump to 10 % … 90 %"),
        ("A / B", "Loop start / end here"),
        ("R", "Loop on / off"),
        ("C", "Clear loop"),
        ("S", "Save loop"),
        ("T / Shift+T", "Next / previous recording"),
        ("M", "Mute"),
        ("E", "Loop editor: zoom in, select exactly"),
        ("Shift+Space", "Hear the loop end (editor)"),
    ],
    "Sheet and view": [
        ("↑ / ↓", "Scroll the sheet"),
        ("PgUp / PgDn", "A screen or page (footswitch)"),
        ("Home / End", "Sheet top / bottom"),
        ("+ / −", "Sheet zoom"),
        ("W / H", "Fit width / fit page"),
        ("O", "Rotate the sheet"),
        ("F", "Full screen (Esc back)"),
        ("V", "Controls: full, simple, none"),
        ("Q", "Song list"),
        ("N / P", "Next / previous song"),
        ("/", "Search songs"),
        ("?", "This help"),
    ],
}
REPEATABLE = {"ArrowLeft", "ArrowRight", "+", "=", "-", ",", "."}


def help_dialog() -> ui.dialog:
    with ui.dialog() as dialog, ui.card().classes("max-w-none"):
        ui.label("Keyboard shortcuts").classes("text-h6")
        # two groups side by side, so the list fits a 720 px high screen
        with ui.row().classes("gap-10 no-wrap items-start"):
            for group, shortcuts in SHORTCUTS.items():
                with ui.column().classes("gap-1"):
                    ui.label(group).classes("text-subtitle2 text-primary")
                    with ui.grid(columns="auto 1fr").classes("gap-x-5 gap-y-1"):
                        for keys, action in shortcuts:
                            ui.label(keys).classes("font-mono font-medium")
                            ui.label(action)
        ui.button("Close", on_click=dialog.close).props("flat").classes("self-end")
    return dialog


def install(
    is_owner: Callable[[], bool],
    player: "Player",
    shell: "Shell",
    songs: "SongList",
    controls: "Controls",
    sheet: "SheetPane",
    editor: "LoopEditor",
) -> None:
    async def on_key(e: events.KeyEventArguments) -> None:
        if (
            not e.action.keydown
            or e.modifiers.ctrl
            or e.modifiers.alt
            or e.modifiers.meta
            or not is_owner()
        ):
            return
        key = e.key.name
        if e.action.repeat and key not in REPEATABLE:
            return
        match key.lower() if len(key) == 1 else key:
            case " " if e.modifiers.shift and editor.is_open:
                editor.hear_end()
            case " " | "k":
                player.toggle_play()
            case "ArrowLeft":
                player.tempo_step(-1)
            case "ArrowRight":
                player.tempo_step(1)
            case "+" | "=":
                sheet.zoom_by(10)
            case "-":
                sheet.zoom_by(-10)
            case "w":
                sheet.set_zoom(100)
            case "h":
                await sheet.fit_page()
            case ",":
                player.skip(-5)
            case ".":
                player.skip(5)
            case "j":
                player.skip(-10)
            case "l":
                player.skip(10)
            case "0":
                player.to_start()
            case digit if len(digit) == 1 and digit.isdigit() and player.audio:
                player.seek(player.engine.duration * int(digit) / 10)
            case "q":
                shell.drawer.toggle()
            case "v":
                shell.cycle_controls()
            case "f":
                shell.set_fullscreen(not shell.fullscreen)
            case "Escape" if editor.is_open:
                await editor.close()
            case "Escape":
                shell.set_fullscreen(False)
            case "e":
                await (editor.close() if editor.is_open else editor.open())
            case "o":
                await sheet.set_rotation(shell.view["rotate"] + 90)
            case "t":
                await player.step_recording(-1 if e.modifiers.shift else 1)
            case "a":
                player.set_a()
            case "b":
                player.set_b()
            case "r":
                player.toggle_loop()
            case "c":
                player.clear_loop()
            case "s":
                controls.save_loop_dialog()
            case "n":
                await songs.step(1)
            case "p":
                await songs.step(-1)
            case "m":
                player.toggle_mute()
            case "/":
                shell.drawer.show()
                songs.focus_search()
            case "?":
                shell.help.open()

    ui.keyboard(on_key=on_key)
