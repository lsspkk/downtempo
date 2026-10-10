"""Dev tool: open a page in Qt WebEngine, run JavaScript steps, save a screenshot after each.

Usage: uv run python scripts/screenshot.py <url> <out-prefix> [--wait MS] [--size WxH] [js ...]
Saves <out-prefix>-0.png after loading, then <out-prefix>-<k>.png after the k-th script. Each script
runs `--wait` ms (default 3000) after the previous one. `key("n")` presses a key (keydown + keyup on
document), `text()` returns the page text; the value of the last statement is printed.

Example (player in --browser mode): press N six times fast, then grab:
  uv run python scripts/screenshot.py http://127.0.0.1:8765 /tmp/shot \
    'for (let i = 0; i < 6; i++) key("n")' 'text().slice(0, 300)'
"""

import argparse
import json
import sys

from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication

HELPERS = """
window.key = (k) => {
  for (const type of ['keydown', 'keyup'])
    document.dispatchEvent(new KeyboardEvent(type, {key: k, bubbles: true}));
};
window.text = () => document.body.innerText;
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("url")
    parser.add_argument("out")
    parser.add_argument("--wait", type=int, default=3000)
    parser.add_argument("--size", default="1400x900", help="window size, e.g. 1280x720")
    parser.add_argument("scripts", nargs="*")
    args = parser.parse_intermixed_args()

    app = QApplication(sys.argv[:1])
    view = QWebEngineView()
    view.resize(*map(int, args.size.split("x")))
    view.load(QUrl(args.url))
    view.show()

    def grab(k: int) -> None:
        path = f"{args.out}-{k}.png"
        view.grab().save(path)
        print(f"saved {path}")

    def step(k: int = 0) -> None:
        grab(k)
        if k >= len(args.scripts):
            app.quit()
            return
        script = f"{HELPERS}\neval({json.dumps(args.scripts[k])})"
        view.page().runJavaScript(
            script, lambda result: print(f"[{k + 1}] {result}") if result else None
        )
        QTimer.singleShot(args.wait, lambda: step(k + 1))

    QTimer.singleShot(args.wait, step)
    app.exec()


if __name__ == "__main__":
    main()
