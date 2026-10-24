// essentia.js ships types only for its package entry; these are the two ES modules the worker loads.
declare module "essentia.js/dist/essentia-wasm.es.js" {
  export const EssentiaWASM: unknown;
}
declare module "essentia.js/dist/essentia.js-core.es.js" {
  export default class Essentia {
    constructor(wasm: unknown);
    arrayToVector(array: Float32Array): unknown;
    PercivalBpmEstimator(
      signal: unknown,
      frameSize?: number,
      frameSizeOSS?: number,
      hopSize?: number,
      hopSizeOSS?: number,
      maxBPM?: number,
      minBPM?: number,
      sampleRate?: number,
    ): { bpm: number };
  }
}
