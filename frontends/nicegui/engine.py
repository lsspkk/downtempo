"""Audio engine of the NiceGUI player: Rubber Band (pylibrb) real-time stretch in a worker thread, sounddevice output.

The worker reads the song from the play position (wrapping inside the A–B loop), stretches it and puts
chunks on a short queue. The audio callback only copies chunks out and ramps the gain, so pause, tempo,
pitch and loop changes are heard within a fraction of a second. Explained in docs/stretch-app-flow.md.
"""

import queue
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
from pylibrb import Option, RubberBandStretcher

BLOCK = 1024  # input frames per stretcher call
QUEUE_CHUNKS = (
    6  # about 0.15 s at 1.0x, 0.3 s at 0.5x: how long a change takes to be heard
)
FADE = 256  # frames faded out/in at the loop seam, against clicks
PEAK_BINS = 1000
DETAIL_FRAMES = 64  # frames per bin of the loop editor's peaks (1.5 ms at 44.1 kHz)


@dataclass
class Chunk:
    gen: int  # seek generation; the callback drops chunks from before the latest seek
    start: float  # song position (frames) of the first output frame
    step: (
        float  # song frames per output frame (= speed), 0 for the pause between repeats
    )
    data: np.ndarray  # (frames, channels)
    wrapped: bool = False  # first chunk after the loop jumped back to A
    end: bool = False  # song finished


class Engine:
    """Plays one loaded recording. Positions are in song frames; the UI converts to seconds."""

    def __init__(self) -> None:
        self.audio = np.zeros((2, 0), np.float32)  # (channels, frames)
        self.rate = 44100
        self.peaks = np.zeros(PEAK_BINS, np.float32)
        self._detail: bytes | None = None
        self.speed = 1.0
        self.semitones = 0
        self.volume = 1.0
        self.loop: tuple[int, int] | None = None
        self.loop_gap = 0.0  # seconds of silence between repeats
        self.playing = False
        self.ended = False
        self.position = 0.0
        self.repeats = 0  # loop jumps heard since the last reset_repeats()
        self.error = ""
        self._gen = 0
        self._seek: int | None = 0
        self._lock = threading.Lock()
        # load() runs in a thread pool; two at once would drop a running stream without closing it,
        # and PortAudio then calls into a freed object (abort).
        self._load_lock = threading.RLock()
        self._chunks: queue.Queue[Chunk] = queue.Queue(maxsize=QUEUE_CHUNKS)
        self._current: Chunk | None = None
        self._offset = 0
        self._gain = 0.0
        self._stop = threading.Event()
        self._worker: threading.Thread | None = None
        self._stream: sd.OutputStream | None = None

    @property
    def frames(self) -> int:
        return self.audio.shape[1]

    @property
    def duration(self) -> float:
        return self.frames / self.rate

    def load(self, path: Path, wanted: Callable[[], bool] = lambda: True) -> bool:
        """Decode the file and start a paused stream. Slow (decoding): call from a thread.

        Loads queue up behind each other; one no longer `wanted` when its turn comes is skipped (False).
        """
        with self._load_lock:
            if not wanted():
                return False
            self._load(path)
            return True

    def _load(self, path: Path) -> None:
        self.close()
        data, self.rate = sf.read(path, dtype="float32", always_2d=True)
        self.audio = np.ascontiguousarray(data.T)
        self.peaks = peaks(self.audio)
        self._detail = None
        self.loop, self.playing, self.ended, self.position = None, False, False, 0.0
        self._seek, self._gen, self._gain = 0, self._gen + 1, 0.0
        self._chunks = queue.Queue(maxsize=QUEUE_CHUNKS)
        self._current = None
        self._stop = threading.Event()
        self._worker = threading.Thread(
            target=self._work, args=(self._stop,), daemon=True
        )
        self._worker.start()
        self._stream = sd.OutputStream(
            samplerate=self.rate, channels=self.audio.shape[0], callback=self._callback
        )
        self._stream.start()

    def detail_peaks(self) -> bytes:
        """Peaks per DETAIL_FRAMES as bytes 0..255 for the loop editor; made on first use (call from a thread)."""
        if self._detail is None:
            mono = np.abs(self.audio).max(axis=0) if self.frames else np.zeros(1)
            pad = -len(mono) % DETAIL_FRAMES
            bins = np.pad(mono, (0, pad)).reshape(-1, DETAIL_FRAMES).max(axis=1)
            self._detail = (
                (bins / max(bins.max(), 1e-6) * 255).astype(np.uint8).tobytes()
            )
        return self._detail

    def close(self) -> None:
        with self._load_lock:
            self._stop.set()
            self.playing = False
            if self._stream is not None:
                self._stream.close()
                self._stream = None
            if self._worker is not None:
                self._worker.join(timeout=1)
                self._worker = None
            self.audio = np.zeros((self.audio.shape[0], 0), np.float32)

    def play(self) -> None:
        if self.ended:
            self.seek(self.loop[0] if self.loop else 0)
        self.playing = True

    def pause(self) -> None:
        self.playing = False

    def seek(self, frame: float) -> None:
        frame = int(min(max(frame, 0), max(self.frames - 1, 0)))
        with self._lock:
            self._gen += 1
            self._seek = frame
            self.position = frame
            self.ended = False

    def set_loop(self, loop: tuple[int, int] | None) -> None:
        """Jumps to A when the play position is outside the new loop."""
        self.loop = loop
        self.reset_repeats()
        if loop and not loop[0] <= self.position < loop[1]:
            self.seek(loop[0])

    def reset_repeats(self) -> None:
        self.repeats = 0

    # Worker thread ---------------------------------------------------------

    def _work(self, stop: threading.Event) -> None:
        channels = self.audio.shape[0]
        rb = RubberBandStretcher(
            sample_rate=self.rate,
            channels=channels,
            options=Option.PROCESS_REALTIME
            | Option.ENGINE_FINER
            | Option.PitchHighConsistency,
        )
        rb.set_max_process_size(BLOCK)
        pos, heard, gen, drop, final = 0, 0.0, 0, 0, False
        fade_in = False
        while not stop.is_set():
            with self._lock:
                seek, self._seek, gen_now = self._seek, None, self._gen
            if seek is not None:
                # Silence pad + dropping the start delay keeps output frame 0 = input frame `pos` (pylibrb README).
                rb.reset()
                rb.time_ratio = 1 / self.speed
                pos, heard, gen, final = seek, float(seek), gen_now, False
                pad = rb.get_preferred_start_pad()
                for k in range(0, pad, BLOCK):
                    rb.process(np.zeros((channels, min(BLOCK, pad - k)), np.float32))
                drop = rb.get_start_delay()
            if final:
                stop.wait(0.02)
                continue

            loop = self.loop
            end = loop[1] if loop and loop[0] <= pos < loop[1] else self.frames
            n = min(BLOCK, end - pos)
            block = self.audio[:, pos : pos + n].copy()
            if fade_in:
                k = min(FADE, n)
                block[:, :k] *= np.linspace(0, 1, k, dtype=np.float32)
                fade_in = False
            pos += n
            wrapped = False
            if pos >= end and loop and end == loop[1]:
                k = min(FADE, n)
                block[:, n - k :] *= np.linspace(1, 0, k, dtype=np.float32)
                pos, wrapped, fade_in = loop[0], True, True
            elif pos >= end:
                final = True

            speed = self.speed
            rb.time_ratio = 1 / speed
            rb.pitch_scale = 2 ** (self.semitones / 12)
            rb.process(block, final=final)
            out = self._retrieve(rb, final)
            if drop:
                cut = min(drop, out.shape[1])
                out, drop = out[:, cut:], drop - cut

            chunks = []
            if out.shape[1]:
                chunks.append(Chunk(gen, heard, speed, np.ascontiguousarray(out.T)))
                heard += out.shape[1] * speed
            if wrapped:
                heard = float(loop[0])
                if gap := int(self.loop_gap * self.rate):
                    silence = np.zeros((gap, channels), np.float32)
                    chunks.append(Chunk(gen, heard, 0.0, silence))
                chunks.append(Chunk(gen, heard, speed, np.zeros((0, channels)), True))
            if final:
                chunks.append(Chunk(gen, heard, 0, np.zeros((0, channels)), end=True))
            for chunk in chunks:
                if not self._put(chunk, stop):
                    break

    @staticmethod
    def _retrieve(rb: RubberBandStretcher, final: bool) -> np.ndarray:
        parts = [rb.retrieve_available()] if rb.available() > 0 else []
        while final and not rb.is_done() and rb.available() > 0:
            parts.append(rb.retrieve_available())
        return np.concatenate(parts, axis=1) if parts else np.zeros((rb.channels, 0))

    def _put(self, chunk: Chunk, stop: threading.Event) -> bool:
        """Wait for room in the queue; give up when stopped or a seek comes in."""
        while not stop.is_set() and chunk.gen == self._gen:
            try:
                self._chunks.put(chunk, timeout=0.05)
                return True
            except queue.Full:
                pass
        return False

    # Audio callback --------------------------------------------------------

    def _callback(self, outdata: np.ndarray, frames: int, time, status) -> None:
        target = self.volume if self.playing else 0.0
        outdata.fill(0)
        if target == 0.0 and self._gain == 0.0:
            return
        filled = 0
        while filled < frames:
            chunk = self._current
            if (
                chunk is None
                or self._offset >= len(chunk.data)
                or chunk.gen != self._gen
            ):
                try:
                    chunk = self._chunks.get_nowait()
                except queue.Empty:
                    break
                self._current, self._offset = chunk, 0
                if chunk.gen != self._gen:
                    continue
                if chunk.wrapped:
                    self.repeats += 1
                if chunk.end:
                    self.playing, self.ended = False, True
                    self.position = self.frames
                    break
            n = min(frames - filled, len(chunk.data) - self._offset)
            outdata[filled : filled + n] = chunk.data[self._offset : self._offset + n]
            self._offset += n
            filled += n
            self.position = chunk.start + self._offset * chunk.step
        outdata *= np.linspace(self._gain, target, frames, dtype=np.float32)[:, None]
        self._gain = target


def peaks(audio: np.ndarray, bins: int = PEAK_BINS) -> np.ndarray:
    """Max absolute level per bin, 0..1, for drawing the waveform."""
    mono = np.abs(audio).max(axis=0)
    if not len(mono):
        return np.zeros(bins, np.float32)
    edges = np.linspace(0, len(mono), bins + 1, dtype=int)
    out = np.maximum.reduceat(mono, np.minimum(edges[:-1], len(mono) - 1))
    return out / max(out.max(), 1e-6)
