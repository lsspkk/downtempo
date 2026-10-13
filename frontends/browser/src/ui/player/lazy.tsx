// wavesurfer.js (the position waveform, the loop editor) loads after the page: these wrappers load
// it with their first use and show the small "being made" icon meanwhile.

import { lazy, Suspense } from "react";
import { WaveBuilding } from "../kit/bits";
import type { Player } from "./usePlayer";

const PositionWave = lazy(() => import("./PositionWave").then((module) => ({ default: module.PositionWave })));
const LoopEditor = lazy(() => import("./LoopEditor").then((module) => ({ default: module.LoopEditor })));

export const Position = ({ player }: { player: Player }) => (
  <Suspense fallback={<WaveBuilding className="h-7 min-w-24 flex-1" />}>
    <PositionWave player={player} />
  </Suspense>
);

export const LoopEditorPanel = ({ player }: { player: Player }) =>
  player.editing && player.recording ? (
    <Suspense fallback={null}>
      <LoopEditor player={player} />
    </Suspense>
  ) : null;
