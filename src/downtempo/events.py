"""What long work reports while it runs (docs/blocks.md#apis), and `print_report` for the CLI.

The core never prints: a download gets a `report` callback and calls it with these events, from
whatever thread it runs on. The CLI passes `print_report`; the player will queue them for the UI.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from downtempo.config import PROJECT_DIR


@dataclass(frozen=True)
class SignIn:
    """The user must open `url` and type `code` before `expires_at` (Unix time)."""

    provider: str
    url: str
    code: str
    expires_at: float


@dataclass(frozen=True)
class Same:
    """A file already up to date; nothing downloaded."""

    source: str
    path: Path


@dataclass(frozen=True)
class Fetching:
    """Download progress in bytes: once with `done` 0 when it starts, then about every MB."""

    source: str
    path: Path
    status: Literal["new", "updated"]
    done: int
    total: int | None


@dataclass(frozen=True)
class Saved:
    source: str
    path: Path
    status: Literal["new", "updated"]


@dataclass(frozen=True)
class Skipped:
    source: str
    path: Path
    reason: str


type Event = SignIn | Same | Fetching | Saved | Skipped
type Report = Callable[[Event], None]


def shown(path: Path) -> Path:
    return path.relative_to(PROJECT_DIR) if path.is_relative_to(PROJECT_DIR) else path


def print_report(event: Event) -> None:
    match event:
        case SignIn(url=url, code=code):
            print(
                f"To sign in, use a web browser to open the page {url} and enter the code {code} to authenticate.",
                flush=True,
            )
        case Same(path=path):
            print(f"Exists: {shown(path)}")
        case Fetching(path=path, status=status, done=0):
            print(
                f"{'Updated' if status == 'updated' else 'Downloading'}: {shown(path)}"
            )
        case Skipped(path=path, reason=reason):
            print(f"Skipping {path.name}: {reason}")
