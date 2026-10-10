"""The window's frame: header, song-list drawer, the controls | sheet grid, Full / Simple / Sheet
controls, full screen, settings and dark mode (docs/practice-layout.md).

The parts put themselves in: the controls fill `pane` and `mini_bar` and list what Full or Simple
shows; the sheet lists what full screen hides or shows.
"""

import json
from typing import Any

from common import tip
from keys import help_dialog
from nicegui import app, ui
from player import Player

# Both remembered: state["view"] and state["settings"].
VIEW = {"library": True, "controls": "full", "rotate": 0}
SETTINGS = {"scroll_step": 20, "page_mode": "screen", "tempo_step": 5, "smooth": True}
# Browser full screen; leaving it with Esc (which the browser keeps) tells the server.
FULLSCREEN_JS = """<script>
window.shell = {fullscreen: (on) => on ? document.documentElement.requestFullscreen?.().catch(() => {})
  : document.fullscreenElement && document.exitFullscreen()};
document.addEventListener('fullscreenchange', () => {
  if (!document.fullscreenElement) emitEvent('fullscreen_left');
});
</script>"""


class Shell:
    def __init__(self, player: Player) -> None:
        self.player = player
        state = player.state
        self.view = state["view"] = {**VIEW, **state.get("view", {})}
        self.settings = state["settings"] = {**SETTINGS, **state.get("settings", {})}
        self.fullscreen = False  # only the sheet; not remembered
        self.full_only: list[ui.element] = []  # hidden in Simple controls
        self.simple_only: list[ui.element] = []  # shown only in Simple controls
        self.fullscreen_hidden: list[ui.element] = []
        self.fullscreen_only: list[ui.element] = []
        self.pane: ui.column | None = None
        ui.add_head_html(FULLSCREEN_JS)
        self.help = help_dialog()
        settings_dialog = self.settings_dialog()
        self.dark = ui.dark_mode(state.get("dark", False))

        with ui.header(elevated=False).classes(
            "app-header items-center gap-2 px-3 py-1 no-wrap"
        ) as self.header:
            # Labelled, not ☰: that reads as the app menu (docs/practice-layout.md#song-list-button)
            self.songs_button = ui.button(
                "Songs", icon="queue_music", on_click=lambda: self.drawer.toggle()
            ).props("flat no-caps")
            tip(self.songs_button, "Song list (Q)")
            ui.label("Downtempo").classes("text-subtitle1 font-bold text-primary gt-md")
            ui.separator().props("vertical").classes("mx-1 gt-md")
            self.title = ui.label("").classes("text-h6 truncate min-w-0")
            ui.space()
            # The basics while the controls are hidden (sheet only); the controls fill it.
            self.mini_bar = ui.row().classes("items-center gap-1 no-wrap")
            self.controls_toggle = (
                ui.toggle(
                    {"full": "Full", "simple": "Simple", "hidden": "Sheet"},
                    value=self.view["controls"],
                    on_change=lambda e: self.set_controls(e.value),
                )
                .props("dense no-caps rounded unelevated toggle-color=primary")
                .classes("border")
            )
            tip(self.controls_toggle, "Controls: full / simple / sheet only (V)")
            ui.button(icon="settings", on_click=settings_dialog.open).props(
                "flat round"
            ).tooltip("Settings")
            ui.button(icon="keyboard", on_click=self.help.open).props(
                "flat round"
            ).tooltip("Keyboard shortcuts (?)")
            ui.button(icon="dark_mode", on_click=self.flip_dark).props(
                "flat round"
            ).tooltip("Dark / light")

        with (
            ui.left_drawer(value=self.view["library"], bordered=True)
            .props("width=290")
            .classes("p-2 gap-2") as self.drawer
        ):
            self.drawer.on_value_change(lambda e: self.on_drawer(bool(e.value)))
        self.show_library_button(self.view["library"])
        player.on("selection", self.show_title)
        ui.on("fullscreen_left", lambda: self.set_fullscreen(False))

    def build_grid(self) -> ui.column:
        """The two columns under the header: `pane` for the controls, and the sheet's (returned)."""
        with (
            ui.element("div")
            .classes("w-full")
            .style("display: grid; height: calc(100vh - 52px)") as self.layout
        ):
            self.pane = ui.column().classes(
                "p-4 gap-3 overflow-y-auto pane-border no-wrap"
            )
            sheet = ui.column().classes("gap-0 h-full overflow-hidden min-w-0")
        return sheet

    def show_title(self, new_song: bool) -> None:
        if new_song and self.player.song:
            self.title.text = self.player.song["title"]

    def set_view(self, **values: Any) -> None:
        self.view.update(values)
        self.player.dirty = True

    def show_layout(self) -> None:
        mode = "hidden" if self.fullscreen else self.view["controls"]
        columns = {
            "full": "minmax(360px, 460px) 1fr",
            "simple": "minmax(250px, 290px) 1fr",
        }
        height = "100vh" if self.fullscreen else "calc(100vh - 52px)"
        self.layout.style(
            f"grid-template-columns: {columns.get(mode, '1fr')}; height: {height}"
        )
        self.pane.set_visibility(mode != "hidden")
        for element in self.full_only:
            element.set_visibility(mode == "full")
        for element in self.simple_only:
            element.set_visibility(mode == "simple")
        self.mini_bar.set_visibility(self.view["controls"] == "hidden")
        self.header.value = not self.fullscreen
        self.drawer.value = self.view["library"] and not self.fullscreen
        for element in self.fullscreen_hidden:
            element.set_visibility(not self.fullscreen)
        for element in self.fullscreen_only:
            element.set_visibility(self.fullscreen)

    def set_controls(self, mode: str) -> None:
        if mode not in ("full", "simple", "hidden"):
            return
        self.set_view(controls=mode)
        self.show_layout()
        if (
            self.controls_toggle.value != mode
        ):  # its on_change comes back and changes nothing
            self.controls_toggle.value = mode

    def cycle_controls(self) -> None:
        order = ["full", "simple", "hidden"]
        self.set_controls(order[(order.index(self.view["controls"]) + 1) % len(order)])

    def set_fullscreen(self, on: bool) -> None:
        if on == self.fullscreen:
            return
        self.fullscreen = on
        self.show_layout()
        if app.native.main_window:
            app.native.main_window.toggle_fullscreen()
        else:
            ui.run_javascript(f"shell.fullscreen({json.dumps(on)})")

    def show_library_button(self, shown: bool) -> None:
        if shown:
            self.songs_button.classes(add="song-active text-primary")
        else:
            self.songs_button.classes(remove="song-active text-primary")

    def on_drawer(self, shown: bool) -> None:
        self.show_library_button(shown)
        if (
            not self.fullscreen
        ):  # full screen hides it without changing the remembered choice
            self.set_view(library=shown)

    def flip_dark(self) -> None:
        self.dark.value = not self.dark.value
        self.player.state["dark"] = self.dark.value
        self.player.dirty = True

    def set_setting(self, key: str, value: Any) -> None:
        self.settings[key] = value
        self.player.dirty = True
        # the sheet's page script (sheet_pane.js) reads them
        ui.run_javascript(f"Object.assign(dt.settings, {json.dumps({key: value})})")

    def settings_dialog(self) -> ui.dialog:
        settings = self.settings
        with ui.dialog() as dialog, ui.card().classes("min-w-[380px] gap-3"):
            ui.label("Settings").classes("text-h6")
            for key, label, options in (
                (
                    "scroll_step",
                    "↑ / ↓ scroll",
                    {v: f"{v} %" for v in (10, 20, 33, 50)},
                ),
                (
                    "page_mode",
                    "PgUp / PgDn",
                    {"screen": "a screen", "page": "to next page"},
                ),
                (
                    "tempo_step",
                    "← / → tempo step",
                    {v: f"{v} %" for v in (1, 2, 5, 10)},
                ),
            ):
                with ui.column().classes("gap-1"):
                    ui.label(label).classes("text-caption text-grey")
                    ui.toggle(
                        options,
                        value=settings[key],
                        on_change=lambda e, key=key: self.set_setting(key, e.value),
                    ).props("dense no-caps")
            ui.switch(
                "Smooth scrolling",
                value=settings["smooth"],
                on_change=lambda e: self.set_setting("smooth", e.value),
            )
            ui.label(
                "↑ / ↓ scroll a share of the visible sheet; a screen keeps the last line."
            ).classes("text-caption text-grey")
            ui.button("Close", on_click=dialog.close).props("flat").classes("self-end")
        return dialog
