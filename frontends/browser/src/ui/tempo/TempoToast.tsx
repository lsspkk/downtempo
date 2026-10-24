// In Sheet only the bars are hidden, so a tempo change there (← / →, X, G) shows for a moment over the
// sheet: "Optimal 100 · 114 % · 100 BPM", "tapped 108 · 123 % · 108 BPM" (docs/tempo-goal.md decision 9).

import { useEffect, useRef, useState } from "react";
import { m } from "../../paraglide/messages.js";
import type { Player } from "../player/usePlayer";
import { whole } from "./TempoBar";

const SHOW_MS = 1500;

export function TempoToast({ player, on }: { player: Player; on: boolean }) {
  const { goal, tempo } = player;
  const [text, setText] = useState("");
  const seen = useRef({ tempo, taps: goal.taps });
  useEffect(() => {
    const changed = seen.current.tempo !== tempo || (goal.taps > 0 && seen.current.taps !== goal.taps);
    seen.current = { tempo, taps: goal.taps };
    if (!on || !changed) return;
    const first = goal.tapped
      ? m.tapped({ bpm: whole(goal.tapped) })
      : goal.atOptimal && goal.optimal
        ? m.optimal_bpm({ bpm: whole(goal.optimal) })
        : "";
    setText([first, `${tempo} %`, goal.now ? `${whole(goal.now)} BPM` : ""].filter(Boolean).join(" · "));
    const timer = setTimeout(() => setText(""), SHOW_MS);
    return () => clearTimeout(timer);
  }, [tempo, goal.taps, on]);
  if (!on || !text) return null;
  return (
    <div className="pointer-events-none fixed top-4 left-1/2 z-[70] -translate-x-1/2 rounded-full bg-zinc-900/85 px-4 py-1.5 text-sm font-medium text-white tabular-nums shadow-lg">
      {text}
    </div>
  );
}
