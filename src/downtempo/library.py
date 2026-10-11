"""The API frontends call for data: one folder (`root`) holding sources, downloads and the catalog.

Long calls (`inspect_link`, `folders`, `sync`) block, report events and stop on `cancel`; run them
off the UI thread. Failures are `UserError`s. Frontends never import `downloaders/` directly.
"""

import shutil
import threading
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path

from downtempo.catalog import Song, list_files, read_catalog
from downtempo.checks import read_checks, record, rename_source
from downtempo.downloaders import PROVIDERS, provider, provider_for, unknown_link
from downtempo.downloaders.remote import (
    Connection,
    Provider,
    RemoteFile,
    RemoteFolderInfo,
)
from downtempo.errors import Cancelled, UserError
from downtempo.events import Report
from downtempo.newmarks import read_marks
from downtempo.publishing import (
    CatalogDiff,
    mark_seen,
    preview,
    publish,
    rebuild,
    songs_with_new,
)
from downtempo.renaming import rename
from downtempo.shapes import FileRef, Grouping
from downtempo.skipping import free_space, skip_folder, skipped_size, unskip_folder
from downtempo.sorting import Sorting
from downtempo.sources import (
    Source,
    add_source,
    check_name,
    check_url,
    is_skipped,
    name_from,
    read_sources,
    remove_source,
    replace_source,
)
from downtempo.sync import SyncResult, update


@dataclass(frozen=True)
class LinkInfo:
    """What a pasted link opens, before anything is saved or downloaded."""

    provider: str  # "OneDrive"
    type: str  # "onedrive"
    url: str
    folder: str  # path inside the share, "" = the shared folder
    folder_name: str
    name: str  # a free source name made from the folder's name
    audio: int
    sheets: int
    bytes: int


@dataclass(frozen=True)
class FolderPreview:
    """ "About 12 songs from 31 files, 180 MB": a folder to add, sorted before downloading."""

    folder_name: str
    name: str  # a free source name made from it
    files: int
    bytes: int
    grouping: Grouping  # with the project's songs; the folder's files under `name`

    def joining(self) -> dict[str, int]:
        """Existing songs the folder's files would join: title → files."""
        return {
            s.title: n
            for s in self.grouping.songs
            if (n := sum(m.file.source == self.name for m in (*s.audio, *s.sheets)))
        }


@dataclass(frozen=True)
class Account:
    type: str
    provider: str
    user: str | None  # None = not signed in on this computer


@dataclass(frozen=True)
class UpdateResult:
    sources: list[SyncResult]
    catalog: CatalogDiff | None  # None on a dry run

    @property
    def saved(self) -> int:
        return sum(len(r.saved) for r in self.sources)

    @property
    def cancelled(self) -> bool:
        return any(r.cancelled for r in self.sources)


class Library:
    """One project's folder: `project.toml` (name + sources), `downloads/`, `grouping.json` (the
    sorting), `songs.json` (derived), `new.json`, `practice.json` (written by the player)."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.sources_file = self.root / "project.toml"
        self.downloads = self.root / "downloads"
        self.songs_file = self.root / "songs.json"
        self.new_file = self.root / "new.json"
        self.practice_file = self.root / "practice.json"
        self.checked_file = self.root / "checked.json"
        self.sorting = Sorting(self)

    def name(self) -> str:
        try:
            text = self.sources_file.read_text(encoding="utf-8")
            return str(tomllib.loads(text).get("name") or self.root.name)
        except (FileNotFoundError, tomllib.TOMLDecodeError):
            return self.root.name

    # ------------------------------------------------------------ sources

    def sources(self) -> list[Source]:
        return read_sources(self.sources_file)

    def source(self, name: str) -> Source:
        for found in self.sources():
            if found.name.casefold() == name.casefold():
                return found
        known = ", ".join(s.name for s in self.sources()) or "none yet"
        raise UserError(f"There is no source called '{name}'.", f"Sources: {known}.")

    def target(self, source: Source) -> Path:
        return self.downloads / source.name

    def add_source(self, source: Source) -> Source:
        """Checks the name and link, then saves; returns the source as saved."""
        taken = [s.name for s in self.sources()]
        url = check_url(source.url)
        provider(source.type)
        self.check_new(url, source.folder)
        added = Source(
            check_name(source.name, taken),
            source.type,
            url,
            source.folder.strip("/"),
            source.skip,
        )
        add_source(self.sources_file, added)
        return added

    def check_new(self, url: str, folder: str) -> None:
        """Refuse a link + folder that's already a source (before any slow listing)."""
        for other in self.sources():
            if (other.url, other.folder.casefold()) == (
                url.strip(),
                folder.strip("/").casefold(),
            ):
                raise UserError(f"This folder is already added, as '{other.name}'.")

    def replace_source(self, name: str, source: Source) -> None:
        old = self.source(name)
        taken = [s.name for s in self.sources() if s.name != old.name]
        check_name(source.name, taken)
        check_url(source.url)
        replace_source(self.sources_file, old.name, source)
        if source.name != old.name and self.target(old).exists():
            self.target(old).rename(self.target(source))
        if source.name != old.name:
            known = {s.name for s in self.sources()}
            rename_source(self.checked_file, old.name, source.name, known)

    def change_link(
        self, name: str, url: str, folder: str, skip: tuple[str, ...] = ()
    ) -> Source:
        """A new link for a source (re-shared or expired), at `folder` inside the new share. The
        name stays, so downloads, sorting and practice memory stay; files the new folder doesn't
        have are counted as gone at the next check. No network: call `has_folder` first."""
        old = self.source(name)
        url = check_url(url)
        found = provider_for(url)
        if found is None:
            raise unknown_link()
        folder = folder.strip("/")
        for other in self.sources():
            if other.name != old.name and (other.url, other.folder.casefold()) == (
                url,
                folder.casefold(),
            ):
                raise UserError(f"This folder is already added, as '{other.name}'.")
        new = replace(old, type=found.type, url=url, folder=folder, skip=skip)
        replace_source(self.sources_file, old.name, new)
        return new

    def has_folder(
        self, url: str, folder: str, report: Report, cancel: threading.Event
    ) -> bool:
        """Whether the share behind `url` has `folder` (False when only the folder is missing;
        a link that doesn't open at all raises its `UserError`)."""
        _, connection = self.connect(url, report, cancel)
        connection.open(url.strip())
        if not folder.strip("/"):
            return True
        try:
            connection.open(url.strip(), folder)
        except UserError:
            return False
        return True

    def rename_source(self, name: str, new_name: str) -> Source:
        """A new name for a source, carried into the sorting, new marks and practice memory
        (`renaming.py`); undo history is cleared. Save the player's practice memory first."""
        old = self.source(name)
        new = replace(old, name=new_name.strip())
        if new.name != old.name:
            rename(self, old, new)
        return new

    def remove_source(self, name: str, delete_files: bool = False) -> None:
        """Forget a source; its downloaded files go too only when `delete_files` (ask first)."""
        old = self.source(name)
        remove_source(self.sources_file, old.name)
        target = self.target(old)
        if delete_files and target.is_dir() and target.parent == self.downloads:
            shutil.rmtree(target)
            self.rebuild()

    # ------------------------------------------------------------ links and sign-in

    def connect(
        self, url: str, report: Report, cancel: threading.Event
    ) -> tuple[Provider, Connection]:
        url = check_url(url)
        found = provider_for(url)
        if found is None:
            raise unknown_link()
        return found, found.connect(report, cancel)

    def inspect_link(
        self, url: str, folder: str, report: Report, cancel: threading.Event
    ) -> LinkInfo:
        """Sign in if needed, open the link at `folder` and count what's there (all levels)."""
        found, connection = self.connect(url, report, cancel)
        opened = connection.open(url.strip(), folder)
        audio = sheets = size = 0
        for file in connection.files(opened):
            if cancel.is_set():
                break
            is_sheet = file.path.suffix.lower() == ".pdf"
            sheets, audio = sheets + is_sheet, audio + (not is_sheet)
            size += file.size or 0
        return LinkInfo(
            found.label,
            found.type,
            url.strip(),
            opened.path,
            opened.name,
            name_from(opened.name, [s.name for s in self.sources()]),
            audio,
            sheets,
            size,
        )

    def link_provider(self, url: str) -> tuple[str, str]:
        """(label, type) of the provider a pasted link belongs to; no network."""
        found = provider_for(check_url(url))
        if found is None:
            raise unknown_link()
        return found.label, found.type

    def free_name(self, name: str) -> str:
        """A source name made from a folder's name, not taken yet ("Songs 2")."""
        return name_from(name, [s.name for s in self.sources()])

    def preview_folder(
        self,
        url: str,
        folder: str,
        skip: tuple[str, ...],
        report: Report,
        cancel: threading.Event,
    ) -> "FolderPreview":
        """What adding this folder would bring, before anything is saved or downloaded: its media
        files (without the skipped folders) sorted with this project's songs."""
        _, connection = self.connect(url, report, cancel)
        opened = connection.open(url.strip(), folder)
        files = []
        for file in connection.files(opened):
            if cancel.is_set():
                raise Cancelled()
            if not is_skipped(file.path.parts, skip):
                files.append(file)
        name = self.free_name(opened.name)
        return FolderPreview(
            opened.name,
            name,
            len(files),
            sum(f.size or 0 for f in files),
            self.preview({name: files}),
        )

    def folders(
        self, url: str, folder: str, report: Report, cancel: threading.Event
    ) -> list[RemoteFolderInfo]:
        """The subfolders of `folder` in a share, for the folder picker (one level)."""
        _, connection = self.connect(url, report, cancel)
        return connection.folders(connection.open(url.strip(), folder))

    def accounts(self) -> list[Account]:
        return [Account(p.type, p.label, p.account()) for p in PROVIDERS]

    def sign_out(self, type: str) -> None:
        provider(type).sign_out()

    # ------------------------------------------------------------ downloading

    def sync(
        self,
        names: list[str],
        report: Report,
        cancel: threading.Event,
        dry_run: bool = False,
    ) -> UpdateResult:
        """Download what changed in these sources (all when `names` is empty), then rebuild."""
        chosen = [self.source(n) for n in names] if names else self.sources()
        results = update([(s, self.target(s)) for s in chosen], report, cancel, dry_run)
        if not dry_run:
            targets = {s.name: self.target(s) for s in chosen}
            known = {s.name for s in self.sources()}
            record(self.checked_file, results, targets, known)
        return UpdateResult(results, None if dry_run else self.rebuild(mark_new=True))

    def checked(self) -> dict[str, str]:
        """When each source was last checked to the end: source name → ISO time."""
        return {s: c.at for s, c in read_checks(self.checked_file).items()}

    def gone(self) -> set[str]:
        """Downloaded files the last check didn't find on the server any more (file ids)."""
        return {g for c in read_checks(self.checked_file).values() for g in c.gone}

    # ------------------------------------------------------------ songs

    def files(self) -> list[FileRef]:
        """Every recording and sheet downloaded, except in skipped folders."""
        return list_files(self.downloads, {s.name: s.skip for s in self.sources()})

    def skip_folder(self, source: str, folder: str) -> None:
        skip_folder(self, source, folder)

    def unskip_folder(self, source: str, folder: str) -> None:
        unskip_folder(self, source, folder)

    def skipped_size(self, source: str) -> int:
        """Bytes of downloaded files in the source's skipped folders."""
        return skipped_size(self, source)

    def free_space(self, source: str) -> int:
        """Delete those files (ask first); returns the bytes freed."""
        return free_space(self, source)

    def songs(self) -> list[Song]:
        return read_catalog(self.songs_file)

    def rebuild(self, mark_new: bool = False) -> CatalogDiff:
        """Group the files again and write `songs.json`; `mark_new`: files that joined a song now
        get a "new" mark (after a download)."""
        return rebuild(self, mark_new)

    def publish(self, result: Grouping) -> list[Song]:
        """Write `songs.json` from a grouping that is already made."""
        return publish(self, result)

    def preview(self, listing: dict[str, list[RemoteFile]]) -> Grouping:
        """How a remote listing (source name → files) would be sorted; changes nothing."""
        return preview(self, listing)

    def new_marks(self) -> dict[str, str]:
        """Files that joined a song since it was last opened: file id → date."""
        return read_marks(self.new_file)

    def songs_with_new(self) -> set[str]:
        return songs_with_new(self)

    def mark_seen(self, song_id: str) -> None:
        mark_seen(self, song_id)

    def path(self, catalog_path: str) -> Path:
        """A catalog path (`downloads/…`) as a file on disk; never outside the library."""
        path = (self.root / catalog_path).resolve()
        if not path.is_relative_to(self.root):
            raise UserError(f"'{catalog_path}' is outside the library.")
        return path
