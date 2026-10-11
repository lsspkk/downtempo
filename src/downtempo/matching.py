"""Matching a file's name or folder against songs' magnets (title, also-called names, linked folders).

Stage two of song grouping: whole words and the typo tolerance (0 / 1 / 2 letters by the magnet's
length), the longest magnet wins, "looks similar" only suggests. Pure."""

import unicodedata
from dataclasses import dataclass

from downtempo.names import Words, clean, edit_distance, letters, similar, tolerance
from downtempo.shapes import FileRef, Memory, Named


@dataclass(frozen=True)
class Magnet:
    song: str
    text: str  # as written, for "why"
    words: tuple[str, ...]
    letters: str


@dataclass(frozen=True)
class Hit:
    song: str
    magnet: Magnet
    start: int  # the words of the file's key it covers
    end: int
    distance: int


def named(file: FileRef, words: Words) -> Named:
    return Named(file, clean(file.path.stem, words))


def magnet_of(song: str, text: str, words: Words) -> Magnet | None:
    key = clean(text, words).key
    return Magnet(song, text, tuple(key.split()), letters(key)) if key else None


def magnets(memory: Memory, words: Words) -> list[Magnet]:
    found = []
    for id in sorted(memory.songs):
        song = memory.songs[id]
        for text in (song.title, *song.also):
            if magnet := magnet_of(id, text, words):
                found.append(magnet)
    return found


def norm_folder(folder: str) -> str:
    return unicodedata.normalize("NFC", folder).casefold()


def folder_songs(memory: Memory) -> dict[str, str]:
    """Linked folder (`source:path`, any case) → the song it is linked to."""
    found: dict[str, str] = {}
    for id in sorted(memory.songs):
        for folder in memory.songs[id].folders:
            found.setdefault(norm_folder(folder), id)
    return found


def find_hits(key: str, wanted: list[Magnet]) -> list[Hit]:
    """Every run of a magnet's number of words in `key`, and the whole key, within the tolerance."""
    parts = key.split()
    if not parts:
        return []
    hits = []
    for magnet in wanted:
        k = len(magnet.words)
        limit = tolerance(len(magnet.letters))
        spans = {(i, i + k) for i in range(len(parts) - k + 1)} | {(0, len(parts))}
        for start, end in sorted(spans):
            distance = edit_distance("".join(parts[start:end]), magnet.letters, limit)
            if distance <= limit:
                hits.append(Hit(magnet.song, magnet, start, end, distance))
    return hits


def best_hits(key: str, wanted: list[Magnet]) -> list[Hit]:
    """The longest magnet wins: a hit inside a longer one's words is dropped; of equal spans only
    the smallest distance stays."""
    hits = find_hits(key, wanted)

    def inside(hit: Hit, other: Hit) -> bool:
        return (
            other.start <= hit.start
            and hit.end <= other.end
            and other.end - other.start > hit.end - hit.start
        )

    hits = [h for h in hits if not any(inside(h, o) for o in hits)]
    nearest: dict[tuple[int, int], int] = {}
    for hit in hits:
        span = (hit.start, hit.end)
        nearest[span] = min(nearest.get(span, hit.distance), hit.distance)
    return [h for h in hits if h.distance == nearest[(h.start, h.end)]]


def related(a: str, b: str) -> bool:
    """One key contains the other (whole words, within the tolerance)."""
    if not a or not b:
        return False
    one = Magnet("", a, tuple(a.split()), letters(a))
    other = Magnet("", b, tuple(b.split()), letters(b))
    return bool(find_hits(b, [one]) or find_hits(a, [other]))


def fuzzy_song(key: str, wanted: list[Magnet]) -> str:
    """The one song whose magnet reads like `key`; "" when none or several do."""
    songs = {m.song for m in wanted if similar(key, " ".join(m.words))}
    return songs.pop() if len(songs) == 1 else ""


def reach(
    files: list[FileRef], texts: list[str], folders: list[str], words: Words
) -> list[FileRef]:
    """The files these names (whole words, within the tolerance) or linked folders reach: the song
    edit box's live "matches n files". Whether a file would join also depends on other songs."""
    wanted = [m for t in texts if (m := magnet_of("", t, words))]
    linked = {norm_folder(f) for f in folders}
    return [
        f
        for f in files
        if norm_folder(f.folder) in linked
        or find_hits(clean(f.path.stem, words).key, wanted)
    ]
