// Keeps a wavesurfer's cursor on the player's time. The waveforms are drawn from the peaks, with no
// media element of their own, so nothing else tells them where the music is.

import type WaveSurfer from "wavesurfer.js";
import type { Player } from "./usePlayer";

/** Call once the waveform exists; returns the way to stop. `playing` lets a zoomed waveform scroll along. */
export function followTime(ws: WaveSurfer, audio: Player["audio"]): () => void {
  const draw = (time: number, playing: boolean) => {
    const duration = ws.getDuration();
    if (duration) ws.getRenderer().renderProgress(time / duration, playing);
  };
  ws.on("ready", () => draw(audio.now(), false));
  return audio.onTime(draw);
}
