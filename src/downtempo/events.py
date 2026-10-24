"""What long work reports while it runs (docs/blocks.md#apis), and `print_report` for the CLI.

The core never prints: a download gets a `report` callback and calls it with these events, from
whatever thread it runs on. The CLI passes `print_report`; the player queues them for the UI.
"""

import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from downtempo.config import DATA_DIR, PROJECT_DIR
from downtempo.errors import UserError


@dataclass(frozen=True)
class SignIn:
    """The user must open `url` and type `code` before `expires_at` (Unix time)."""

    provider: str
    url: str
    code: str
    expires_at: float


@dataclass(frozen=True)
class Checking:
    """Listing a source's files on the server."""

    source: str


@dataclass(frozen=True)
class Planned:
    """What a source's update will do; `bytes` is what will be downloaded, `compress` the wavs
    already here to make into mp3."""

    source: str
    new: int
    updated: int
    same: int
    gone: int
    bytes: int
    compress: int = 0


@dataclass(frozen=True)
class Fetching:
    """Download progress in bytes: once with `done` 0 when it starts, then about every MB. A wav
    already here being made into an mp3 (`compressed`) reports only the start."""

    source: str
    path: Path
    status: Literal["new", "updated", "compressed"]
    done: int
    total: int | None


@dataclass(frozen=True)
class Saved:
    source: str
    path: Path
    status: Literal["new", "updated", "compressed"]


@dataclass(frozen=True)
class Skipped:
    source: str
    path: Path
    reason: str


@dataclass(frozen=True)
class Failed:
    """A source (or a whole job when `source` is "") stopped with an error; others go on."""

    source: str
    error: UserError


type Event = SignIn | Checking | Planned | Fetching | Saved | Skipped | Failed
type Report = Callable[[Event], None]


def shown(path: Path) -> Path:
    """A path as short as it can be read: inside the data folder, else the project."""
    for base in (DATA_DIR, PROJECT_DIR):
        if path.is_relative_to(base):
            return path.relative_to(base)
    return path


def size(count: int) -> str:
    """Bytes for people: 980 KB, 12.4 MB, 1.2 GB."""
    for unit, scale in (("GB", 1 << 30), ("MB", 1 << 20)):
        if count >= scale:
            return f"{count / scale:.1f} {unit}"
    return f"{max(count >> 10, 1 if count else 0)} KB"


def count(number: int, word: str) -> str:
    """`1 recording`, `3 recordings`."""
    return f"{number} {word}{'s' * (number != 1)}"


def plan_line(event: Planned) -> str:
    """`5 new, 1 changed, 23 up to date (180.2 MB to download)`, and files gone from the server."""
    parts = [
        f"{event.new} new" if event.new else "",
        f"{event.updated} changed" if event.updated else "",
        f"{event.same} up to date" if event.same else "",
        f"{event.compress} to make into mp3" if event.compress else "",
    ]
    line = ", ".join(p for p in parts if p) or "no files"
    if event.bytes:
        line += f" ({size(event.bytes)} to download)"
    if event.gone:
        line += f"; {event.gone} no longer on the server (kept here)"
    return line


def print_report(event: Event) -> None:
    match event:
        case SignIn(provider=provider, url=url, code=code):
            print(
                f"Sign in to {provider}: open {url} in a web browser and enter the code {code}",
                flush=True,
            )
        case Checking(source=source):
            print(f"{source}: checking…", flush=True)
        case Planned(source=source):
            print(f"{source}: {plan_line(event)}", flush=True)
        case Fetching(path=path, status=status, done=0):
            verb = {"updated": "Updating", "compressed": "Compressing"}.get(
                status, "Downloading"
            )
            print(f"{verb}: {shown(path)}")
        case Skipped(path=path, reason=reason):
            print(f"Skipping {path.name}: {reason}")
        case Failed(source=source, error=error):
            print_error(error, source)


def print_error(error: UserError, source: str = "") -> None:
    print(f"{source}: {error.message}" if source else error.message, file=sys.stderr)
    if error.hint:
        print(f"  {error.hint}", file=sys.stderr)
