// The tempo in BPM in the bar (docs/tempo-goal.md#browser-app-t232): after the tempo slider
// `75 BPM (TAP) (metronome)  ○ Play at 100`. "75 BPM" is BpmButton, which opens the BPM strip (BpmStrip.tsx);
// Tap sets the speed like a DAW's tap tempo; the Play at switch plays every recording of the song at the optimal tempo.

import { Square } from "lucide-react";
import { m } from "../../paraglide/messages.js";
import { Button } from "../kit/Button";
import { Switch } from "../kit/Switch";
import type { Player } from "../player/usePlayer";

export const whole = (value: number) => String(Math.round(value));

/** "75 BPM": the BPM now; "finding…" on first load; "–" without a recording tempo. */
export function BpmButton({ player }: { player: Player }) {
  const goal = player.goal;
  return (
    <Button
      kind="quiet"
      active={goal.open}
      aria-expanded={goal.open}
      onClick={() => goal.setOpen(!goal.open)}
      title={m.bpm_open_title()}
      className="!px-2 tabular-nums"
    >
      {goal.now ? (
        <>
          <span className="font-semibold">{whole(goal.now)}</span>
          <span className="text-xs text-zinc-500">BPM</span>
        </>
      ) : (
        <span className="text-xs text-zinc-500">{goal.finding ? m.tempo_finding() : "– BPM"}</span>
      )}
    </Button>
  );
}

/** Round TAP; the tapped BPM for a moment after each tap. */
export function TapButton({ player, className = "" }: { player: Player; className?: string }) {
  const goal = player.goal;
  return (
    <Button
      disabled={!goal.bpm}
      onClick={goal.tap}
      title={goal.bpm ? m.tap_title() : m.tap_needs_bpm()}
      className={`h-10 min-w-10 !rounded-full !px-2 text-xs !text-accent-700 dark:!text-accent-300 font-bold tracking-wide uppercase tabular-nums ${className}`}
    >
      {goal.tapped ? whole(goal.tapped) : goal.taps ? goal.taps : m.tap()}
    </Button>
  );
}

/** Round like TAP: outlined with a metronome; while it ticks (at the BPM now) filled, with ■. */
export function MetronomeButton({ player }: { player: Player }) {
  const goal = player.goal;
  const on = goal.metronome;
  return (
    <button
      type="button"
      disabled={!goal.now}
      onClick={goal.toggleMetronome}
      aria-pressed={on}
      title={goal.now ? (on ? m.metronome_off() : m.metronome_on({ bpm: whole(goal.now) })) : m.metronome_needs_bpm()}
      className={`inline-flex size-10 shrink-0 items-center justify-center rounded-full border transition-colors disabled:opacity-40 ${on ? "border-accent-600 bg-accent-600 text-white" : "border-zinc-300 bg-white text-accent-700 hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-900 dark:text-accent-300 dark:hover:bg-zinc-800"}`}
    >
      {on ? (
        <Square size={16} fill="currentColor" aria-hidden />
      ) : (
        <svg
          viewBox="0 0 24 24"
          width="20"
          height="20"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden
        >
          <path d="M9 3h6l4 18H5z" />
          <path d="M7 16h10" />
          <path d="M12 16l4.5-9" />
        </svg>
      )}
    </button>
  );
}

/** "Play at 98": on, the song plays at its optimal tempo; grey without one, and then a click opens the strip. */
export function OptimalSwitch({ player }: { player: Player }) {
  const goal = player.goal;
  const ready = !!goal.optimalPercent;
  return (
    <Switch
      on={goal.atOptimal}
      onChange={goal.toggleOptimal}
      muted={!ready}
      label={goal.optimal ? m.optimal_bpm({ bpm: whole(goal.optimal) }) : m.optimal()}
      title={
        ready && goal.optimal && goal.optimalPercent
          ? m.optimal_title({ bpm: whole(goal.optimal), percent: whole(goal.optimalPercent) })
          : m.optimal_none_title()
      }
    />
  );
}
