"""HTTP shared by all downloaders: saving a URL to a file, and request failures in plain words."""

import os
from datetime import datetime
from pathlib import Path

import requests

from downtempo.errors import UserError
from downtempo.events import Fetching, Report, Same, Saved

SAME_TIME = 2.0  # seconds; some file systems store times coarsely
CHUNK = 1 << 20  # progress is reported once per chunk


def save_url(
    url: str,
    destination: Path,
    source: str,
    report: Report,
    size: int | None = None,
    modified: str | None = None,
) -> None:
    """Stream `url` to `destination` unless the local copy is current.

    `modified` is the server's ISO 8601 change time; a saved file gets it as its own mtime. A file
    with the expected size counts as current when its mtime isn't older than the server's: files
    from before mtimes were set (download time, so newer) are adopted without a download.
    """
    stamp = datetime.fromisoformat(modified).timestamp() if modified else None
    exists = destination.exists()
    if exists and destination.stat().st_size == size:
        if stamp is None:
            return report(Same(source, destination))
        if destination.stat().st_mtime > stamp - SAME_TIME:
            if abs(destination.stat().st_mtime - stamp) > SAME_TIME:
                os.utime(destination, (stamp, stamp))
            return report(Same(source, destination))

    status = "updated" if exists else "new"
    report(Fetching(source, destination, status, 0, size))
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    done = 0
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with partial.open("wb") as output:
            for chunk in response.iter_content(chunk_size=CHUNK):
                output.write(chunk)
                done += len(chunk)
                report(Fetching(source, destination, status, done, size))
    if stamp is not None:
        os.utime(partial, (stamp, stamp))
    partial.replace(destination)
    report(Saved(source, destination, status))


def request_error(error: requests.RequestException) -> UserError:
    """A failed request as the user should read it: what happened and what to do."""
    match error:
        case requests.ConnectionError():
            return UserError(
                "Can't reach the server.",
                "Check the internet connection and try again.",
            )
        case requests.Timeout():
            return UserError(
                "The server took too long to answer.", "Try again in a moment."
            )
        case requests.HTTPError(response=response) if response is not None:
            code = response.status_code
            if code == 401:
                return UserError("The sign-in was not accepted.", "Sign in again.")
            if code == 403:
                return UserError(
                    "No access to this folder.",
                    "Ask the owner to share it with your account.",
                )
            if code == 404:
                return UserError(
                    "Not found.",
                    "Check the link: the folder may have been moved or is no longer shared.",
                )
            if code == 429 or code >= 500:
                return UserError(
                    f"The server is busy or failing (HTTP {code}).", "Try again later."
                )
            return UserError(f"The server refused the request (HTTP {code}).")
    return UserError(f"The download failed: {error}")
