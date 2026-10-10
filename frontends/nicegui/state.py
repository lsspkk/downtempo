"""What the player remembers between runs, in `data/player-state.json`.

```
{"last_song": "<collection>/<title>", "volume": 80, "dark": false, "zoom": 100, "fit": "page",
 "view": {"library": true, "controls": "full", "rotate": 0},
 "settings": {"scroll_step": 20, "page_mode": "screen", "tempo_step": 5, "smooth": true},
 "songs": {"<collection>/<title>": {"audio": "<path>", "pdf": "<path>", "speed": 0.75, "semitones": 0,
                                     "trainer": {"step": 0.05, "every": 2, "target": 1.0}}},
 "recordings": {"<audio path>": {"position": 12.5, "loop": [10.0, 18.5], "loops": [{"name": "B part", "a": 10.0, "b": 18.5}]}}}
```
Loops belong to a recording (times differ between recordings), tempo and the chosen files to the song.
"""

import json
from typing import Any

from downtempo.config import DATA_DIR

STATE_FILE = DATA_DIR / "player-state.json"


def load_state() -> dict[str, Any]:
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}
    state.setdefault("songs", {})
    state.setdefault("recordings", {})
    return state


def save_state(state: dict[str, Any]) -> None:
    partial = STATE_FILE.with_suffix(".partial")
    partial.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    partial.replace(STATE_FILE)
