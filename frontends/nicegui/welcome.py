"""What the page shows before there are songs: on the first start "Paste a link to your group's
shared folder" (the Add folder flow takes it from there); with folders but no songs yet, the way
to the unknown files or a download (docs/project-screen.md#getting-there)."""

from collections.abc import Callable

from nicegui import ui

from downtempo.library import Library


def welcome(
    library: Library,
    add_folder: Callable[[str], None],
    open_screen: Callable[[], None],
    download: Callable[[], None],
) -> None:
    with ui.column().classes("w-full items-center mt-20 gap-3 px-4"):
        ui.icon("library_music", size="64px").classes("text-primary")
        if not library.sources():
            ui.label("Welcome to Downtempo").classes("text-h5")
            ui.label(
                "Practise your group's songs slower, in loops, with the sheet music beside."
            ).classes("text-body1 text-grey text-center")
            ui.label("Paste a link to your group's shared folder:").classes(
                "text-body1 mt-4"
            )
            with ui.row().classes("items-center gap-2 no-wrap w-full max-w-[560px]"):
                link = (
                    ui.input(placeholder="https://1drv.ms/f/…")
                    .props("outlined autofocus clearable")
                    .classes("grow")
                )
                go = ui.button(
                    "Next",
                    icon="arrow_forward",
                    on_click=lambda: add_folder(link.value or ""),
                ).props("unelevated no-caps")
            link.on("keydown.enter", lambda: add_folder(link.value or ""))
            go.tooltip("Sign in if asked, pick the folder, see what's there, download")
            ui.label(
                "In OneDrive: open the folder, press Share, then Copy link."
            ).classes("text-caption text-grey")
            return
        ui.label("No songs yet").classes("text-h6")
        if library.files():
            ui.label(
                "The files are here, but none is in a song yet: make songs of them."
            ).classes("text-body1 text-grey text-center")
            ui.button("Edit song list", icon="edit_note", on_click=open_screen).props(
                "unelevated no-caps"
            )
        else:
            ui.label("Download the files of your shared folders.").classes(
                "text-body1 text-grey"
            )
            ui.button("Check for new files", icon="sync", on_click=download).props(
                "unelevated no-caps"
            )
