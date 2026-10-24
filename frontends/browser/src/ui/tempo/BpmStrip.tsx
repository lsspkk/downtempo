// The BPM strip under the bar (where the loop editor opens; a page of its own on a phone, where it also
// holds the Play at switch, TAP and the metronome): the recording tempo and the song's optimal tempo
// (−/+, typed), and under the optimal tempo the speed it needs. ✕ or Esc closes it
// (docs/tempo-goal.md#browser-app-t232).

import { ArrowLeft, Minus, Plus, X } from "lucide-react";
import { type ReactNode, useEffect, useState } from "react";
import { m } from "../../paraglide/messages.js";
import { IconButton } from "../kit/Button";
import { useKeys } from "../kit/keys";
import { TEMPO_MAX, TEMPO_MIN } from "../player/Tempo";
import type { Player } from "../player/usePlayer";
import { MetronomeButton, OptimalSwitch, TapButton, whole } from "./TempoBar";

export function BpmStrip({ player }: { player: Player }) {
  const goal = player.goal;
  const close = () => goal.setOpen(false);
  useKeys({ Escape: close }, goal.open);
  if (!goal.open || !player.recording) return null;
  const { bpm, optimal, optimalPercent } = goal;
  const reachable = optimalPercent !== null && optimalPercent >= TEMPO_MIN - 0.5 && optimalPercent <= TEMPO_MAX + 0.5;
  return (
    <section className="relative shrink-0 border-b border-zinc-200 bg-white px-3 py-1.5 dark:border-zinc-800 dark:bg-zinc-900 max-sm:fixed max-sm:inset-x-0 max-sm:top-24 max-sm:bottom-0 max-sm:z-30 max-sm:space-y-4 max-sm:overflow-y-auto max-sm:pb-6">
      <div className="-mx-2 -mt-1 flex items-center gap-2 border-b border-zinc-200 pb-1 sm:hidden dark:border-zinc-800">
        <IconButton label={m.back()} onClick={close}>
          <ArrowLeft size={22} />
        </IconButton>
        <h2 className="truncate font-semibold">{m.bpm_title()}</h2>
      </div>
      <div className="flex items-center gap-3 sm:hidden">
        <span className="text-lg font-semibold tabular-nums">{goal.now ? `${whole(goal.now)} BPM` : "– BPM"}</span>
        <span className="text-sm text-zinc-500 tabular-nums">{player.tempo} %</span>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-2 px-10 max-sm:justify-start max-sm:px-0">
        <Field
          label={m.recording_tempo()}
          note={!bpm && (goal.finding ? m.tempo_finding() : goal.failed ? m.tempo_none_found() : "")}
        >
          <BpmStepper value={bpm} onChange={goal.setBpm} />
        </Field>
        <Field
          label={m.optimal_tempo()}
          note={
            optimalPercent !== null &&
            (reachable
              ? m.optimal_needs({ percent: whole(optimalPercent) })
              : m.optimal_out_of_range({ percent: whole(optimalPercent) }))
          }
        >
          {/* the first − / + of an empty optimal tempo starts from the recording tempo */}
          <BpmStepper value={optimal} start={bpm} onChange={goal.setOptimal} />
        </Field>
        <div className="flex items-center gap-3 sm:hidden">
          <OptimalSwitch player={player} />
          <TapButton player={player} />
          <MetronomeButton player={player} />
        </div>
      </div>
      <IconButton label={`${m.close()} (Esc)`} onClick={close} className="absolute top-1 right-2 max-sm:hidden">
        <X size={20} />
      </IconButton>
    </section>
  );
}

/** A label and its stepper, and a note line under the stepper that keeps its height when empty, so the two
 * fields line up side by side (and stacked on a phone). */
function Field({ label, note, children }: { label: string; note?: ReactNode; children: ReactNode }) {
  return (
    <div className="grid grid-cols-[auto_auto] items-center gap-x-3 max-sm:grid-cols-1">
      <span className="w-32 text-sm whitespace-nowrap">{label}</span>
      <span className="inline-flex items-center">{children}</span>
      <span className="col-start-2 h-4 text-xs leading-4 text-zinc-500 tabular-nums max-sm:col-start-1">{note}</span>
    </div>
  );
}

/** −, a typed BPM (counts on Enter or leaving the field; empty = none), +: whole BPM steps. */
function BpmStepper({
  value,
  start = null,
  onChange,
}: {
  value: number | null;
  start?: number | null;
  onChange: (value: number | null) => void;
}) {
  const [text, setText] = useState(value ? whole(value) : "");
  useEffect(() => setText(value ? whole(value) : ""), [value]);
  const from = value ?? start;
  const typed = () => {
    const next = Number(text) || null;
    if (next !== (value ? Math.round(value) : null)) onChange(next); // leaving it unchanged is no change
  };
  return (
    <span className="inline-flex items-center gap-0.5">
      <IconButton label={m.bpm_down()} disabled={!from} onClick={() => from && onChange(Math.round(from) - 1)}>
        <Minus size={16} />
      </IconButton>
      <input
        inputMode="numeric"
        className="w-14 rounded-lg border border-zinc-300 bg-white px-1.5 py-0.5 text-center tabular-nums dark:border-zinc-700 dark:bg-zinc-900"
        value={text}
        onChange={(e) => setText(e.target.value.replace(/[^\d.]/g, ""))}
        onKeyDown={(e) => e.key === "Enter" && typed()}
        onBlur={typed}
        aria-label="BPM"
      />
      <IconButton label={m.bpm_up()} disabled={!from} onClick={() => from && onChange(Math.round(from) + 1)}>
        <Plus size={16} />
      </IconButton>
      <span className="text-xs text-zinc-500">BPM</span>
    </span>
  );
}
