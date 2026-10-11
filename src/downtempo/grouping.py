"""Song grouping: files + memory → songs, suggestions, loose files. The one entry point is `group`.

Pure and repeatable: the same input gives the same output (every list is sorted), because the CLI
and the screen compare results. The stages live in `names`, `matching`, `suggesting`, `arranging`;
`offers` has the one-time offers. Plan: docs/song-grouping.md."""

from dataclasses import dataclass

from downtempo.arranging import arrange, folder_name
from downtempo.matching import (
    Magnet,
    best_hits,
    folder_songs,
    fuzzy_song,
    magnets,
    named,
    norm_folder,
)
from downtempo.names import Words
from downtempo.shapes import FileRef, Grouping, Loose, Memory, Named, Placement
from downtempo.suggesting import suggest


def group(files: list[FileRef], memory: Memory, words: Words) -> Grouping:
    """Where every file goes. Files with a place in `memory` stay there (sticky); the others are
    matched to songs. The matches made now are in `joined`: the caller saves them, or a later
    change could pull those files to another song."""
    wanted = magnets(memory, words)
    linked = folder_songs(memory)
    placed: dict[str, list[tuple[Named, Placement]]] = {id: [] for id in memory.songs}
    reasons: dict[str, str] = {}
    joined: dict[str, str] = {}
    not_song: list[FileRef] = []
    loose: list[Loose] = []
    to_sort: list[Named] = []
    for item in sorted(
        {f.id: named(f, words) for f in files}.values(), key=lambda n: n.file.id
    ):
        entry = memory.files.get(item.file.id)
        if entry and entry.to_sort:
            to_sort.append(item)
        elif entry and not entry.songs:
            not_song.append(item.file)
        elif entry and (songs := [s for s in entry.songs if s in memory.songs]):
            for song in songs:
                placed[song].append((item, entry))
        elif found := match_file(item, wanted, linked, memory):
            if found.song:
                placed[found.song].append((item, Placement((found.song,), "auto")))
                joined[item.file.id] = found.song
                reasons[item.file.id] = found.why
            else:
                loose.append(Loose(item.file, found.maybe, found.why))
        else:
            to_sort.append(item)
    suggestions, extra = suggest(to_sort, words)
    songs = tuple(
        arrange(song, placed[song.id], memory.first.get(song.id, ()), words, reasons)
        for song in sorted(
            memory.songs.values(), key=lambda s: (s.title.casefold(), s.id)
        )
    )
    return Grouping(
        songs,
        tuple(suggestions),
        tuple(sorted(loose + extra, key=lambda x: x.file.id)),
        tuple(not_song),
        joined,
    )


@dataclass(frozen=True)
class Found:
    """What matching decided about one file: join `song`, or wait as loose (`maybe`, `why`)."""

    song: str = ""
    maybe: str = ""
    why: str = ""


def match_file(
    item: Named, wanted: list[Magnet], linked: dict[str, str], memory: Memory
) -> Found | None:
    """A file with no song: its linked folder, then its name (the longest magnet wins), then
    only a look-alike. None = nothing fits; the file waits in To sort."""
    title = {id: s.title for id, s in memory.songs.items()}
    hits = best_hits(item.name.key, wanted)
    by_name = sorted({h.song for h in hits})
    folder_song = linked.get(norm_folder(item.file.folder), "")
    if folder_song:
        others = [s for s in by_name if s != folder_song]
        if not others:
            name = folder_name(item.file.folder)
            return Found(folder_song, why=f"in the linked folder “{name}”")
        return Found(
            maybe=others[0] if len(others) == 1 else "",
            why=f"in the folder of “{title[folder_song]}” but named like “{title[others[0]]}”",
        )
    if len(by_name) == 1:
        hit = next(h for h in hits if h.song == by_name[0])
        return Found(by_name[0], why=f"name contains “{hit.magnet.text}”")
    if by_name:
        names = " and ".join(f"“{title[s]}”" for s in by_name)
        return Found(why=f"matches {names}")
    if item.name.key and (maybe := fuzzy_song(item.name.key, wanted)):
        return Found(maybe=maybe, why=f"looks like “{title[maybe]}”")
    return None
