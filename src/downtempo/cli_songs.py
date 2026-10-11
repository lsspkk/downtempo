"""The sorting on the command line: `downtempo songs [--explain | --to-sort | --create]` and
`downtempo move <file> <song>` (smoke runs, and users without the project screen)."""

from downtempo.errors import UserError
from downtempo.events import count
from downtempo.library import Library
from downtempo.shapes import FileRef, GroupedSong, Member


def songs(library: Library, explain: bool, to_sort: bool, create: bool = False) -> int:
    grouping = library.sorting.grouping()
    if create and grouping.suggestions:
        library.sorting.create(list(grouping.suggestions))
        print(f"Made {count(len(grouping.suggestions), 'song')}.")
        grouping = library.sorting.grouping()
    if not to_sort:
        for song in grouping.songs:
            if explain:
                print_song(song)
            else:
                kinds = [
                    count(len(song.audio), "recording")
                    if song.audio
                    else "no recording",
                    count(len(song.sheets), "sheet") if song.sheets else "no sheet",
                ]
                print(f"{song.title[:30]:32} {', '.join(kinds)}")
        if not grouping.songs:
            print("No songs yet.")
    waiting = sum(len(s.files) for s in grouping.suggestions) + len(grouping.loose)
    if to_sort or explain:
        titles = {s.id: s.title for s in grouping.songs}
        for suggestion in grouping.suggestions:
            files = "  ".join(f.id for f in suggestion.files)
            print(f"? {suggestion.title}    {files}")
        for loose in grouping.loose:
            maybe = (
                f"    maybe: {titles.get(loose.maybe, loose.maybe)}"
                if loose.maybe
                else ""
            )
            print(f"~ {loose.file.id}{maybe}")
        for file in grouping.not_song:
            print(f"- {file.id}    (not a song file)")
    print(
        f"Unknown files: {count(waiting, 'file')} "
        f"({count(len(grouping.suggestions), 'suggested song')}, "
        f"{len(grouping.loose)} loose)"
    )
    return 0


def print_song(song: GroupedSong) -> None:
    extra = [f"also: {'; '.join(song.also)}"] * bool(song.also) + [
        f"folder {'; '.join(song.folders)}"
    ] * bool(song.folders)
    print(song.title + (f"  ({', '.join(extra)})" if extra else ""))
    for icon, member in [("♪", m) for m in song.audio] + [
        ("📄", m) for m in song.sheets
    ]:
        print(f"  {icon} {chip(member):34} {member.file.id:50} {member.why}")


def chip(member: Member) -> str:
    """A file as the screen's chip would say it: label, ✋ by hand, n versions."""
    text = member.label
    if member.older:
        text += f" · {len(member.older) + 1} versions"
    return text + (" ✋" if member.by == "hand" else "")


def move(library: Library, file: str, song: str) -> int:
    id = find_file(library, file)
    target = library.sorting.find_song(song)
    offers = library.sorting.move([id], target)
    title = library.sorting.read().songs[target].title
    print(f"Moved 1 file to {title}.")
    for offer in offers:
        print(f"  Offer: {offer.text}")
    return 0


def find_file(library: Library, text: str) -> str:
    """A file id from the id itself or a unique ending of it (any case)."""
    files: list[FileRef] = library.files()
    ids = [f.id for f in files]
    if text in ids:
        return text
    found = [i for i in ids if i.casefold().endswith(text.casefold())]
    if len(found) == 1:
        return found[0]
    if found:
        raise UserError(f"'{text}' fits {len(found)} files.", "  ".join(found[:5]))
    raise UserError(
        f"There is no file '{text}'.", "See the ids: uv run downtempo songs --explain"
    )
