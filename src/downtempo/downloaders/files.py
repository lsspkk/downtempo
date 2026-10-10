"""File saving shared by all downloaders."""

import os
from datetime import datetime
from pathlib import Path

import requests

from downtempo.config import PROJECT_DIR

SAME_TIME = 2.0  # seconds; some file systems store times coarsely


def save_url(
    url: str, destination: Path, size: int | None = None, modified: str | None = None
) -> None:
    """Stream `url` to `destination` unless the local copy is current.

    `modified` is the server's ISO 8601 change time; a saved file gets it as its own mtime. A file
    with the expected size counts as current when its mtime isn't older than the server's: files
    from before mtimes were set (download time, so newer) are adopted without a download.
    """
    shown = destination.relative_to(PROJECT_DIR)
    stamp = datetime.fromisoformat(modified).timestamp() if modified else None
    exists = destination.exists()
    if exists and destination.stat().st_size == size:
        if stamp is None:
            print(f"Exists: {shown}")
            return
        if destination.stat().st_mtime > stamp - SAME_TIME:
            if abs(destination.stat().st_mtime - stamp) > SAME_TIME:
                os.utime(destination, (stamp, stamp))
            print(f"Exists: {shown}")
            return

    print(f"{'Updated' if exists else 'Downloading'}: {shown}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with partial.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1 << 20):
                output.write(chunk)
    if stamp is not None:
        os.utime(partial, (stamp, stamp))
    partial.replace(destination)
