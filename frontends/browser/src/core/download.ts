// Getting a project's files: list every shared folder, plan, then stream what's new into the device.
// Wavs are kept as mp3 (docs/compress.md): new and changed ones are encoded after the download, ones
// already on the device without downloading them again. One run at a time; its state is a store the
// page shows (progress, preview, errors, Stop).

import { m } from "../paraglide/messages.js";
import { toMp3 } from "./compress";
import * as files from "./files";
import { group } from "./grouping";
import * as onedrive from "./onedrive";
import { type Fetch, type Listing, type Plan, plan } from "./plan";
import { moveRecording } from "./practice";
import * as projects from "./projects";
import { memory } from "./store";

export type Preview = { project: string; plan: Plan; songs: number; files: number };
export type Status =
  | { phase: "idle" }
  | { phase: "listing"; project: string; text: string }
  | { phase: "preview"; preview: Preview }
  | {
      phase: "downloading";
      project: string;
      done: number;
      total: number;
      bytes: number;
      allBytes: number;
      text: string; // the file's name
      compressing: boolean;
    }
  | { phase: "done"; project: string; text: string; at: number }
  | { phase: "failed"; project: string; text: string; signIn: boolean };

export const status = memory<Status>({ phase: "idle" });
let stopper: AbortController | null = null;

export const busy = () => ["listing", "downloading"].includes(status.get().phase);

/** List the project's folders. A project with nothing on the device first shows a preview
 * ("about 12 songs from 31 files") and waits for `download`; otherwise it downloads at once. */
export async function check(projectId: string) {
  if (busy()) return;
  const project = projects.find(projectId);
  if (!project?.sources.length) return;
  stopper = new AbortController();
  const signal = stopper.signal;
  try {
    const listings: Listing[] = [];
    for (const source of project.sources) {
      status.set({ phase: "listing", project: projectId, text: m.opening_share() });
      const share = await onedrive.listShare(source.link, source.folders ?? [], source.skip ?? [], (folder) =>
        status.set({ phase: "listing", project: projectId, text: m.looking_in({ folder }) }),
      );
      if (signal.aborted) throw new DOMException("Stopped", "AbortError");
      projects.update(projectId, (p) => ({
        ...p,
        sources: p.sources.map((s) => (s.id === source.id ? { ...s, name: share.name } : s)),
      }));
      listings.push({ source: source.id, files: share.files });
    }
    const todo = plan(projects.find(projectId)?.files ?? {}, listings);
    const all = listings.flatMap((l) => l.files.map((f) => ({ key: `${l.source}/${f.path}`, modified: f.modified })));
    if (!Object.keys(project.files).length && todo.fetch.length) {
      const songs = group(all).filter((s) => s.id !== "other-files").length;
      status.set({ phase: "preview", preview: { project: projectId, plan: todo, songs, files: all.length } });
      return;
    }
    await run(projectId, todo, signal);
  } catch (error) {
    fail(projectId, error);
  }
}

export async function download(preview: Preview) {
  stopper = new AbortController();
  try {
    await run(preview.project, preview.plan, stopper.signal);
  } catch (error) {
    fail(preview.project, error);
  }
}

export function stop() {
  stopper?.abort();
}

export function dismiss() {
  if (!busy()) status.set({ phase: "idle" });
}

async function run(projectId: string, todo: Plan, signal: AbortSignal) {
  const total = todo.compress.length + todo.fetch.length;
  let bytes = 0;
  let kept = 0; // wavs that couldn't be encoded: kept as wavs, tried again next time
  const show = (index: number, item: Fetch, got: number, compressing: boolean) =>
    status.set({
      phase: "downloading",
      project: projectId,
      done: index,
      total,
      bytes: bytes + got,
      allBytes: todo.bytes,
      text: item.file.path.split("/").pop() ?? item.file.path,
      compressing,
    });
  // Wavs already here first: no download, and the space comes back soonest.
  for (const [index, item] of todo.compress.entries()) {
    show(index, item, 0, true);
    const mp3 = await encode(await files.open(projectId, item.listed), signal);
    if (mp3) await keepMp3(projectId, item, mp3, signal);
    else kept++;
  }
  for (const [n, item] of todo.fetch.entries()) {
    const index = todo.compress.length + n;
    show(index, item, 0, false);
    const { file } = item;
    const response = await fetch(await onedrive.downloadUrl(file), { signal });
    if (!response.ok || !response.body)
      throw new Error(m.download_failed({ file: file.path, status: response.status }));
    if (item.key === item.listed) {
      await files.save(projectId, item.key, response.body, (got) => show(index, item, got, false), signal);
      record(projectId, item.key, file.size, file.modified);
    } else {
      const wav = await collect(response.body, (got) => show(index, item, got, false), signal);
      show(index, item, file.size, true);
      const mp3 = await encode(wav, signal);
      if (mp3) await keepMp3(projectId, item, mp3, signal);
      else {
        kept++;
        await files.save(projectId, item.listed, wav.stream(), () => {}, signal);
        record(projectId, item.listed, file.size, file.modified);
      }
    }
    bytes += file.size;
  }
  projects.update(projectId, (p) => ({ ...p, checked: Date.now() }));
  const parts: string[] = [];
  if (todo.fetch.length || !total) parts.push(total ? m.n_downloaded({ count: todo.fetch.length }) : m.up_to_date());
  if (todo.compress.length) parts.push(m.n_compressed({ count: todo.compress.length - kept }));
  if (kept) parts.push(m.n_kept_wav({ count: kept }));
  if (todo.gone.length) parts.push(m.n_gone({ count: todo.gone.length }));
  status.set({ phase: "done", project: projectId, text: parts.join(", "), at: Date.now() });
}

const record = (projectId: string, key: string, size: number, modified: string) =>
  projects.update(projectId, (p) => ({ ...p, files: { ...p.files, [key]: { size, modified } } }));

/** A response body as a Blob, with progress; the whole wav is needed before encoding. */
async function collect(body: ReadableStream<Uint8Array>, onBytes: (n: number) => void, signal: AbortSignal) {
  const parts: Uint8Array<ArrayBuffer>[] = [];
  const reader = body.getReader();
  let total = 0;
  try {
    for (;;) {
      signal.throwIfAborted();
      const { done, value } = await reader.read();
      if (done) break;
      parts.push(value as Uint8Array<ArrayBuffer>);
      total += value.length;
      onBytes(total);
    }
  } catch (error) {
    await reader.cancel().catch(() => {});
    throw error;
  }
  return new Blob(parts, { type: "audio/wav" });
}

/** The mp3, or null when the wav can't be encoded (it stays a wav); a Stop goes on up. */
async function encode(wav: Blob, signal: AbortSignal): Promise<Blob | null> {
  try {
    return await toMp3(wav, signal);
  } catch (error) {
    if (signal.aborted) throw error;
    console.warn("Downtempo: kept as wav:", error);
    return null;
  }
}

/** Save the mp3 whole, then in one step: the project lists it instead of the wav and the practice
 * memory follows; then the wav leaves the device. */
async function keepMp3(projectId: string, item: Fetch, mp3: Blob, signal: AbortSignal) {
  await files.save(projectId, item.key, mp3.stream(), () => {}, signal);
  const hadWav = !!projects.find(projectId)?.files[item.listed];
  projects.update(projectId, (p) => {
    const { [item.listed]: _, ...rest } = p.files;
    return { ...p, files: { ...rest, [item.key]: { size: mp3.size, modified: item.file.modified } } };
  });
  if (hadWav) {
    moveRecording(projectId, item.listed, item.key);
    await files.remove(projectId, item.listed);
  }
}

function fail(projectId: string, error: unknown) {
  const stopped = error instanceof DOMException && error.name === "AbortError";
  const text = stopped ? m.stopped() : error instanceof Error ? error.message : String(error);
  status.set({ phase: "failed", project: projectId, text, signIn: error instanceof onedrive.SignInNeeded });
}
