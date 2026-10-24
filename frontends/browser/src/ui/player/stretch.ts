// One recording decoded into memory and played through Signalsmith Stretch (an AudioWorklet): play,
// pause, seek, tempo with the pitch kept, and the A–B loop, which the worklet runs inside the audio
// (sample-accurate, no jump from the screen's clock). No <audio> element; the screen follows `onTime`.

import SignalsmithStretch, { type StretchNode } from "signalsmith-stretch";
import type { Loop } from "../../core/practice";

/** The waveform: one channel of ±maximum per PEAK_BLOCK samples (the signs make the bars symmetric). */
export type Peaks = { data: Float32Array[]; duration: number };
export type Handlers = {
  onTime: (time: number, playing: boolean) => void;
  /** Playing changed on its own: the song ended. */
  onEnded: () => void;
};

const PEAK_BLOCK = 8;
const UPDATE_SECONDS = 0.03;

let context: AudioContext | null = null;
export const audioContext = () => (context ??= new AudioContext());

export class Stretch {
  readonly duration: number;
  readonly peaks: Peaks;
  private position = 0;
  private playing = false;
  private rate = 1;
  private loop: Loop | null = null;

  private constructor(
    private node: StretchNode,
    duration: number,
    peaks: Peaks,
    private handlers: Handlers,
  ) {
    this.duration = duration;
    this.peaks = peaks;
  }

  /** Decode the file (resampled to the context's rate), hand it to the worklet, connect to the speakers. */
  static async open(file: Blob, handlers: Handlers): Promise<Stretch> {
    const ctx = audioContext();
    const decoded = await ctx.decodeAudioData(await file.arrayBuffer());
    const channels = Array.from({ length: decoded.numberOfChannels }, (_, i) => {
      const data = new Float32Array(decoded.length);
      decoded.copyFromChannel(data, i);
      return data;
    });
    const peaks = { data: [peaksOf(channels)], duration: decoded.duration };
    if (channels.length === 1) channels.push(channels[0].slice()); // the node plays stereo
    const node = await SignalsmithStretch(ctx);
    const stretch = new Stretch(node, decoded.duration, peaks, handlers);
    await node.addBuffers(
      channels,
      channels.map((c) => c.buffer as ArrayBuffer),
    );
    await node.setUpdateInterval(UPDATE_SECONDS, (time) => stretch.heard(time));
    node.connect(ctx.destination);
    return stretch;
  }

  time = () => this.position;
  isPlaying = () => this.playing;

  /** False when the browser still wants a click before it lets sound out. */
  async play(): Promise<boolean> {
    const ctx = audioContext();
    if (ctx.state !== "running") await Promise.race([ctx.resume(), new Promise((r) => setTimeout(r, 1000))]);
    if (ctx.state !== "running") return false;
    if (this.position >= this.duration) this.position = 0;
    this.playing = true;
    await this.node.schedule({ active: true, input: this.position, ...this.settings() });
    return true;
  }

  pause() {
    if (!this.playing) return;
    this.playing = false;
    void this.node.stop();
    this.handlers.onTime(this.position, false);
  }

  seek(time: number) {
    this.position = Math.max(0, Math.min(time, this.duration));
    void this.node.schedule({ input: this.position });
    this.handlers.onTime(this.position, this.playing);
  }

  /** Tempo and loop, live. A loop that ends before the playhead takes it back to the loop's start. */
  set(rate: number, loop: Loop | null) {
    this.rate = rate;
    this.loop = loop;
    const jump = this.playing && loop?.on && this.position >= loop.end;
    if (jump) this.position = loop.start;
    void this.node.schedule({ ...(jump ? { input: this.position } : {}), ...this.settings() });
  }

  close() {
    this.playing = false;
    void this.node.stop();
    this.node.disconnect();
    void this.node.dropBuffers();
  }

  private settings() {
    const on = this.loop?.on;
    return { rate: this.rate, loopStart: on ? this.loop!.start : 0, loopEnd: on ? this.loop!.end : 0 };
  }

  // The worklet reports the input position about every UPDATE_SECONDS.
  private heard(time: number) {
    if (!this.playing) return;
    this.position = Math.min(time, this.duration);
    if (!this.loop?.on && time >= this.duration) {
      this.pause();
      this.handlers.onEnded();
      return;
    }
    this.handlers.onTime(this.position, true);
  }
}

function peaksOf(channels: Float32Array[]): Float32Array {
  const length = channels[0].length;
  const peaks = new Float32Array(Math.ceil(length / PEAK_BLOCK));
  for (let i = 0; i < peaks.length; i++) {
    let top = 0;
    for (const data of channels) {
      const end = Math.min(length, (i + 1) * PEAK_BLOCK);
      for (let j = i * PEAK_BLOCK; j < end; j++) top = Math.max(top, Math.abs(data[j]));
    }
    peaks[i] = i % 2 ? -top : top;
  }
  return peaks;
}
