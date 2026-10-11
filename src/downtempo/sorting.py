"""The user's sorting: the operations on `grouping.json` (create songs, move files, rename, merge …),
undo / redo, and the one-time offers after an action. `Library.sorting` is one of these per project.

Every operation: remember the memory (for undo) → change it → group again and save the matches made
now (so they stay put) → work out the offers. Plan and operations table: docs/song-grouping.md.
"""

import difflib
import unicodedata
from collections.abc import Callable
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from downtempo.errors import UserError
from downtempo.grouping import group
from downtempo.matching import reach
from downtempo.memory_file import read_memory, write_memory
from downtempo.names import Words, words_for
from downtempo.offers import better_offers, gather_offer
from downtempo.shapes import (
    FileRef,
    Grouping,
    Memory,
    Offer,
    Placement,
    SongMemory,
    Suggestion,
)
from downtempo.skipping import check_folder
from downtempo.sources import free_id

if TYPE_CHECKING:
    from downtempo.library import Library

MAX_UNDO = 50
MAX_TITLE = 120

type Change = Callable[[Memory, Grouping], Memory]
type Offering = Callable[[Memory, Grouping, list[FileRef]], list[Offer]]


class Sorting:
    def __init__(self, library: "Library") -> None:
        self.library = library
        self.path = library.root / "grouping.json"
        self.offers: list[Offer] = []  # pending: the last operation's, never saved
        self.raw: dict[str, Any] = {}
        self.undo_stack: list[Memory] = []
        self.redo_stack: list[Memory] = []

    # ------------------------------------------------------------ reading

    def read(self) -> Memory:
        memory, self.raw = read_memory(self.path)
        return memory

    def words(self, memory: Memory) -> Words:
        return words_for(memory.words_add, memory.words_keep)

    def grouping(self) -> Grouping:
        """The project's songs, suggestions and loose files now. Matches made by this call are saved
        as automatic placements, so they stay where they are."""
        return self.settle(self.read(), self.library.files())[1]

    def settle(self, memory: Memory, files: list[FileRef]) -> tuple[Memory, Grouping]:
        result = group(files, memory, self.words(memory))
        if result.joined:
            placed = {
                id: Placement((song,), "auto") for id, song in result.joined.items()
            }
            memory = replace(memory, files={**memory.files, **placed})
            self.save(memory)
        return memory, result

    def save(self, memory: Memory) -> None:
        self.raw = write_memory(self.path, memory, self.raw)

    def replace_memory(self, memory: Memory) -> None:
        """Take a whole memory (a settings-file import); undo goes back to what was here."""
        self.undo_stack = [*self.undo_stack, self.read()][-MAX_UNDO:]
        self.redo_stack = []
        self.offers = []
        self.save(memory)
        self.refresh()

    def reach(self, texts: list[str], folders: list[str]) -> int:
        """How many of the project's files these names or folders reach (live in the edit box)."""
        memory = self.read()
        return len(reach(self.library.files(), texts, folders, self.words(memory)))

    def folders(self) -> list[str]:
        """Every folder (`source:path`) that holds a file: what a song can be linked to."""
        return sorted({f.folder for f in self.library.files()}, key=str.casefold)

    def find_song(self, text: str) -> str:
        """A song id from an id, a title or an also-called name (any case)."""
        memory = self.read()
        wanted = text.strip().casefold()
        for id, song in memory.songs.items():
            if wanted in (
                id,
                song.title.casefold(),
                *(a.casefold() for a in song.also),
            ):
                return id
        titles = [s.title for s in memory.songs.values()]
        close = difflib.get_close_matches(text.strip(), titles, n=3, cutoff=0.5)
        raise UserError(
            f"There is no song called '{text}'.",
            f"Did you mean: {', '.join(close)}?" if close else "",
        )

    # ------------------------------------------------------------ running an operation

    def run(self, change: Change, offering: Offering | None = None) -> list[Offer]:
        files = self.library.files()
        base, before = self.settle(self.read(), files)
        after = change(base, before)
        self.undo_stack = [*self.undo_stack, base][-MAX_UNDO:]
        self.redo_stack = []
        self.save(after)
        memory, now = self.settle(after, files)
        self.library.publish(now)
        self.offers = offering(memory, now, files) if offering else []
        return self.offers

    def refresh(self) -> None:
        """Write `songs.json` again from the memory on disk (after undo, redo or an import)."""
        _, result = self.settle(self.read(), self.library.files())
        self.library.publish(result)

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        self.redo_stack.append(self.read())
        self.save(self.undo_stack.pop())
        self.offers = []
        self.refresh()
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            return False
        self.undo_stack.append(self.read())
        self.save(self.redo_stack.pop())
        self.offers = []
        self.refresh()
        return True

    # ------------------------------------------------------------ songs

    def create(self, suggestions: list[Suggestion]) -> list[Offer]:
        """Make a song of each suggestion; matching then pulls in other To-sort files at once."""
        made: list[str] = []

        def change(memory: Memory, _: Grouping) -> Memory:
            songs, files = dict(memory.songs), dict(memory.files)
            for s in suggestions:
                id = free_id(check_title(s.title), set(songs), "song")
                if s.folder:
                    check_folder(s.folder.partition(":")[2])
                folders = (s.folder,) if s.folder else ()
                songs[id] = SongMemory(id, s.title.strip(), (), folders)
                files |= {f.id: Placement((id,), "auto") for f in s.files}
                made.append(id)
            return replace(memory, songs=songs, files=files)

        return self.run(change, lambda m, g, files: self.better(m, files, made))

    def new_song(self, files: list[str], title: str) -> list[Offer]:
        """A song with `title`, holding `files` (placed by hand)."""
        made: list[str] = []

        def change(memory: Memory, _: Grouping) -> Memory:
            self.need_files(files)
            id = free_id(check_title(title), set(memory.songs), "song")
            made.append(id)
            songs = {**memory.songs, id: SongMemory(id, title.strip())}
            return place(replace(memory, songs=songs), files, id)

        def offering(m: Memory, g: Grouping, all_files: list[FileRef]) -> list[Offer]:
            gather = gather_offer(g, m, self.words(m), files[0], made[0])
            return [*([gather] if gather else []), *self.better(m, all_files, made)]

        return self.run(change, offering)

    def rename(self, song: str, title: str, keep_old: bool = True) -> list[Offer]:
        """The files stay. The old title becomes an also-called name unless `keep_old` is off
        (fixing a wrong title)."""

        def change(memory: Memory, _: Grouping) -> Memory:
            old = need_song(memory, song)
            title_ = check_title(title)
            also = [a for a in old.also if a.casefold() != title_.casefold()]
            if keep_old and old.title.casefold() != title_.casefold():
                also.append(old.title)
            return with_song(memory, replace(old, title=title_, also=unique(also)))

        return self.run(change, lambda m, g, files: self.better(m, files, [song]))

    def alias(self, song: str, add: str = "", remove: str = "") -> list[Offer]:
        """Add or remove an also-called name; removing moves nothing."""

        def change(memory: Memory, _: Grouping) -> Memory:
            old = need_song(memory, song)
            also = [a for a in old.also if a.casefold() != remove.strip().casefold()]
            if add.strip() and add.strip().casefold() != old.title.casefold():
                also.append(check_title(add))
            return with_song(memory, replace(old, also=unique(also)))

        offering: Offering | None = (
            (lambda m, g, files: self.better(m, files, [song])) if add.strip() else None
        )
        return self.run(change, offering)

    def link_folder(self, song: str, folder: str) -> list[Offer]:
        """Link a folder (`source:path`): its files with no song join this one."""

        def change(memory: Memory, now: Grouping) -> Memory:
            old = need_song(memory, song)
            source, _, path = folder.partition(":")
            self.library.source(source)
            linked = f"{source}:{check_folder(path)}"
            for other in memory.songs.values():
                if linked.casefold() in {f.casefold() for f in other.folders}:
                    raise UserError(
                        f"That folder is already linked to “{other.title}”."
                    )
            return with_song(memory, replace(old, folders=(*old.folders, linked)))

        return self.run(change)

    def unlink_folder(self, song: str, folder: str) -> list[Offer]:
        def change(memory: Memory, _: Grouping) -> Memory:
            old = need_song(memory, song)
            kept = tuple(f for f in old.folders if f.casefold() != folder.casefold())
            return with_song(memory, replace(old, folders=kept))

        return self.run(change)

    def merge(self, song: str, into: str) -> list[Offer]:
        """`into` gets the files of `song`, its title and also-called names, and its folders."""

        def change(memory: Memory, _: Grouping) -> Memory:
            gone, keep = need_song(memory, song), need_song(memory, into)
            if song == into:
                raise UserError("A song can't be merged into itself.")
            also = [*keep.also, gone.title, *gone.also]
            also = [a for a in also if a.casefold() != keep.title.casefold()]
            merged = replace(
                keep,
                also=unique(also),
                folders=unique([*keep.folders, *gone.folders]),
            )
            files = {
                id: replace(
                    p, songs=unique([into if s == song else s for s in p.songs])
                )
                if song in p.songs
                else p
                for id, p in memory.files.items()
            }
            songs = {id: s for id, s in memory.songs.items() if id != song}
            songs[into] = merged
            first = {id: ids for id, ids in memory.first.items() if id != song}
            return replace(memory, songs=songs, files=files, first=first)

        return self.run(change)

    def delete(self, song: str) -> list[Offer]:
        """Its names and folder links go; its files return to To sort as if new, except files that
        are also in another song."""

        def change(memory: Memory, _: Grouping) -> Memory:
            need_song(memory, song)
            files = {}
            for id, p in memory.files.items():
                if song not in p.songs:
                    files[id] = p
                elif remaining := tuple(s for s in p.songs if s != song):
                    files[id] = replace(p, songs=remaining)
            songs = {id: s for id, s in memory.songs.items() if id != song}
            first = {id: ids for id, ids in memory.first.items() if id != song}
            return replace(memory, songs=songs, files=files, first=first)

        return self.run(change)

    # ------------------------------------------------------------ files

    def move(self, files: list[str], song: str, from_song: str = "") -> list[Offer]:
        """Place files in a song by hand. With `from_song`, only that song is replaced (a file in
        two songs stays in the other)."""

        def change(memory: Memory, _: Grouping) -> Memory:
            self.need_files(files)
            need_song(memory, song)
            return place(memory, files, song, from_song)

        def offering(m: Memory, g: Grouping, _files: list[FileRef]) -> list[Offer]:
            offer = gather_offer(g, m, self.words(m), files[0], song)
            return [offer] if offer else []

        return self.run(change, offering)

    def move_from(self, chosen: list[tuple[str, str]], song: str) -> list[Offer]:
        """`move` of (from song, file) pairs picked in several songs, as one undo step."""
        files = [file for _, file in chosen]

        def change(memory: Memory, _: Grouping) -> Memory:
            self.need_files(files)
            need_song(memory, song)
            for from_song, file in chosen:
                memory = place(memory, [file], song, from_song)
            return memory

        def offering(m: Memory, g: Grouping, _files: list[FileRef]) -> list[Offer]:
            offer = gather_offer(g, m, self.words(m), files[0], song)
            return [offer] if offer else []

        return self.run(change, offering)

    def also_add(self, files: list[str], song: str) -> list[Offer]:
        """The files are in this song too (by hand)."""

        def change(memory: Memory, _: Grouping) -> Memory:
            self.need_files(files)
            need_song(memory, song)
            placed = dict(memory.files)
            for id in files:
                old = placed.get(id)
                songs = unique([*(old.songs if old else ()), song])
                placed[id] = Placement(songs, "hand", old.label if old else "")
            return replace(memory, files=placed)

        return self.run(change)

    def not_song(self, files: list[str]) -> list[Offer]:
        """Set files aside: hidden, still downloaded."""
        return self.run(lambda m, g: self.mark(m, files, to_sort=False))

    def back_to_sort(self, files: list[str]) -> list[Offer]:
        """Send files back to To sort; magnets leave them there."""
        return self.run(lambda m, g: self.mark(m, files, to_sort=True))

    def mark(self, memory: Memory, files: list[str], to_sort: bool) -> Memory:
        self.need_files(files)
        marked = {id: Placement((), "hand", "", to_sort) for id in files}
        return replace(memory, files={**memory.files, **marked})

    def label(self, file: str, text: str) -> list[Offer]:
        """A label of your own for a file in a song; "" brings back the computed one."""

        def change(memory: Memory, _: Grouping) -> Memory:
            old = memory.files.get(file)
            if not old or not old.songs:
                raise UserError("Put the file in a song first.")
            label = text.strip()
            if len(label) > MAX_TITLE or (label and not label.isprintable()):
                raise UserError(f"A label is at most {MAX_TITLE} printable characters.")
            return replace(
                memory, files={**memory.files, file: replace(old, label=label)}
            )

        return self.run(change)

    def make_first(self, song: str, file: str) -> list[Offer]:
        """The file becomes the song's default (first); the others keep their order."""

        def change(memory: Memory, now: Grouping) -> Memory:
            need_song(memory, song)
            grouped = next(s for s in now.songs if s.id == song)
            order = [m.file.id for m in (*grouped.audio, *grouped.sheets)]
            if file not in order:
                raise UserError("That file isn't in the song.")
            first = {**memory.first, song: (file, *[i for i in order if i != file])}
            return replace(memory, first=first)

        return self.run(change)

    # ------------------------------------------------------------ offers

    def accept(self, offer: Offer) -> list[Offer]:
        """Do what an offer said: gathered files are placed by hand; better-match files move and
        stay automatic."""
        pending = [o for o in self.offers if o != offer]

        def change(memory: Memory, _: Grouping) -> Memory:
            need_song(memory, offer.song)
            placed = dict(memory.files)
            for id in offer.files:
                old = placed.get(id)
                by = "hand" if offer.kind == "gather" else "auto"
                placed[id] = Placement((offer.song,), by, old.label if old else "")
            return replace(memory, files=placed)

        self.run(change)
        self.offers = pending
        return pending

    def dismiss(self, offer: Offer) -> None:
        self.offers = [o for o in self.offers if o != offer]

    def better(
        self, memory: Memory, files: list[FileRef], songs: list[str]
    ) -> list[Offer]:
        return [
            offer
            for song in songs
            if song in memory.songs
            for offer in better_offers(files, memory, self.words(memory), song)
        ]

    def need_files(self, ids: list[str]) -> None:
        if not ids:
            raise UserError("No files chosen.")
        known = {f.id for f in self.library.files()} | set(self.read().files)
        for id in ids:
            if id not in known:
                raise UserError(f"There is no file '{id}'.")


def need_song(memory: Memory, id: str) -> SongMemory:
    if id not in memory.songs:
        raise UserError(f"There is no song '{id}'.")
    return memory.songs[id]


def with_song(memory: Memory, song: SongMemory) -> Memory:
    return replace(memory, songs={**memory.songs, song.id: song})


def place(memory: Memory, files: list[str], song: str, from_song: str = "") -> Memory:
    """`files` into `song` by hand; with `from_song` only that song is replaced."""
    placed = dict(memory.files)
    for id in files:
        old = placed.get(id)
        songs = (song,)
        if from_song and old and from_song in old.songs:
            songs = unique([song if s == from_song else s for s in old.songs])
        placed[id] = Placement(songs, "hand", old.label if old else "")
    return replace(memory, files=placed)


def unique[T](items: list[T]) -> tuple[T, ...]:
    return tuple(dict.fromkeys(items))


def check_title(text: str) -> str:
    """A title or also-called name, trimmed."""
    text = unicodedata.normalize("NFC", text.strip())
    if not text:
        raise UserError("The name is empty.")
    if len(text) > MAX_TITLE or not text.isprintable():
        raise UserError(f"A name is at most {MAX_TITLE} printable characters.")
    return text
