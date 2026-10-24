"""A song's recordings: the labelled dropdown at the top of the controls, the "♪ 2/3" menu of the
sheet-only bar and the chips of the loop editor. Clicks only, so code never sets a value that
would fire a pick (docs/player-switching.md); T steps through them (keys.py)."""

from common import tip
from nicegui import ui
from player import Player

# Quasar menus take Tab and Enter, not arrows: ↑ / ↓ move between a menu's rows here (before the
# player's keys, which would change the tempo or scroll the sheet). Esc closes it (Quasar).
MENU_KEYS = """<script>
window.addEventListener('keydown', (e) => {
  if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
  const menu = [...document.querySelectorAll('.q-menu')].pop();
  if (!menu) return;
  const rows = [...menu.querySelectorAll('.q-item[tabindex]')];
  if (!rows.length) return;
  e.preventDefault(); e.stopImmediatePropagation();
  const at = rows.indexOf(document.activeElement);
  const to = at < 0 ? (e.key === 'ArrowDown' ? 0 : rows.length - 1)
    : (at + (e.key === 'ArrowDown' ? 1 : rows.length - 1)) % rows.length;
  rows[to].focus();
}, true);
</script>"""


def recording_name(label: str, title: str) -> str:
    """`<Title> - live 2025` -> `live 2025`; the title is shown elsewhere."""
    return label.replace(title, "").strip(" -_()") or label


def recording_names(player: Player) -> dict[str, str]:
    song = player.song
    return {a["path"]: recording_name(a["label"], song["title"]) for a in song["audio"]}


def menu_rows(player: Player) -> None:
    """One row per recording: ✓ on the current one, the name in full, its recording tempo."""
    current = player.selection.audio
    for path, name in recording_names(player).items():
        bpm = player.state["recordings"].get(path, {}).get("bpm")
        with (
            ui.menu_item(on_click=lambda path=path: player.pick_recording(path)),
            ui.row().classes("w-full items-center gap-2 no-wrap"),
        ):
            ui.icon("check" if path == current else "", size="18px").classes(
                "text-primary w-5"
            )
            ui.label(name).classes(
                "grow" + (" text-primary font-medium" if path == current else "")
            )
            ui.label(f"{bpm:.0f} BPM" if bpm else "").classes("text-caption text-grey")


def recording_chips(box: ui.element, player: Player) -> None:
    """One chip per recording when there are several (the loop editor's header)."""
    box.clear()
    names = recording_names(player)
    if len(names) < 2:
        return
    current = player.selection.audio
    with box, ui.row().classes("w-full items-center gap-1"):
        ui.icon("audiotrack", size="20px").classes("text-grey")
        for path, name in names.items():
            chip = ui.chip(
                name, on_click=lambda path=path: player.pick_recording(path)
            ).props(
                "dense clickable square color=primary"
                + (" text-color=white" if path == current else " outline")
            )
            tip(chip, "Recording (T: next)")


class RecordingPicker:
    """`Recording [ live 2025 ▾ ] 2 of 3`; with one recording its name as plain text, and
    nothing when it is named after the song."""

    def __init__(self, player: Player) -> None:
        self.player = player
        ui.add_head_html(MENU_KEYS)
        with ui.row().classes("w-full items-center gap-2 no-wrap") as self.row:
            ui.label("Recording").classes("text-subtitle2 shrink-0")
            self.box = ui.element("div").classes("min-w-0 grow")
        self.row.set_visibility(False)
        self.shown: tuple = ()
        player.on("selection", lambda new_song: self.show())
        player.on("bpm", self.show)

    def show(self) -> None:
        player = self.player
        if not player.song:
            return
        names = recording_names(player)
        current = player.selection.audio
        tempos = player.state["recordings"]
        shown = (
            current,
            *names.items(),
            *(tempos.get(p, {}).get("bpm") for p in names),
        )
        if (
            shown == self.shown
        ):  # "bpm" comes with every tempo change; an open menu stays
            return
        self.shown = shown
        self.box.clear()
        label = next(
            (a["label"] for a in player.song["audio"] if a["path"] == current), ""
        )
        self.row.set_visibility(
            len(names) > 1 or (len(names) == 1 and label != player.song["title"])
        )
        with self.box, ui.row().classes("w-full items-center gap-2 no-wrap"):
            if len(names) < 2:
                ui.label(label).classes("text-grey truncate")
                return
            button = (
                ui.button(names.get(current, ""))
                .props(
                    "outline dense no-caps no-wrap align=between content-class=truncate "
                    "icon-right=arrow_drop_down"
                )
                .classes("grow min-w-0 px-2")
            )
            tip(button, f"{names.get(current, '')} (T: next recording)")
            with button, ui.menu().props("fit"):
                menu_rows(player)
            number = list(names).index(current) + 1 if current in names else 0
            ui.label(f"{number} of {len(names)}").classes(
                "text-caption text-grey shrink-0"
            )
