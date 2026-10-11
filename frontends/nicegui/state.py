"""What the player remembers between runs: the layout in `data/app.json` (the computer's), the
practice memory in the project's `practice.json`. The player sees them as one dict.

```
app.json:      {"project": "<id>", "volume": 80, "dark": false, "zoom": 100, "fit": "page",
                "view": {"library": true, "controls": "full", "rotate": 0},
                "settings": {"scroll_step": 20, "page_mode": "screen", "tempo_step": 5, "smooth": true}}
practice.json: {"last_song": "<song id>",
 "songs": {"<song id>": {"audio": "<path>", "pdf": "<path>", "pdf_picked": false, "speed": 0.75, "semitones": 0,
                                     "trainer": {"step": 0.05, "every": 2, "target": 1.0}}},
 "recordings": {"<audio path>": {"position": 12.5, "loop": [10.0, 18.5], "loops": [{"name": "B part", "a": 10.0, "b": 18.5}]}}}
```
Loops belong to a recording (times differ between recordings), tempo and the chosen files to the song.
`pdf_picked`: the user chose that sheet; otherwise the newest version (the first) opens.
"""

from pathlib import Path
from typing import Any

from downtempo.projects import PRACTICE_KEYS, read_json, update_json, write_json

# Where `save_state` writes; set by `load_state` (a project switch loads again).
files: dict[str, Path] = {}


def load_state(app_file: Path, practice_file: Path) -> dict[str, Any]:
    files.update(app=app_file, practice=practice_file)
    state = read_json(app_file) | read_json(practice_file)
    state.setdefault("songs", {})
    state.setdefault("recordings", {})
    return state


def save_state(state: dict[str, Any]) -> None:
    write_json(files["practice"], {k: state[k] for k in PRACTICE_KEYS if k in state})
    # The current project is the workspace's to change (the CLI may have, meanwhile).
    layout = {k: v for k, v in state.items() if k not in (*PRACTICE_KEYS, "project")}
    update_json(files["app"], **layout)
