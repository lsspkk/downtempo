// A recording's tempo estimate in the browser: decode it again at 44.1 kHz, cut the pieces (mono),
// let the worker find each piece's BPM, then the median (core/tempo.ts). essentia.js (about 2.5 MB)
// loads with the first estimate only.

import * as files from "../../core/files";
import { type Estimate, pieceRanges, RATE, summarize } from "../../core/tempo";

export async function estimate(project: string, recording: string): Promise<Estimate | null> {
  const file = await files.open(project, recording);
  const decoded = await new OfflineAudioContext(1, 1, RATE).decodeAudioData(await file.arrayBuffer());
  const channels = Array.from({ length: decoded.numberOfChannels }, (_, i) => decoded.getChannelData(i));
  const pieces = pieceRanges(decoded.length).map(([start, end]) => {
    const mono = new Float32Array(end - start);
    for (const data of channels) for (let i = 0; i < mono.length; i++) mono[i] += data[start + i] / channels.length;
    return mono;
  });
  const worker = new Worker(new URL("./tempoWorker.ts", import.meta.url), { type: "module" });
  try {
    const found = await new Promise<number[]>((resolve, reject) => {
      worker.onmessage = (event: MessageEvent<number[]>) => resolve(event.data);
      worker.onerror = (event) => reject(new Error(event.message));
      worker.postMessage(
        pieces,
        pieces.map((p) => p.buffer),
      );
    });
    return summarize(found);
  } finally {
    worker.terminate();
  }
}
