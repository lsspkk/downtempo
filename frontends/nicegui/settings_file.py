"""Export… / Import… from the project menu: the project's settings file (its shared folders and
the sorting, never sign-ins) to send to a bandmate, and taking one in (docs/settings-file.md).

Export shows the text with Copy and Save as file… (a save dialog in the window, a download in a
browser tab). Import takes pasted text or a file, shows what would change (as a new project or
into this one) and asks nothing else; after Apply, "Download now?"."""

from collections.abc import Callable
from pathlib import Path

import webview
from chips import close
from common import copy_text
from nicegui import app, events, ui

from downtempo import bundle
from downtempo.errors import UserError
from downtempo.library import Library
from downtempo.projects import Workspace


class SettingsFile:
    def __init__(
        self,
        workspace: Workspace,
        library: Callable[[], Library],
        imported: Callable[[bool, bool], None],
    ) -> None:
        """`imported(new_project, download_now)` runs after an import was applied."""
        self.workspace, self.library, self.imported = workspace, library, imported

    async def open(self) -> None:
        library = self.library()
        with (
            ui.dialog() as dialog,
            ui.card().classes("w-[760px] max-w-[95vw] gap-2"),
        ):
            with ui.row().classes("w-full items-center no-wrap"):
                ui.label("Settings file").classes("text-h6")
                ui.space()
                ui.button(icon="close", on_click=dialog.close).props("flat round dense")
            with ui.tabs().props("dense no-caps align=left") as tabs:
                ui.tab("export", "Export (send it)")
                ui.tab("import", "Import (got one)")
            with ui.tab_panels(tabs, value="export").classes("w-full"):
                with ui.tab_panel("export").classes("p-0 gap-2"):
                    self.export_panel(library)
                with ui.tab_panel("import").classes("p-0 gap-2"):
                    self.import_panel(library, dialog)
        dialog.on("hide", lambda: close(dialog))
        dialog.open()

    # ------------------------------------------------------------ export

    def export_panel(self, library: Library) -> None:
        text = bundle.export(library)
        name = f"{library.name()}.toml"
        ui.label(
            "The shared folders of this project and how their files are sorted into songs. "
            "No sign-ins or passwords: whoever gets it signs in with their own account."
        ).classes("text-body2 text-grey")
        ui.textarea(value=text).props(
            "readonly outlined input-class=font-mono"
        ).classes("w-full").style("height: 300px")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(
                "Copy",
                icon="content_copy",
                on_click=lambda: (
                    copy_text(text),
                    ui.notify("Copied: paste it into an email or a message"),
                ),
            ).props("flat no-caps")
            ui.button(
                "Save as file…", icon="save", on_click=lambda: self.save(text, name)
            ).props("unelevated no-caps")

    async def save(self, text: str, name: str) -> None:
        window = app.native.main_window
        if window is None:  # a browser tab: the browser saves it
            ui.download.content(text, name, "application/toml")
            return
        chosen = await window.create_file_dialog(
            int(webview.FileDialog.SAVE), save_filename=name
        )
        if not chosen:
            return
        path = Path(chosen if isinstance(chosen, str) else chosen[0])
        try:
            path.write_text(text, encoding="utf-8")
        except OSError as error:
            ui.notify(f"Can't save {path.name}: {error.strerror}", type="negative")
            return
        ui.notify(f"Saved {path.name}")

    # ------------------------------------------------------------ import

    def import_panel(self, library: Library, dialog: ui.dialog) -> None:
        ui.label(
            "Paste the text you got, or open the file. Nothing changes before you press Import."
        ).classes("text-body2 text-grey")
        pasted = (
            ui.textarea(placeholder="downtempo = 1\nproject = …")
            .props("outlined input-class=font-mono")
            .classes("w-full")
            .style("height: 160px")
        )
        with ui.row().classes("w-full items-center gap-2"):
            if app.native.main_window is None:
                ui.upload(
                    label="Open a file", auto_upload=True, on_upload=lambda e: got(e)
                ).props("accept=.toml flat dense").classes("w-56")
            else:
                ui.button(
                    "Open a file…", icon="folder_open", on_click=lambda: pick()
                ).props("flat no-caps")
            ui.space()
            ui.button(
                "Check it", icon="fact_check", on_click=lambda: check(pasted.value)
            ).props("unelevated no-caps")
        result = ui.column().classes("w-full gap-1")

        async def got(e: events.UploadEventArguments) -> None:
            pasted.value = await e.file.text()
            check(pasted.value)

        async def pick() -> None:
            chosen = await app.native.main_window.create_file_dialog(
                int(webview.FileDialog.OPEN),
                file_types=("Settings files (*.toml)", "All files (*.*)"),
            )
            if not chosen:
                return
            path = Path(chosen if isinstance(chosen, str) else chosen[0])
            try:
                pasted.value = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as error:
                ui.notify(f"Can't read {path.name}: {error}", type="negative")
                return
            check(pasted.value)

        def check(text: str | None) -> None:
            result.clear()
            try:
                found = bundle.read(text or "")
            except UserError as error:
                with result:
                    ui.label(f"{error.message} {error.hint}".strip()).classes(
                        "text-negative"
                    )
                return
            with result:
                for line in found.refused:
                    ui.label(f"Not used: {line}").classes("text-caption text-negative")
                if found.ignored:
                    ui.label(f"Unknown, ignored: {', '.join(found.ignored)}").classes(
                        "text-caption text-grey"
                    )
                new_name = self.workspace.free_name(found.project)
                where = ui.radio(
                    {
                        "new": f"As a new project “{new_name}”",
                        "here": f"Into “{library.name()}”",
                    },
                    value="new" if library.sources() else "here",
                    on_change=lambda e: show(e.value),
                ).props("inline dense")
                changes_box = ui.column().classes("w-full gap-0 pl-2")
                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button(
                        "Import",
                        icon="download_done",
                        on_click=lambda: apply(where.value),
                    ).props("unelevated no-caps")

            def show(target: str) -> None:
                changes_box.clear()
                with changes_box:
                    for change in bundle.preview(
                        library if target == "here" else None, found
                    ):
                        ui.label(change.describe()).classes(
                            "text-body2 whitespace-pre-line"
                        )

            async def apply(target: str) -> None:
                new = target == "new"
                changes = bundle.preview(None if new else library, found)
                if all(c.kind == "same" for c in changes):
                    ui.notify("Nothing to import: it's all here already.")
                    return
                try:
                    into = (
                        self.workspace.create(self.workspace.free_name(found.project))
                        if new
                        else library
                    )
                    bundle.apply(into, changes)
                except UserError as error:
                    ui.notify(f"{error.message} {error.hint}".strip(), type="negative")
                    return
                # asked over this dialog: closing it first would delete what the question sits in
                download = await ask_download(into.name())
                self.imported(new, download)
                dialog.close()

            show(where.value)


async def ask_download(name: str) -> bool:
    with ui.dialog() as dialog, ui.card().classes("gap-3"):
        ui.label(f"Imported into “{name}”.").classes("text-h6")
        ui.label("Download its files now? You may be asked to sign in.").classes(
            "text-body2"
        )
        with ui.row().classes("self-end"):
            ui.button("Later", on_click=lambda: dialog.submit(False)).props(
                "flat no-caps"
            )
            ui.button("Download now", on_click=lambda: dialog.submit(True)).props(
                "unelevated no-caps autofocus"
            )
    answer = await dialog
    close(dialog)
    return bool(answer)
