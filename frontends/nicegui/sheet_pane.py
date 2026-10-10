"""The sheet pane: the song's PDFs as pages, tabs per PDF, zoom, fit width / page, rotation,
full screen button. Scrolling and fitting run in the page (sheet_pane.js)."""

import json
import re
import webbrowser
from pathlib import Path

import pypdfium2 as pdfium
from common import tip
from layout import Shell
from nicegui import run, ui
from player import Player, Selection
from sheets import page_images

from downtempo.config import DATA_DIR

SHEET_JS = (Path(__file__).parent / "sheet_pane.js").read_text(encoding="utf-8")
# The frame is a size container: 100cqw/100cqh are its width/height.
ROTATIONS = {
    0: "width: 100%; height: 100%",
    90: "width: 100cqh; height: 100cqw; transform-origin: 0 0; transform: translateX(100cqw) rotate(90deg)",
    180: "width: 100%; height: 100%; transform: rotate(180deg)",
    270: "width: 100cqh; height: 100cqw; transform-origin: 0 0; transform: translateY(100cqh) rotate(-90deg)",
}
CSS = """
.sheet-bg { background: #e8e8ec; }
.body--dark .sheet-bg { background: #2a2a2e; }
.sheet-frame { position: relative; overflow: hidden; container-type: size; min-height: 0; }
.sheet-view { position: absolute; top: 0; left: 0; overflow: auto; }
.turn-90 i { transform: rotate(90deg); }
.sheet-tabs { max-width: 100%; }
.sheet-tabs .q-btn { min-width: 3rem; flex: 0 1 auto; }
.sheet-tabs .q-btn__content { min-width: 0; flex-wrap: nowrap; }
.sheet-tabs .q-btn .block { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fullscreen-exit { position: absolute; top: 8px; right: 24px; z-index: 10; opacity: 0.35; }
.fullscreen-exit:hover { opacity: 1; }
"""


def sheet_label(pdf: str, title: str) -> str:
    """`<Title> SOINNUT-2026-10-07.pdf` -> `SOINNUT · 2026-10-07`; the title is shown elsewhere."""
    rest = Path(pdf).stem.replace(title, "").strip(" -_")
    if match := re.search(r"(\d{4}-\d{2}-\d{2})$", rest):
        name = rest[: match.start()].strip(" -_")
        return f"{name} · {match[1]}" if name else f"Sheet · {match[1]}"
    return rest or "Sheet"


class SheetPane:
    def __init__(self, column: ui.column, shell: Shell, player: Player) -> None:
        self.player, self.shell, self.state = player, shell, player.state
        ui.add_head_html(
            f"<script>{SHEET_JS.replace('__SETTINGS__', json.dumps(shell.settings))}</script>"
        )
        ui.add_css(CSS)
        view = shell.view
        with column:
            with ui.row().classes(
                "w-full items-center gap-2 px-3 py-1 min-h-[44px] no-wrap"
            ) as toolbar:
                # long sheet names get "…" (full name in the tooltip); the buttons keep their room
                self.tabs_box = ui.element("div").classes("min-w-0 flex")
                ui.space()
                ui.button(icon="zoom_out", on_click=lambda: self.zoom_by(-10)).props(
                    "flat round dense"
                ).tooltip("Smaller (−)")
                self.zoom_label = ui.label("100 %").classes(
                    "text-caption w-12 text-center whitespace-nowrap"
                )
                ui.button(icon="zoom_in", on_click=lambda: self.zoom_by(10)).props(
                    "flat round dense"
                ).tooltip("Larger (+)")
                self.fit_width_button = ui.button(
                    icon="expand", on_click=lambda: self.set_zoom(100)
                ).props("flat round dense")
                self.fit_width_button.classes("turn-90").tooltip("Fit width (W)")
                self.fit_page_button = ui.button(
                    icon="expand", on_click=self.fit_page
                ).props("flat round dense")
                self.fit_page_button.tooltip("Fit page: the whole page in view (H)")
                ui.button(
                    icon="fullscreen", on_click=lambda: shell.set_fullscreen(True)
                ).props("flat round dense").tooltip("Full screen (F)")
                # set once (how the laptop stands) or rarely: kept out of the way
                with ui.button(icon="more_vert").props("flat round dense"):
                    ui.tooltip("Rotate, open the PDF")
                    with ui.menu():
                        ui.menu_item(
                            "Rotate right (O)",
                            on_click=lambda: self.set_rotation(view["rotate"] + 90),
                            auto_close=False,
                        )
                        ui.menu_item(
                            "Rotate left",
                            on_click=lambda: self.set_rotation(view["rotate"] - 90),
                            auto_close=False,
                        )
                        ui.separator()
                        self.open_pdf = ui.menu_item(
                            "Open in PDF viewer",
                            on_click=lambda: webbrowser.open(
                                (DATA_DIR / player.selection.pdf).as_uri()
                            ),
                        )
            with ui.element("div").classes("w-full grow sheet-frame sheet-bg"):
                exit_button = ui.button(
                    icon="fullscreen_exit", on_click=lambda: shell.set_fullscreen(False)
                ).props("round unelevated dense color=grey-8")
                exit_button.classes("fullscreen-exit").tooltip(
                    "Leave full screen (Esc, F)"
                )
                with ui.element("div").classes("sheet-view p-4") as self.view:
                    self.pages = ui.column().classes("gap-4 mx-auto")
        shell.fullscreen_hidden.append(toolbar)
        shell.fullscreen_only.append(exit_button)
        player.on("selection", self.on_selection)
        player.on("sheet", self.load)
        ui.on("refit", self.fit_page, throttle=0.3)
        self.set_zoom(self.state.get("zoom", 100), self.state.get("fit"))
        self.show_rotation()

    def watch(self) -> None:
        """Refit on resize; once the page is up."""
        ui.run_javascript("dt.watch()")

    def on_selection(self, new_song: bool) -> None:
        """A new song: its tabs (value set at creation, so on_change = real picks only), and the
        old song's pages must not stay while the audio loads."""
        if not new_song:
            return
        song, sel = self.player.song, self.player.selection
        self.tabs_box.clear()
        if len(song["pdf"]) > 1:
            labels = {p: sheet_label(p, song["title"]) for p in song["pdf"]}
            with self.tabs_box:
                tabs = ui.toggle(
                    labels,
                    value=sel.pdf,
                    on_change=lambda e: self.player.pick_sheet(e.value),
                ).props("dense no-caps no-wrap")
                tabs.classes("sheet-tabs")
                tip(tabs, " / ".join(labels.values()))
        self.pages.clear()

    def message(self, icon: str, text: str) -> None:
        self.pages.clear()
        with self.pages, ui.column().classes("w-full items-center mt-16 text-grey"):
            ui.icon(icon, size="48px")
            ui.label(text)

    async def load(self, sel: Selection, ticket: int) -> None:
        tickets = self.player.tickets
        if ticket != tickets["sheet"]:
            return  # another sheet was picked while this song's audio loaded
        self.open_pdf.set_visibility(bool(sel.pdf))
        if not sel.pdf:
            self.message("music_off", "No sheet music for this song")
            return
        try:
            names = await run.io_bound(page_images, DATA_DIR / sel.pdf)
        except (OSError, pdfium.PdfiumError) as error:
            if ticket == tickets["sheet"]:
                self.message("broken_image", f"Cannot show {Path(sel.pdf).name}")
                ui.notify(f"Cannot show {Path(sel.pdf).name}: {error}", type="negative")
            return
        if ticket != tickets["sheet"]:
            return  # overtaken by another song or sheet
        self.player.remember(pdf=sel.pdf)
        self.player.loaded(sel)
        self.pages.clear()
        with self.pages:
            for name in names:
                ui.element("img").props(f'src="/pages/{name}" draggable=false').classes(
                    "w-full shadow-md bg-white block"
                )
        if self.state.get("fit") == "page":
            await self.fit_page()

    def zoom_by(self, step: int) -> None:
        self.set_zoom(self.state.get("zoom", 100) + step)

    def set_zoom(self, value: int, fit: str | None = None) -> None:
        """Zoom = page width in % of the view; fit "page" is kept up to date by fit_page()."""
        state = self.state
        state["zoom"] = max(20, min(200, value))
        state["fit"] = fit
        self.player.dirty = True
        self.pages.style(f"width: {state['zoom']}%")
        self.zoom_label.text = f"{state['zoom']} %"
        for button, on in (
            (self.fit_width_button, fit is None and state["zoom"] == 100),
            (self.fit_page_button, fit == "page"),
        ):
            if on:
                button.classes(add="song-active")
            else:
                button.classes(remove="song-active")
        ui.run_javascript(f"dt.fit = {json.dumps(fit)}")

    async def fit_page(self) -> None:
        try:
            fit = await ui.run_javascript("dt.fitPage()", timeout=10)
        except TimeoutError:
            return
        if not fit:  # no sheet (yet): load() fits when one comes
            self.set_zoom(self.state.get("zoom", 100), fit="page")
            return
        self.set_zoom(fit["zoom"], fit="page")
        ui.run_javascript(f"dt.toPage({int(fit['page'])})")

    def show_rotation(self) -> None:
        self.view.style(replace=ROTATIONS[self.shell.view["rotate"]])

    async def set_rotation(self, degrees: int) -> None:
        self.shell.set_view(rotate=degrees % 360)
        self.show_rotation()
        if self.state.get("fit") == "page":  # the frame keeps its size: no resize event
            await self.fit_page()
