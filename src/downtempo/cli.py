"""Command line: `uv run downtempo <command>`."""

import argparse
import sys

from downtempo.catalog import build_catalog
from downtempo.config import load_env, load_sources
from downtempo.downloaders import DOWNLOADERS
from downtempo.errors import UserError
from downtempo.events import print_report


def download(names: list[str]) -> int:
    load_env()
    try:
        sources = load_sources()
    except UserError as error:
        print_error(error)
        return 2
    if unknown := set(names) - {source.name for source in sources}:
        print(
            f"Unknown sources: {', '.join(sorted(unknown))}. Known: {', '.join(s.name for s in sources)}",
            file=sys.stderr,
        )
        return 2

    status = 0
    for source in sources:
        if names and source.name not in names:
            continue
        print(f"== {source.name} ({source.type})")
        downloader = DOWNLOADERS.get(source.type)
        if not downloader:
            print(
                f"{source.name}: unknown type '{source.type}'. Known: {', '.join(DOWNLOADERS)}",
                file=sys.stderr,
            )
            status = 2
            continue
        try:
            downloader(source, print_report)
        except UserError as error:
            print_error(error, source.name)
            status = 1
    return status


def print_error(error: UserError, source: str = "") -> None:
    print(f"{source}: {error.message}" if source else error.message, file=sys.stderr)
    if error.hint:
        print(f"  {error.hint}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="downtempo")
    commands = parser.add_subparsers(dest="command", required=True)
    download_parser = commands.add_parser(
        "download", help="download every source in data/sources.toml"
    )
    download_parser.add_argument("names", nargs="*", help="only these sources")
    commands.add_parser("catalog", help="scan data/downloads/ into data/songs.json")
    args = parser.parse_args(argv)

    match args.command:
        case "download":
            return download(args.names)
        case "catalog":
            build_catalog()
            return 0
    return 2
