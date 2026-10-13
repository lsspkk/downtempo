// Small pieces many screens use: muted text, a progress bar, the first start's step count, and the
// small icon shown while a waveform is being made.

import type { ReactNode } from "react";
import { m } from "../../paraglide/messages.js";

export const Muted = ({ children, className = "" }: { children: ReactNode; className?: string }) => (
  <p className={`text-sm text-zinc-500 dark:text-zinc-400 ${className}`}>{children}</p>
);

export function Progress({ value }: { value: number }) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
      <div
        className="h-full rounded-full bg-accent-500 transition-[width]"
        style={{ width: `${Math.round(value * 100)}%` }}
      />
    </div>
  );
}

/** "Step 2 of 4" over each question of the first start (name, link, sign in, folders). */
export const Step = ({ n }: { n: number }) => (
  <p className="text-xs font-medium tracking-wide text-zinc-500 uppercase">{m.step_of({ n, total: 4 })}</p>
);

// A made-up waveform: gently changing heights (% of the icon's height).
const BARS = Array.from({ length: 12 }, (_, i) => Math.round(55 + 30 * Math.sin(i * 0.9) * Math.cos(i * 0.31)));

/** While a waveform is being made: a small made-up waveform at the left of its box (vertically
 * centred), seen only under a soft-edged spotlight sweeping left to right and back. No text. */
export function WaveBuilding({ className = "" }: { className?: string }) {
  return (
    <div aria-hidden className={`pointer-events-none flex items-center ${className}`}>
      <span className="relative h-4 w-[46px]">
        <span className="wave-building absolute inset-0 flex items-center gap-0.5">
          {BARS.map((height, i) => (
            <span
              key={i}
              className="w-0.5 rounded-full bg-zinc-500 dark:bg-zinc-400"
              style={{ height: `${height}%` }}
            />
          ))}
        </span>
      </span>
    </div>
  );
}
