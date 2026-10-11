"""What a song looks like once its files are known: a label for each file, sheet versions folded
together, a display order, and why each file is here. Stage four of song grouping. Pure."""

from dataclasses import dataclass
from pathlib import PurePosixPath

from downtempo.matching import (
    best_hits,
    magnet_of,
    norm_folder,
)
from downtempo.names import Words, clean, is_type_name
from downtempo.shapes import GroupedSong, Member, Named, Placement, SongMemory


@dataclass
class Row:
    named: Named
    placement: Placement
    label: str
    why: str
    own: bool  # in the song's own (linked or same-named) folder


def folder_name(folder: str) -> str:
    return PurePosixPath(folder.partition(":")[2]).name


def arrange(
    song: SongMemory,
    members: list[tuple[Named, Placement]],
    first: tuple[str, ...],
    words: Words,
    reasons: dict[str, str],
) -> GroupedSong:
    """`reasons` holds the "why" of files that joined in this run; the others get theirs here."""
    wanted = [
        m for t in (song.title, *song.also) if (m := magnet_of(song.id, t, words))
    ]
    own_keys = {" ".join(m.words) for m in wanted}
    linked = {norm_folder(f): f for f in song.folders}
    rows = []
    for named, placement in members:
        folder = named.file.folder
        own = norm_folder(folder) in linked or (
            clean(folder_name(folder), words).key in own_keys
        )
        linked_name = linked.get(norm_folder(folder), "")
        if named.file.id in reasons:
            why = reasons[named.file.id]
        elif placement.by == "hand":
            why = "you placed it"
        elif linked_name:
            why = f"in the linked folder “{folder_name(folder) or linked_name}”"
        elif hits := best_hits(named.name.key, wanted):
            why = f"name contains “{hits[0].magnet.text}”"
        else:
            why = "placed when the song was made"
        label = placement.label or default_label(named, own, words)
        rows.append(Row(named, placement, label, why, own))
    song_key = " ".join(wanted[0].words) if wanted else ""
    index = {id: i for i, id in enumerate(first)}
    audio = sorted(
        (r for r in rows if r.named.file.kind == "audio"),
        key=lambda r: audio_rank(r, index, song_key),
    )
    sheets = fold_versions([r for r in rows if r.named.file.kind == "sheet"], index)
    return GroupedSong(
        song.id,
        song.title,
        song.also,
        song.folders,
        tuple(member(r) for r in audio),
        tuple(sheets),
    )


def default_label(named: Named, own: bool, words: Words) -> str:
    """The container folder (unless it is the song's own, or only a type word like `Uudet`) and
    the extras: `Rehearsal 9.10.2026 · 2`; when there are neither, the file name."""
    folder = "" if own else folder_name(named.file.folder)
    if folder and type_folder(folder, words):
        folder = ""
    parts = [p for p in (folder, " ".join(named.name.extras)) if p]
    return " · ".join(parts) or named.file.path.stem


def type_folder(name: str, words: Words) -> bool:
    """`Uudet`, `Audio`: says what kind of files are inside, not which song or rehearsal."""
    cleaned = clean(name, words)
    return is_type_name(cleaned.key, words) or not (cleaned.key or cleaned.extras)


def audio_rank(row: Row, index: dict[str, int], song_key: str) -> tuple:
    """The user's first choice, then the plain recording, then the song's own folder, then the one
    with the fewest extras, then by date."""
    n = row.named
    main = n.name.key == song_key and not n.name.extras
    return (
        index.get(n.file.id, len(index)),
        not main,
        not row.own,
        len(n.name.extras),
        n.name.date or n.file.day,
        n.file.id,
    )


def newest(row: Row) -> tuple:
    n = row.named
    return (n.name.date or n.file.day, n.file.id)


def fold_versions(rows: list[Row], index: dict[str, int]) -> list[Member]:
    """Sheets with the same key and the same tags (`soinnut`, a key) are versions of one another:
    the newest shows, the older ones go under it. Newest sheet first."""
    groups: dict[tuple, list[Row]] = {}
    for row in rows:
        n = row.named.name
        groups.setdefault((n.key, tuple(t.casefold() for t in n.tags)), []).append(row)
    ordered = []
    for group in groups.values():
        group.sort(key=newest, reverse=True)
        position = min(index.get(r.named.file.id, len(index)) for r in group)
        ordered.append((position, group))
    ordered.sort(
        key=lambda p: (p[0], [-newest(p[1][0])[0].toordinal()], p[1][0].named.file.id)
    )
    return [
        member(group[0], tuple(r.named.file for r in group[1:])) for _, group in ordered
    ]


def member(row: Row, older: tuple = ()) -> Member:
    return Member(row.named.file, row.placement.by, row.label, row.why, older)
