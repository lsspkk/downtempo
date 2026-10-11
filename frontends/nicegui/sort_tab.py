"""The project screen's Unknown files tab (To sort in the plan): suggested songs to tick and create (titles editable), loose
files with their one-click suggestion, and the files set aside as not song files
(docs/project-screen.md#to-sort-tab). Every action is a click; dragging (drag.js, the screen
handles the drop): chips or a whole suggestion (its ⠿) onto a title in the Your songs column on the
right, onto another suggestion (one song of both, with that one's title), or onto the zones that
appear while dragging (New song, Not a song file).
"""

import json
from typing import TYPE_CHECKING

from chips import file_chip, pick_song
from nicegui import ui

from downtempo.shapes import FileRef, Suggestion

if TYPE_CHECKING:
    from project_screen import ProjectScreen


def key_of(suggestion: Suggestion) -> tuple[str, ...]:
    """A suggestion's identity across refreshes: its files."""
    return tuple(f.id for f in suggestion.files)


class SortTab:
    def __init__(self, screen: "ProjectScreen") -> None:
        self.screen = screen
        self.unticked: set[tuple[str, ...]] = (
            set()
        )  # all are ticked unless the user unticks
        self.titles: dict[tuple[str, ...], str] = {}  # titles the user edited
        with ui.row().classes("w-full h-full no-wrap gap-0"):
            with ui.column().classes("grow h-full p-0 gap-0 no-wrap min-w-0"):
                # shown only while files are dragged (drag.js sets the body's class)
                with ui.row().classes("drag-zones w-full gap-2 px-3 pt-2 no-wrap"):
                    for target, icon, label in (
                        ("new", "add", "New song"),
                        ("notsong", "block", "Not a song file"),
                    ):
                        with ui.row().classes(
                            "drag-zone items-center gap-1 text-body2"
                        ) as zone:
                            ui.icon(icon, size="18px")
                            ui.label(label)
                        zone.props["data-drop"] = target
                self.body = ui.column().classes(
                    "w-full grow overflow-y-auto p-3 gap-1 no-wrap"
                )
            with ui.column().classes(
                "w-[220px] h-full p-2 gap-1 no-wrap border-l"
            ) as self.side:
                ui.label("Your songs").classes("text-subtitle2")
                ui.label("Drop files on a title").classes("text-caption text-grey")
                self.search = (
                    ui.input(placeholder="Search", on_change=self.show_side)
                    .props("dense outlined clearable")
                    .classes("w-full")
                )
                self.song_list = ui.column().classes(
                    "w-full grow overflow-y-auto gap-0 no-wrap"
                )

    def show_side(self) -> None:
        titles = self.screen.titles()
        self.side.set_visibility(bool(titles))
        text = (self.search.value or "").casefold()
        self.song_list.clear()
        with self.song_list:
            for id, title in sorted(titles.items(), key=lambda x: x[1].casefold()):
                if text in title.casefold():
                    with ui.row().classes(
                        "w-full px-2 py-1 rounded-borders text-body2 no-wrap"
                    ) as row:
                        ui.label(title).classes("truncate")
                    row.props["data-drop"] = f"song:{id}"

    def show(self) -> None:
        grouping = self.screen.grouping
        self.show_side()
        self.body.clear()
        with self.body:
            if not grouping.suggestions and not grouping.loose:
                ui.label("No unknown files: every file is in a song.").classes(
                    "text-grey p-4"
                )
            if grouping.suggestions:
                self.suggestions(grouping.suggestions)
            if grouping.loose:
                ui.label(f"Loose files ({len(grouping.loose)})").classes(
                    "text-subtitle2 mt-4"
                )
                titles = self.screen.titles()
                for loose in grouping.loose:
                    with ui.row().classes("items-center gap-2 no-wrap"):
                        file_chip(
                            loose.file,
                            loose.file.path.stem,
                            loose.why,
                            drag_from="",
                            preview=self.screen.show_sheet,
                        )
                        if loose.maybe in titles:
                            ui.button(
                                f"{titles[loose.maybe]}?",
                                on_click=lambda f=loose.file.id, s=loose.maybe: (
                                    self.screen.do(
                                        lambda: self.library.sorting.move([f], s)
                                    )
                                ),
                            ).props("dense flat no-caps color=primary").tooltip(
                                "Put it in this song"
                            )
                        ui.button(
                            "Move to…",
                            on_click=lambda f=loose.file.id: self.move([f]),
                        ).props("dense flat no-caps")
                        ui.button(
                            "Not a song file",
                            on_click=lambda f=loose.file.id: self.screen.do(
                                lambda: self.library.sorting.not_song([f])
                            ),
                        ).props("dense flat no-caps color=grey")
            if grouping.not_song:
                with ui.expansion(f"Not song files ({len(grouping.not_song)})").classes(
                    "w-full mt-4"
                ):
                    for file in grouping.not_song:
                        with ui.row().classes("items-center gap-2 no-wrap"):
                            file_chip(file, file.path.stem)
                            ui.button(
                                "Back to unknown files",
                                on_click=lambda f=file.id: self.screen.do(
                                    lambda: self.library.sorting.back_to_sort([f])
                                ),
                            ).props("dense flat no-caps")

    @property
    def library(self):
        return self.screen.library

    def suggestions(self, suggestions: tuple[Suggestion, ...]) -> None:
        keys = [key_of(s) for s in suggestions]
        ticked = [k for k in keys if k not in self.unticked]
        with ui.row().classes("items-center gap-3 pb-2 no-wrap"):
            ui.checkbox(
                "Select all",
                value=len(ticked) == len(keys),
                on_change=lambda e: self.tick_all(keys, e.value),
            )
            ui.button(
                f"Create selected ({len(ticked)})",
                icon="playlist_add",
                on_click=lambda: self.create(suggestions),
            ).props("no-caps unelevated").set_enabled(bool(ticked))
            ui.label(
                "Suggested songs: tick the right ones, fix titles, then create."
            ).classes("text-caption text-grey")
        for number, (suggestion, key) in enumerate(zip(suggestions, keys)):
            with ui.row().classes(
                "items-center gap-2 no-wrap w-full rounded-borders"
            ) as row:
                row.props["data-drop"] = f"sugg:{number}"
                handle = ui.icon("drag_indicator", size="20px").classes(
                    "text-grey cursor-grab"
                )
                handle.props["draggable"] = "true"
                handle.props["data-files"] = json.dumps(
                    [f.id for f in suggestion.files]
                )
                handle.tooltip(
                    "Drag onto a song (right) or onto another suggestion: one song of both"
                )
                ui.checkbox(
                    value=key not in self.unticked,
                    on_change=lambda e, k=key: self.tick(k, e.value),
                )
                ui.input(
                    value=self.titles.get(key, suggestion.title),
                    on_change=lambda e, k=key: self.titles.__setitem__(k, e.value),
                ).props("dense borderless").classes("w-56 font-medium")
                with ui.row().classes("gap-1 items-center grow min-w-0"):
                    for file in suggestion.files:
                        file_chip(
                            file,
                            file.path.stem,
                            drag_from="",
                            preview=self.screen.show_sheet,
                        )
                if suggestion.folder:
                    ui.label(f"📁 {suggestion.folder.replace(':', ' / ', 1)}").classes(
                        "text-caption text-grey truncate max-w-[30%]"
                    ).tooltip("Create links this folder: its new files join the song")
                with (
                    ui.button(icon="more_vert").props("dense flat round"),
                    ui.menu(),
                ):
                    ui.menu_item(
                        "Add to a song…",
                        on_click=lambda s=suggestion: self.move(
                            [f.id for f in s.files]
                        ),
                    )
                    ui.menu_item(
                        "Not song files",
                        on_click=lambda s=suggestion: self.screen.do(
                            lambda: self.library.sorting.not_song(
                                [f.id for f in s.files]
                            )
                        ),
                    )

    def tick(self, key: tuple[str, ...], on: bool) -> None:
        (self.unticked.discard if on else self.unticked.add)(key)
        self.show()

    def tick_all(self, keys: list[tuple[str, ...]], on: bool) -> None:
        self.unticked = set() if on else set(keys)
        self.show()

    def title_of(self, suggestion: Suggestion) -> str:
        return self.titles.get(key_of(suggestion), suggestion.title).strip() or (
            suggestion.title
        )

    def merge(self, number: int, files: list[str]) -> None:
        """Files (another suggestion's, or chips) dropped onto suggestion `number`: one song of all
        of them, with that suggestion's title, linking its folder."""
        suggestions = self.screen.grouping.suggestions
        if not 0 <= number < len(suggestions):
            return
        target = suggestions[number]
        grouping = self.screen.grouping
        known = {
            f.id: f
            for f in (
                *(f for x in grouping.suggestions for f in x.files),
                *(x.file for x in grouping.loose),
            )
        }
        both = {f.id: f for f in target.files} | {
            id: known.get(id) or FileRef.from_id(id) for id in files
        }
        title = self.title_of(target)
        merged = Suggestion(title, tuple(both.values()), target.folder)
        self.screen.do(
            lambda: self.library.sorting.create([merged]),
            f"Made “{title}” of {len(both)} files",
        )

    def create(self, suggestions: tuple[Suggestion, ...]) -> None:
        chosen = [
            Suggestion(self.title_of(s), s.files, s.folder)
            for s in suggestions
            if key_of(s) not in self.unticked
        ]
        waiting = self.screen.waiting()
        if not self.screen.do(lambda: self.library.sorting.create(chosen)):
            return
        # the new titles pull matching files that were loose or in other suggestions
        made = sum(len(s.files) for s in chosen)
        pulled = waiting - made - self.screen.waiting()
        with self.screen.dialog:
            ui.notify(
                f"Created {len(chosen)} song{'s' * (len(chosen) != 1)}"
                + (
                    f", and {pulled} more file{'s' * (pulled != 1)} joined them"
                    if pulled > 0
                    else ""
                )
            )

    async def move(self, files: list[str]) -> None:
        picked = await pick_song(self.screen.titles(), "Move to")
        if not picked:
            return
        id, title = picked
        sorting = self.library.sorting
        self.screen.do(
            (lambda: sorting.move(files, id))
            if id
            else (lambda: sorting.new_song(files, title))
        )
