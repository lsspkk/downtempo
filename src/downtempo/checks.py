"""`checked.json`: what the last check of each source found: when it ran to the end, and which
downloaded files are no longer on the server (the project screen's "removed on server"). This
computer's, not exported. `{"<source>": {"at": "<ISO time>", "gone": ["<file id>", …]}}`."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from downtempo.jsonfile import write_json
from downtempo.sync import SyncResult


@dataclass(frozen=True)
class Check:
    at: str  # ISO time
    gone: tuple[str, ...] = ()  # file ids


def read_checks(path: Path) -> dict[str, Check]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    found = {}
    for source, entry in data.items() if isinstance(data, dict) else ():
        if isinstance(entry, str):  # the first version kept only the time
            found[source] = Check(entry)
        elif isinstance(entry, dict) and isinstance(entry.get("at"), str):
            gone = entry.get("gone", [])
            found[source] = Check(
                entry["at"], tuple(g for g in gone if isinstance(g, str))
            )
    return found


def write_checks(path: Path, checks: dict[str, Check], known: set[str]) -> None:
    write_json(
        path,
        {
            s: {"at": c.at, "gone": list(c.gone)}
            for s, c in checks.items()
            if s in known
        },
    )


def record(
    path: Path, results: list[SyncResult], targets: dict[str, Path], known: set[str]
) -> None:
    """Sources checked to the end get the time and their gone files; the others keep theirs."""
    checks = read_checks(path)
    now = datetime.now().isoformat(timespec="seconds")
    for result in results:
        if result.plan is None or result.cancelled:
            continue
        target = targets[result.source]
        gone = tuple(
            f"{result.source}:{p.relative_to(target).as_posix()}"
            for p in result.plan.gone
            if p.is_relative_to(target)
        )
        checks[result.source] = Check(now, gone)
    write_checks(path, checks, known)


def rename_source(path: Path, old: str, new: str, known: set[str]) -> None:
    checks = read_checks(path)
    if old in checks:
        check = checks.pop(old)
        gone = tuple(f"{new}:{g.partition(':')[2]}" for g in check.gone)
        checks[new] = Check(check.at, gone)
        write_checks(path, checks, known)
