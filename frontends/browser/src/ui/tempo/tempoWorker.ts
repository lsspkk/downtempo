// The tempo estimate's heavy part, off the page's thread (essentia.js's docs advise a worker for its
// WebAssembly): PercivalBpmEstimator on each piece, with the Python player's settings.

import { EssentiaWASM } from "essentia.js/dist/essentia-wasm.es.js";
import Essentia from "essentia.js/dist/essentia.js-core.es.js";
import { MAX_BPM, MIN_BPM, RATE } from "../../core/tempo";

const essentia = new Essentia(EssentiaWASM);

self.onmessage = (event: MessageEvent<Float32Array[]>) => {
  const found = event.data.map(
    (piece) =>
      essentia.PercivalBpmEstimator(essentia.arrayToVector(piece), 1024, 2048, 128, 128, MAX_BPM, MIN_BPM, RATE).bpm,
  );
  self.postMessage(found);
};
