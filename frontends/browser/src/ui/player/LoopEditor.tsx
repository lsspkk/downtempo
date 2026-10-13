// The loop editor under the top bar: the recording's waveform (wavesurfer.js, drawn from the
// peaks the player decoded), the loop as a region with handles, a time ruler, zoom; start and end to nudge;
// the saved regions. Click, click or drag selects; a click on the ruler seeks. E or Esc closes it. On a
// phone it fills the screen under the top line and the position line (▶ stays at hand).

import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Ear,
  Expand,
  X,
  ZoomIn,
} from "lucide-react";
import { type ReactNode, useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin, { type Region } from "wavesurfer.js/dist/plugins/regions.esm.js";
import TimelinePlugin from "wavesurfer.js/dist/plugins/timeline.esm.js";
import ZoomPlugin from "wavesurfer.js/dist/plugins/zoom.esm.js";
import { clock } from "../../core/format";
import type { Loop } from "../../core/practice";
import { m } from "../../paraglide/messages.js";
import { useKeys } from "../kit/keys";
import { Muted, WaveBuilding } from "../kit/bits";
import { Button, IconButton } from "../kit/Button";
import { followTime } from "./followTime";
import { SavedLoops } from "./SavedLoops";
import type { Player } from "./usePlayer";

const WAVE_HEIGHT = 110; // also the h-[110px] of the bars shown while it is made
const LOOP = "loop"; // region ids
const MARK = "mark"; // the first click of a click, click selection
// The Python player's colours: amber loop (#f59e0b), indigo playhead and progress (#4f5bd5), grey-blue wave.
const color = (on: boolean) => (on ? "rgba(245, 158, 11, 0.3)" : "rgba(128, 128, 140, 0.2)");

export function LoopEditor({ player }: { player: Player }) {
  const { project, loop, setLoop: onLoop } = player;
  const recording = player.recording?.key ?? "";
  const audio = player.audio;
  const peaks = audio.peaks;
  const duration = player.audio.state.duration;
  const onClose = () => player.setEditing(false);
  const box = useRef<HTMLDivElement>(null);
  const wave = useRef<HTMLDivElement>(null); // wavesurfer's, faded in once drawn
  const [surfer, setSurfer] = useState<{ ws: WaveSurfer; regions: ReturnType<typeof RegionsPlugin.create> } | null>(
    null,
  );
  const [drawn, setDrawn] = useState(false);
  const [problem, setProblem] = useState("");
  const [zoom, setZoom] = useState(1);
  const [mark, setMark] = useState<number | null>(null);
  const latest = useRef({ loop, onLoop });
  latest.current = { loop, onLoop };

  // One wavesurfer per opening, drawn from the peaks the player already made.
  useEffect(() => {
    if (!wave.current || !peaks) return;
    const dark = document.documentElement.classList.contains("dark");
    const regions = RegionsPlugin.create();
    const ws = WaveSurfer.create({
      container: wave.current,
      peaks: peaks.data,
      duration: peaks.duration,
      height: WAVE_HEIGHT,
      waveColor: dark ? "#7d87a8" : "#8a94b0",
      progressColor: dark ? "#8f98ff" : "#4f5bd5",
      cursorColor: "#4f5bd5",
      cursorWidth: 2,
      interact: false, // a click selects here; the ruler and the seek bar seek
      dragToSeek: false,
      autoScroll: true,
      autoCenter: false,
      plugins: [
        regions,
        TimelinePlugin.create({ height: 18, style: { color: dark ? "#c8c8d0" : "#55555f", fontSize: "10px" } }),
        ZoomPlugin.create({ scale: 0.25, maxZoom: 2000 }),
      ],
    });
    const stopDragging = regions.enableDragSelection({ color: color(true) });
    regions.on("region-created", (region: Region) => {
      if (region.id === LOOP || region.id === MARK) return;
      region.remove(); // a drag made it: it becomes the loop
      setMark(null);
      latest.current.onLoop({ start: region.start, end: region.end, on: true });
    });
    regions.on("region-updated", (region: Region) => {
      if (region.id === LOOP)
        latest.current.onLoop({ start: region.start, end: region.end, on: latest.current.loop?.on ?? true });
    });
    ws.on("zoom", (pxPerSec) => {
      const width = box.current?.clientWidth || 1;
      setZoom(Math.max(1, (pxPerSec * ws.getDuration()) / width));
    });
    ws.on("ready", () => {
      setDrawn(true);
      const l = latest.current.loop;
      if (l) zoomTo(ws, box.current, l);
    });
    ws.on("error", (error) => setProblem(error.message));
    const unfollow = followTime(ws, audio);
    setSurfer({ ws, regions });
    return () => {
      unfollow();
      stopDragging();
      ws.destroy();
      setSurfer(null);
      setDrawn(false);
    };
  }, [audio, peaks]);

  // The loop as a region: drawn from the player's loop, resized by its handles.
  useEffect(() => {
    if (!surfer || !drawn) return;
    const region = surfer.regions.getRegions().find((r) => r.id === LOOP);
    if (!loop) region?.remove();
    else if (region) region.setOptions({ start: loop.start, end: loop.end, color: color(loop.on) });
    else
      surfer.regions.addRegion({
        id: LOOP,
        start: loop.start,
        end: loop.end,
        color: color(loop.on),
        drag: false,
        resize: true,
        minLength: 0.1,
      });
  }, [surfer, drawn, loop]);

  // The first click of a click, click selection shows as a marker.
  useEffect(() => {
    if (!surfer || !drawn) return;
    surfer.regions
      .getRegions()
      .find((r) => r.id === MARK)
      ?.remove();
    if (mark !== null) surfer.regions.addRegion({ id: MARK, start: mark, color: "rgba(245, 158, 11, 1)" });
  }, [surfer, drawn, mark]);

  // A click (not a drag): on the waveform it selects, on the ruler below it seeks.
  const down = useRef<{ x: number; y: number } | null>(null);
  function clicked(x: number, y: number) {
    const start = down.current;
    down.current = null;
    if (!surfer || !box.current || !start || Math.hypot(x - start.x, y - start.y) > 4) return;
    const rect = box.current.getBoundingClientRect();
    const { startTime, endTime } = surfer.ws.getRenderer().getVisibleRange().value;
    const time = startTime + ((x - rect.left) / rect.width) * (endTime - startTime);
    if (y - rect.top > WAVE_HEIGHT) player.audio.seek(time);
    else if (mark === null) setMark(time);
    else {
      onLoop({ start: Math.min(mark, time), end: Math.max(mark, time), on: true });
      setMark(null);
    }
  }

  useKeys({ Escape: () => (mark !== null ? setMark(null) : onClose()) });

  const nudge = (side: "start" | "end", by: number) => {
    if (!loop) return;
    const start = side === "start" ? Math.min(Math.max(0, loop.start + by), loop.end - 0.1) : loop.start;
    const end = side === "end" ? Math.max(Math.min(duration, loop.end + by), loop.start + 0.1) : loop.end;
    onLoop({ ...loop, start, end });
  };

  return (
    <section className="space-y-2 bg-white px-3 py-2 dark:bg-zinc-900 max-sm:fixed max-sm:inset-x-0 max-sm:top-24 max-sm:bottom-0 max-sm:z-30 max-sm:overflow-y-auto shrink-0 border-b border-zinc-200 dark:border-zinc-800">
      {/* On a phone a page of its own: ← and its title, as any page; the buttons on the line under it. */}
      <div className="-mx-2 -mt-1 flex items-center gap-2 border-b border-zinc-200 pb-1 sm:hidden dark:border-zinc-800">
        <IconButton label={m.back()} onClick={onClose}>
          <ArrowLeft size={22} />
        </IconButton>
        <h2 className="truncate font-semibold">{m.loop_editor_title()}</h2>
      </div>
      <div className="flex flex-wrap items-center gap-1">
        <Button kind="quiet" onClick={() => surfer && wholeSong(surfer.ws, box.current)}>
          <Expand size={16} /> <span className="sm:hidden">{m.whole_song_short()}</span>
          <span className="max-sm:hidden">{m.whole_song()}</span>
        </Button>
        <Button kind="quiet" disabled={!loop} onClick={() => surfer && loop && zoomTo(surfer.ws, box.current, loop)}>
          <ZoomIn size={16} /> <span className="sm:hidden">{m.zoom_to_loop_short()}</span>
          <span className="max-sm:hidden">{m.zoom_to_loop()}</span>
        </Button>
        <span className="w-12 text-center text-xs text-zinc-500 tabular-nums">{zoom.toFixed(zoom < 10 ? 1 : 0)}×</span>
        <Button kind="quiet" disabled={!loop} onClick={player.hearEnd} title={m.hear_end_title()}>
          <Ear size={16} /> {m.hear_end()}
        </Button>
        <Button kind="quiet" disabled={!loop} onClick={() => onLoop(null)}>
          <X size={16} className="max-sm:hidden" /> {m.clear_loop()}
        </Button>
        <span className="mx-2 hidden truncate text-xs text-zinc-500 lg:inline">
          {mark !== null ? m.click_end() : m.editor_hint()}
        </span>
        <IconButton label={m.close_editor()} onClick={onClose} className="ml-auto max-sm:hidden">
          <X size={20} />
        </IconButton>
      </div>
      <div
        ref={box}
        className={`relative min-h-32 ${mark !== null ? "cursor-crosshair" : ""}`}
        onPointerDown={(e) => (down.current = { x: e.clientX, y: e.clientY })}
        onPointerUp={(e) => clicked(e.clientX, e.clientY)}
      >
        {!drawn &&
          (problem ? (
            <Muted className="absolute inset-0 grid place-items-center">{m.waveform_failed({ reason: problem })}</Muted>
          ) : (
            <WaveBuilding className="absolute top-0 left-2 h-[110px]" />
          ))}
        <div ref={wave} className={`transition-opacity duration-500 ${drawn ? "opacity-100" : "opacity-0"}`} />
      </div>
      <div className="grid max-w-2xl grid-cols-1 gap-2 sm:grid-cols-2">
        <Edge label={m.loop_start()} value={loop?.start} onNudge={(by) => nudge("start", by)} />
        <Edge label={m.loop_end()} value={loop?.end} onNudge={(by) => nudge("end", by)} />
      </div>
      <SavedLoops project={project} recording={recording} loop={loop} onUse={onLoop} />
    </section>
  );
}

/** One loop edge, as in the Python player: its name over « ‹ time › » (1 s and 0.1 s). */
function Edge({ label, value, onNudge }: { label: string; value: number | undefined; onNudge: (by: number) => void }) {
  const off = value === undefined;
  const step = (icon: ReactNode, by: number, title: string) => (
    <Button
      kind="quiet"
      className="!rounded-full !p-1.5"
      disabled={off}
      onClick={() => onNudge(by)}
      title={title}
      aria-label={`${label} ${title}`}
    >
      {icon}
    </Button>
  );
  return (
    <div className="flex flex-col items-center rounded-lg bg-amber-500/10 py-1">
      <span className="text-xs text-zinc-500 dark:text-zinc-400">{label}</span>
      <div className="flex items-center">
        {step(<ChevronsLeft size={18} />, -1, "−1 s")}
        {step(<ChevronLeft size={18} />, -0.1, m.minus_tenth())}
        <span className="w-20 text-center font-mono tabular-nums">{off ? "–" : clock(value, true)}</span>
        {step(<ChevronRight size={18} />, 0.1, m.plus_tenth())}
        {step(<ChevronsRight size={18} />, 1, "+1 s")}
      </div>
    </div>
  );
}

function wholeSong(ws: WaveSurfer, box: HTMLElement | null) {
  ws.zoom((box?.clientWidth ?? 800) / Math.max(1, ws.getDuration()));
}

/** The loop with a tenth of its length on each side. */
function zoomTo(ws: WaveSurfer, box: HTMLElement | null, loop: Loop) {
  const length = Math.max(0.5, loop.end - loop.start);
  ws.zoom((box?.clientWidth ?? 800) / (length * 1.2));
  ws.setScrollTime(Math.max(0, loop.start - length * 0.1));
}
