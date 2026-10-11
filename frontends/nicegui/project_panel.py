"""The top of the song list: a "Project" caption with ⟳ (check for new files; again = stop), the
project's name as plain text (the project's actions are in the ☰ menu, main_menu.py), and one status line that always keeps its
height, so the songs below never jump: "Checked 2 h ago", "Downloading 3 of 7 · 45 %" with a
thin bar, "5 new files: …", or "⚠ <folder>: <what went wrong>", which opens Project settings at
that folder (docs/practice-layout.md#song-list)."""

from collections.abc import Callable

from nicegui import ui
from updates import Updates, ago

from downtempo.library import Library

CSS = """
@keyframes dt-spin { to { transform: rotate(360deg); } }
.dt-spinning .q-icon { animation: dt-spin 1.2s linear infinite; }
.dt-status { height: 20px; line-height: 20px; }
.dt-bar { height: 2px; }
"""
TICK = 60  # seconds between "checked n min ago" updates


class ProjectPanel:
    def __init__(
        self,
        library: Callable[[], Library],
        updates: Updates,
        settings: Callable[[str], None],
    ) -> None:
        """Builds into the current container (the drawer); `settings(folder)` opens Project
        settings at a folder."""
        self.library, self.updates, self.settings = library, updates, settings
        ui.add_css(CSS)
        with ui.column().classes("w-full gap-0 flex-none"):
            with ui.row().classes("items-center w-full no-wrap gap-0 pl-2"):
                ui.label("Project").classes(
                    "text-caption text-grey uppercase tracking-wider"
                )
                ui.space()
                self.sync = ui.button(icon="sync", on_click=self.sync_click).props(
                    "flat round dense"
                )
                with self.sync:
                    self.sync_tip = ui.tooltip("")
            self.name = ui.label("").classes(
                "text-subtitle1 font-medium truncate w-full px-2 leading-tight"
            )
            with self.name:
                self.name_tip = ui.tooltip("")
            self.status = ui.label("").classes(
                "dt-status text-caption truncate w-full px-2"
            )
            with self.status:
                self.status_tip = ui.tooltip("").classes("whitespace-pre-line")
            self.status.on("click", self.status_click)
            self.bar = ui.linear_progress(value=0, show_value=False).classes(
                "dt-bar mx-2"
            )
        self.show_name()
        updates.changed.append(self.show)
        ui.timer(TICK, self.show)
        self.show()

    def show_name(self) -> None:
        name = self.library().name()
        self.name.text = name
        self.name_tip.text = name

    def show(self) -> None:
        updates = self.updates
        running = bool(updates.running)
        self.sync.classes(
            add="dt-spinning" if running else "",
            remove="" if running else "dt-spinning",
        )
        self.sync_tip.text = "Stop the download" if running else "Check for new files"
        self.bar.value = updates.fraction
        self.bar.style(f"visibility: {'visible' if running else 'hidden'}")
        text, tip, warn = self.line()
        self.status.text = text
        self.status_tip.text = tip
        self.status.classes(
            add="text-negative cursor-pointer" if warn else "text-grey",
            remove="text-grey" if warn else "text-negative cursor-pointer",
        )

    def line(self) -> tuple[str, str, bool]:
        """(the status line, its tooltip, whether it's a warning)."""
        updates = self.updates
        if updates.running:
            return updates.status, updates.status, False
        if updates.errors:
            name, error = next(iter(updates.errors.items()))
            text = f"⚠ {name}: {error.message}" if name else f"⚠ {error.message}"
            return text, f"{error.message} {error.hint}\nClick to fix it.".strip(), True
        if updates.result:
            return updates.result, updates.result, False
        library = self.library()
        sources = library.sources()
        if not sources:
            return "No shared folder yet", "Add one with ☰ → Project settings…", False
        checked = library.checked()
        if missing := [s.name for s in sources if s.name not in checked]:
            return (
                "Not downloaded yet",
                f"Press ⟳ to download {', '.join(missing)}",
                False,
            )
        oldest = min(checked[s.name] for s in sources)
        return (
            ago(oldest).capitalize(),
            "When every shared folder was last checked",
            False,
        )

    def sync_click(self) -> None:
        if self.updates.running:
            self.updates.cancel()
        else:
            self.updates.start()

    def status_click(self) -> None:
        if self.updates.errors and not self.updates.running:
            self.settings(next(iter(self.updates.errors)))
