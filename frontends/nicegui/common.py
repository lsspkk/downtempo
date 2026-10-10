"""Small helpers every part of the player page uses: tooltips, times, page events, shared CSS."""

from typing import Any

from nicegui import events, ui

LOOP_COLOR = "#f59e0b"
# The shared look; each part adds its own CSS next to its code.
CSS = """
.song-active { background: rgba(79, 91, 213, 0.12); }
.app-header { background: white; color: #1d1d1f; border-bottom: 1px solid #e0e0e6; }
.body--dark .app-header { background: #1d1d1f; color: white; border-color: #333; }
.pane-border { border-right: 1px solid rgba(128, 128, 128, 0.25); }
"""
# Buttons and sliders keep focus after a click, and NiceGUI's keyboard ignores keys on a focused
# button; blurring after a mouse click keeps the shortcuts working. Tab focus is left alone.
BLUR_AFTER_CLICK = """<script>
document.addEventListener('pointerup', () => setTimeout(() => {
  const el = document.activeElement;
  if (el && !['INPUT', 'TEXTAREA'].includes(el.tagName)) el.blur();
}, 0));
</script>"""
# A select refocuses itself when its menu closes, which would swallow the next shortcut key.
BLUR_SELECT = "() => setTimeout(() => document.activeElement.blur(), 50)"


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
