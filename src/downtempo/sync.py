"""Bring sources' local folders up to date with their shares: list, plan what differs, download it.

Doesn't know which provider: it asks `provider(type)` for a connection and the connection for
files. Downloads go to `<name>.part` first and get the server's change time; a cancel stops
between chunks and keeps every finished file. Nothing local is ever deleted.
"""

import os
import threading
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Literal

import requests

from downtempo.config import MEDIA_EXTENSIONS
from downtempo.downloaders import provider
from downtempo.downloaders.remote import Connection, RemoteFile
from downtempo.downloaders.web import request_error
from downtempo.errors import Cancelled, UserError
from downtempo.events import (
    Checking,
    Failed,
    Fetching,
    Planned,
    Report,
    Saved,
    Skipped,
)
from downtempo.sources import Source, is_skipped

SAME_TIME = 2.0  # seconds; some file systems store times coarsely
CHUNK = 1 << 20  # progress is reported, and a cancel noticed, once per chunk


@dataclass(frozen=True)
class Item:
    remote: RemoteFile
    local: Path


@dataclass
class SyncPlan:
    source: str
    target: Path
    new: list[Item] = field(default_factory=list)
    updated: list[Item] = field(default_factory=list)
    same: list[Item] = field(default_factory=list)
    gone: list[Path] = field(
        default_factory=list
    )  # local files no longer on the server
    skipped: list[tuple[PurePosixPath, str]] = field(default_factory=list)

    @property
    def bytes(self) -> int:
        return sum(i.remote.size or 0 for i in self.new + self.updated)

    def event(self) -> Planned:
        return Planned(
            self.source,
            len(self.new),
            len(self.updated),
            len(self.same),
            len(self.gone),
            self.bytes,
        )


@dataclass
class SyncResult:
    source: str
    plan: SyncPlan | None = None
    saved: list[Path] = field(default_factory=list)
    error: UserError | None = None
    cancelled: bool = False


def plan(
    source: str,
    files: Iterable[RemoteFile],
    target: Path,
    cancel: threading.Event,
    skip: tuple[str, ...] = (),
) -> SyncPlan:
    """Compare a listing with the files under `target`; reads the disk, changes nothing. Files in
    skipped folders are neither downloaded nor counted as gone."""
    result = SyncPlan(source, target)
    seen: set[Path] = set()
    for file in files:
        if cancel.is_set():
            raise Cancelled()
        if is_skipped(file.path.parts, skip):
            continue
        local = safe_path(target, file.path)
        if local is None:
            result.skipped.append((file.path, "the name can't be saved here"))
            continue
        seen.add(local)
        item = Item(file, local)
        if not local.is_file():
            result.new.append(item)
        elif current(local, file):
            result.same.append(item)
        else:
            result.updated.append(item)
    if target.exists():
        result.gone = sorted(
            p
            for p in target.rglob("*")
            if p.is_file()
            and p.suffix.lower() in MEDIA_EXTENSIONS
            and p not in seen
            and not is_skipped(p.relative_to(target).parts, skip)
        )
    return result


def safe_path(target: Path, path: PurePosixPath) -> Path | None:
    """Where a server's file goes, or None when its name would leave the source's folder."""
    parts = path.parts
    if not parts or path.is_absolute():
        return None
    if any(p in ("", ".", "..") or "\\" in p or "\0" in p for p in parts):
        return None
    return target.joinpath(*parts)


def current(local: Path, file: RemoteFile) -> bool:
    """Same size, and not older than the server's copy. Files from before change times were
    copied (download time, so newer) count as current and get the server's time in `run`."""
    stat = local.stat()
    if file.size is not None and stat.st_size != file.size:
        return False
    return (
        file.modified is None or stat.st_mtime > file.modified.timestamp() - SAME_TIME
    )


def run(
    plan: SyncPlan, connection: Connection, report: Report, cancel: threading.Event
) -> SyncResult:
    result = SyncResult(plan.source, plan)
    for item in plan.same:
        stamp_with_server_time(item)
    work = [(i, "new") for i in plan.new] + [(i, "updated") for i in plan.updated]
    for item, status in work:
        outcome = (
            "cancelled"
            if cancel.is_set()
            else fetch(item, status, connection, plan.source, report, cancel)
        )
        if outcome == "cancelled":
            result.cancelled = True
            break
        if outcome == "saved":
            result.saved.append(item.local)
    return result


def stamp_with_server_time(item: Item) -> None:
    if item.remote.modified is None:
        return
    stamp = item.remote.modified.timestamp()
    if abs(item.local.stat().st_mtime - stamp) > SAME_TIME:
        os.utime(item.local, (stamp, stamp))


def fetch(
    item: Item,
    status: str,
    connection: Connection,
    source: str,
    report: Report,
    cancel: threading.Event,
) -> Literal["saved", "skipped", "cancelled"]:
    """Download one file through `.part`; a cancel removes the part. A file deleted on the
    server since the listing is skipped; other failures stop the source."""
    size = item.remote.size
    report(Fetching(source, item.local, status, 0, size))
    item.local.parent.mkdir(parents=True, exist_ok=True)
    partial = item.local.with_name(item.local.name + ".part")
    done = 0
    try:
        url, headers = connection.request(item.remote)
        with requests.get(
            url, headers=dict(headers), stream=True, timeout=60
        ) as response:
            response.raise_for_status()
            with partial.open("wb") as output:
                for chunk in response.iter_content(chunk_size=CHUNK):
                    if cancel.is_set():
                        break
                    output.write(chunk)
                    done += len(chunk)
                    report(Fetching(source, item.local, status, done, size))
    except requests.RequestException as error:
        partial.unlink(missing_ok=True)
        response = getattr(error, "response", None)
        if response is not None and response.status_code in (404, 410):
            report(Skipped(source, item.local, "deleted on the server meanwhile"))
            return "skipped"
        raise request_error(error) from error
    if cancel.is_set():
        partial.unlink(missing_ok=True)
        return "cancelled"
    if item.remote.modified is not None:
        stamp = item.remote.modified.timestamp()
        os.utime(partial, (stamp, stamp))
    partial.replace(item.local)
    report(Saved(source, item.local, status))
    return "saved"


def update(
    sources: list[tuple[Source, Path]],
    report: Report,
    cancel: threading.Event,
    dry_run: bool = False,
) -> list[SyncResult]:
    """Each (source, its local folder) in turn; one sign-in per provider. A failing source is
    reported (`Failed`) and the rest go on; a cancel stops all and keeps finished files."""
    connections: dict[str, Connection | UserError] = {}
    results: list[SyncResult] = []
    for source, target in sources:
        if cancel.is_set():
            break
        try:
            if source.type not in connections:
                try:
                    connections[source.type] = provider(source.type).connect(
                        report, cancel
                    )
                except UserError as error:
                    # don't ask to sign in again
                    connections[source.type] = error
            connection = connections[source.type]
            if isinstance(connection, UserError):
                raise connection
            report(Checking(source.name))
            folder = connection.open(source.url, source.folder)
            found = plan(
                source.name, connection.files(folder), target, cancel, source.skip
            )
            report(found.event())
            for path, reason in found.skipped:
                report(Skipped(source.name, target / path.name, reason))
            results.append(
                SyncResult(source.name, found)
                if dry_run
                else run(found, connection, report, cancel)
            )
        except UserError as error:
            report(Failed(source.name, error))
            results.append(SyncResult(source.name, error=error))
        except Cancelled:
            results.append(SyncResult(source.name, cancelled=True))
            break
        if results[-1].cancelled:
            break
    return results
