"""Command line: `uv run downtempo <command>`."""

import argparse
import sys

import requests

from downtempo.config import load_env, load_sources
from downtempo.downloaders import DOWNLOADERS


def download(names: list[str]) -> int:
    load_env()
    try:
        sources = load_sources()
    except RuntimeError as error:
        print(error, file=sys.stderr)
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
            downloader(source)
        except requests.HTTPError as error:
            print(
                f"{source.name}: request failed: {error}\n{error.response.text}",
                file=sys.stderr,
            )
            status = 1
        except (requests.RequestException, RuntimeError) as error:
            print(f"{source.name}: {error}", file=sys.stderr)
            status = 1
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="downtempo")
    commands = parser.add_subparsers(dest="command", required=True)
    download_parser = commands.add_parser(
        "download", help="download every source in data/sources.toml"
    )
    download_parser.add_argument("names", nargs="*", help="only these sources")
    args = parser.parse_args(argv)

    match args.command:
        case "download":
            return download(args.names)
    return 2
