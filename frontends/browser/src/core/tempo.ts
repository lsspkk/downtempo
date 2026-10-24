// A recording's tempo, the same way as the Python player (src/downtempo/tempo.py, docs/tempo-goal.md):
// pieces spread over the song, one BPM per piece (essentia.js, ui/tempo/tempoWorker.ts), the median with
// half and double counted as the same; and where the beats fall, so the click lines up with the music.

export const RATE = 44100;
export const PIECES = 10;
export const PIECE_SECONDS = 10;
export const MIN_BPM = 50;
export const MAX_BPM = 210;
const SAME = 0.04; // within 4 % counts as the same tempo

export type Estimate = { bpm: number; sure: number };

/** [start, end) sample ranges of the pieces, evenly spread (one piece when the song is short). */
export function pieceRanges(length: number, rate = RATE): [number, number][] {
  const size = Math.floor(PIECE_SECONDS * rate);
  if (length <= size) return [[0, length]];
  const count = Math.min(PIECES, Math.floor(length / size));
  const gap = (length - size) / Math.max(count - 1, 1);
  return Array.from({ length: count }, (_, i) => [Math.floor(i * gap), Math.floor(i * gap) + size]);
}

const median = (values: number[]) => {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = sorted.length >> 1;
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
};

/** Half or double of `middle` counts as `middle`'s octave. */
export function fold(bpm: number, middle: number): number {
  for (const factor of [2, 0.5]) if (Math.abs(bpm / (middle * factor) - 1) <= SAME) return bpm / factor;
  return bpm;
}

/** The pieces' BPMs (0 = none found) → the estimate, or null. */
export function summarize(found: number[]): Estimate | null {
  const real = found.filter((bpm) => bpm > 0);
  if (!real.length) return null;
  const middle = median(real);
  const folded = real.map((bpm) => fold(bpm, middle));
  const bpm = median(folded);
  const same = folded.filter((b) => Math.abs(b / bpm - 1) <= SAME).length;
  return { bpm: Math.round(bpm * 10) / 10, sure: Math.round((same / real.length) * 100) / 100 };
}
