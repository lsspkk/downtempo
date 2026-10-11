"""The data shapes of song grouping: files in, `Memory` in, a `Grouping` out. Plain dataclasses, no
logic beyond a few properties. The stages that use them: `matching`, `suggesting`, `arranging`,
`grouping` (docs/song-grouping.md, docs/song-grouping-tasks.md)."""

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import PurePosixPath
from typing import Literal

from downtempo.config import AUDIO_EXTENSIONS, SHEET_EXTENSIONS
from downtempo.names import Cleaned


@dataclass(frozen=True)
class FileRef:
    source: str  # source name in the project
    path: PurePosixPath  # inside the source, as on the server
    kind: Literal["audio", "sheet"]
    size: int | None = None
    modified: datetime | None = None

    @property
    def id(self) -> str:
        return f"{self.source}:{self.path}"

    @property
    def folder(self) -> str:
        """`source:folder` of the folder it is in; `source:` for the source's top level."""
        parent = "" if str(self.path.parent) == "." else str(self.path.parent)
        return f"{self.source}:{parent}"

    @property
    def day(self) -> date:
        return self.modified.date() if self.modified else date.min

    @classmethod
    def from_id(
        cls, id: str, size: int | None = None, modified: datetime | None = None
    ) -> "FileRef":
        """A file from its id; the kind comes from the ending."""
        source, _, rest = id.partition(":")
        path = PurePosixPath(rest)
        kind = "sheet" if path.suffix.lower() in SHEET_EXTENSIONS else "audio"
        if path.suffix.lower() not in AUDIO_EXTENSIONS | SHEET_EXTENSIONS:
            raise ValueError(f"'{id}' is not an audio or sheet file")
        return cls(source, path, kind, size, modified)


@dataclass(frozen=True)
class Named:
    """A file with its cleaned name (the ending is not part of it)."""

    file: FileRef
    name: Cleaned


@dataclass(frozen=True)
class SongMemory:
    id: str
    title: str
    also: tuple[str, ...] = ()
    folders: tuple[str, ...] = ()  # "source:path"


@dataclass(frozen=True)
class Placement:
    songs: tuple[str, ...]  # song ids; () and not to_sort = not a song file
    by: Literal["auto", "hand"]
    label: str = ""  # "" = the computed label
    to_sort: bool = False  # sent back to To sort: stays there, magnets leave it


@dataclass(frozen=True)
class Memory:
    songs: dict[str, SongMemory] = field(default_factory=dict)
    files: dict[str, Placement] = field(
        default_factory=dict
    )  # entries of gone files stay
    first: dict[str, tuple[str, ...]] = field(default_factory=dict)  # song → file ids
    words_add: tuple[str, ...] = ()
    words_keep: tuple[str, ...] = ()


@dataclass(frozen=True)
class Member:
    """A file in a song, as shown."""

    file: FileRef
    by: str
    label: str
    why: str  # “name contains “harbour waltz””, “in the linked folder …”, “you placed it”
    # sheets: older versions folded under this one
    older: tuple[FileRef, ...] = ()


@dataclass(frozen=True)
class GroupedSong:
    id: str
    title: str
    also: tuple[str, ...]
    folders: tuple[str, ...]
    audio: tuple[Member, ...]  # display order, default first
    sheets: tuple[Member, ...]


@dataclass(frozen=True)
class Suggestion:
    title: str
    files: tuple[FileRef, ...]
    folder: str = ""  # "source:path" to link on Create


@dataclass(frozen=True)
class Loose:
    file: FileRef
    maybe: str = ""  # a song id: the one-click suggestion
    why: str = ""


@dataclass(frozen=True)
class Offer:
    kind: Literal["gather", "better"]
    song: str
    files: tuple[str, ...]
    text: str


@dataclass(frozen=True)
class Grouping:
    songs: tuple[GroupedSong, ...]
    suggestions: tuple[Suggestion, ...]
    loose: tuple[Loose, ...]
    not_song: tuple[FileRef, ...]
    joined: dict[
        str, str
    ]  # file id → song id: auto placements made by this run; the caller saves them
