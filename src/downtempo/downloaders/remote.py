"""What a provider gives back: the `Provider` and `Connection` faces every downloader module has,
and the folders and files it finds. Providers only find files; `sync.py` fetches them."""

import threading
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any, Protocol

from downtempo.events import Report


@dataclass(frozen=True)
class RemoteFolder:
    """An opened folder of a share. `path` is inside the share ("" = the shared folder itself)."""

    name: str
    path: str
    ref: Any = field(compare=False)  # the provider's own handle


@dataclass(frozen=True)
class RemoteFolderInfo:
    """A subfolder for the folder picker: media files at all levels below it."""

    name: str
    path: str  # inside the share
    audio: int
    sheets: int
    folders: int  # subfolders that hold media files


@dataclass(frozen=True)
class RemoteFile:
    """A media file below an opened folder; `path` is relative to that folder."""

    path: PurePosixPath
    size: int | None
    modified: datetime | None
    ref: Any = field(compare=False)


class Connection(Protocol):
    """A signed-in session with one provider; blocking calls, failures raise `UserError`."""

    def open(self, url: str, folder: str = "") -> RemoteFolder: ...

    def folders(self, folder: RemoteFolder) -> list[RemoteFolderInfo]: ...

    def files(self, folder: RemoteFolder) -> Iterator[RemoteFile]:
        """Media files only, all levels down."""
        ...

    def request(self, file: RemoteFile) -> tuple[str, Mapping[str, str]]:
        """A fresh URL and headers to GET the file's content (asked just before downloading)."""
        ...


class Provider(Protocol):
    type: str  # "onedrive", as in sources.toml
    label: str  # "OneDrive", what the user reads

    def owns(self, url: str) -> bool:
        """Whether a pasted link is this provider's; no network."""
        ...

    def account(self) -> str | None:
        """Who is signed in on this computer, from the saved sign-in; None if nobody."""
        ...

    def sign_out(self) -> None: ...

    def connect(self, report: Report, cancel: threading.Event) -> Connection:
        """Signs in when needed (a `SignIn` event); raises `Cancelled` when `cancel` is set."""
        ...
