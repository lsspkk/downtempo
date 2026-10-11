"""Suggested songs: the files that have no song, proposed as songs for the user to approve.

Stage three of song grouping. A folder holding media directly is a **song folder** when its name
means something and most of its files agree with it; other files join a song folder's title by name;
the rest are grouped by name within the typo tolerance. Pure."""

from collections import Counter
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from downtempo.matching import Magnet, best_hits, related
from downtempo.names import (
    Words,
    clean,
    edit_distance,
    is_type_name,
    letters,
    tolerance,
)
from downtempo.shapes import Loose, Named, Suggestion


@dataclass
class Seed:
    title: str
    key: str
    folder: str = ""  # "source:path" when it came from a song folder
    files: list[Named] = field(default_factory=list)


def suggest(rest: list[Named], words: Words) -> tuple[list[Suggestion], list[Loose]]:
    """Suggestions for `rest`, and the files that can't be one: names that say nothing, or that
    match two suggestions."""
    seeds = song_folders(rest, words)
    taken = {n.file.id for seed in seeds for n in seed.files}
    loose: list[Loose] = []
    remaining: list[Named] = []
    wanted = [
        Magnet(s.key, s.title, tuple(s.key.split()), letters(s.key)) for s in seeds
    ]
    by_key = {s.key: s for s in seeds}
    for n in sorted(
        (n for n in rest if n.file.id not in taken), key=lambda n: n.file.id
    ):
        if not n.name.key:
            loose.append(Loose(n.file, why="the name says nothing about a song"))
            continue
        found = sorted({h.song for h in best_hits(n.name.key, wanted)})
        if len(found) == 1:
            by_key[found[0]].files.append(n)
        elif found:
            titles = " and ".join(f"“{by_key[k].title}”" for k in found)
            loose.append(Loose(n.file, why=f"matches {titles}"))
        else:
            remaining.append(n)
    suggestions = seeds + group_by_key(remaining)
    return (
        sorted(
            (
                Suggestion(
                    s.title,
                    tuple(sorted((n.file for n in s.files), key=lambda f: f.id)),
                    s.folder,
                )
                for s in suggestions
            ),
            key=lambda s: (s.title.casefold(), s.title),
        ),
        loose,
    )


def song_folders(rest: list[Named], words: Words) -> list[Seed]:
    """Folders with a meaningful name whose direct files mostly agree with it (a file with an
    empty key agrees). `Set 1/` or `Songs/` with several songs in it is not one."""
    by_folder: dict[str, list[Named]] = {}
    for n in rest:
        by_folder.setdefault(n.file.folder, []).append(n)
    seeds: dict[str, Seed] = {}
    for folder, members in sorted(by_folder.items()):
        name = PurePosixPath(folder.partition(":")[2]).name
        cleaned = clean(name, words) if name else None
        if not cleaned or not cleaned.key or is_type_name(cleaned.key, words):
            continue
        agree = sum(
            1 for n in members if not n.name.key or related(n.name.key, cleaned.key)
        )
        if agree < len(members) - agree:
            continue
        seed = seeds.setdefault(cleaned.key, Seed(cleaned.title, cleaned.key, folder))
        seed.files += members
    return list(seeds.values())


def group_by_key(files: list[Named]) -> list[Seed]:
    """Files whose keys are the same within the tolerance make one suggestion; its title is the
    most common spelling (ties: A–Z)."""
    clusters: list[Seed] = []
    for n in sorted(files, key=lambda n: (n.name.key, n.file.id)):
        for cluster in clusters:
            wanted = letters(cluster.key)
            if edit_distance(
                letters(n.name.key), wanted, tolerance(len(wanted))
            ) <= tolerance(len(wanted)):
                cluster.files.append(n)
                break
        else:
            clusters.append(Seed("", n.name.key, files=[n]))
    for cluster in clusters:
        counts = Counter(n.name.title for n in cluster.files)
        cluster.title = min(counts, key=lambda title: (-counts[title], title))
    return clusters
