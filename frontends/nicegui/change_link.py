"""Change link…: a shared folder got a new link (re-shared, or the old one expired). Paste it → (sign
in) → if the new share has the same folder, say so; if not, pick the folder → "Save and check for
new files". The folder keeps its name here, so its downloads, songs, tempo and loops stay; nothing
is saved before the last step (docs/project-screen.md#project-settings)."""

from collections.abc import Callable

from folder_picker import FolderPicker
from jobs import Jobs
from nicegui import ui
from player import Player
from updates import Updates

from downtempo.errors import UserError
from downtempo.sources import Source


def where(folder: str) -> str:
    return f"“{folder}”" if folder else "the whole shared folder"


class ChangeLink:
    def __init__(
        self,
        player: Player,
        jobs: Jobs,
        updates: Updates,
        changed: Callable[[], None],
    ) -> None:
        """`changed` runs after a new link was saved."""
        self.player, self.jobs, self.updates, self.changed = (
            player,
            jobs,
            updates,
            changed,
        )
        self.source = Source("", "", "")
        self.url = ""
        with (
            ui.dialog().props("persistent") as self.dialog,
            ui.card().classes("w-[760px] max-w-[95vw] gap-3"),
        ):
            with ui.row().classes("items-center w-full no-wrap"):
                self.heading = ui.label("").classes("text-h6")
                ui.space()
                ui.button(icon="close", on_click=self.close).props(
                    "flat round dense"
                ).tooltip("Cancel (Esc)")
            self.body = ui.column().classes("w-full gap-3")
        self.dialog.on("keydown.esc", self.close)

    @property
    def library(self):
        return self.player.library

    def open(self, source: Source) -> None:
        self.source, self.url = source, ""
        self.link_step()
        self.dialog.open()

    def close(self) -> None:
        if self.jobs.running and not self.updates.running:
            self.jobs.stop()  # our look at the link; a download goes on
        self.dialog.close()

    # ------------------------------------------------------------ 1. the new link

    def link_step(self) -> None:
        source = self.source
        self.heading.text = f"New link for “{source.name}”"
        self.body.clear()
        with self.body:
            ui.label(
                "Paste the new link to the shared folder. In OneDrive: open the folder, "
                "press Share, then Copy link. Your songs, tempo and loops stay."
            ).classes("text-body2")
            with ui.row().classes("items-center gap-2 w-full no-wrap text-grey"):
                ui.label("Now:").classes("text-caption")
                ui.label(source.url).classes("text-caption truncate min-w-0")
            self.link = (
                ui.input("New link", value=self.url, placeholder="https://1drv.ms/f/…")
                .props("autofocus outlined clearable")
                .classes("w-full")
            )
            self.link_error = ui.label("").classes("text-negative text-body2")
            self.link_error.set_visibility(False)
            self.link.on("keydown.enter", self.next_step)
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=self.close).props("flat no-caps")
                self.next_button = ui.button(
                    "Next", icon="arrow_forward", on_click=self.next_step
                ).props("unelevated no-caps")

    def problem(self, text: str) -> None:
        self.link_error.text = text
        self.link_error.set_visibility(True)

    def next_step(self) -> None:
        text = (self.link.value or "").strip()
        try:
            self.library.link_provider(text)
        except UserError as error:
            self.problem(f"{error.message} {error.hint}".strip())
            return
        if text == self.source.url:
            self.problem("That is the link it has now. Paste the new one.")
            return
        self.url = text
        library, folder = self.library, self.source.folder
        if not self.jobs.start(
            "Open the new link",
            lambda report, cancel: library.has_folder(text, folder, report, cancel),
            self.opened,
        ):
            return
        self.link_error.set_visibility(False)
        self.next_button.props("loading")

    def opened(self, found: bool | None) -> None:
        if not self.dialog.value:
            return
        if found is None:  # the link didn't open, or Cancel in the sign-in card
            error = self.jobs.error
            self.link_step()
            if error:
                self.problem(f"{error.message} {error.hint}".strip())
            return
        if found:
            self.confirm_step(self.source.folder, self.source.skip, same=True)
        else:
            self.pick_step()

    # ------------------------------------------------------------ 2. only when the folder isn't there

    def pick_step(self) -> None:
        self.heading.text = "Which folder holds the songs?"
        self.body.clear()
        with self.body:
            ui.label(
                f"The new link has no folder {where(self.source.folder)}. "
                "Pick the one that holds the songs."
            ).classes("text-body2")
            box = ui.column().classes("w-full gap-2")
            ui.button("Back", icon="arrow_back", on_click=self.back).props(
                "flat no-caps"
            )
        FolderPicker(
            box,
            self.library,
            self.jobs,
            self.url,
            lambda folder, skip: self.confirm_step(folder, skip, same=False),
        )

    def back(self) -> None:
        if self.jobs.running and not self.updates.running:
            self.jobs.stop()
        self.link_step()

    # ------------------------------------------------------------ 3. save

    def confirm_step(self, folder: str, skip: tuple[str, ...], same: bool) -> None:
        name = self.source.name
        self.heading.text = "Use the new link?"
        self.body.clear()
        with self.body:
            if same:
                ui.label(f"The new link has the same folder {where(folder)}.").classes(
                    "text-body1"
                )
                ui.label(
                    "Your songs, sorting, tempo and loops stay as they are."
                ).classes("text-body2 text-grey")
            else:
                ui.label(f"“{name}” downloads {where(folder)} from now on.").classes(
                    "text-body1"
                )
                ui.label(
                    "Files already downloaded stay. The ones the new folder doesn't have "
                    "show as removed on server in Edit song list."
                ).classes("text-body2 text-grey")
            with ui.row().classes("w-full items-center gap-2"):
                ui.button(
                    "Back",
                    icon="arrow_back",
                    on_click=self.link_step if same else self.pick_step,
                ).props("flat no-caps")
                ui.space()
                ui.button(
                    "Save and check for new files",
                    icon="check",
                    on_click=lambda: self.save(folder, skip),
                ).props("unelevated no-caps")

    def save(self, folder: str, skip: tuple[str, ...]) -> None:
        try:
            source = self.library.change_link(self.source.name, self.url, folder, skip)
        except UserError as error:
            ui.notify(f"{error.message} {error.hint}".strip(), type="negative")
            return
        self.dialog.close()
        self.updates.errors.pop(source.name, None)
        self.changed()
        ui.notify(f"New link saved for “{source.name}”")
        self.updates.start([source.name])
