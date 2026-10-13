// The play position in the top bar: the recording as a small bar waveform (wavesurfer.js over the
// player's own <audio>), played part in indigo, the loop as an amber band; click or drag to seek.
// Unlike a slider it shows where the music is loud, quiet or silent.

import { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.esm.js";
import type { Loop } from "../../core/practice";
import { m } from "../../paraglide/messages.js";
import { WaveBuilding } from "../kit/bits";
import type { Player } from "./usePlayer";

const LOOP = "loop";
const color = (on: boolean) => (on ? "rgba(245, 158, 11, 0.35)" : "rgba(128, 128, 140, 0.2)");

export function PositionWave({ player }: { player: Player }) {
  const media = player.audio.element;
  const source = player.recording?.key;
  const ready = player.audio.state.ready;
  const rate = player.tempo / 100;
  const loop = player.loop;
  const box = useRef<HTMLDivElement>(null);
  const surfer = useRef<{ ws: WaveSurfer; regions: ReturnType<typeof RegionsPlugin.create>; drawn: boolean } | null>(
    null,
  );
  const [drawn, setDrawn] = useState(false);
  const latest = useRef({ rate, loop });
  latest.current = { rate, loop };

  // One per recording (`source`); it reads the file the <audio> already plays (same URL: no reload).
  useEffect(() => {
    if (!box.current || !ready) return;
    setDrawn(false);
    const dark = document.documentElement.classList.contains("dark");
    const regions = RegionsPlugin.create();
    const ws = WaveSurfer.create({
      container: box.current,
      media,
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
      audioRate: latest.current.rate,
      plugins: [regions],
    });
    const current = { ws, regions, drawn: false };
    surfer.current = current;
    ws.on("ready", () => {
      // wavesurfer sets its own rate on the shared <audio>: give back the tempo, pitch kept
      media.preservesPitch = true;
      media.playbackRate = latest.current.rate;
      current.drawn = true;
      setDrawn(true);
      showLoop(current.regions, latest.current.loop);
    });
    void ws.load(media.currentSrc || media.src).catch(() => {}); // no picture: the bar stays empty
    return () => {
      surfer.current = null;
      ws.destroy();
    };
  }, [media, source, ready]);

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
