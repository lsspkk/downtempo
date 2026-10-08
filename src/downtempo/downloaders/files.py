"""File saving shared by all downloaders."""

from pathlib import Path

import requests

from downtempo.config import PROJECT_DIR


def save_url(url: str, destination: Path, size: int | None = None) -> None:
    """Stream `url` to `destination`, skipping files that already exist with the expected size."""
    shown = destination.relative_to(PROJECT_DIR)
    if destination.exists() and destination.stat().st_size == size:
        print(f"Exists: {shown}")
        return

    print(f"Downloading: {shown}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with partial.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1 << 20):
                output.write(chunk)
    partial.replace(destination)
