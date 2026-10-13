// The browser's private file system (OPFS): a project's downloaded files under
// projects/<project id>/<path>, written as they stream; storage used and "keep my files".

import { m } from "../paraglide/messages.js";

async function folder(parts: string[], create: boolean): Promise<FileSystemDirectoryHandle> {
  let dir = await navigator.storage.getDirectory();
  for (const part of parts) dir = await dir.getDirectoryHandle(part, { create });
  return dir;
}

/** "a/b/c.mp3" → ["a", "b"], "c.mp3"; names that would climb out of the project are refused. */
export function splitPath(path: string): [string[], string] {
  const parts = path.split("/").filter(Boolean);
  if (!parts.length || parts.some((p) => p === "." || p === "..")) throw new Error(m.unsafe_name({ path }));
  return [parts.slice(0, -1), parts[parts.length - 1]];
}

/** Stream a response body into the project; the old file stays until the new one is complete. */
export async function save(
  project: string,
  path: string,
  body: ReadableStream<Uint8Array>,
  onBytes: (n: number) => void,
  signal: AbortSignal,
) {
  const [dirs, name] = splitPath(path);
  const handle = await (await folder(["projects", project, ...dirs], true)).getFileHandle(name, { create: true });
  if (!("createWritable" in handle)) throw new Error(m.cant_save());
  const writable = await handle.createWritable();
  const reader = body.getReader();
  let total = 0;
  try {
    for (;;) {
      if (signal.aborted) throw new DOMException("Stopped", "AbortError");
      const { done, value } = await reader.read();
      if (done) break;
      await writable.write(value as Uint8Array<ArrayBuffer>);
      total += value.length;
      onBytes(total);
    }
    await writable.close();
  } catch (error) {
    await writable.abort().catch(() => {});
    await reader.cancel().catch(() => {});
    throw error;
  }
}

export async function open(project: string, path: string): Promise<File> {
  const [dirs, name] = splitPath(path);
  return (await (await folder(["projects", project, ...dirs], false)).getFileHandle(name)).getFile();
}

export async function removeProject(project: string) {
  const projects = await folder(["projects"], true);
  await projects.removeEntry(project, { recursive: true }).catch(() => {});
}

/** A file or a folder, with what is in it. */
export async function remove(project: string, path: string) {
  const [dirs, name] = splitPath(path);
  const dir = await folder(["projects", project, ...dirs], false).catch(() => null);
  await dir?.removeEntry(name, { recursive: true }).catch(() => {});
}

export type Usage = { used: number; allowed: number; kept: boolean };

export async function usage(): Promise<Usage> {
  const { usage = 0, quota = 0 } = await navigator.storage.estimate();
  return { used: usage, allowed: quota, kept: await navigator.storage.persisted() };
}

export const askToKeep = () => navigator.storage.persist();
