"""Command line: `uv run downtempo <command>`, a thin front door to `Library` and `Workspace`
(README "Use")."""

import argparse
import sys
import threading
from collections.abc import Callable
from pathlib import Path

from downtempo import bundle, cli_songs
from downtempo.config import DATA_DIR, MEDIA_EXTENSIONS
from downtempo.errors import Cancelled, UserError
from downtempo.events import count, print_error, print_report, shown, size
from downtempo.library import CatalogDiff, Library, UpdateResult
from downtempo.projects import Workspace
from downtempo.sources import Source


def cancellable[T](work: Callable[[threading.Event], T]) -> T:
    """Run `work` in a thread so Ctrl+C becomes a clean cancel (finished files are kept)."""
    cancel = threading.Event()
    box: dict[str, T | BaseException] = {}

    def target() -> None:
        try:
            box["result"] = work(cancel)
        except BaseException as error:  # noqa: BLE001 (re-raised in the main thread)
            box["error"] = error

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    try:
        while thread.is_alive():
            thread.join(0.2)
    except KeyboardInterrupt:
        print("\nStopping…", file=sys.stderr)
        cancel.set()
        thread.join()
    if "error" in box:
        raise box["error"]
    if "result" not in box:
        raise Cancelled()
    return box["result"]


def download(library: Library, names: list[str], dry_run: bool) -> int:
    if not library.sources():
        print("No shared folders yet. Add one:\n  uv run downtempo add '<link>'")
        return 0
    for name in names:
        library.source(name)  # unknown names fail before any sign-in
    result = cancellable(
        lambda cancel: library.sync(names, print_report, cancel, dry_run)
    )
    if dry_run:
        print_plans(result)
        return 1 if any(r.error for r in result.sources) else 0
    if result.cancelled:
        print("Stopped. Finished files are kept; run it again to get the rest.")
    elif result.saved:
        print(f"Downloaded {result.saved} file{'s' * (result.saved != 1)}.")
    if result.catalog:
        print_diff(result.catalog)
    return 1 if any(r.error for r in result.sources) else 0


def print_plans(result: UpdateResult) -> None:
    for each in result.sources:
        if not each.plan:
            continue
        for label, items in (("new", each.plan.new), ("changed", each.plan.updated)):
            for item in items:
                print(f"  {label}: {shown(item.local)}")
        for path in each.plan.gone:
            print(f"  no longer on the server: {shown(path)}")
    print("Nothing was downloaded (--dry-run).")


def print_diff(diff: CatalogDiff) -> None:
    print(f"Song list: {count(diff.songs, 'song')}.")
    for label, names in (
        ("New songs", diff.new_songs),
        ("Songs no longer here", diff.gone_songs),
    ):
        if names:
            print(f"  {label}: {', '.join(names)}")
    for title, files in sorted(diff.joined.items()):
        print(f"  {count(files, 'file')} joined {title}")
    if diff.to_sort:
        print(
            f"  {count(diff.to_sort, 'file')} unknown, in no song (see them: uv run downtempo songs --to-sort; make songs of the suggestions: --create)"
        )


def add(library: Library, url: str, name: str, folder: str) -> int:
    library.check_new(url, folder)
    info = cancellable(
        lambda cancel: library.inspect_link(url, folder, print_report, cancel)
    )
    where = f"'{info.folder_name}'" + (f" ({info.folder})" if info.folder else "")
    print(
        f"{info.provider} folder {where}: {count(info.audio, 'recording')}, "
        f"{count(info.sheets, 'sheet')}, "
        f"{size(info.bytes)}"
    )
    if not info.audio and not info.sheets:
        raise UserError(
            "There are no recordings or sheets in this folder (mp3, wav and pdf count).",
            f"See its folders: uv run downtempo folders '{info.url}'",
        )
    source = library.add_source(
        Source(name or info.name, info.type, info.url, info.folder)
    )
    print(f"Added as '{source.name}'. Download it now:")
    print(f"  uv run downtempo download '{source.name}'")
    return 0


def folders(library: Library, url: str, folder: str) -> int:
    found = cancellable(
        lambda cancel: library.folders(url, folder, print_report, cancel)
    )
    if not found:
        print(
            "No folders inside." if folder else "No folders inside the shared folder."
        )
    for each in found:
        counts = ", ".join(
            [count(each.audio, "recording"), count(each.sheets, "sheet")]
            + [count(each.folders, "folder")] * bool(each.folders)
        )
        print(f"  {each.path + '/':40} {counts}")
    if found:
        print(f"Add one: uv run downtempo add '{url}' --folder '<path>'")
    return 0


def list_sources(library: Library) -> int:
    sources = library.sources()
    if not sources:
        print("No shared folders yet. Add one:\n  uv run downtempo add '<link>'")
    for source in sources:
        files = [
            p
            for p in library.target(source).rglob("*")
            if p.is_file() and p.suffix.lower() in MEDIA_EXTENSIONS
        ]
        here = f"{len(files)} files here, {size(sum(p.stat().st_size for p in files))}"
        folder = f", folder '{source.folder}'" if source.folder else ""
        print(f"{source.name}  ({source.type}{folder}; {here})\n  {source.url}")
    for account in library.accounts():
        print(
            f"{account.provider}: "
            + (f"signed in as {account.user}" if account.user else "not signed in")
        )
    return 0


def remove(library: Library, name: str, delete_files: bool) -> int:
    source = library.source(name)
    library.remove_source(name, delete_files)
    target = library.target(source)
    if delete_files:
        print(f"Removed '{source.name}' and its downloaded files.")
    else:
        print(f"Removed '{source.name}'. Its files stay in {shown(target)}")
        print("  (remove --delete-files deletes them too)")
    return 0


def sign_out(library: Library, type: str) -> int:
    library.sign_out(type)
    print(f"Signed out of {type} on this computer.")
    return 0


def project(workspace: Workspace, action: str, names: list[str], yes: bool) -> int:
    match action, names:
        case "list", []:
            current = workspace.current_id()
            for each in workspace.projects():
                mark = "*" if each.id == current else " "
                print(
                    f"{mark} {each.name}  ({count(each.sources, 'source')}, "
                    f"{count(each.songs, 'song')}; folder projects/{each.id})"
                )
        case "new", [name]:
            library = workspace.create(name)
            print(f"Made '{library.name()}' the current project. Add a shared folder:")
            print("  uv run downtempo add '<link>'")
        case "use", [name]:
            library = workspace.use(workspace.find(name))
            print(f"Now working on '{library.name()}'.")
        case "rename", [name, new]:
            workspace.rename(workspace.find(name), new)
            print(f"Renamed to '{new.strip()}'.")
        case "delete", [name]:
            library = workspace.library(workspace.find(name))
            files = [p for p in library.downloads.rglob("*") if p.is_file()]
            what = f"'{library.name()}' with its {count(len(files), 'downloaded file')}"
            if not yes and input(f"Delete {what}? [y/N] ").strip().lower() != "y":
                print("Kept.")
                return 1
            workspace.delete(library.root.name)
            print(f"Deleted {what}.")
        case _:
            raise UserError(
                f"'project {action}' takes other arguments.",
                "uv run downtempo project list | new <name> | use <name> | "
                "rename <name> <new> | delete <name>",
            )
    return 0


def export(library: Library, file: str) -> int:
    text = bundle.export(library)
    if file == "-":
        print(text, end="")
        return 0
    path = Path(file)
    if path.exists():
        raise UserError(f"{path} already exists.", "Pick another file name.")
    path.write_text(text, encoding="utf-8")
    print(
        f"Saved '{library.name()}' ({count(len(library.sources()), 'source')}) to {path}"
    )
    return 0


def import_(
    workspace: Workspace, chosen: Callable[[], Library], file: str, into: str, yes: bool
) -> int:
    """Import a settings file as a new project, or into the chosen one (`into`: new / current).
    The chosen project is looked up only when needed: a first import makes no empty project."""
    if file == "-" and not yes:
        raise UserError("Reading the file from stdin needs --yes (nothing can ask).")
    found = (
        bundle.read(sys.stdin.read()) if file == "-" else bundle.read_file(Path(file))
    )
    for line in found.refused:
        print(f"  refused: {line}")
    if found.ignored:
        print(f"  ignored (unknown): {', '.join(found.ignored)}")
    new_name = workspace.free_name(found.project)
    if not into and not workspace.projects():
        into = "new"
    current = chosen() if into != "new" else None
    if not into:
        if yes:
            into = "new"
        else:
            answer = input(
                f"1) New project '{new_name}'  2) Add to '{chosen().name()}'  [1/2] "
            ).strip()
            into = {"1": "new", "": "new", "2": "current"}.get(answer, "")
            if not into:
                print("Nothing imported.")
                return 1
            current = chosen() if into == "current" else None
    changes = bundle.preview(current, found)
    print(f"Into {f"'{current.name()}'" if current else f"new project '{new_name}'"}:")
    for change in changes:
        print(f"  {change.describe()}")
    if all(c.kind == "same" for c in changes):
        print("Nothing to import.")
        return 0 if changes else 1
    if not yes and input("Import? [y/N] ").strip().lower() != "y":
        print("Nothing imported.")
        return 1
    library = current or workspace.create(new_name)
    bundle.apply(library, changes)
    print(f"Imported into '{library.name()}'. Download it:")
    if not current:
        print("  uv run downtempo download   (it's the current project now)")
    else:
        print(f"  uv run downtempo --project '{library.name()}' download")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="downtempo")
    parser.add_argument(
        "--project", default="", help="work on this project (default: the current one)"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("project", help="list, add, switch, rename, delete")
    command.add_argument(
        "action",
        nargs="?",
        default="list",
        choices=("list", "new", "use", "rename", "delete"),
    )
    command.add_argument(
        "names", nargs="*", help="a project's name (rename: and the new one)"
    )
    command.add_argument("--yes", action="store_true", help="delete without asking")
    command = commands.add_parser("add", help="add a shared folder by its link")
    command.add_argument("link")
    command.add_argument("--name", default="", help="default: the folder's name")
    command.add_argument("--folder", default="", help="a folder inside the share, a/b")
    command = commands.add_parser("folders", help="list the folders inside a share")
    command.add_argument("link")
    command.add_argument("path", nargs="?", default="", help="a folder inside, a/b")
    commands.add_parser("sources", help="list the shared folders and sign-ins")
    command = commands.add_parser("remove", help="forget a shared folder")
    command.add_argument("name")
    command.add_argument("--delete-files", action="store_true")
    command = commands.add_parser(
        "download", help="download what's new, then update the song list"
    )
    command.add_argument("names", nargs="*", help="only these sources")
    command.add_argument(
        "--dry-run", action="store_true", help="only show what would be downloaded"
    )
    commands.add_parser("catalog", help="rebuild the song list from the downloads")
    command = commands.add_parser("export", help="save the project's settings file")
    command.add_argument("file", help="e.g. my-band.downtempo.toml; - prints it")
    command = commands.add_parser("import", help="add sources from a settings file")
    command.add_argument("file", help="a .downtempo.toml file; - reads it from stdin")
    command.add_argument(
        "--new",
        dest="into",
        action="store_const",
        const="new",
        default="",
        help="as a new project",
    )
    command.add_argument(
        "--add",
        dest="into",
        action="store_const",
        const="current",
        help="into the current project",
    )
    command.add_argument(
        "--yes", action="store_true", help="don't ask (default: a new project)"
    )
    command = commands.add_parser(
        "songs", help="the songs, and the files in no song yet"
    )
    command.add_argument(
        "--explain", action="store_true", help="each file, its label and why"
    )
    command.add_argument(
        "--to-sort", action="store_true", help="only the unknown files (in no song yet)"
    )
    command.add_argument(
        "--create",
        action="store_true",
        help="make a song of every suggested song first (the player's Create selected)",
    )
    command = commands.add_parser("move", help="put a file into a song (by hand)")
    command.add_argument("file", help="a file id (source:path) or a unique end of it")
    command.add_argument("song", help="a song's title, also-called name or id")
    command = commands.add_parser("sign-out", help="forget a sign-in on this computer")
    command.add_argument("type", nargs="?", default="onedrive")
    args = parser.parse_args(argv)

    try:
        # moves data from before projects in, once
        workspace = Workspace(DATA_DIR)
        if args.command == "project":
            return project(workspace, args.action, args.names, args.yes)

        def chosen() -> Library:
            if args.project:
                return workspace.library(workspace.find(args.project))
            return workspace.current()

        if args.command == "import":
            return import_(workspace, chosen, args.file, args.into, args.yes)
        library = chosen()
        match args.command:
            case "add":
                return add(library, args.link, args.name, args.folder)
            case "folders":
                return folders(library, args.link, args.path)
            case "sources":
                return list_sources(library)
            case "remove":
                return remove(library, args.name, args.delete_files)
            case "download":
                return download(library, args.names, args.dry_run)
            case "catalog":
                print_diff(library.rebuild(mark_new=True))
                return 0
            case "export":
                return export(library, args.file)
            case "songs":
                return cli_songs.songs(library, args.explain, args.to_sort, args.create)
            case "move":
                return cli_songs.move(library, args.file, args.song)
            case "sign-out":
                return sign_out(library, args.type)
    except UserError as error:
        print_error(error)
        return 1
    except Cancelled:
        print("Stopped.", file=sys.stderr)
        return 130
    return 2
