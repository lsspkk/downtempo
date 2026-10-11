"""Where things live (the data folder, sign-ins), which file endings count, `.env` loading."""

import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
# DOWNTEMPO_DATA points everything at another folder: a scratch copy, a fresh start.
DATA_DIR = Path(os.environ.get("DOWNTEMPO_DATA") or PROJECT_DIR / "data").resolve()
TOKENS_DIR = DATA_DIR / "tokens"  # sign-ins belong to the computer, not to a library
# Lower case; file endings are compared lower-cased, so `.WAV` counts too.
AUDIO_EXTENSIONS = {".mp3", ".wav"}
SHEET_EXTENSIONS = {".pdf"}
MEDIA_EXTENSIONS = AUDIO_EXTENSIONS | SHEET_EXTENSIONS


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
