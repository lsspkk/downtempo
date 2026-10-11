"""The project screen's Song files tab: one row per song with its file chips, selecting chips (click,
Shift+click for a range) and acting on them (Move to… `M`, Also add to…, New song `N`, Not a song
file `Delete`, Not in this song), or dragging them onto a song (Ctrl: also add) or a drop zone; a
chip's right-click menu (Make first, Rename label, Skip folder); the song's edit box (song_box.py;
dragging a title onto another song merges); the one-time offers under their song
(docs/project-screen.md#songs-tab). Drops are handled by the screen (`ProjectScreen.drop`).
"""

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from chips import ask_text, file_chip, pick_song
from nicegui import events, ui

from downtempo.shapes import GroupedSong, Member, Offer

if TYPE_CHECKING:
    from project_screen import ProjectScreen


# filter chips: key → (label, tooltip after "Only songs …")
FILTERS = {
    "new": ("New files", "with files that joined since you last opened them"),
    "offers": ("Suggestions", "with an “Also collect …?” question to answer"),
    "gone": ("Removed on server", "with a file no longer in the shared folder"),
}


class SongsTab:
    def __init__(self, screen: "ProjectScreen") -> None:
        self.screen = screen
        # (song id, file id): a file may be in two songs
        self.selected: set[tuple[str, str]] = set()
        self.order: list[tuple[str, str]] = []  # chips as shown, for Shift+click ranges
        self.anchor: tuple[str, str] | None = (
            None  # the last chip clicked without Shift
        )
        with ui.column().classes("w-full h-full p-3 gap-1 no-wrap"):
            with ui.row().classes("items-center gap-2 w-full no-wrap"):
                self.search = (
                    ui.input(placeholder="Search songs", on_change=self.show)
                    .props("dense outlined clearable")
                    .classes("w-64")
                )
                # filter chips, only those with songs; none selected = every song
                self.filter = ""
                self.filters = ui.row().classes("items-center gap-1 no-wrap")
                ui.space()
                self.bar = ui.row().classes("items-center gap-1 no-wrap")
            # shown only while files are dragged (drag.js sets the body's class)
            with ui.row().classes("drag-zones w-full gap-2 py-1 no-wrap"):
                for target, icon, label in (
                    ("new", "add", "New song"),
                    ("notsong", "block", "Not a song file"),
                    ("tosort", "undo", "Back to unknown files"),
                ):
                    with ui.row().classes(
                        "drag-zone items-center gap-1 text-body2"
                    ) as zone:
                        ui.icon(icon, size="18px")
                        ui.label(label)
                    zone.props["data-drop"] = target
            self.body = ui.column().classes("w-full grow overflow-y-auto gap-0 no-wrap")

    @property
    def sorting(self):
        return self.screen.library.sorting

    def show_filters(self, found: dict[str, set[str]]) -> set[str] | None:
        """Draws the filter chips that have songs; returns the songs to show (None = all)."""
        if not found.get(self.filter):
            self.filter = ""  # its songs are gone (answered, opened): back to all
        self.filters.clear()
        with self.filters:
            for key, (label, why) in FILTERS.items():
                if not found[key]:
                    continue
                on = key == self.filter
                chip = ui.button(
                    f"{label} {len(found[key])}",
                    icon="check" if on else None,
                    on_click=lambda key=key: self.set_filter(key),
                ).props(
                    "rounded dense no-caps unelevated"
                    + (" color=primary" if on else " outline color=grey-7")
                )
                chip.classes("px-3").tooltip(
                    "Click again to show every song" if on else f"Only songs {why}"
                )
        return found[self.filter] if self.filter else None

    def set_filter(self, key: str) -> None:
        self.filter = "" if key == self.filter else key
        self.show()

    def show(self) -> None:
        grouping = self.screen.grouping
        if grouping is None:
            return
        self.show_bar()
        text = (self.search.value or "").casefold()
        new = self.screen.new_files
        offers: dict[str, list[Offer]] = {}
        for offer in self.sorting.offers:
            offers.setdefault(offer.song, []).append(offer)
        gone = self.screen.gone
        wanted = self.show_filters(
            {
                "new": {
                    s.id
                    for s in grouping.songs
                    if any(m.file.id in new for m in members(s))
                },
                "offers": set(offers),
                "gone": {
                    s.id
                    for s in grouping.songs
                    if any(m.file.id in gone for m in members(s))
                },
            }
        )
        shown = [
            s
            for s in grouping.songs
            if (not text or text in f"{s.title} {' '.join(s.also)}".casefold())
            and (wanted is None or s.id in wanted)
        ]
        self.order = [(s.id, m.file.id) for s in shown for m in (*s.sheets, *s.audio)]
        self.body.clear()
        with self.body:
            if not shown:
                ui.label(
                    "No songs match." if grouping.songs else "No songs yet."
                ).classes("text-grey p-4")
            for song in shown:
                self.row(song, offers.get(song.id, []))

    def row(self, song: GroupedSong, offers: list[Offer]) -> None:
        with ui.row().classes(
            "song-row items-start gap-2 w-full no-wrap py-1 border-b"
        ) as row:
            row.props["data-drop"] = f"song:{song.id}"
            title = (
                ui.button(
                    song.title,
                    icon="edit",
                    on_click=lambda s=song: self.screen.song_box.open(s.id),
                )
                .props("flat dense no-caps align=left")
                .classes("w-56 font-medium song-title")
            )
            title.props["draggable"] = "true"
            title.props["data-title"] = song.id
            tip = "\n".join(
                ["Edit: title, also called, folders, merge, delete (F2)"]
                + [f"Also called: {', '.join(song.also)}"] * bool(song.also)
                + [f"📁 {', '.join(song.folders)}"] * bool(song.folders)
                + ["Drag onto another song to merge them"]
            )
            with title:
                ui.tooltip(tip).classes("whitespace-pre-line text-body2")
            with ui.column().classes("gap-1 grow min-w-0"):
                if not song.sheets and not song.audio:
                    with ui.row().classes("gap-2 items-center"):
                        ui.label("No files: drop some here, or").classes(
                            "text-caption text-grey px-1"
                        )
                        ui.button(
                            "Delete song", on_click=lambda s=song: self.delete(s)
                        ).props("dense flat no-caps color=grey")
                with ui.row().classes("gap-1 items-center") as chips:
                    chips.set_visibility(bool(song.sheets or song.audio))
                    for member in song.sheets:
                        self.chip(song, member)
                    if not song.sheets:
                        ui.label("no sheet").classes("text-caption text-grey px-1")
                    for member in song.audio:
                        self.chip(song, member)
                    if not song.audio:
                        ui.label("no recording").classes("text-caption text-grey px-1")
                for offer in offers:
                    with ui.row().classes("items-center gap-2 text-body2"):
                        ui.icon("subdirectory_arrow_right", size="18px").classes(
                            "text-grey"
                        )
                        ui.label(offer.text)
                        ui.button(
                            "Yes",
                            on_click=lambda o=offer: self.screen.do(
                                lambda: self.sorting.accept(o)
                            ),
                        ).props("dense unelevated no-caps")
                        ui.button("No", on_click=lambda o=offer: self.dismiss(o)).props(
                            "dense flat no-caps"
                        )

    def chip(self, song: GroupedSong, member: Member) -> None:
        key = (song.id, member.file.id)
        marks = " ".join(
            ["removed on server"] * (member.file.id in self.screen.gone)
            + ["✋"] * (member.by == "hand")
            + [f"{len(member.older) + 1} versions"] * bool(member.older)
            + ["×2"] * (self.shared(member.file.id) > 1)
        )
        file_chip(
            member.file,
            member.label,
            member.why,
            marks,
            new=member.file.id in self.screen.new_files,
            selected=key in self.selected,
            on_click=lambda e: self.click(key, e),
            drag_from=song.id,
            menu=lambda: self.chip_menu(song, member),
            preview=self.screen.show_sheet,
        )

    def chip_menu(self, song: GroupedSong, member: Member) -> None:
        """One file's own actions; the selection's are in the bar."""
        file, sorting, do = member.file, self.sorting, self.screen.do
        first = (song.audio if file.kind == "audio" else song.sheets)[0].file
        if file != first:
            ui.menu_item(
                "Make it the default",
                on_click=lambda: do(lambda: sorting.make_first(song.id, file.id)),
            )
        ui.menu_item("Rename label…", on_click=lambda: self.rename_label(member))
        ui.menu_item("Move to…", on_click=lambda: self.move_one(song.id, file.id))
        ui.menu_item(
            "Not in this song",
            on_click=lambda: do(lambda: sorting.back_to_sort([file.id])),
        )
        ui.menu_item(
            "Not a song file", on_click=lambda: do(lambda: sorting.not_song([file.id]))
        )
        if member.older:
            ui.separator()
            ui.label(f"Older versions of this sheet ({len(member.older)})").classes(
                "text-caption text-grey px-4"
            )
            for older in member.older:
                ui.label(older.path.name).classes("text-caption px-6")
        folder = str(PurePosixPath(file.path).parent)
        if folder != ".":
            ui.separator()
            ui.menu_item(
                f"Skip the folder “{PurePosixPath(folder).name}”",
                on_click=lambda: self.screen.skip_folder(file.source, folder),
            )

    def shared(self, file_id: str) -> int:
        return sum(
            any(m.file.id == file_id for m in members(s))
            for s in self.screen.grouping.songs
        )

    # ------------------------------------------------------------ selection

    def click(self, key: tuple[str, str], e: events.GenericEventArguments) -> None:
        if e.args.get("shiftKey") and self.anchor in self.order and key in self.order:
            a, b = sorted((self.order.index(self.anchor), self.order.index(key)))
            self.selected |= set(self.order[a : b + 1])
        else:
            (self.selected.discard if key in self.selected else self.selected.add)(key)
            self.anchor = key
        self.show()

    def show_bar(self) -> None:
        self.bar.clear()
        if not self.selected:
            with self.bar:
                ui.label(
                    "Click files to select them (Shift: a range), or drag them onto a song "
                    "(Ctrl: also add)"
                ).classes("text-caption text-grey")
            return
        with self.bar:
            ui.label(f"{len(self.selected)} selected").classes("text-body2 font-medium")
            for label, key, action in (
                ("Move to…", "M", self.move_selected),
                ("Also add to…", "", self.also_add_selected),
                ("New song…", "N", self.new_song_from_selected),
                ("Not a song file", "Delete", self.not_song_selected),
                ("Not in this song", "", self.back_to_sort_selected),
            ):
                button = ui.button(label, on_click=action).props("dense flat no-caps")
                if key:
                    button.tooltip(key)
            ui.button(icon="close", on_click=self.clear).props(
                "dense flat round"
            ).tooltip("Clear the selection")

    def clear(self) -> None:
        self.selected.clear()
        self.show()

    def files(self) -> list[str]:
        return sorted({file for _, file in self.selected})

    async def move_selected(self) -> None:
        if not self.selected:
            return
        picked = await pick_song(self.screen.titles(), f"Move {len(self.selected)} to")
        if not picked:
            return
        id, title = picked
        if not id:
            self.screen.do(lambda: self.sorting.new_song(self.files(), title))
            return
        # each from its own song: a file shared with a third song stays there
        chosen = [(song, file) for song, file in sorted(self.selected) if song != id]
        if chosen:
            self.screen.do(lambda: self.sorting.move_from(chosen, id))

    async def also_add_selected(self) -> None:
        if not self.selected:
            return
        picked = await pick_song(self.screen.titles(), "Also add to", allow_new=False)
        if picked and picked[0]:
            self.screen.do(lambda: self.sorting.also_add(self.files(), picked[0]))

    async def new_song_from_selected(self) -> None:
        if not self.selected:
            return
        first = next(
            m
            for s in self.screen.grouping.songs
            for m in members(s)
            if m.file.id == self.files()[0]
        )
        answer = await ask_text("New song", first.file.path.stem)
        if answer:
            self.screen.do(lambda: self.sorting.new_song(self.files(), answer[0]))

    async def move_one(self, song: str, file: str) -> None:
        picked = await pick_song(self.screen.titles(), "Move to")
        if not picked:
            return
        id, title = picked
        if not id:
            self.screen.do(lambda: self.sorting.new_song([file], title))
        elif id != song:
            self.screen.do(lambda: self.sorting.move_from([(song, file)], id))

    async def rename_label(self, member: Member) -> None:
        answer = await ask_text(
            "Label (empty: the one made from the name)", member.label, empty_ok=True
        )
        if answer is not None and answer[0] != member.label:
            self.screen.do(lambda: self.sorting.label(member.file.id, answer[0]))

    def not_song_selected(self) -> None:
        if self.selected:
            self.screen.do(lambda: self.sorting.not_song(self.files()))

    def back_to_sort_selected(self) -> None:
        if self.selected:
            self.screen.do(lambda: self.sorting.back_to_sort(self.files()))

    # ------------------------------------------------------------ the song

    def delete(self, song: GroupedSong) -> None:
        self.screen.do(
            lambda: self.sorting.delete(song.id),
            f"Deleted “{song.title}”: its files are back in Unknown files (Undo: Ctrl+Z)",
        )

    def dismiss(self, offer: Offer) -> None:
        self.sorting.dismiss(offer)
        self.show()


def members(song: GroupedSong) -> tuple[Member, ...]:
    return (*song.sheets, *song.audio)
