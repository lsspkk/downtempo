// The Metronome by Web Audio (docs/tempo-goal.md): a steady tick at the BPM now, scheduled a little
// ahead, playing or not.

import { audioContext } from "../player/stretch";

const AHEAD = 0.12; // seconds of clicks scheduled ahead
const PITCH = 1800; // Hz, like the Python player's
const LENGTH = 0.03;

function tick(at: number) {
  const ctx = audioContext();
  const tone = new OscillatorNode(ctx, { frequency: PITCH });
  const gain = new GainNode(ctx, { gain: 0.4 });
  gain.gain.setValueAtTime(0.4, at);
  gain.gain.exponentialRampToValueAtTime(0.001, at + LENGTH);
  tone.connect(gain).connect(ctx.destination);
  tone.start(at);
  tone.stop(at + LENGTH);
}

export class Click {
  private timer = 0;

  /** Ticks at `bpm` from now on; null stops. */
  play(bpm: number | null) {
    clearInterval(this.timer);
    this.timer = 0;
    if (!bpm) return;
    let at = audioContext().currentTime + 0.05;
    const schedule = () => {
      for (const now = audioContext().currentTime; at < now + AHEAD * 2; at += 60 / bpm) tick(Math.max(at, now));
    };
    void audioContext().resume();
    schedule();
    this.timer = window.setInterval(schedule, 50);
  }
}
