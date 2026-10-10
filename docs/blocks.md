# Blocks: the core behind the CLI and the players (plan)

**Summary**: Plan; `events.py` + `errors.py` built (T55), the rest not built; library choices for TOML writing, MSAL sign-in from a thread, a built-in client ID and NiceGUI background jobs decided (T54). The core splits into parts with one job each (events, sources, providers, sync, grouping, catalog, library, bundle, projects); frontends call only `Library`, never downloaders. The core never prints, long work is cancellable and off the UI thread, writes are atomic, nothing is deleted without asking.

Plan for four ideas: **Downloader UI**, **Settings file**, **Song grouping** and **Projects**; why they exist: [purpose.md](purpose.md). Tasks are in [todo.md](todo.md). Details: [song-grouping.md](song-grouping.md), [project-screen.md](project-screen.md) (the UI), [settings-file.md](settings-file.md), [projects.md](projects.md); review of this plan: [downloader-review.md](downloader-review.md). Once a block is built, its rules move into [architecture.md](architecture.md).

## Why change the core

Today the core is written for one person at a terminal:

- downloaders `print()`, and the OneDrive sign-in prints its device code, so a window can't show progress or the code;
- a download can't be cancelled, and there's no "what would change" before it starts;
- `sources.toml` is only read (`tomllib`), so nothing but a text editor can add a link;
- the catalog knows one layout (folder = song, plus `extra_folders`), one song comes from one source, and fixes are hand edits in `songs.json`;
- the player reads `songs.json` once at start, and everything lives directly in `data/`, so there's room for only one project.

All four ideas need the same things: a source list that code can edit, downloads that report and can be cancelled, songs grouped by name across sources with the user's fixes remembered, a catalog that can be rebuilt and diffed, and one folder ("library") that holds a project. So the work starts with those blocks, and each idea then adds a thin part on top.

## Blocks

Each block has one job. Lower blocks never import upper ones.

| Block | Job | Doesn't know about |
|---|---|---|
| `config.py` | data folder (`DOWNTEMPO_DATA` overrides it, for scratch runs), file endings | everything else |
| `events.py` | what long work reports (dataclasses), and `print_report` for the CLI | UI, providers |
| `errors.py` | `UserError(message, hint)`: failures in plain words | — |
| `sources.py` | `Source` (link + folder path inside the share), checks on names and links, read and write `sources.toml` | downloading, catalog |
| `downloaders/` | providers: sign-in, open a share link, list its folders and files. One module per provider | files on disk, songs, UI |
| `sync.py` | compare a remote listing with local files, download the difference (`.part`, mtime, progress, cancel) | which provider, catalog |
| `grouping.py` | files → songs by names, folders as hints, the user's fixes on top; pure (file refs in, songs out), so it also runs on a listing before download ([song-grouping.md](song-grouping.md)) | providers, disk, JSON |
| `catalog.py` | list a library's files, run `grouping`, keep `grouping.json` (fixes, song ids), write the derived `songs.json`, return a diff | providers, UI |
| `library.py` | **the API**: one folder holding sources, downloads, catalog, practice memory | UI, which provider |
| `bundle.py` | the settings file: export, read (untrusted), preview, apply | UI |
| `projects.py` | many libraries in `data/projects/`, the current one, moving old data in | UI |
| CLI, players | front doors: call `library` / `bundle` / `projects`, show events | providers' internals |

```
CLI ─┐                                   ┌─ sources.py
     ├─> projects ─> library ─> bundle   ├─ sync.py ─> downloaders/ (provider_for)
player ┘               │                 ├─ catalog.py ─> grouping.py
                       └─────────────────┴─ events.py, errors.py, config.py
```

## APIs

Sketches; names may change while building, the split shouldn't.

```python
# events.py: frozen dataclasses; long work reports through one callback, from the worker thread
class SignIn:   provider: str; url: str; code: str; expires_at: float
class Checking: source: str
class Planned:  source: str; new: int; updated: int; same: int; gone: int; bytes: int
class Fetching: source: str; path: str; done: int; total: int   # bytes, ~ every MB
class Saved:    source: str; path: str; status: Literal["new", "updated"]
class Failed:   source: str; error: UserError
type Event = SignIn | Checking | Planned | Fetching | Saved | Failed
type Report = Callable[[Event], None]

# downloaders/: a provider only finds files; sync.py fetches them
class Provider(Protocol):
    type: str                                    # "onedrive"
    label: str                                   # "OneDrive"
    def owns(self, url: str) -> bool             # link detection, no network
    def account(self) -> str | None              # "Signed in as …", from the token cache
    def sign_out(self) -> None
    def connect(self, report: Report, cancel: Event) -> Connection   # signs in when needed
class Connection(Protocol):
    def open(self, url: str, folder: str = "") -> RemoteFolder        # folder path inside the share; raises UserError
    def folders(self, folder: RemoteFolder) -> list[RemoteFolderInfo]  # the folder picker: name, path, ♪/📄 counts
    def files(self, folder: RemoteFolder) -> Iterator[RemoteFile]    # media files only, recursive
class RemoteFolder: name: str; ref: Any
class RemoteFile:   path: PurePosixPath; size: int | None; modified: datetime | None
                                            url: str; headers: Mapping[str, str] = {}
def provider_for(url: str) -> Provider | None

# sync.py
def plan(files: Iterable[RemoteFile], target: Path) -> SyncPlan     # new / updated / same / gone
def run(plan: SyncPlan, report: Report, cancel: threading.Event) -> SyncResult

# library.py: the only thing frontends call for data
class Library:
    root: Path
    def sources(self) -> list[Source]
    def add_source(self, source: Source) -> None          # checks name, writes sources.toml
    def replace_source(self, name: str, source: Source) -> None
    def remove_source(self, name: str, delete_files: bool = False) -> None
    def inspect_link(self, url: str, report: Report, cancel) -> LinkInfo  # type, folder name, free name, files, bytes
    def sync(self, names: list[str], report: Report, cancel) -> SyncResult  # downloads, then rebuild()
    def songs(self) -> list[Song]
    def grouping(self) -> Grouping                        # songs, to sort, not song files, flags
    def preview(self, files: list[FileRef]) -> Grouping   # a listing before download: "about 12 songs"
    # + create / move / also_add / rename / alias / link_folder / merge / delete / skip_folder / undo … (song-grouping.md#operations-library-api)
    def rebuild(self) -> CatalogDiff                      # new / gone songs, new recordings and sheets
    def path(self, catalog_path: str) -> Path             # "downloads/…" → file on disk
    practice_file: Path
```

`bundle.py` and `projects.py`: [settings-file.md](settings-file.md#api), [projects.md](projects.md#api).

## Main flows

- **Add a link** (player or `downtempo add <link>`): `inspect_link` → `provider_for` (unknown → "This link isn't OneDrive or Google Drive") → `connect` (a `SignIn` event if needed) → `open` → `folders` (the user picks one) → `preview` ("about 12 songs from 31 files, 180 MB") → `add_source` → `sync([name])` → `rebuild()` → the project screen shows the songs and the To sort tray ([project-screen.md](project-screen.md#getting-there)).
- **Update**: `sync([])`: every source, one plan each, then one rebuild; new files join songs or wait in To sort.
- **Fix a song**: the project screen calls `move` / `merge` / `rename` …; `grouping.json` changes, `songs.json` is rebuilt. Placement is sticky: magnets only place files that have no song yet.
- **Import a settings file**: `bundle.read` → `preview` (nothing written yet) → `apply` → offer `sync`.
- **Switch project**: the player stops, swaps its `Library`, reloads songs and practice memory.

## Rules

- **The core never prints or asks.** It reports events and raises `UserError`; the CLI prints them, the player shows them. Same code for both.
- **Frontends never import `downloaders/`.** They know a provider only by its `label` in events and `LinkInfo`.
- **Long work is blocking, cancellable, and runs off the UI thread.** The core uses plain threads and a `cancel` `threading.Event`, no asyncio. The player runs one job at a time and hands events to the UI through a queue drained by a `ui.timer`; it never touches widgets from the worker.
- **Untrusted input is checked at the edge**: pasted links (`https`, known provider), imported files ([settings-file.md](settings-file.md#import-rules)), names from the server (a saved file must stay inside its source folder).
- **Writes are atomic**: `.part` + rename for downloads, temp + `replace` for JSON and TOML. A cancelled or crashed run leaves the old state.
- **Songs belong to the project, not to a source**: one song may hold files from several sources; its `id` is stable across renames and re-sorting.
- **`songs.json` is derived**: written from the files and `grouping.json`, never edited by hand.
- **Paths in `songs.json` are relative to the library root** (`downloads/…`, as today), so moving a library (Projects) changes no catalog path or practice key.
- **Nothing is deleted without asking.** Files gone from the server are marked "removed on server", not removed.
- **app.py stays wiring only** (split by screen part in T105): new player UI goes into its own modules (`project_screen.py` + its `project_screen.js`, `jobs.py`).

## Decided from the docs (T54, 2026-10-11)

- **`sources.toml` is written with `tomlkit`** (MIT, 0.15.1 July 2026, Python ≥ 3.9; [pypi-tomlkit-json](web/pypi-tomlkit-json.txt)). `parse` then `dumps` gives back exactly the original text, comments included, and the document acts like a dict ([tomlkit-quickstart](web/tomlkit-quickstart.txt)). `[[source]]` is an `AoT` (array of tables): add a source with `doc["source"].append(table)`, remove it with `del doc["source"][i]`, create the array with `tomlkit.aot()` for a new file ([tomlkit-api](web/tomlkit-api.txt)). Reading stays plain `tomllib` everywhere else; only `sources.py` writes, via temp + `replace`.
- **Device code from a thread**: `initiate_device_flow(scopes)` returns a dict with `user_code`, `verification_uri`, `message` and `expires_at` (Entra: 15 minutes by default, no `verification_uri_complete`; [entra-device-code-flow](web/entra-device-code-flow.txt)). `connect` turns it into a `SignIn(provider, url, code, expires_at)` event, then calls `acquire_token_by_device_flow(flow)` in the worker thread; it blocks while polling. **Cancel = set `flow["expires_at"] = 0`** from another thread: MSAL documents this as the way to stop the polling loop ([msal-python-api](web/msal-python-api.txt)). It stops at the next poll (a few seconds), so the cancel watcher is a small thread waiting on the `cancel` event that sets it. A result with `error` becomes a `UserError` ("Sign-in expired, try again" for `expired_token`).
- **A built-in client ID may ship with the app.** A desktop app is a *public client*: it can't keep secrets and so has none; the client ID is "a public value that identifies the application", only a secret proves identity ([entra-public-confidential-clients](web/entra-public-confidential-clients.txt)). So the ID can be in the code. The registration needs "Allow public client flows" on and "Personal accounts only" (or + work accounts) ([entra-register-app](web/entra-register-app.txt)). Catch: the registration belongs to whoever made it; if it's deleted, sign-in breaks for everyone, so `.env` keeps overriding it (T59). Sign-out = `remove_account` for each of `get_accounts()`; "Signed in as …" = the account's `username`.
- **Background work in the player**: the job function stays plain and blocking (core rule). The player starts it with `await run.io_bound(job, report, cancel)` (a worker thread, the event loop stays free; [nicegui-run-io-bound](web/nicegui-run-io-bound.txt)) from an async handler or a task made with `background_tasks.create` (keeps a reference, logs exceptions; [nicegui-background-tasks-src](web/nicegui-background-tasks-src.txt)). `report` only does `queue.put(event)`; a `ui.timer` (≈ 0.1 s) drains the queue and updates widgets, so widgets are touched only on the UI side. Exceptions from `run.io_bound` go to `app.on_exception` without UI context, so the job wrapper catches them and puts a `Failed` event instead. This is T60's plan.

## Open points (tasks)

- Google Drive fits `Provider` (T14, T17).
- Name matching: `rapidfuzz` or `difflib`, thresholds (T87, T86).
- Drag and drop in NiceGUI (T92).
