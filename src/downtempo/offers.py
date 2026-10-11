"""One-time offers after the user's actions (never stored as rules): gather similar files after a drag,
move files to a song that fits them better after a new song, a rename or a new alias. Pure.
Plan: docs/song-grouping.md ("What the user's actions do")."""

from pathlib import PurePosixPath

from downtempo.matching import Hit, best_hits, find_hits, magnets
from downtempo.names import Words, clean, letters
from downtempo.shapes import FileRef, Grouping, Memory, Offer


def gather_offer(
    grouping: Grouping, memory: Memory, words: Words, moved: str, song: str
) -> Offer | None:
    """After `moved` was placed in `song` (`grouping` is made after the move): files in To sort named
    like what is left of its name once the song's own name is taken out, when that is something."""
    parts = clean(PurePosixPath(moved.partition(":")[2]).stem, words).key.split()
    every = magnets(memory, words)
    covered = {
        i
        for h in best_hits(" ".join(parts), [m for m in every if m.song == song])
        for i in range(h.start, h.end)
    }
    rest = [w for i, w in enumerate(parts) if i not in covered]
    if len(letters("".join(rest))) < 2:
        return None
    if best_hits(" ".join(rest), [m for m in every if m.song != song]):
        return None  # what's left is another song's name
    waiting = [f for s in grouping.suggestions for f in s.files] + [
        x.file for x in grouping.loose
    ]
    found = sorted(
        f.id
        for f in waiting
        if f.id != moved and contains(clean(f.path.stem, words).key.split(), rest)
    )
    if not found:
        return None
    text = f"Also collect files named “{' '.join(rest)} …”? {len(found)} more in To sort match"
    return Offer("gather", song, tuple(found), text)


def contains(parts: list[str], run: list[str]) -> bool:
    return any(parts[i : i + len(run)] == run for i in range(len(parts) - len(run) + 1))


def size(hits: list[Hit]) -> tuple[int, int]:
    """How much of a name the longest magnet covers: words, then letters."""
    return max(
        ((len(h.magnet.words), len(h.magnet.letters)) for h in hits), default=(0, 0)
    )


def better_offers(
    files: list[FileRef], memory: Memory, words: Words, song: str
) -> list[Offer]:
    """Files that matching placed in another song by a shorter name than `song` has: one offer
    per other song. Files the user placed are never offered."""
    every = magnets(memory, words)
    mine = [m for m in every if m.song == song]
    found: dict[str, list[str]] = {}
    for f in files:
        placement = memory.files.get(f.id)
        if not placement or placement.by != "auto" or len(placement.songs) != 1:
            continue
        other = placement.songs[0]
        if other == song or other not in memory.songs:
            continue
        key = clean(f.path.stem, words).key
        theirs = [m for m in every if m.song == other]
        if size(find_hits(key, mine)) > size(find_hits(key, theirs)):
            found.setdefault(other, []).append(f.id)
    title = memory.songs[song].title
    return [
        Offer(
            "better",
            song,
            tuple(sorted(ids)),
            f"“{title}” better matches {len(ids)} file{'s' * (len(ids) != 1)} "
            f"in “{memory.songs[other].title}”",
        )
        for other, ids in sorted(found.items())
    ]
