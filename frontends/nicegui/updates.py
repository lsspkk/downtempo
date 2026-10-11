"""Downloading, for the whole page: ⟳ beside the project's name in the song list, ⟳ Update and a
folder's "Update this folder" in the project screen, and the start after Add folder or Change
link. Runs `library.sync` as a background job; playback goes on, and the songs update without a
restart. One download at a time. This holds the state only; whoever shows it (the song list's
status line, the folder chips) listens to `changed`.
"""

import time
from collections.abc import Awaitable, Callable
from datetime import datetime

from jobs import Jobs
from nicegui import ui
from player import Player

from downtempo.errors import UserError
from downtempo.events import (
    Checking,
    Event,
    Failed,
    Fetching,
    Planned,
    Saved,
    SignIn,
    count,
)
from downtempo.library import UpdateResult


class Updates:
    def __init__(self, player: Player, jobs: Jobs) -> None:
        self.player, self.jobs = player, jobs
        self.planned = self.saved = 0  # files, over all sources
        self.running: list[str] = []  # the sources being downloaded; [] when idle
        self.source = ""  # the one being checked or downloaded now
        self.status = ""  # "Downloading 2 of 7: name · 45 %"
        self.fraction = 0.0
        self.errors: dict[str, UserError] = {}  # source → what went wrong last time
        self.result = ""  # the last result line
        self.changed: list[Callable[[], None]] = []  # progress or result changed
        self.arrived: list[Callable[[], None]] = []  # a file was saved (screen refresh)
        self.finished: list[Callable[[UpdateResult], Awaitable[None] | None]] = []
        self.add_folder: Callable[[], None] = lambda: None  # set by the page
        jobs.on_event(self.show)

    @property
    def library(self):
        return self.player.library

    def start(self, names: list[str] | None = None) -> bool:
        """Download what changed in these sources (all when None); False when it can't start."""
        if not self.library.sources():
            self.add_folder()  # nothing to check yet: the first step is adding a folder
            return False
        names = names or []
        library = self.library
        if not self.jobs.start(
            "Check for new files",
            lambda report, cancel: library.sync(names, report, cancel),
            self.done,
        ):
            return False
        self.planned = self.saved = 0
        self.running = names or [s.name for s in library.sources()]
        self.source, self.status, self.fraction = "", "Connecting…", 0.0
        for name in self.running:
            self.errors.pop(name, None)
        self.result = ""
        self.redraw()
        return True

    def cancel(self) -> None:
        self.status = "Stopping…"
        self.redraw()
        self.jobs.stop()

    def show(self, event: Event) -> None:
        if not self.running:
            return  # another job's events (adding a folder, the folder picker)
        match event:
            case SignIn():
                self.status = f"Waiting for the {event.provider} sign-in…"
            case Checking(source=source):
                self.source, self.status = source, f"Checking {source}…"
            case Planned(new=new, updated=updated):
                self.planned += new + updated
            case Fetching(source=source, path=path, done=done, total=total):
                part = f" · {done * 100 // total} %" if total else ""
                self.source = source
                self.status = (
                    f"Downloading {self.saved + 1} of {self.planned}: {path.name}{part}"
                )
                whole = self.saved + (done / total if total else 0)
                self.fraction = whole / self.planned if self.planned else 0
            case Saved():
                self.saved += 1
                for listener in self.arrived:
                    listener()
            case Failed(source=source, error=error):
                self.errors[source] = error
                where = f"{source}: " if source else ""
                ui.notify(
                    f"{where}{error.message} {error.hint}".strip(),
                    type="negative",
                    multi_line=True,
                    timeout=0,
                    close_button="OK",
                )
        self.redraw()

    def redraw(self) -> None:
        for listener in self.changed:
            listener()

    async def done(self, result: UpdateResult | None) -> None:
        self.running, self.source = [], ""
        stamp = time.strftime("%H:%M")
        self.result = (summary(result) if result else "Not checked") + f" ({stamp})"
        self.redraw()
        if result is None or (not result.saved and not result.catalog):
            return
        for listener in self.finished:
            if (answer := listener(result)) is not None:
                await answer


def summary(result: UpdateResult) -> str:
    """`Stopped: 2 new files kept`, `5 new files: 4 joined songs, 1 unknown`, `Everything is up to date`."""
    files = count(result.saved, "new file")
    if result.cancelled:
        return f"Stopped: {files} kept" if result.saved else "Stopped"
    if any(r.error for r in result.sources) and not result.saved:
        return "Couldn't check everything"
    if not result.saved:
        return "Everything is up to date"
    diff = result.catalog
    news = diff.news() if diff else ""
    return f"{files}: {news}" if news else files


def ago(when: str) -> str:
    """`checked 2 h ago`, from an ISO time."""
    try:
        seconds = (datetime.now() - datetime.fromisoformat(when)).total_seconds()
    except ValueError:
        return ""
    for unit, length in (("d", 86400), ("h", 3600), ("min", 60)):
        if seconds >= length:
            return f"checked {int(seconds // length)} {unit} ago"
    return "checked just now"
