"""Previews in the project screen: ▶ plays the first 15 s of a recording in a plain audio element
(not the tempo engine), 👁 shows a sheet's first page. Files reach the page only through
`/preview/<source>/<path>`, which serves the current project's downloaded recordings and sheets
and nothing else (docs/project-screen.md#file-chip)."""

from collections.abc import Callable
from pathlib import Path
from urllib.parse import quote

import pypdfium2 as pdfium
from fastapi import HTTPException
from fastapi.responses import FileResponse
from nicegui import app, run, ui
from sheets import page_images

from downtempo.config import MEDIA_EXTENSIONS
from downtempo.errors import UserError
from downtempo.library import Library
from downtempo.shapes import FileRef

SECONDS = 15
# One audio element for the page; the same ▶ again stops it. `#t=0,15` stops at 15 s.
PREVIEW_JS = f"""<script>
window.dtPreview = {{
  audio: null, url: "",
  toggle(url) {{
    const a = this.audio || (this.audio = new Audio());
    if (this.url === url && !a.paused) {{ a.pause(); return; }}
    this.url = url;
    a.src = url + "#t=0,{SECONDS}";
    a.play().catch(() => {{}});
  }},
  stop() {{ this.audio && this.audio.pause(); }},
}};
</script>"""


def serve(library: Callable[[], Library]) -> None:
    """Register the route once (module level): files under the current project's `downloads/`
    with a media ending; Range requests work, so the audio element can seek."""

    @app.get("/preview/{path:path}")
    def preview(path: str) -> FileResponse:
        current = library()
        try:
            file = current.path(f"downloads/{path}")
        except UserError as error:
            raise HTTPException(404) from error
        if (
            not file.is_relative_to(current.downloads.resolve())
            or file.suffix.lower() not in MEDIA_EXTENSIONS
            or not file.is_file()
        ):
            raise HTTPException(404)
        return FileResponse(file)


def url(file: FileRef) -> str:
    return f"/preview/{quote(file.source)}/{quote(str(file.path))}"


def play_js(file: FileRef) -> str:
    return f"() => dtPreview.toggle({url(file)!r})"


async def show_sheet(library: Library, file: FileRef) -> None:
    """The sheet's first page in a dialog (rendered and cached like the player's pages)."""
    path = library.downloads / file.source / Path(str(file.path))
    try:
        pages = await run.io_bound(page_images, path)
    except (OSError, pdfium.PdfiumError) as error:
        ui.notify(f"Can't show {file.path.name}: {error}", type="negative")
        return
    with ui.dialog() as dialog, ui.card().classes("max-w-[95vw] gap-2 p-3"):
        with ui.row().classes("w-full items-center no-wrap"):
            ui.label(file.path.name).classes("text-subtitle1 truncate")
            ui.space()
            ui.label(f"page 1 of {len(pages)}").classes("text-caption text-grey")
            ui.button(icon="close", on_click=dialog.close).props("flat round dense")
        if pages:
            ui.element("img").props(f'src="/pages/{pages[0]}"').classes(
                "block shadow-md bg-white"
            ).style("max-height: calc(100vh - 120px); max-width: 90vw")
    dialog.on("hide", dialog.delete)
    dialog.open()
