// Downloaded wavs are kept as mp3, like the Python app (docs/compress.md): `storedAs` says under which
// key a server's file lives on this device, `toMp3` encodes one wav at about 128 kbit/s by Mediabunny
// with its WASM LAME encoder, both loaded with the first wav only.

const BITRATE = 128e3;

const isWav = (path: string) => /\.wav$/i.test(path);
const asMp3 = (path: string) => path.replace(/\.wav$/i, ".mp3");

/** `Song.wav` is stored as `Song.mp3`, unless the server also has a `Song.mp3` there (`listed`: the
 * server's paths, any case). */
export function storedAs(path: string, listed: Set<string>): string {
  if (!isWav(path)) return path;
  const mp3 = asMp3(path);
  return listed.has(mp3.toLowerCase()) ? path : mp3;
}

let ready: Promise<typeof import("mediabunny")> | null = null;

function mediabunny() {
  ready ??= (async () => {
    const mb = await import("mediabunny");
    if (!(await mb.canEncodeAudio("mp3"))) (await import("@mediabunny/mp3-encoder")).registerMp3Encoder();
    return mb;
  })();
  return ready;
}

/** The wav as an mp3; throws when it can't be read or encoded, and an AbortError when stopped. */
export async function toMp3(wav: Blob, signal: AbortSignal): Promise<Blob> {
  const mb = await mediabunny();
  signal.throwIfAborted();
  const output = new mb.Output({ format: new mb.Mp3OutputFormat(), target: new mb.BufferTarget() });
  const conversion = await mb.Conversion.init({
    input: new mb.Input({ source: new mb.BlobSource(wav), formats: mb.ALL_FORMATS }),
    output,
    audio: { codec: "mp3", quality: new mb.Quality({ bitrate: BITRATE }) },
  });
  if (!conversion.isValid) throw new Error("can't encode");
  const stop = () => void conversion.cancel();
  signal.addEventListener("abort", stop);
  try {
    await conversion.execute();
  } catch (error) {
    if (signal.aborted) throw new DOMException("Stopped", "AbortError");
    throw error;
  } finally {
    signal.removeEventListener("abort", stop);
  }
  if (!output.target.buffer) throw new Error("no output");
  return new Blob([output.target.buffer], { type: "audio/mpeg" });
}
