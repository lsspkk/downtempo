"""Background work for the page, one job at a time (docs/blocks.md#decided-from-the-docs-t54-2026-10-11).

A job is plain blocking core work, `work(report, cancel)`. It runs in a worker thread; `report`
only queues events, and a timer on the page hands them to the listeners and then calls `done` with
the result. So widgets are only touched on the UI side, never from the worker.
"""

import inspect
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from queue import Empty, SimpleQueue
from typing import Any

from nicegui import background_tasks, run, ui

from downtempo.errors import Cancelled, UserError
from downtempo.events import Event, Failed, Report

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Finished:
    """Queued after the job's last event: `result` is None when it failed or was cancelled."""

    result: Any
    done: Callable[[Any], Any]


class Jobs:
    def __init__(self) -> None:
        self.queue: SimpleQueue[Event | Finished] = SimpleQueue()
        self.cancel = threading.Event()
        self.name = ""  # what is running, "" when idle
        self.error: UserError | None = None  # why the last job failed (dialogs show it)
        self.listeners: list[Callable[[Event], None]] = []
        self.idle_listeners: list[
            Callable[[], None]
        ] = []  # after each job, before `done`
        ui.timer(0.1, self.drain)

    @property
    def running(self) -> bool:
        return bool(self.name)

    def on_event(self, listener: Callable[[Event], None]) -> None:
        self.listeners.append(listener)

    def on_idle(self, listener: Callable[[], None]) -> None:
        self.idle_listeners.append(listener)

    def start(
        self,
        name: str,
        work: Callable[[Report, threading.Event], Any],
        done: Callable[[Any], Any] = lambda result: None,
    ) -> bool:
        """Start `work` unless another job runs (then say so and return False)."""
        if self.running:
            ui.notify(f"Wait until “{self.name}” has finished.")
            return False
        self.name, self.error = name, None
        self.cancel = threading.Event()
        background_tasks.create(self.run(work, done, self.cancel))
        return True

    def stop(self) -> None:
        """Ask the job to stop; it ends at its next check (finished files are kept)."""
        self.cancel.set()

    async def run(
        self,
        work: Callable[[Report, threading.Event], Any],
        done: Callable[[Any], Any],
        cancel: threading.Event,
    ) -> None:
        result = None
        try:
            result = await run.io_bound(work, self.queue.put, cancel)
        except UserError as error:
            self.queue.put(Failed("", error))
        except Cancelled:
            pass
        except Exception as error:
            log.exception("Job %s failed", self.name)
            self.queue.put(
                Failed(
                    "",
                    UserError(
                        f"Something went wrong: {error}", "Details are in the terminal."
                    ),
                )
            )
        self.queue.put(Finished(result, done))

    async def drain(self) -> None:
        while True:
            try:
                item = self.queue.get_nowait()
            except Empty:
                return
            if isinstance(item, Finished):
                self.name = ""
                for listener in self.idle_listeners:
                    listener()
                if inspect.isawaitable(answer := item.done(item.result)):
                    await answer
                continue
            if isinstance(item, Failed) and not item.source:
                self.error = item.error
            for listener in self.listeners:
                listener(item)
