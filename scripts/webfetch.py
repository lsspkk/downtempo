"""Save a web page to docs/web (raw .html + readable .txt) and record it in docs/web/INDEX.md.

Usage: uv run python scripts/webfetch.py <name> <url> "<one-line summary>"
       uv run python scripts/webfetch.py --text-only   # rebuild .txt for every saved .html
"""

from __future__ import annotations

import html
import re
import sys
from datetime import date
from pathlib import Path

import requests

WEB_DIR = Path(__file__).resolve().parent.parent / "docs" / "web"
INDEX = WEB_DIR / "INDEX.md"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
)


def html_to_text(source: str) -> str:
    text = re.sub(
        r"(?is)<(script|style|nav|header|footer|svg)[^>]*>.*?</\1>", " ", source
    )
    text = re.sub(r"(?i)<(br|/p|/div|/li|/h\d|/tr|/pre)[^>]*>", "\n", text)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n", text).strip() + "\n"


def save(name: str, url: str, summary: str) -> None:
    if f"| {url} |" in INDEX.read_text(encoding="utf-8"):
        print(f"Already saved: {url} (see {INDEX})")
        return
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    (WEB_DIR / f"{name}.html").write_text(response.text, encoding="utf-8")
    (WEB_DIR / f"{name}.txt").write_text(html_to_text(response.text), encoding="utf-8")
    with INDEX.open("a", encoding="utf-8") as index:
        index.write(f"| {name} | {date.today()} | {url} | {summary} |\n")
    print(f"Saved docs/web/{name}.txt ({len(response.text)} bytes html)")


def main() -> int:
    if sys.argv[1:] == ["--text-only"]:
        for page in sorted(WEB_DIR.glob("*.html")):
            page.with_suffix(".txt").write_text(
                html_to_text(page.read_text(encoding="utf-8", errors="ignore")),
                encoding="utf-8",
            )
        return 0
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    save(*sys.argv[1:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
