"""The device code sign-in card: the code big, Copy, Open the page, time left, Cancel. One per
page; it opens on a job's `SignIn` event and closes when the job moves on or ends, whichever job
it is (an update, adding a folder, the folder picker)."""

import time
import webbrowser

from common import copy_text
from jobs import Jobs
from nicegui import ui

from downtempo.events import Event, SignIn


class SignInCard:
    """The device code sign-in: the code big, Copy, Open the page, time left, Cancel."""

    def __init__(self, jobs: Jobs) -> None:
        self.expires_at, self.url = 0.0, ""
        with (
            ui.dialog().props("persistent") as self.dialog,
            ui.card().classes("items-center gap-3 p-6 min-w-[360px]"),
        ):
            self.title = ui.label("").classes("text-h6")
            ui.label("Open the sign-in page and type this code:")
            with ui.row().classes("items-center gap-2"):
                self.code = ui.label("").classes("text-h4 font-mono tracking-widest")
                ui.button(icon="content_copy", on_click=self.copy).props(
                    "flat round"
                ).tooltip("Copy the code")
            ui.button(
                "Open the sign-in page",
                icon="open_in_new",
                on_click=lambda: webbrowser.open(self.url),
            ).props("unelevated no-caps")
            self.left = ui.label("").classes("text-caption text-grey")
            ui.label("Downtempo goes on by itself once you have signed in.").classes(
                "text-caption"
            )
            ui.button("Cancel", on_click=jobs.stop).props("flat no-caps")
        ui.timer(1.0, self.tick)
        jobs.on_event(self.on_event)
        jobs.on_idle(self.close)

    def on_event(self, event: Event) -> None:
        if isinstance(event, SignIn):
            self.open(event)
        else:
            self.close()

    def open(self, event: SignIn) -> None:
        self.title.text = f"Sign in to {event.provider}"
        self.code.text = event.code
        self.expires_at = event.expires_at
        self.url = event.url
        self.tick()
        self.dialog.open()

    def close(self) -> None:
        self.dialog.close()

    def copy(self) -> None:
        copy_text(self.code.text)
        ui.notify("Code copied", timeout=1000)

    def tick(self) -> None:
        if self.dialog.value:
            left = max(int(self.expires_at - time.time()), 0)
            self.left.text = f"The code works for {left // 60}:{left % 60:02} more"
