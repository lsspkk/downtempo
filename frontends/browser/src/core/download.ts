// Getting a project's files: list every shared folder, plan, then stream what's new into the device.
// One run at a time; its state is a store the page shows (progress, preview, errors, Stop).

import { m } from "../paraglide/messages.js";
import * as files from "./files";
import { group } from "./grouping";
import * as onedrive from "./onedrive";
import { type Listing, type Plan, plan } from "./plan";
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
      text: string;
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
  const total = todo.fetch.length;
  let bytes = 0;
  for (const [index, { key, file }] of todo.fetch.entries()) {
    const show = (got: number) =>
      status.set({
        phase: "downloading",
        project: projectId,
        done: index,
        total,
        bytes: bytes + got,
        allBytes: todo.bytes,
        text: file.path.split("/").pop() ?? file.path,
      });
    show(0);
    const response = await fetch(await onedrive.downloadUrl(file), { signal });
    if (!response.ok || !response.body)
      throw new Error(m.download_failed({ file: file.path, status: response.status }));
    await files.save(projectId, key, response.body, show, signal);
    bytes += file.size;
    projects.update(projectId, (p) => ({
      ...p,
      files: { ...p.files, [key]: { size: file.size, modified: file.modified } },
    }));
  }
  projects.update(projectId, (p) => ({ ...p, checked: Date.now() }));
  const parts: string[] = [total ? m.n_downloaded({ count: total }) : m.up_to_date()];
  if (todo.gone.length) parts.push(m.n_gone({ count: todo.gone.length }));
  status.set({ phase: "done", project: projectId, text: parts.join(", "), at: Date.now() });
}

function fail(projectId: string, error: unknown) {
  const stopped = error instanceof DOMException && error.name === "AbortError";
  const text = stopped ? m.stopped() : error instanceof Error ? error.message : String(error);
  status.set({ phase: "failed", project: projectId, text, signIn: error instanceof onedrive.SignInNeeded });
}
