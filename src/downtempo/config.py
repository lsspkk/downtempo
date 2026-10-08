"""Project paths, `.env` loading and the source list in `data/sources.toml`."""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_DIR / "data"
DOWNLOADS_DIR = DATA_DIR / "downloads"
SOURCES_FILE = DATA_DIR / "sources.toml"
MEDIA_EXTENSIONS = {".mp3", ".pdf"}


@dataclass(frozen=True)
class Source:
    """One shared folder to download; its files go to `data/downloads/<name>/`."""

    name: str
    type: str
    url: str
    subfolder: str = ""

    @property
    def target(self) -> Path:
        return DOWNLOADS_DIR / self.name


def load_env(path: Path = PROJECT_DIR / ".env") -> None:
    """Load simple KEY=VALUE settings without replacing shell-provided values."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_sources(path: Path = SOURCES_FILE) -> list[Source]:
    if not path.exists():
        raise RuntimeError(
            f"No {path.relative_to(PROJECT_DIR)}: copy data/sources.example.toml and fill it in."
        )
    sources = [
        Source(**entry)
        for entry in tomllib.loads(path.read_text(encoding="utf-8")).get("source", [])
    ]
    names = [source.name for source in sources]
    if len(names) != len(set(names)):
        raise RuntimeError(f"Source names must be unique: {names}")
    return sources
