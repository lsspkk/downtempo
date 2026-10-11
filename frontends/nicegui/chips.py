"""Pieces both tabs of the project screen use: a file chip (♪ / 📄, label, marks, tooltip; it can
be dragged and has a right-click menu) and the song picker behind "Move to…" (type to search, or
type a new title). Dragging itself runs in drag.js."""

from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any

from nicegui import events, ui
from previews import play_js

from downtempo.shapes import FileRef

CSS = """
.fchip { display: inline-flex; align-items: center; gap: 4px; padding: 1px 8px 1px 6px;
  border: 1px solid rgba(128, 128, 128, 0.45); border-radius: 12px; font-size: 13px;
  cursor: pointer; user-select: none; max-width: 280px; }
.fchip.sheet { border-style: dashed; }
.fchip .fl { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fchip.sel { background: rgba(79, 91, 213, 0.18); border-color: #4f5bd5; border-style: solid; }
.fchip .mark { font-size: 11px; opacity: 0.75; }
.fchip .new { color: #4f5bd5; font-weight: bold; }
.fchip[draggable=true] { cursor: grab; }
.fchip .pv { display: none; cursor: pointer; opacity: 0.8; }
.fchip:hover .pv, .fchip:focus-within .pv { display: inline-flex; }
.fchip .pv:hover { opacity: 1; color: #4f5bd5; }
.drop-hi { outline: 2px dashed #4f5bd5; outline-offset: -2px; background: rgba(79, 91, 213, 0.10); }
.drag-zones { display: none; }
body.dt-dragging .drag-zones { display: flex; }
.drag-zone { border: 2px dashed rgba(128, 128, 128, 0.6); border-radius: 8px; padding: 6px 14px; }
body.dt-dragging-song .song-row:not(.drop-hi) { opacity: 0.85; }
"""
DRAG_JS = (Path(__file__).parent / "drag.js").read_text(encoding="utf-8")


def file_chip(
    file: FileRef,
    label: str,
    why: str = "",
    marks: str = "",
    new: bool = False,
    selected: bool = False,
    on_click: Callable[[events.GenericEventArguments], None] | None = None,
    drag_from: str | None = None,
    menu: Callable[[], None] | None = None,
    preview: Callable[[FileRef], Any] | None = None,
) -> ui.element:
    """Sheets have a dashed outline, recordings a solid one: the kinds differ in dark mode too.
    `on_click` gets the click with `shiftKey`; `drag_from` (a song id, "" for none) makes it
    draggable; `menu` fills its right-click menu; with `preview` a ▶ (recordings, played in the
    page) or 👁 (sheets, `preview(file)`) shows on hover."""
    classes = "fchip" + (" sheet" if file.kind == "sheet" else "") + (" sel" * selected)
    with ui.element("div").classes(classes) as chip:
        ui.icon("description" if file.kind == "sheet" else "music_note", size="15px")
        ui.label(label).classes("fl")
        if new:
            ui.label("•").classes("new")
        if marks:
            ui.label(marks).classes("mark")
        if preview and file.kind == "audio":
            play = ui.icon("play_circle", size="17px").classes("pv")
            play.on(
                "click",
                js_handler=f"(e) => {{ e.stopPropagation(); ({play_js(file)})(); }}",
            )
            play.tooltip("Listen to the first 15 s (again: stop)")
        elif preview:
            look = ui.icon("visibility", size="17px").classes("pv")
            look.on("click.stop", lambda: preview(file))
            look.tooltip("The first page")
        where = f"{file.source} / {file.path}"
        hint = "Drag it to a song · right-click: more" if drag_from is not None else ""
        ui.tooltip("\n".join(x for x in (where, why, hint) if x)).classes(
            "whitespace-pre-line text-body2"
        ).props("delay=600")
        if menu:
            with ui.context_menu():
                menu()
    if on_click:
        chip.on("click", on_click, ["shiftKey", "ctrlKey", "metaKey"])
    if drag_from is not None:
        chip.props["draggable"] = "true"
        chip.props["data-file"] = file.id
        chip.props["data-from"] = drag_from
    return chip


async def pick_song(
    titles: dict[str, str], heading: str, allow_new: bool = True
) -> tuple[str, str] | None:
    """Ask for a song: (song id, "") for an existing one, ("", title) for a new title, None = Esc."""
    by_title = {t.casefold(): id for id, t in titles.items()}
    with ui.dialog() as dialog, ui.card().classes("min-w-[360px] gap-2"):
        ui.label(heading).classes("text-h6")
        select = (
            ui.select(
                sorted(titles.values(), key=str.casefold),
                with_input=True,
                new_value_mode="add-unique" if allow_new else None,
                label="Song" + (" (or type a new title)" if allow_new else ""),
            )
            .props("autofocus dense outlined")
            .classes("w-full")
        )

        def ok() -> None:
            value = (select.value or "").strip()
            if not value:
                return
            id = by_title.get(value.casefold(), "")
            dialog.submit((id, "") if id else ("", value))

        select.on("keydown.enter", ok)
        with ui.row().classes("self-end"):
            ui.button("Cancel", on_click=lambda: dialog.submit(None)).props(
                "flat no-caps"
            )
            ui.button("OK", on_click=ok).props("no-caps")
    result = await dialog
    close(dialog)
    return result


async def ask_text(
    heading: str, value: str = "", check: str = "", empty_ok: bool = False
) -> tuple[str, bool] | None:
    """A one-line text with an optional checkbox (`check` = its label); None = Esc."""
    with ui.dialog() as dialog, ui.card().classes("min-w-[360px] gap-2"):
        ui.label(heading).classes("text-h6")
        text = ui.input(value=value).props("autofocus dense outlined").classes("w-full")
        box = ui.checkbox(check, value=True) if check else None

        def ok() -> None:
            if text.value.strip() or empty_ok:
                dialog.submit((text.value.strip(), bool(box and box.value)))

        text.on("keydown.enter", ok)
        with ui.row().classes("self-end"):
            ui.button("Cancel", on_click=lambda: dialog.submit(None)).props(
                "flat no-caps"
            )
            ui.button("OK", on_click=ok).props("no-caps")
    result = await dialog
    close(dialog)
    return result


def close(dialog: ui.dialog) -> None:
    """Remove a finished dialog; it may be gone already (the page closed while it was open)."""
    with suppress(ValueError, KeyError):
        dialog.delete()
