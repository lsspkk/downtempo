// Types for the parts of signalsmith-stretch (no types of its own) that stretch.ts uses.
declare module "signalsmith-stretch" {
  export type StretchChange = {
    active?: boolean;
    input?: number;
    rate?: number;
    semitones?: number;
    loopStart?: number;
    loopEnd?: number;
  };
  export type StretchNode = AudioNode & {
    schedule(change: StretchChange): Promise<unknown>;
    stop(): Promise<unknown>;
    addBuffers(buffers: Float32Array[], transfer?: ArrayBuffer[]): Promise<number>;
    dropBuffers(): Promise<unknown>;
    setUpdateInterval(seconds: number, callback: (inputTime: number) => void): Promise<unknown>;
  };
  export default function SignalsmithStretch(context: BaseAudioContext): Promise<StretchNode>;
}
