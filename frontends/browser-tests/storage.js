// The browser's private file system (OPFS): save a download, list, open, delete; quota and persist.

const folder = () => navigator.storage.getDirectory();

/** Stream a response into the private file system; onBytes(n) reports progress. */
export async function save(name, response, onBytes) {
  const handle = await (await folder()).getFileHandle(name, { create: true });
  if (!handle.createWritable) throw new Error("This browser can't write here (no createWritable).");
  const writable = await handle.createWritable();
  const reader = response.body.getReader();
  let total = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      await writable.write(value);
      total += value.length;
      onBytes(total);
    }
    await writable.close();
  } catch (error) {
    await writable.abort();
    throw error;
  }
}

export async function list() {
  const files = [];
  for await (const handle of (await folder()).values()) {
    if (handle.kind === "file") files.push(await handle.getFile());
  }
  return files.sort((a, b) => a.name.localeCompare(b.name));
}

export async function open(name) {
  return (await (await folder()).getFileHandle(name)).getFile();
}

export async function remove(name) {
  await (await folder()).removeEntry(name);
}

export async function usage() {
  const { usage, quota } = await navigator.storage.estimate();
  return { usage, quota, kept: await navigator.storage.persisted() };
}

export const askToKeep = () => navigator.storage.persist();
