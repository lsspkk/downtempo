// The play position in the top bar: the recording as a small bar waveform (wavesurfer.js over the
// peaks the player decoded), played part in indigo, the loop as an amber band; click or drag to seek.
// Unlike a slider it shows where the music is loud, quiet or silent.

import { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.esm.js";
import type { Loop } from "../../core/practice";
import { m } from "../../paraglide/messages.js";
import { WaveBuilding } from "../kit/bits";
import { followTime } from "./followTime";
import type { Player } from "./usePlayer";

const LOOP = "loop";
const color = (on: boolean) => (on ? "rgba(245, 158, 11, 0.35)" : "rgba(128, 128, 140, 0.2)");

export function PositionWave({ player }: { player: Player }) {
  const audio = player.audio;
  const peaks = audio.peaks;
  const loop = player.loop;
  const box = useRef<HTMLDivElement>(null);
  const surfer = useRef<{ ws: WaveSurfer; regions: ReturnType<typeof RegionsPlugin.create>; drawn: boolean } | null>(
    null,
  );
  const [drawn, setDrawn] = useState(false);
  const latest = useRef({ loop });
  latest.current = { loop };

  // One per recording: the peaks are new with each one.
  useEffect(() => {
    if (!box.current || !peaks) return;
    setDrawn(false);
    const dark = document.documentElement.classList.contains("dark");
    const regions = RegionsPlugin.create();
    const ws = WaveSurfer.create({
      container: box.current,
      peaks: peaks.data,
      duration: peaks.duration,
      height: 28,
      barWidth: 2,
      barGap: 1,
      barRadius: 1,
      normalize: true,
      waveColor: dark ? "#55555f" : "#c8c8d0",
      progressColor: dark ? "#8f98ff" : "#4f5bd5",
      cursorColor: dark ? "#8f98ff" : "#4f5bd5",
      cursorWidth: 2,
      dragToSeek: true,
      hideScrollbar: true,
      autoScroll: false,
      plugins: [regions],
    });
    const current = { ws, regions, drawn: false };
    surfer.current = current;
    ws.on("ready", () => {
      current.drawn = true;
      setDrawn(true);
      showLoop(current.regions, latest.current.loop);
    });
    ws.on("interaction", (time) => audio.seek(time));
    const unfollow = followTime(ws, audio);
    return () => {
      unfollow();
      surfer.current = null;
      ws.destroy();
    };
  }, [audio, peaks]);

  useEffect(() => {
    if (surfer.current?.drawn) showLoop(surfer.current.regions, loop);
  }, [loop]);

  return (
    <div className="relative h-7 min-w-24 flex-1">
      {!drawn && <WaveBuilding className="absolute inset-y-0 left-1" />}
      <div
        ref={box}
        className={`position-wave h-7 cursor-pointer transition-opacity duration-500 ${drawn ? "opacity-100" : "opacity-0"}`}
        aria-label={m.position()}
      />
    </div>
  );
}

function showLoop(regions: ReturnType<typeof RegionsPlugin.create>, loop: Loop | null) {
  const region = regions.getRegions().find((r) => r.id === LOOP);
  if (!loop) region?.remove();
  else if (region) region.setOptions({ start: loop.start, end: loop.end, color: color(loop.on) });
  else
    regions.addRegion({
      id: LOOP,
      start: loop.start,
      end: loop.end,
      color: color(loop.on),
      drag: false,
      resize: false,
    });
}
