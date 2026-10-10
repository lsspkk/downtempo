"""Python player: NiceGUI in a native window (pywebview), sound stretched and played in Python.

Run: `uv run python frontends/nicegui/app.py`. Features and shortcuts: docs/player.md.
"""

import base64
import json
import re
import sys
import webbrowser
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium
import sounddevice as sd
from engine import DETAIL_FRAMES, Engine
from nicegui import app, events, run, ui
from sheets import CACHE_DIR, page_images
from state import load_state, save_state

from downtempo.catalog import Song, read_catalog
from downtempo.config import DATA_DIR

# Module level, not under the main guard: the native window runs in its own process (NiceGUI docs).
# Qt comes as wheels (pyproject); GTK would need the system's PyGObject.
if sys.platform == "linux":
    app.native.start_args["gui"] = "qt"

SPEEDS = (0.5, 1.3)  # min, max
PRESETS = (0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 1.0)
TRAINER = {"step": 0.05, "every": 2, "target": 1.0}  # defaults; remembered per song
# Layout and keys: docs/practice-layout.md. Both remembered in state["view"] / state["settings"].
VIEW = {"library": True, "controls": "full", "rotate": 0}
SETTINGS = {"scroll_step": 20, "page_mode": "screen", "tempo_step": 5, "smooth": True}
WAVE_W, WAVE_H = 1000, 200
LOOP_COLOR = "#f59e0b"
SHORTCUTS = {
    "Playing": [
        ("Space / K", "Play / pause"),
        ("← / →", "Tempo slower / faster"),
        (", / .", "Back / forward 5 s"),
        ("J / L", "Back / forward 10 s"),
        ("0", "To start (loop start when looping)"),
        ("1 … 9", "Jump to 10 % … 90 %"),
        ("A / B", "Loop start / end here"),
        ("R", "Loop on / off"),
        ("C", "Clear loop"),
        ("S", "Save loop"),
        ("T / Shift+T", "Next / previous recording"),
        ("M", "Mute"),
        ("E", "Loop editor: zoom in, select exactly"),
        ("Shift+Space", "Hear the loop end (editor)"),
    ],
    "Sheet and view": [
        ("↑ / ↓", "Scroll the sheet"),
        ("PgUp / PgDn", "A screen or page (footswitch)"),
        ("Home / End", "Sheet top / bottom"),
        ("+ / −", "Sheet zoom"),
        ("W / H", "Fit width / fit page"),
        ("O", "Rotate the sheet"),
        ("F", "Full screen (Esc back)"),
        ("V", "Controls: full, simple, none"),
        ("Q", "Song list"),
        ("N / P", "Next / previous song"),
        ("/", "Search songs"),
        ("?", "This help"),
    ],
}
# The sheet viewport turns as a whole, so its scrollbar, the wheel and the scroll keys follow the
# page. The frame is a size container: 100cqw/100cqh are its width/height.
ROTATIONS = {
    0: "width: 100%; height: 100%",
    90: "width: 100cqh; height: 100cqw; transform-origin: 0 0; transform: translateX(100cqw) rotate(90deg)",
    180: "width: 100%; height: 100%; transform: rotate(180deg)",
    270: "width: 100cqh; height: 100cqw; transform-origin: 0 0; transform: translateY(100cqh) rotate(-90deg)",
}
# Sheet scroll keys run in the page: no server round trip, and preventDefault stops the browser
# from scrolling too. A press during a smooth scroll continues from its target, so a quick
# double tap on a footswitch moves two steps. Space and ←/→ only get preventDefault (the server
# handles them) so a focused scroll area doesn't also scroll.
SHEET_KEYS = """<script>
window.dt = {settings: %s, target: null, timer: null, fit: null};
dt.scrollTo = (el, top) => {
  top = Math.max(0, Math.min(top, el.scrollHeight - el.clientHeight));
  clearTimeout(dt.timer);
  dt.target = dt.settings.smooth ? top : null;
  if (dt.settings.smooth) dt.timer = setTimeout(() => { dt.target = null; }, 600);
  el.scrollTo({top, behavior: dt.settings.smooth ? 'smooth' : 'instant'});
};
dt.scroll = (kind, dir) => {
  const el = document.querySelector('.sheet-view');
  if (!el) return;
  const from = dt.target ?? el.scrollTop;
  if (kind === 'step') return dt.scrollTo(el, from + dir * el.clientHeight * dt.settings.scroll_step / 100);
  if (kind === 'end') return dt.scrollTo(el, dir < 0 ? 0 : el.scrollHeight);
  if (dt.settings.page_mode === 'page') {
    const tops = [...el.querySelectorAll('img')].map((img) => img.offsetTop - 8);
    const next = dir > 0 ? tops.find((t) => t > from + 24) : tops.reverse().find((t) => t < from - 24);
    return dt.scrollTo(el, next ?? (dir > 0 ? el.scrollHeight : 0));
  }
  dt.scrollTo(el, from + dir * el.clientHeight * 0.85);
};
const SCROLL_KEYS = {ArrowUp: ['step', -1], ArrowDown: ['step', 1], PageUp: ['screen', -1],
                     PageDown: ['screen', 1], Home: ['end', -1], End: ['end', 1]};
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey || e.altKey || e.metaKey) return;
  if (['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return;
  if (document.querySelector('.q-dialog')) return;
  const action = SCROLL_KEYS[e.key];
  if (action) { e.preventDefault(); dt.scroll(...action); }
  else if ([' ', 'ArrowLeft', 'ArrowRight'].includes(e.key)) e.preventDefault();
});
// Fit page: the zoom (width %%) at which the page at the top of the view fits whole, in the
// view's own (rotated) axes; never wider than fit width. Waits for the image to load.
dt.fitPage = async () => {
  const el = document.querySelector('.sheet-view');
  const imgs = el ? [...el.querySelectorAll('img')] : [];
  if (!imgs.length) return null;
  const img = imgs.filter((i) => i.offsetTop - 16 <= el.scrollTop + 24).pop() ?? imgs[0];
  if (!img.naturalWidth) await new Promise((done) => {
    img.addEventListener('load', done, {once: true});
    img.addEventListener('error', done, {once: true});
  });
  if (!img.naturalWidth) return null;
  const width = el.clientWidth - 32, height = el.clientHeight - 32;  // minus p-4
  const zoom = height * img.naturalWidth / img.naturalHeight / width * 100;
  return {zoom: Math.floor(Math.min(100, zoom)), page: imgs.indexOf(img)};
};
// After the server changed the zoom: put that page at the top again.
dt.toPage = (page) => requestAnimationFrame(() => requestAnimationFrame(() => {
  const el = document.querySelector('.sheet-view');
  const img = el?.querySelectorAll('img')[page];
  if (img) el.scrollTo({top: img.offsetTop - 16, behavior: 'instant'});
}));
// The frame changes size with the window, song list, controls and full screen: fit again.
dt.watch = () => new ResizeObserver(() => { if (dt.fit === 'page') emitEvent('refit'); })
  .observe(document.querySelector('.sheet-frame'));
// Browser full screen; leaving it with Esc (which the browser keeps) tells the server.
dt.fullscreen = (on) => on ? document.documentElement.requestFullscreen?.().catch(() => {})
  : document.fullscreenElement && document.exitFullscreen();
document.addEventListener('fullscreenchange', () => {
  if (!document.fullscreenElement) emitEvent('fullscreen_left');
});
</script>"""
# Buttons and sliders keep focus after a click, and NiceGUI's keyboard ignores keys on a focused
# button; blurring after a mouse click keeps the shortcuts working. Tab focus is left alone.
BLUR_AFTER_CLICK = """<script>
document.addEventListener('pointerup', () => setTimeout(() => {
  const el = document.activeElement;
  if (el && !['INPUT', 'TEXTAREA'].includes(el.tagName)) el.blur();
}, 0));
</script>"""
# A select refocuses itself when its menu closes, which would swallow the next shortcut key.
LOOP_EDITOR_JS = (Path(__file__).parent / "loop_editor.js").read_text(encoding="utf-8")
BLUR_SELECT = "() => setTimeout(() => document.activeElement.blur(), 50)"
CSS = """
.song-active { background: rgba(79, 91, 213, 0.12); }
.sheet-bg { background: #e8e8ec; }
.body--dark .sheet-bg { background: #2a2a2e; }
.app-header { background: white; color: #1d1d1f; border-bottom: 1px solid #e0e0e6; }
.body--dark .app-header { background: #1d1d1f; color: white; border-color: #333; }
.loop-edge { background: rgba(245, 158, 11, 0.08); }
.pane-border { border-right: 1px solid rgba(128, 128, 128, 0.25); }
.le-header { border-bottom: 1px solid rgba(128, 128, 128, 0.25); }
.sheet-frame { position: relative; overflow: hidden; container-type: size; min-height: 0; }
.sheet-view { position: absolute; top: 0; left: 0; overflow: auto; }
.turn-90 i { transform: rotate(90deg); }
.sheet-tabs { max-width: 100%; }
.sheet-tabs .q-btn { min-width: 3rem; flex: 0 1 auto; }
.sheet-tabs .q-btn__content { min-width: 0; flex-wrap: nowrap; }
.sheet-tabs .q-btn .block { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fullscreen-exit { position: absolute; top: 8px; right: 24px; z-index: 10; opacity: 0.35; }
.fullscreen-exit:hover { opacity: 1; }
"""

engine = Engine()
# One engine, so one page drives it: the newest (a reload is a new page while the old one lingers).
owner = {"client": ""}
state = load_state()
CACHE_DIR.mkdir(parents=True, exist_ok=True)
app.add_static_files("/pages", CACHE_DIR)


def song_key(song: Song) -> str:
    return f"{song['collection']}/{song['title']}"


def tip(element: ui.element, text: str) -> ui.tooltip:
    """One tooltip to change later via `.text` (`element.tooltip()` adds a new one per call)."""
    with element:
        return ui.tooltip(text)


def clock(seconds: float) -> str:
    seconds = max(int(seconds), 0)
    return f"{seconds // 60}:{seconds % 60:02}"


def clock_tenths(seconds: float) -> str:
    return f"{clock(seconds)}.{int(seconds * 10) % 10}"


def parse_clock(text: str) -> float | None:
    """`1:11.2` or `71.2` -> seconds; None when it isn't a time."""
    try:
        minutes, _, seconds = text.strip().rpartition(":")
        return (int(minutes) * 60 if minutes else 0) + float(seconds)
    except ValueError:
        return None


def event_arg(e: events.GenericEventArguments) -> Any:
    """The single argument of a page event (emitEvent)."""
    return e.args[0] if isinstance(e.args, list) else e.args


def recording_name(label: str, title: str) -> str:
    """`<Title> - live 2025` -> `live 2025`; the title is shown elsewhere."""
    return label.replace(title, "").strip(" -_()") or label


def sheet_label(pdf: str, title: str) -> str:
    """`<Title> SOINNUT-2026-10-07.pdf` -> `SOINNUT · 2026-10-07`; the title is shown elsewhere."""
    rest = Path(pdf).stem.replace(title, "").strip(" -_")
    if match := re.search(r"(\d{4}-\d{2}-\d{2})$", rest):
        name = rest[: match.start()].strip(" -_")
        return f"{name} · {match[1]}" if name else f"Sheet · {match[1]}"
    return rest or "Sheet"


def wave_svg(peaks) -> str:
    """The waveform as an SVG data URL: mirrored bars, one per peak bin."""
    mid = WAVE_H / 2
    bars = " ".join(
        f"M{x} {mid - p * mid * 0.95:.1f}V{mid + p * mid * 0.95:.1f}"
        for x, p in enumerate(peaks)
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WAVE_W}" height="{WAVE_H}" '
        f'viewBox="0 0 {WAVE_W} {WAVE_H}"><path d="{bars}" stroke="%238a94b0" '
        'stroke-width="1"/></svg>'
    )
    return "data:image/svg+xml;utf8," + svg.replace("#", "%23").replace('"', "'")


@dataclass(frozen=True, eq=False)
class Selection:
    """What the user picked. Only user actions make a new one; loaders work on this snapshot."""

    song: Song
    audio: str  # "" when the song has no recording
    pdf: str  # "" when the song has no sheet


@dataclass
class Session:
    """What the window shows; persisted parts live in `state`."""

    songs: list[Song]
    selection: Selection | None = None
    audio: str = ""  # path of the loaded recording; "" while loading
    loop: tuple[float, float] | None = None  # seconds, kept while looping is off
    looping: bool = False
    drag_from: float | None = None
    drag_to: float | None = None
    muted: bool = False
    trainer: dict[str, Any] = field(default_factory=lambda: {"on": False, **TRAINER})
    dirty: bool = False
    fullscreen: bool = False  # only the sheet; not remembered
    editor: bool = False  # the loop editor is open
    undo_base: Any = None  # (loop, looping) the editor's undo starts from
    loop_history: list[Any] = field(
        default_factory=list
    )  # earlier (loop, looping), newest last
    # Newest-wins tickets per part: a load gives up when a newer one of its part was asked for.
    # Separate, so a sheet tab click doesn't cancel the song's audio load (and the other way).
    tickets: dict[str, int] = field(default_factory=lambda: {"audio": 0, "sheet": 0})

    @property
    def song(self) -> Song | None:
        return self.selection.song if self.selection else None

    def ticket(self, part: str) -> int:
        self.tickets[part] += 1
        return self.tickets[part]

    @property
    def song_state(self) -> dict[str, Any]:
        return state["songs"].setdefault(song_key(self.song), {}) if self.song else {}

    @property
    def recording_state(self) -> dict[str, Any]:
        return state["recordings"].setdefault(self.audio, {}) if self.audio else {}


def root() -> None:
    view = state["view"] = {**VIEW, **state.get("view", {})}
    settings = state["settings"] = {**SETTINGS, **state.get("settings", {})}
    ui.add_head_html(BLUR_AFTER_CLICK)
    ui.add_head_html(SHEET_KEYS % json.dumps(settings))
    ui.add_body_html(f"<script>{LOOP_EDITOR_JS}</script>")
    ui.add_css(CSS)
    ui.colors(primary="#4f5bd5", accent=LOOP_COLOR)
    ui.query(".nicegui-content").classes("p-0 gap-0")
    dark = ui.dark_mode(state.get("dark", False))
    s = Session(songs=read_catalog())
    me = owner["client"] = ui.context.client.id

    # ---------------------------------------------------------------- actions

    def remember(**song_values: Any) -> None:
        s.song_state.update(song_values)
        s.dirty = True

    def remember_loops() -> None:
        s.recording_state["loop"] = list(s.loop) if s.loop and s.looping else None
        s.dirty = True

    def set_speed(value: float) -> None:
        if not s.audio:  # loading: the value would land on the new song
            return
        engine.speed = round(min(max(value, SPEEDS[0]), SPEEDS[1]), 2)
        remember(speed=engine.speed)
        show_speed()

    def tempo_step(direction: int) -> None:
        set_speed(engine.speed + direction * settings["tempo_step"] / 100)

    def set_semitones(value: int) -> None:
        if not s.audio:
            return
        engine.semitones = max(-12, min(12, value))
        remember(semitones=engine.semitones)
        pitch_label.text = f"{engine.semitones:+d}" if engine.semitones else "0"

    def set_volume(value: float) -> None:
        state["volume"] = value
        s.dirty = True
        engine.volume = 0.0 if s.muted else (value / 100) ** 2

    def toggle_mute() -> None:
        s.muted = not s.muted
        set_volume(state.get("volume", 80))
        mute_button.props(f"icon={'volume_off' if s.muted else 'volume_up'}")

    def toggle_play() -> None:
        if not s.audio:
            return
        engine.pause() if engine.playing else engine.play()

    def seek(seconds: float) -> None:
        if s.audio:
            engine.seek(seconds * engine.rate)

    def skip(seconds: float) -> None:
        seek(engine.position / engine.rate + seconds)

    def to_start() -> None:
        seek(s.loop[0] if s.loop and s.looping else 0)

    def apply_loop() -> None:
        if s.editor and (s.loop, s.looping) != s.undo_base:  # undo in the loop editor
            s.loop_history.append(s.undo_base)
            s.undo_base = (s.loop, s.looping)
        frames = None
        if s.loop and s.looping:
            frames = (int(s.loop[0] * engine.rate), int(s.loop[1] * engine.rate))
        engine.set_loop(frames)
        remember_loops()
        show_loop()

    def set_loop(a: float, b: float) -> None:
        a, b = sorted((max(a, 0), min(b, engine.duration)))
        if b - a < 0.2:
            ui.notify("Loop too short: at least 0.2 s", type="warning")
            return
        s.loop, s.looping = (a, b), True
        apply_loop()

    def set_a() -> None:
        now = engine.position / engine.rate
        b = s.loop[1] if s.loop and s.loop[1] > now + 0.2 else engine.duration
        set_loop(now, b)

    def set_b() -> None:
        now = engine.position / engine.rate
        a = s.loop[0] if s.loop and s.loop[0] < now - 0.2 else 0.0
        set_loop(a, now)

    def nudge(edge: int, seconds: float) -> None:
        if s.loop:
            loop = list(s.loop)
            loop[edge] += seconds
            set_loop(*loop)

    def toggle_loop() -> None:
        if not s.loop:
            ui.notify("Set a loop first: press A and B, or drag over the waveform")
            return
        s.looping = not s.looping
        apply_loop()

    def clear_loop() -> None:
        s.loop, s.looping = None, False
        apply_loop()

    def set_gap(value: float) -> None:
        engine.loop_gap = value
        state["loop_gap"] = value
        s.dirty = True

    def save_loop_dialog() -> None:
        if not s.loop:
            ui.notify("Set a loop first: press A and B, or drag over the waveform")
            return
        loops = s.recording_state.setdefault("loops", [])
        with ui.dialog() as dialog, ui.card().classes("min-w-[320px]"):
            ui.label("Save loop").classes("text-h6")
            ui.label(f"{clock(s.loop[0])} – {clock(s.loop[1])}").classes("text-grey")
            name = ui.input("Name", value=f"Part {len(loops) + 1}").props("autofocus")

            def save() -> None:
                loops.append(
                    {
                        "name": name.value.strip() or "Loop",
                        "a": s.loop[0],
                        "b": s.loop[1],
                    }
                )
                s.dirty = True
                dialog.close()
                show_saved_loops()

            name.on("keydown.enter", save)
            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button("Save", on_click=save)
        dialog.open()

    def use_saved_loop(saved: dict[str, Any]) -> None:
        set_loop(saved["a"], saved["b"])
        seek(saved["a"])

    def delete_saved_loop(saved: dict[str, Any]) -> None:
        s.recording_state.get("loops", []).remove(saved)
        s.dirty = True
        show_saved_loops()

    def toggle_trainer(on: bool) -> None:
        s.trainer["on"] = on
        engine.reset_repeats()
        show_trainer()

    def set_trainer(key: str, value: float) -> None:
        if s.trainer[key] == value:  # also when restore_trainer() sets the inputs
            return
        s.trainer[key] = value
        if s.audio:
            remember(trainer={k: s.trainer[k] for k in TRAINER})
        show_trainer()

    def restore_trainer() -> None:
        saved = {**TRAINER, **s.song_state.get("trainer", {})}
        for key, widget in trainer_inputs.items():
            s.trainer[key] = saved[key]
            widget.value = saved[key]
        show_trainer()

    async def step_song(offset: int) -> None:
        shown = filtered_songs()
        if not shown:
            return
        index = shown.index(s.song) if s.song in shown else -1
        await open_song(shown[(index + offset) % len(shown)])

    # Switching (docs/player-switching.md): user actions make a new Selection and update the
    # screen at once; the loaders then work on that snapshot and give up when overtaken. Code
    # never sets the recording select or sheet toggle value: they are rebuilt per song, so their
    # on_change fires only for real user picks.

    async def open_song(song: Song) -> None:
        engine.pause()
        save_position()
        saved = state["songs"].get(song_key(song), {})
        audios = [a["path"] for a in song["audio"]]
        audio = saved.get("audio")
        if audio not in audios:
            audio = audios[0] if audios else ""
        pdf = saved.get("pdf")
        if pdf not in song["pdf"]:
            pdf = song["pdf"][0] if song["pdf"] else ""
        sel = s.selection = Selection(song, audio, pdf)
        s.audio = ""
        audio_ticket, sheet_ticket = s.ticket("audio"), s.ticket("sheet")
        show_library()
        title.text = song["title"]
        show_pickers(sel)
        sheet_pages.clear()  # the old song's sheet must not stay while the audio loads
        await load_audio(sel, audio_ticket)
        await load_sheet(sel, sheet_ticket)

    async def pick_recording(path: str | None) -> None:
        if not path or not s.selection or path == s.selection.audio:
            return
        engine.pause()
        save_position()
        sel = s.selection = replace(s.selection, audio=path)
        s.audio = ""
        show_recordings(sel)
        await load_audio(sel, s.ticket("audio"))

    async def step_recording(offset: int) -> None:
        if not s.selection:
            return
        paths = [a["path"] for a in s.selection.song["audio"]]
        if len(paths) > 1:
            index = paths.index(s.selection.audio) if s.selection.audio in paths else 0
            await pick_recording(paths[(index + offset) % len(paths)])

    async def pick_sheet(pdf: str | None) -> None:
        if not pdf or not s.selection or pdf == s.selection.pdf:
            return
        sel = s.selection = replace(s.selection, pdf=pdf)
        await load_sheet(sel, s.ticket("sheet"))

    def show_recordings(sel: Selection) -> None:
        """Recording chips in the pane and a menu in the sheet-only bar. Clicks only, so no
        value for code to set (docs/player-switching.md, option E)."""
        audios = sel.song["audio"]
        for box in (recording_box, mini_recordings, editor_recordings):
            box.clear()
        mini_recordings.set_visibility(len(audios) > 1)
        if len(audios) < 2:
            return
        names = {
            a["path"]: recording_name(a["label"], sel.song["title"]) for a in audios
        }
        for box in (recording_box, editor_recordings):
            with box, ui.row().classes("w-full items-center gap-1"):
                ui.icon("audiotrack", size="20px").classes("text-grey")
                for path, name in names.items():
                    chip = ui.chip(
                        name, on_click=lambda path=path: pick_recording(path)
                    ).props(
                        "dense clickable square color=primary"
                        + (" text-color=white" if path == sel.audio else " outline")
                    )
                    tip(chip, "Recording (T: next)")
        number = list(names).index(sel.audio) + 1 if sel.audio in names else 0
        with (
            mini_recordings,
            ui.button(f"{number}/{len(names)}", icon="audiotrack").props(
                "flat dense no-caps"
            ),
        ):
            ui.tooltip("Recording (T: next)")
            with ui.menu():
                for path, name in names.items():
                    ui.menu_item(
                        name, on_click=lambda path=path: pick_recording(path)
                    ).classes("text-primary font-medium" if path == sel.audio else "")

    def show_pickers(sel: Selection) -> None:
        """New recording chips and sheet toggle with the value set at creation (no on_change)."""
        song = sel.song
        show_recordings(sel)
        recording_label.text = next(
            (a["label"] for a in song["audio"] if a["path"] == sel.audio), ""
        )
        # a single recording is named after the song most of the time: then the title says it
        recording_label.set_visibility(
            len(song["audio"]) == 1 and recording_label.text != song["title"]
        )
        sheet_box.clear()
        if len(song["pdf"]) > 1:
            labels = {p: sheet_label(p, song["title"]) for p in song["pdf"]}
            with sheet_box:
                tabs = ui.toggle(
                    labels, value=sel.pdf, on_change=lambda e: pick_sheet(e.value)
                ).props("dense no-caps no-wrap")
                tabs.classes("sheet-tabs")
                tip(tabs, " / ".join(labels.values()))

    def loaded(sel: Selection) -> None:
        """Remember the song only once something of it loaded (S6)."""
        if state.get("last_song") != song_key(sel.song):
            state["last_song"] = song_key(sel.song)
            s.dirty = True

    async def load_audio(sel: Selection, ticket: int) -> None:
        def wanted() -> bool:
            return ticket == s.tickets["audio"]

        wave.set_source(wave_svg([0] * WAVE_W))
        wave.content = last["overlay"] = ""
        player.set_visibility(bool(sel.audio))
        no_audio.set_visibility(not sel.audio)
        if not sel.audio:
            await close_editor()
            await run.io_bound(engine.close)
            return
        loading.set_visibility(True)
        try:
            done = await run.io_bound(engine.load, DATA_DIR / sel.audio, wanted)
        except (OSError, RuntimeError, sd.PortAudioError) as error:
            if wanted():
                ui.notify(
                    f"Cannot play {Path(sel.audio).name}: {error}",
                    type="negative",
                    multi_line=True,
                )
                player.set_visibility(False)
            return
        finally:
            if wanted():
                loading.set_visibility(False)
        if not done or not wanted():
            return
        # Still the newest audio load, so no other song was opened: s.song is sel.song.
        s.audio = sel.audio
        remember(audio=sel.audio)
        loaded(sel)
        wave.set_source(wave_svg(engine.peaks))
        set_speed(s.song_state.get("speed", 1.0))
        set_semitones(s.song_state.get("semitones", 0))
        restore_trainer()
        loop = s.recording_state.get("loop")
        s.loop, s.looping = (tuple(loop), True) if loop else (None, False)
        apply_loop()
        seek(s.recording_state.get("position", 0.0))
        show_saved_loops()
        if s.editor:
            await show_editor()

    def sheet_message(icon: str, text: str) -> None:
        sheet_pages.clear()
        with sheet_pages, ui.column().classes("w-full items-center mt-16 text-grey"):
            ui.icon(icon, size="48px")
            ui.label(text)

    async def load_sheet(sel: Selection, ticket: int) -> None:
        if ticket != s.tickets["sheet"]:
            return  # another sheet was picked while this song's audio loaded
        open_pdf.set_visibility(bool(sel.pdf))
        if not sel.pdf:
            sheet_message("music_off", "No sheet music for this song")
            return
        try:
            names = await run.io_bound(page_images, DATA_DIR / sel.pdf)
        except (OSError, pdfium.PdfiumError) as error:
            if ticket == s.tickets["sheet"]:
                sheet_message("broken_image", f"Cannot show {Path(sel.pdf).name}")
                ui.notify(f"Cannot show {Path(sel.pdf).name}: {error}", type="negative")
            return
        if ticket != s.tickets["sheet"]:
            return  # overtaken by another song or sheet
        remember(pdf=sel.pdf)
        loaded(sel)
        sheet_pages.clear()
        with sheet_pages:
            for name in names:
                ui.element("img").props(f'src="/pages/{name}" draggable=false').classes(
                    "w-full shadow-md bg-white block"
                )
        if state.get("fit") == "page":
            await fit_page()

    def set_zoom(value: int, fit: str | None = None) -> None:
        """Zoom = page width in % of the view; fit "page" is kept up to date by fit_page()."""
        state["zoom"] = max(20, min(200, value))
        state["fit"] = fit
        s.dirty = True
        sheet_pages.style(f"width: {state['zoom']}%")
        zoom_label.text = f"{state['zoom']} %"
        for button, on in (
            (fit_width_button, fit is None and state["zoom"] == 100),
            (fit_page_button, fit == "page"),
        ):
            if on:
                button.classes(add="song-active")
            else:
                button.classes(remove="song-active")
        ui.run_javascript(f"dt.fit = {json.dumps(fit)}")

    async def fit_page() -> None:
        try:
            fit = await ui.run_javascript("dt.fitPage()", timeout=10)
        except TimeoutError:
            return
        if not fit:  # no sheet (yet): load_sheet fits when one comes
            set_zoom(state.get("zoom", 100), fit="page")
            return
        set_zoom(fit["zoom"], fit="page")
        ui.run_javascript(f"dt.toPage({int(fit['page'])})")

    # Layout (docs/practice-layout.md): song list, controls Full/Simple/Hidden, full screen,
    # sheet rotation.

    def set_view(**values: Any) -> None:
        view.update(values)
        s.dirty = True

    def show_layout() -> None:
        mode = "hidden" if s.fullscreen else view["controls"]
        columns = {
            "full": "minmax(360px, 460px) 1fr",
            "simple": "minmax(250px, 290px) 1fr",
        }
        height = "100vh" if s.fullscreen else "calc(100vh - 52px)"
        layout.style(
            f"grid-template-columns: {columns.get(mode, '1fr')}; height: {height}"
        )
        pane.set_visibility(mode != "hidden")
        for element in full_only:
            element.set_visibility(mode == "full")
        for element in simple_only:
            element.set_visibility(mode == "simple")
        mini_bar.set_visibility(view["controls"] == "hidden")
        header.value = not s.fullscreen
        drawer.value = view["library"] and not s.fullscreen
        sheet_toolbar.set_visibility(not s.fullscreen)
        fullscreen_exit.set_visibility(s.fullscreen)

    def set_controls(mode: str) -> None:
        if mode not in ("full", "simple", "hidden"):
            return
        set_view(controls=mode)
        show_layout()
        if (
            controls_toggle.value != mode
        ):  # its on_change comes back and changes nothing
            controls_toggle.value = mode

    def cycle_controls() -> None:
        order = ["full", "simple", "hidden"]
        set_controls(order[(order.index(view["controls"]) + 1) % len(order)])

    def set_fullscreen(on: bool) -> None:
        if on == s.fullscreen:
            return
        s.fullscreen = on
        show_layout()
        if app.native.main_window:
            app.native.main_window.toggle_fullscreen()
        else:
            ui.run_javascript(f"dt.fullscreen({json.dumps(on)})")

    def show_library_button(shown: bool) -> None:
        if shown:
            songs_button.classes(add="song-active text-primary")
        else:
            songs_button.classes(remove="song-active text-primary")

    def on_drawer(shown: bool) -> None:
        show_library_button(shown)
        if (
            not s.fullscreen
        ):  # full screen hides it without changing the remembered choice
            set_view(library=shown)

    def show_rotation() -> None:
        sheet_view.style(replace=ROTATIONS[view["rotate"]])

    async def set_rotation(degrees: int) -> None:
        set_view(rotate=degrees % 360)
        show_rotation()
        if state.get("fit") == "page":  # the frame keeps its size: no resize event
            await fit_page()

    # Loop editor (docs/loop-editor.md): drawing and gestures live in loop_editor.js; it sends
    # le_loop / le_seek / le_undo here, and gets the loop and play position back.

    async def open_editor() -> None:
        if s.editor:
            return
        if not s.audio:
            ui.notify("No recording loaded")
            return
        s.editor = True
        editor.open()
        await show_editor()

    async def show_editor() -> None:
        """Peaks to the page and the editor drawn at this recording's last view."""
        audio, data = s.audio, await run.io_bound(engine.detail_peaks)
        if not s.editor or s.audio != audio:
            return
        b64 = base64.b64encode(data).decode("ascii")
        ui.run_javascript(
            f"le.load('{b64}', {DETAIL_FRAMES / engine.rate}, {engine.duration})"
        )
        loop = json.dumps(list(s.loop) if s.loop else None)
        view = json.dumps(s.recording_state.get("editor_view"))
        ui.run_javascript(f"le.show({view}, {loop}, {json.dumps(s.looping)})")
        editor_title.text = s.song["title"]
        s.loop_history.clear()
        s.undo_base = (s.loop, s.looping)
        last["le"] = None  # the tick sends the play position again
        show_loop()

    async def close_editor() -> None:
        if not s.editor:
            return
        s.editor = False
        editor.close()
        try:
            view = await ui.run_javascript("le.hide()")
        except TimeoutError:
            return
        if view and s.audio:
            s.recording_state["editor_view"] = view
            s.dirty = True

    def editor_loop(e: events.GenericEventArguments) -> None:
        if not s.audio:
            return
        selection = event_arg(e)
        before = s.loop
        set_loop(float(selection["a"]), float(selection["b"]))
        if s.loop == before:
            show_loop()  # too short: the page shows the loop that stays
        elif not selection.get("edge"):
            seek(s.loop[0])  # a new loop plays from its start

    def editor_undo(_: Any = None) -> None:
        if not s.loop_history:
            ui.notify("Nothing to undo", timeout=1000)
            return
        s.loop, s.looping = s.undo_base = s.loop_history.pop()
        apply_loop()

    def hear_end() -> None:
        """The last 2 s of the loop and the jump back to its start: the seam that needs fixing."""
        if not (s.audio and s.loop):
            ui.notify("Set a loop first: drag over the waveform")
            return
        if not s.looping:
            s.looping = True
            apply_loop()
        seek(max(s.loop[0], s.loop[1] - 2))
        engine.play()

    def type_edge(edge: int, text: str) -> None:
        shown = clock_tenths(s.loop[edge]) if s.loop else ""
        if text.strip() in (
            "",
            shown,
        ):  # unchanged: keep the exact time, not the rounded one
            return
        seconds = parse_clock(text)
        if seconds is None or not s.audio:
            ui.notify("Type a time like 1:11.2", type="warning")
            show_loop()
            return
        loop = list(s.loop) if s.loop else [0.0, engine.duration]
        loop[edge] = seconds
        set_loop(*loop)
        show_loop()
        ui.run_javascript("document.activeElement.blur()")

    def set_setting(key: str, value: Any) -> None:
        settings[key] = value
        s.dirty = True
        ui.run_javascript(f"Object.assign(dt.settings, {json.dumps({key: value})})")

    def save_position() -> None:
        if s.audio:
            s.recording_state["position"] = round(engine.position / engine.rate, 2)
            s.dirty = True

    def filtered_songs() -> list[Song]:
        text = (search.value or "").casefold()
        return [
            x for x in s.songs if text in f"{x['title']} {x['collection']}".casefold()
        ]

    # ---------------------------------------------------------------- views

    def show_speed() -> None:
        percent = round(engine.speed * 100)
        speed_label.text = mini_speed.text = editor_speed.text = f"{percent} %"
        speed_slider.value = percent
        for preset, chip in preset_chips.items():
            if round(preset * 100) == percent:
                chip.props(remove="outline")
            else:
                chip.props("outline")
        if s.audio:
            real = engine.duration / engine.speed
            speed_hint.text = f"Song takes {clock(real)} at this tempo"

    def show_loop() -> None:
        on = bool(s.loop and s.looping)
        for button in (loop_button, mini_loop):
            button.props(f"color={'accent' if on else 'grey'}")
        loop_tip.text = mini_loop_tip.text = "Loop off (R)" if on else "Loop on (R)"
        loop_a.text = (
            clock(s.loop[0]) + f".{int(s.loop[0] * 10) % 10}" if s.loop else "–"
        )
        loop_b.text = (
            clock(s.loop[1]) + f".{int(s.loop[1] * 10) % 10}" if s.loop else "–"
        )
        loop_switch.value = on
        loop_switch.set_enabled(bool(s.loop))
        show_trainer()
        if s.editor:
            editor_a.value = clock_tenths(s.loop[0]) if s.loop else ""
            editor_b.value = clock_tenths(s.loop[1]) if s.loop else ""
            undo_button.set_enabled(bool(s.loop_history))
            loop = json.dumps(list(s.loop) if s.loop else None)
            ui.run_javascript(f"le.setLoop({loop}, {json.dumps(on)})")

    def show_saved_loops() -> None:
        saved_loops.clear()
        with saved_loops:
            loops = s.recording_state.get("loops", [])
            if not loops:
                ui.label("No saved loops yet").classes("text-caption text-grey")
            for saved in loops:
                ui.chip(
                    f"{saved['name']}  {clock(saved['a'])}–{clock(saved['b'])}",
                    icon="repeat",
                    removable=True,
                    on_click=lambda saved=saved: use_saved_loop(saved),
                    on_value_change=lambda e, saved=saved: delete_saved_loop(saved),
                ).props("outline color=accent")

    def show_trainer() -> None:
        t = s.trainer
        if not t["on"]:
            trainer_status.text = "Raise the tempo step by step while the loop repeats."
        elif not (s.loop and s.looping):
            trainer_status.text = "Set a loop to start."
        elif engine.speed >= t["target"] - 1e-6:
            trainer_status.text = f"Target {round(t['target'] * 100)} % reached."
        else:
            trainer_status.text = (
                f"Repeat {engine.repeats + 1} of {t['every']} at {round(engine.speed * 100)} %, "
                f"then {round(min(engine.speed + t['step'], t['target']) * 100)} %"
            )

    def show_library() -> None:
        many_collections = len({x["collection"] for x in s.songs}) > 1
        library.clear()
        shown = filtered_songs()
        with library:
            if not shown:
                ui.label("No songs match").classes("p-4 text-grey")
            for song in shown:
                current = song is s.song
                with (
                    ui.item(on_click=lambda song=song: open_song(song))
                    .props("clickable")
                    .classes(
                        "rounded-borders"
                        + (" song-active text-primary" if current else "")
                    )
                ):
                    with ui.item_section():
                        ui.item_label(song["title"]).classes(
                            "font-medium" if current else ""
                        )
                        if many_collections:
                            ui.item_label(song["collection"]).props("caption")
                    with (
                        ui.item_section().props("side"),
                        ui.row().classes("gap-1 items-center"),
                    ):
                        if len(song["audio"]) > 1:
                            ui.badge(str(len(song["audio"]))).props("outline").tooltip(
                                "recordings"
                            )
                        if song["pdf"]:
                            ui.icon("description", size="18px").classes("text-grey")
                        if not song["audio"]:
                            ui.icon("volume_off", size="18px").classes(
                                "text-grey"
                            ).tooltip("no recording")

    def wave_overlay() -> str:
        if not s.audio or not engine.duration:
            return ""
        x = lambda seconds: seconds / engine.duration * WAVE_W
        parts = [
            (
                f'<rect x="0" y="0" width="{x(engine.position / engine.rate):.1f}" '
                f'height="{WAVE_H}" fill="#4f5bd5" fill-opacity="0.18"/>'
            )
        ]
        region = (
            sorted((s.drag_from, s.drag_to))
            if s.drag_from is not None and s.drag_to is not None
            else s.loop
        )
        if region:
            a, b = x(region[0]), x(region[1])
            opacity = 0.3 if s.looping or s.drag_to is not None else 0.12
            parts.append(
                f'<rect x="{a:.1f}" y="0" width="{b - a:.1f}" height="{WAVE_H}" '
                f'fill="{LOOP_COLOR}" fill-opacity="{opacity}"/>'
                f'<line x1="{a:.1f}" x2="{a:.1f}" y1="0" y2="{WAVE_H}" stroke="{LOOP_COLOR}" stroke-width="2"/>'
                f'<line x1="{b:.1f}" x2="{b:.1f}" y1="0" y2="{WAVE_H}" stroke="{LOOP_COLOR}" stroke-width="2"/>'
                f'<text x="{a + 4:.1f}" y="14" font-size="13" font-weight="bold" fill="{LOOP_COLOR}">A</text>'
                f'<text x="{b - 13:.1f}" y="14" font-size="13" font-weight="bold" fill="{LOOP_COLOR}">B</text>'
            )
        head = x(engine.position / engine.rate)
        parts.append(
            f'<line x1="{head:.1f}" x2="{head:.1f}" y1="0" y2="{WAVE_H}" stroke="#4f5bd5" stroke-width="2.5"/>'
        )
        return "".join(parts)

    def on_wave_mouse(e: events.MouseEventArguments) -> None:
        if not s.audio:
            return
        seconds = min(max(e.image_x, 0), WAVE_W) / WAVE_W * engine.duration
        match e.type:
            case "mousedown":
                s.drag_from, s.drag_to = seconds, None
            case "mousemove" if s.drag_from is not None and e.buttons & 1:
                if abs(seconds - s.drag_from) / engine.duration * WAVE_W > 4:
                    s.drag_to = seconds
            case "mouseup" if s.drag_from is not None:
                if s.drag_to is None:
                    seek(seconds)
                else:
                    set_loop(s.drag_from, seconds)
                    seek(s.loop[0]) if s.loop else None
                s.drag_from = s.drag_to = None
            case "mouseleave":
                s.drag_from = s.drag_to = None

    # ---------------------------------------------------------------- timer

    last = {"overlay": "", "time": "", "playing": None, "save": 0, "le": None}

    def tick() -> None:
        if owner["client"] != me:
            taken_over()
            return
        if s.audio:
            t = s.trainer
            if (
                t["on"]
                and s.loop
                and s.looping
                and engine.repeats >= t["every"]
                and engine.speed < t["target"] - 1e-6
            ):
                engine.reset_repeats()
                set_speed(min(engine.speed + t["step"], t["target"]))
                ui.notify(
                    f"Tempo {round(engine.speed * 100)} %", position="top", timeout=1500
                )
            if t["on"]:
                show_trainer()
            overlay = wave_overlay()
            if overlay != last["overlay"]:
                wave.content = last["overlay"] = overlay
            now = f"{clock(engine.position / engine.rate)} / {clock(engine.duration)}"
            if now != last["time"]:
                time_label.text = mini_time.text = last["time"] = now
            if s.editor:  # the page moves the playhead between these updates
                now = (round(engine.position / engine.rate, 3), engine.playing)
                if engine.playing or now != last["le"]:
                    last["le"] = now
                    ui.run_javascript(
                        f"le.setPlay({now[0]}, {json.dumps(now[1])}, {engine.speed})"
                    )
            if engine.playing != last["playing"]:
                last["playing"] = engine.playing
                for button in (play_button, mini_play, editor_play):
                    button.props(f"icon={'pause' if engine.playing else 'play_arrow'}")
                play_tip.text = mini_play_tip.text = editor_play_tip.text = (
                    "Pause (Space)" if engine.playing else "Play (Space)"
                )
        last["save"] += 1
        if last["save"] >= 20:  # every 2 s
            last["save"] = 0
            save_position()
            if s.dirty:
                save_state(state)
                s.dirty = False

    def taken_over() -> None:
        ticker.cancel()
        s.audio = ""  # nothing here touches the engine any more
        with ui.dialog().props("persistent") as dialog, ui.card():
            ui.label("The player was opened in another tab or window.")
            ui.label("Reload this page to use it here.").classes("text-grey")
        dialog.open()

    # ---------------------------------------------------------------- keys

    async def on_key(e: events.KeyEventArguments) -> None:
        if (
            not e.action.keydown
            or e.modifiers.ctrl
            or e.modifiers.alt
            or e.modifiers.meta
            or owner["client"] != me
        ):
            return
        # ↑/↓, PgUp/PgDn, Home/End scroll the sheet in the page itself (SHEET_KEYS).
        key = e.key.name
        repeatable = {"ArrowLeft", "ArrowRight", "+", "=", "-", ",", "."}
        if e.action.repeat and key not in repeatable:
            return
        match key.lower() if len(key) == 1 else key:
            case " " if e.modifiers.shift and s.editor:
                hear_end()
            case " " | "k":
                toggle_play()
            case "ArrowLeft":
                tempo_step(-1)
            case "ArrowRight":
                tempo_step(1)
            case "+" | "=":
                set_zoom(state.get("zoom", 100) + 10)
            case "-":
                set_zoom(state.get("zoom", 100) - 10)
            case "w":
                set_zoom(100)
            case "h":
                await fit_page()
            case ",":
                skip(-5)
            case ".":
                skip(5)
            case "j":
                skip(-10)
            case "l":
                skip(10)
            case "0":
                to_start()
            case digit if len(digit) == 1 and digit.isdigit() and s.audio:
                seek(engine.duration * int(digit) / 10)
            case "q":
                drawer.toggle()
            case "v":
                cycle_controls()
            case "f":
                set_fullscreen(not s.fullscreen)
            case "Escape" if s.editor:
                await close_editor()
            case "Escape":
                set_fullscreen(False)
            case "e":
                await (close_editor() if s.editor else open_editor())
            case "o":
                await set_rotation(view["rotate"] + 90)
            case "t":
                await step_recording(-1 if e.modifiers.shift else 1)
            case "a":
                set_a()
            case "b":
                set_b()
            case "r":
                toggle_loop()
            case "c":
                clear_loop()
            case "s":
                save_loop_dialog()
            case "n":
                await step_song(1)
            case "p":
                await step_song(-1)
            case "m":
                toggle_mute()
            case "/":
                drawer.show()
                search.run_method("focus")
            case "?":
                help_dialog.open()

    ui.keyboard(on_key=on_key)

    # ---------------------------------------------------------------- layout

    with ui.dialog() as help_dialog, ui.card().classes("max-w-none"):
        ui.label("Keyboard shortcuts").classes("text-h6")
        # two groups side by side, so the list fits a 720 px high screen
        with ui.row().classes("gap-10 no-wrap items-start"):
            for group, shortcuts in SHORTCUTS.items():
                with ui.column().classes("gap-1"):
                    ui.label(group).classes("text-subtitle2 text-primary")
                    with ui.grid(columns="auto 1fr").classes("gap-x-5 gap-y-1"):
                        for keys, action in shortcuts:
                            ui.label(keys).classes("font-mono font-medium")
                            ui.label(action)
        ui.button("Close", on_click=help_dialog.close).props("flat").classes("self-end")

    with ui.dialog() as settings_dialog, ui.card().classes("min-w-[380px] gap-3"):
        ui.label("Settings").classes("text-h6")
        for key, label, options in (
            ("scroll_step", "↑ / ↓ scroll", {v: f"{v} %" for v in (10, 20, 33, 50)}),
            (
                "page_mode",
                "PgUp / PgDn",
                {"screen": "a screen", "page": "to next page"},
            ),
            ("tempo_step", "← / → tempo step", {v: f"{v} %" for v in (1, 2, 5, 10)}),
        ):
            with ui.column().classes("gap-1"):
                ui.label(label).classes("text-caption text-grey")
                ui.toggle(
                    options,
                    value=settings[key],
                    on_change=lambda e, key=key: set_setting(key, e.value),
                ).props("dense no-caps")
        ui.switch(
            "Smooth scrolling",
            value=settings["smooth"],
            on_change=lambda e: set_setting("smooth", e.value),
        )
        ui.label(
            "↑ / ↓ scroll a share of the visible sheet; a screen keeps the last line."
        ).classes("text-caption text-grey")
        ui.button("Close", on_click=settings_dialog.close).props("flat").classes(
            "self-end"
        )

    # Loop editor: the whole window, opened with E (docs/loop-editor.md)
    with (
        ui.dialog().props(
            "maximized persistent transition-show=none transition-hide=none"
        ) as editor,
        ui.card().classes("w-full h-full p-0 gap-0 no-wrap"),
    ):
        with ui.row().classes(
            "le-header w-full items-center gap-2 px-4 py-1 min-h-[52px] no-wrap"
        ):
            ui.label("Loop").classes("text-subtitle1 font-bold text-primary")
            editor_title = ui.label("").classes("text-h6 truncate")
            editor_recordings = ui.element("div").classes(
                "min-w-0"
            )  # show_recordings()
            ui.space()
            undo_button = ui.button("Undo", icon="undo", on_click=editor_undo).props(
                "flat no-caps"
            )
            tip(undo_button, "Back to the previous loop (Ctrl+Z)")
            done_button = ui.button("Done", on_click=close_editor).props(
                "unelevated no-caps"
            )
            tip(done_button, "Back to the player (E, Esc)")
        with ui.row().classes("w-full items-center gap-2 px-4 py-2 no-wrap"):
            ui.button(
                icon="zoom_out", on_click=lambda: ui.run_javascript("le.zoomBy(0.5)")
            ).props("flat round dense").tooltip("Zoom out (−)")
            ui.label("1×").classes("le-zoom font-mono w-12 text-center")
            ui.button(
                icon="zoom_in", on_click=lambda: ui.run_javascript("le.zoomBy(2)")
            ).props("flat round dense").tooltip("Zoom in (+), also pinch")
            ui.button(
                "Whole song", on_click=lambda: ui.run_javascript("le.wholeSong()")
            ).props("outline no-caps dense").classes("px-2")
            ui.button(
                "Zoom to loop", on_click=lambda: ui.run_javascript("le.zoomToLoop()")
            ).props("outline no-caps dense").classes("px-2")
            ui.separator().props("vertical").classes("mx-2")
            editor_play = ui.button(icon="play_arrow", on_click=toggle_play).props(
                "round unelevated dense"
            )
            editor_play_tip = tip(editor_play, "Play (Space)")
            hear_button = (
                ui.button("Hear end", icon="skip_next", on_click=hear_end)
                .props("outline no-caps dense")
                .classes("px-2")
            )
            tip(
                hear_button,
                "The last 2 s of the loop and the jump back to its start (Shift+Space)",
            )
            ui.space()
            ui.label("Tempo").classes("text-caption text-grey")
            ui.button(icon="remove", on_click=lambda: tempo_step(-1)).props(
                "flat round dense"
            ).tooltip("Slower (←)")
            editor_speed = ui.label("100 %").classes("font-bold w-12 text-center")
            ui.button(icon="add", on_click=lambda: tempo_step(1)).props(
                "flat round dense"
            ).tooltip("Faster (→)")
        with ui.column().classes("w-full grow min-h-0 gap-1 px-4 no-wrap"):
            ui.element("canvas").classes("le-overview w-full h-12 block").style(
                "touch-action: none; cursor: grab"
            ).tooltip("The whole song: drag the box to scroll")
            ui.element("canvas").classes("le-ruler w-full h-6 block").style(
                "touch-action: none; cursor: pointer"
            ).tooltip("Click: play from here · drag down / up: zoom in / out")
            with ui.element("div").classes("w-full grow min-h-0 relative"):
                ui.element("canvas").classes(
                    "le-main absolute inset-0 w-full h-full block"
                ).style("touch-action: none; cursor: crosshair")
        with ui.row().classes("w-full items-center gap-1 px-4 py-1 no-wrap"):
            edge_fields = []
            for edge, name in ((0, "Start"), (1, "End")):
                if edge == 1:
                    ui.space()
                ui.label(name).classes("text-caption text-grey")
                ui.button(
                    icon="chevron_left", on_click=lambda edge=edge: nudge(edge, -0.1)
                ).props("flat dense round size=sm").tooltip("0.1 s earlier")
                time_input = (
                    ui.input()
                    .props("dense outlined input-class=text-center")
                    .classes("w-24 font-mono")
                )
                time_input.on(
                    "keydown.enter",
                    lambda e, edge=edge: type_edge(edge, e.sender.value),
                )
                time_input.on(
                    "blur", lambda e, edge=edge: type_edge(edge, e.sender.value)
                )
                edge_fields.append(time_input)
                ui.button(
                    icon="chevron_right", on_click=lambda edge=edge: nudge(edge, 0.1)
                ).props("flat dense round size=sm").tooltip("0.1 s later")
            editor_a, editor_b = edge_fields
        ui.label("").classes("le-hint text-caption text-grey px-4 pb-2")

    with ui.header(elevated=False).classes(
        "app-header items-center gap-2 px-3 py-1 no-wrap"
    ) as header:
        # Labelled, not ☰: that reads as the app menu (docs/practice-layout.md#song-list-button)
        songs_button = ui.button(
            "Songs", icon="queue_music", on_click=lambda: drawer.toggle()
        ).props("flat no-caps")
        tip(songs_button, "Song list (Q)")
        ui.label("Downtempo").classes("text-subtitle1 font-bold text-primary gt-md")
        ui.separator().props("vertical").classes("mx-1 gt-md")
        title = ui.label("").classes("text-h6 truncate min-w-0")
        ui.space()
        # The basics while the controls are hidden (sheet only)
        with ui.row().classes("items-center gap-1 no-wrap") as mini_bar:
            mini_play = ui.button(icon="play_arrow", on_click=toggle_play).props(
                "round unelevated dense"
            )
            mini_play_tip = tip(mini_play, "Play (Space)")
            mini_time = ui.label("").classes("font-mono text-caption mx-1")
            ui.button(icon="remove", on_click=lambda: tempo_step(-1)).props(
                "flat round dense"
            ).tooltip("Slower (←)")
            mini_speed = ui.label("100 %").classes("font-bold w-12 text-center")
            ui.button(icon="add", on_click=lambda: tempo_step(1)).props(
                "flat round dense"
            ).tooltip("Faster (→)")
            mini_loop = ui.button(icon="repeat", on_click=toggle_loop).props(
                "flat round dense color=grey"
            )
            mini_loop_tip = tip(mini_loop, "Loop on (R)")
            ui.button(icon="open_in_full", on_click=open_editor).props(
                "flat round dense"
            ).tooltip("Loop editor (E)")
            mini_recordings = ui.element("div")  # show_recordings()
            ui.separator().props("vertical").classes("mx-1")
        controls_toggle = (
            ui.toggle(
                {"full": "Full", "simple": "Simple", "hidden": "Sheet"},
                value=view["controls"],
                on_change=lambda e: set_controls(e.value),
            )
            .props("dense no-caps rounded unelevated toggle-color=primary")
            .classes("border")
        )
        tip(controls_toggle, "Controls: full / simple / sheet only (V)")
        ui.button(icon="settings", on_click=settings_dialog.open).props(
            "flat round"
        ).tooltip("Settings")
        ui.button(icon="keyboard", on_click=help_dialog.open).props(
            "flat round"
        ).tooltip("Keyboard shortcuts (?)")

        def flip_dark() -> None:
            dark.value = not dark.value
            state["dark"] = dark.value
            s.dirty = True

        ui.button(icon="dark_mode", on_click=flip_dark).props("flat round").tooltip(
            "Dark / light"
        )

    with (
        ui.left_drawer(value=view["library"], bordered=True)
        .props("width=290")
        .classes("p-2 gap-2") as drawer
    ):
        drawer.on_value_change(lambda e: on_drawer(bool(e.value)))
        search = (
            ui.input(
                placeholder="Search songs  ( / )", on_change=lambda: show_library()
            )
            .props("dense outlined clearable")
            .classes("w-full")
        )
        library = ui.list().props("dense").classes("w-full")

    if not s.songs:
        with ui.column().classes("w-full items-center mt-24 gap-2"):
            ui.icon("library_music", size="64px").classes("text-grey")
            ui.label("No songs yet").classes("text-h6")
            ui.label("Download and build the song list, then restart the player:")
            ui.code("uv run downtempo download\nuv run downtempo catalog").classes(
                "w-96"
            )
        return

    full_only = []  # hidden in Simple controls
    simple_only = []  # shown only in Simple controls
    with (
        ui.element("div")
        .classes("w-full")
        .style("display: grid; height: calc(100vh - 52px)") as layout
    ):
        # Left: player
        with ui.column().classes(
            "p-4 gap-3 overflow-y-auto pane-border no-wrap"
        ) as pane:
            with ui.row().classes("w-full items-center gap-2"):
                recording_box = ui.element("div").classes("grow")  # show_pickers()
                recording_label = ui.label("").classes("text-subtitle2 text-grey")
                loading = ui.spinner(size="sm")
                loading.set_visibility(False)

            no_audio = ui.label("This song has no recording.").classes("text-grey")
            no_audio.set_visibility(False)

            with ui.column().classes("w-full gap-3") as player:
                # Waveform + transport
                with ui.card().classes("w-full p-3 gap-2"):
                    wave = ui.interactive_image(
                        wave_svg([0] * WAVE_W),
                        events=["mousedown", "mousemove", "mouseup", "mouseleave"],
                        on_mouse=on_wave_mouse,
                    ).classes("w-full cursor-pointer rounded")
                    wave.tooltip("Click: play from here · Drag: set a loop")
                    with ui.row().classes("w-full items-center justify-between"):
                        time_label = ui.label("0:00 / 0:00").classes("font-mono")
                        speed_hint = ui.label("").classes("text-caption text-grey")
                    with ui.row().classes("w-full items-center justify-center gap-1"):
                        ui.button(icon="skip_previous", on_click=to_start).props(
                            "flat round"
                        ).tooltip("To start (0)")
                        full_only.append(
                            ui.button(icon="replay_5", on_click=lambda: skip(-5))
                            .props("flat round")
                            .tooltip("Back 5 s ( , )")
                        )
                        play_button = ui.button(
                            icon="play_arrow", on_click=toggle_play
                        ).props("round size=lg unelevated")
                        play_tip = tip(play_button, "Play (Space)")
                        full_only.append(
                            ui.button(icon="forward_5", on_click=lambda: skip(5))
                            .props("flat round")
                            .tooltip("Forward 5 s ( . )")
                        )
                        loop_button = ui.button(
                            icon="repeat", on_click=toggle_loop
                        ).props("flat round color=grey")
                        loop_tip = tip(loop_button, "Loop on (R)")
                        # Simple has no loop card: the editor sits next to the loop button
                        simple_only.append(
                            ui.button("Loop", icon="open_in_full", on_click=open_editor)
                            .props("flat dense no-caps")
                            .tooltip("Loop editor: zoom in, set the loop exactly (E)")
                        )

                # Tempo
                with ui.card().classes("w-full p-3 gap-1"):
                    with ui.row().classes("w-full items-center gap-1 no-wrap"):
                        ui.label("Tempo").classes("text-subtitle2")
                        ui.space()
                        ui.button(icon="remove", on_click=lambda: tempo_step(-1)).props(
                            "flat round dense"
                        ).tooltip("Slower (←)")
                        speed_label = ui.label("100 %").classes(
                            "text-h5 font-bold w-20 text-center"
                        )
                        ui.button(icon="add", on_click=lambda: tempo_step(1)).props(
                            "flat round dense"
                        ).tooltip("Faster (→)")
                    speed_slider = ui.slider(
                        min=round(SPEEDS[0] * 100),
                        max=round(SPEEDS[1] * 100),
                        step=1,
                        value=100,
                        on_change=lambda e: (
                            set_speed(e.value / 100)
                            if round(engine.speed * 100) != e.value
                            else None
                        ),
                    ).props(":markers=5")
                    with ui.row().classes("w-full gap-1 justify-between") as presets:
                        preset_chips = {
                            preset: ui.chip(
                                f"{round(preset * 100)}",
                                on_click=lambda preset=preset: set_speed(preset),
                            ).props("outline dense clickable")
                            for preset in PRESETS
                        }

                    with (
                        ui.expansion("Step-up trainer", icon="trending_up")
                        .classes("w-full")
                        .props("dense") as trainer_box
                    ):
                        ui.switch(
                            "Raise tempo while looping",
                            on_change=lambda e: toggle_trainer(e.value),
                        )
                        trainer_inputs = {}
                        with ui.row().classes("items-center gap-2 no-wrap"):
                            for key, options, after in (
                                ("step", {0.05: "+5 %", 0.1: "+10 %"}, "every"),
                                (
                                    "every",
                                    {n: str(n) for n in range(1, 6)},
                                    "repeats, up to",
                                ),
                                (
                                    "target",
                                    {
                                        round(v / 100, 2): f"{v} %"
                                        for v in range(60, 135, 5)
                                    },
                                    "",
                                ),
                            ):
                                trainer_inputs[key] = (
                                    ui.select(
                                        options,
                                        value=TRAINER[key],
                                        on_change=lambda e, key=key: set_trainer(
                                            key, e.value
                                        ),
                                    )
                                    .props("dense outlined options-dense")
                                    .on("popup-hide", js_handler=BLUR_SELECT)
                                )
                                if after:
                                    ui.label(after)
                        trainer_status = ui.label("").classes("text-caption text-grey")

                # Loop
                with ui.card().classes("w-full p-3 gap-2") as loop_card:
                    with ui.row().classes("w-full items-center"):
                        ui.label("Loop").classes("text-subtitle2")
                        loop_switch = ui.switch(
                            on_change=lambda e: (
                                toggle_loop()
                                if e.value != bool(s.loop and s.looping)
                                else None
                            )
                        ).props("color=accent dense")
                        ui.space()
                        edit_button = ui.button(
                            "Edit", icon="open_in_full", on_click=open_editor
                        ).props("flat dense no-caps")
                        tip(
                            edit_button,
                            "Loop editor: zoom in, set the loop exactly (E)",
                        )
                    loop_times = []
                    with ui.grid(columns=2).classes("w-full gap-2"):
                        for edge in (0, 1):
                            with ui.column().classes(
                                "items-center gap-0 py-1 rounded-borders loop-edge"
                            ):
                                ui.label("Start" if edge == 0 else "End").classes(
                                    "text-caption text-grey"
                                )
                                with ui.row().classes("items-center gap-0 no-wrap"):
                                    ui.button(
                                        icon="chevron_left",
                                        on_click=lambda edge=edge: nudge(edge, -0.1),
                                    ).props("flat dense round size=sm").tooltip(
                                        "0.1 s earlier"
                                    )
                                    loop_times.append(
                                        ui.label("–").classes(
                                            "font-mono text-subtitle1 w-16 text-center"
                                        )
                                    )
                                    ui.button(
                                        icon="chevron_right",
                                        on_click=lambda edge=edge: nudge(edge, 0.1),
                                    ).props("flat dense round size=sm").tooltip(
                                        "0.1 s later"
                                    )
                    loop_a, loop_b = loop_times
                    with ui.row().classes("w-full items-center gap-1"):
                        ui.button(
                            "Save loop", icon="bookmark_add", on_click=save_loop_dialog
                        ).props("dense flat no-caps").tooltip("Save loop (S)")
                        ui.button("Clear", icon="close", on_click=clear_loop).props(
                            "dense flat no-caps"
                        ).tooltip("Clear loop (C)")
                    with ui.row().classes("items-center gap-2"):
                        ui.label("Pause between repeats").classes("text-caption")
                        ui.toggle(
                            {0.0: "none", 1.0: "1 s", 2.0: "2 s", 4.0: "4 s"},
                            value=state.get("loop_gap", 0.0),
                            on_change=lambda e: set_gap(e.value),
                        ).props("dense no-caps toggle-color=accent")
                    saved_loops = ui.row().classes("w-full gap-1")

                # Pitch + volume
                with ui.card().classes("w-full p-3 gap-1") as pitch_card:
                    with ui.row().classes("w-full items-center gap-1 no-wrap"):
                        ui.label("Pitch").classes("text-subtitle2 w-14")
                        ui.button(
                            icon="remove",
                            on_click=lambda: set_semitones(engine.semitones - 1),
                        ).props("flat round dense").tooltip("Down a semitone")
                        pitch_label = ui.label("0").classes("font-mono w-8 text-center")
                        ui.button(
                            icon="add",
                            on_click=lambda: set_semitones(engine.semitones + 1),
                        ).props("flat round dense").tooltip("Up a semitone")
                        ui.label("semitones").classes("text-caption text-grey")
                        ui.space()
                        ui.button("Reset", on_click=lambda: set_semitones(0)).props(
                            "flat dense no-caps"
                        )
                    with ui.row().classes("w-full items-center gap-1 no-wrap"):
                        mute_button = (
                            ui.button(icon="volume_up", on_click=toggle_mute)
                            .props("flat round dense")
                            .tooltip("Mute (M)")
                        )
                        ui.slider(
                            min=0,
                            max=100,
                            value=state.get("volume", 80),
                            on_change=lambda e: set_volume(e.value),
                        ).classes("grow")

        full_only += [
            speed_hint,
            speed_slider,
            presets,
            trainer_box,
            loop_card,
            pitch_card,
        ]

        # Right: sheet music
        with ui.column().classes("gap-0 h-full overflow-hidden min-w-0"):
            with ui.row().classes(
                "w-full items-center gap-2 px-3 py-1 min-h-[44px] no-wrap"
            ) as sheet_toolbar:
                # long sheet names get "…" (full name in the tooltip); the buttons keep their room
                sheet_box = ui.element("div").classes("min-w-0 flex")
                ui.space()
                ui.button(
                    icon="zoom_out",
                    on_click=lambda: set_zoom(state.get("zoom", 100) - 10),
                ).props("flat round dense").tooltip("Smaller (−)")
                zoom_label = ui.label("100 %").classes(
                    "text-caption w-12 text-center whitespace-nowrap"
                )
                ui.button(
                    icon="zoom_in",
                    on_click=lambda: set_zoom(state.get("zoom", 100) + 10),
                ).props("flat round dense").tooltip("Larger (+)")
                fit_width_button = ui.button(
                    icon="expand", on_click=lambda: set_zoom(100)
                ).props("flat round dense")
                fit_width_button.classes("turn-90").tooltip("Fit width (W)")
                fit_page_button = ui.button(icon="expand", on_click=fit_page).props(
                    "flat round dense"
                )
                fit_page_button.tooltip("Fit page: the whole page in view (H)")
                ui.button(
                    icon="fullscreen", on_click=lambda: set_fullscreen(True)
                ).props("flat round dense").tooltip("Full screen (F)")
                # set once (how the laptop stands) or rarely: kept out of the way
                with ui.button(icon="more_vert").props("flat round dense"):
                    ui.tooltip("Rotate, open the PDF")
                    with ui.menu():
                        ui.menu_item(
                            "Rotate right (O)",
                            on_click=lambda: set_rotation(view["rotate"] + 90),
                            auto_close=False,
                        )
                        ui.menu_item(
                            "Rotate left",
                            on_click=lambda: set_rotation(view["rotate"] - 90),
                            auto_close=False,
                        )
                        ui.separator()
                        open_pdf = ui.menu_item(
                            "Open in PDF viewer",
                            on_click=lambda: webbrowser.open(
                                (DATA_DIR / s.selection.pdf).as_uri()
                            ),
                        )
            with (
                ui.element("div").classes("w-full grow sheet-frame sheet-bg"),
            ):
                fullscreen_exit = ui.button(
                    icon="fullscreen_exit", on_click=lambda: set_fullscreen(False)
                ).props("round unelevated dense color=grey-8")
                fullscreen_exit.classes("fullscreen-exit").tooltip(
                    "Leave full screen (Esc, F)"
                )
                with ui.element("div").classes("sheet-view p-4") as sheet_view:
                    sheet_pages = ui.column().classes("gap-4 mx-auto")

    engine.volume = (state.get("volume", 80) / 100) ** 2
    engine.loop_gap = state.get("loop_gap", 0.0)
    set_zoom(state.get("zoom", 100), state.get("fit"))
    set_controls(view["controls"])
    show_library_button(view["library"])
    show_rotation()
    show_library()
    show_trainer()
    ui.on("refit", fit_page, throttle=0.3)
    ui.on("le_loop", editor_loop)
    ui.on("le_seek", lambda e: seek(float(event_arg(e))))
    ui.on("le_undo", editor_undo)
    ui.on("fullscreen_left", lambda: set_fullscreen(False))
    ticker = ui.timer(0.1, tick)
    by_key = {song_key(x): x for x in s.songs}
    first = by_key.get(state.get("last_song", ""), s.songs[0])

    async def start() -> None:
        ui.run_javascript("dt.watch()")
        await open_song(first)

    ui.timer(0, start, once=True)


def shutdown() -> None:
    engine.close()
    save_state(state)


def main() -> None:
    app.on_shutdown(shutdown)
    if "--browser" in sys.argv:  # a normal browser tab instead of the native window
        ui.run(root, title="Downtempo", reload=False, show=False, port=8765)
    else:
        ui.run(
            root, title="Downtempo", reload=False, native=True, window_size=(1400, 900)
        )


if __name__ in {"__main__", "__mp_main__"}:
    main()
