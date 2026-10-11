"""The shared folders in the project screen's header, for watching them: one chip per folder with
its state (checked 2 h ago / 45 % / ⚠ the last error), then + Add folder and ⟳ Update. A chip's
menu updates that folder or opens Project settings at it, where the folder is changed
(docs/project-screen.md#source-menu). Downloads run in updates.py; this only shows them."""

from collections.abc import Callable

from nicegui import ui
from updates import Updates, ago

from downtempo.errors import UserError
from downtempo.library import Library
from downtempo.sources import Source

CSS = """
.src-chip { display: inline-flex; align-items: center; gap: 6px; padding: 2px 10px 2px 8px;
  border: 1px solid rgba(128, 128, 128, 0.45); border-radius: 14px; font-size: 13px;
  cursor: pointer; white-space: nowrap; max-width: 260px; }
.src-chip:hover { background: rgba(79, 91, 213, 0.08); }
.src-chip .st { opacity: 0.7; font-size: 12px; overflow: hidden; text-overflow: ellipsis; }
.src-chip.warn { border-color: #c62828; }
.src-chip.warn .st { color: #c62828; opacity: 1; }
"""


class SourcesBar:
    def __init__(
        self,
        row: ui.row,
        library: Callable[[], Library],
        updates: Updates,
        add_folder: Callable[[], None],
        settings: Callable[[str], None],
        shown: Callable[[], bool],
    ) -> None:
        """`settings(folder name)` opens Project settings at that folder; `shown` says whether
        the bar is on screen (no redraws while hidden)."""
        self.row, self.library, self.updates = row, library, updates
        self.add_folder, self.settings, self.shown = add_folder, settings, shown
        ui.add_css(CSS)
        updates.changed.append(lambda: self.show() if self.shown() else None)

    def show(self) -> None:
        library, updates = self.library(), self.updates
        try:
            sources = library.sources()
        except UserError as error:
            sources = []
            ui.notify(error.message, type="negative")
        checked = library.checked()
        self.row.clear()
        with self.row:
            for source in sources:
                self.chip(source, checked.get(source.name, ""))
            ui.button("Add folder", icon="add", on_click=self.add_folder).props(
                "flat dense no-caps"
            ).tooltip("Add another shared folder to this project")
            if updates.running:
                with ui.row().classes("items-center gap-1 no-wrap"):
                    ui.spinner(size="xs")
                    ui.label(f"{round(updates.fraction * 100)} %").classes(
                        "text-caption"
                    ).tooltip(updates.status)
                    ui.button("Cancel", on_click=updates.cancel).props(
                        "flat dense no-caps color=negative"
                    )
            elif sources:
                ui.button(
                    "Update", icon="sync", on_click=lambda: updates.start()
                ).props("flat dense no-caps").tooltip(
                    "Download what's new in every folder"
                )
            if updates.result and not updates.running:
                ui.label(updates.result).classes(
                    "text-caption text-grey truncate max-w-[260px]"
                ).tooltip(updates.result)

    def state(self, source: Source, checked: str) -> tuple[str, bool]:
        """What the chip says after the name, and whether it's a warning."""
        updates = self.updates
        if source.name in updates.running:
            if updates.source == source.name:
                return f"{round(updates.fraction * 100)} %", False
            return "waiting", False
        if error := updates.errors.get(source.name):
            if "sign" in error.message.casefold():
                return "⚠ sign in again", True
            return "⚠ " + error.message, True
        if checked:
            return ago(checked), False
        target = self.library().target(source)
        return (
            "" if target.is_dir() and any(target.iterdir()) else "not downloaded yet"
        ), False

    def chip(self, source: Source, checked: str) -> None:
        text, warn = self.state(source, checked)
        with ui.element("div").classes("src-chip" + " warn" * warn) as chip:
            ui.icon("cloud", size="16px")
            ui.label(source.name).classes("font-medium truncate")
            ui.label(text).classes("st")
            where = source.folder or "the whole shared folder"
            error = self.updates.errors.get(source.name)
            ui.tooltip(
                f"{source.type}: {where}"
                + (f"\n{error.message} {error.hint}" if error else "")
            ).classes("whitespace-pre-line text-body2")
            with ui.menu():
                ui.label(f"{source.name} · {where}").classes(
                    "text-caption text-grey px-4 pt-2 max-w-[320px] truncate"
                )
                ui.menu_item(
                    "Update this folder",
                    on_click=lambda: self.updates.start([source.name]),
                ).set_enabled(not self.updates.running)
                ui.menu_item(
                    "Folder settings…",
                    on_click=lambda: self.settings(source.name),
                )
        chip.props("tabindex=0")
