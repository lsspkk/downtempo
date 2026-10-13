// Tempo 50–130 %: a slider with clickable marks right under it (the current one bold); ← / → step it.
// TempoSlider sits in the bar with a pointer; TempoButton (a gauge over the %) opens it in a drop-down
// with − and + for a phone, which has no keys.

import { Gauge, Minus, Plus } from "lucide-react";
import { m } from "../../paraglide/messages.js";
import { IconButton } from "../kit/Button";
import { DropDown } from "../kit/DropDown";
import type { Player } from "./usePlayer";

export const TEMPO_MIN = 50;
export const TEMPO_MAX = 130;
export const TEMPO_STEP = 5;
const MARKS = [50, 60, 70, 80, 90, 100, 110, 120, 130];

export const clampTempo = (value: number) =>
  Math.min(TEMPO_MAX, Math.max(TEMPO_MIN, Math.round(value / TEMPO_STEP) * TEMPO_STEP));

// The thumb (16 px) travels from 8 px to width − 8 px; marks sit under its centre.
const at = (value: number) => `calc(8px + (100% - 16px) * ${(value - TEMPO_MIN) / (TEMPO_MAX - TEMPO_MIN)})`;

export function TempoSlider({
  player,
  className = "relative min-w-36 flex-1 pb-3 sm:w-48 sm:flex-none lg:w-64",
}: {
  player: Player;
  className?: string;
}) {
  const { tempo, setTempo } = player;
  return (
    <div className={className}>
      <input
        type="range"
        className="range block"
        min={TEMPO_MIN}
        max={TEMPO_MAX}
        step={TEMPO_STEP}
        value={tempo}
        onChange={(e) => setTempo(Number(e.target.value))}
        title={`${m.tempo()} ${tempo} % (← →)`}
        aria-label={m.tempo()}
      />
      {MARKS.map((mark) => (
        <button
          key={mark}
          onClick={() => setTempo(mark)}
          style={{ left: at(mark) }}
          className={`absolute bottom-0 -translate-x-1/2 px-0.5 text-[10px] leading-none tabular-nums ${mark === tempo ? "font-bold text-accent-600 dark:text-accent-400" : "text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"}`}
        >
          {mark}
        </button>
      ))}
    </div>
  );
}

export function TempoButton({ player }: { player: Player }) {
  const { tempo, setTempo } = player;
  return (
    <DropDown
      width="sm:w-96"
      title={`${m.tempo()} ${tempo} %`}
      trigger={(open, toggle) => (
        <IconButton
          label={`${m.tempo()} ${tempo} %`}
          active={open}
          aria-expanded={open}
          onClick={toggle}
          className="flex-col"
        >
          <Gauge size={20} />
          <span className="text-[10px] leading-none font-semibold tabular-nums">{tempo}</span>
        </IconButton>
      )}
    >
      <div className="flex items-center gap-2 px-1 pt-3 pb-1">
        <IconButton label={m.slower()} onClick={() => setTempo((t) => t - TEMPO_STEP)}>
          <Minus size={20} />
        </IconButton>
        <TempoSlider player={player} className="relative flex-1 pb-4" />
        <IconButton label={m.faster()} onClick={() => setTempo((t) => t + TEMPO_STEP)}>
          <Plus size={20} />
        </IconButton>
      </div>
    </DropDown>
  );
}
