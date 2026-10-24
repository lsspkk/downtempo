// What a download has to do: compare the shared folders' listings with the files on this device. Pure.
// A server's wav is kept as an mp3 under its own key (core/compress.ts, docs/compress.md).

import { storedAs } from "./compress";
import type { RemoteFile } from "./onedrive";
import type { Local } from "./projects";

export type Listing = { source: string; files: RemoteFile[] };
/** `key`: where it is stored; `listed`: the server's name, which differs for a wav kept as mp3. */
export type Fetch = { key: string; listed: string; file: RemoteFile; fresh: boolean };
export type Plan = { fetch: Fetch[]; compress: Fetch[]; same: number; gone: string[]; bytes: number };

const current = (copy: Local | undefined, file: RemoteFile, sameSize = true) =>
  !!copy && (!sameSize || copy.size === file.size) && copy.modified >= file.modified;

/** New and changed files to fetch, smallest first (a copy counts as current when its size matches and it isn't older;
 * an mp3 made from a wav by its time alone), wavs on this device to make into mp3 without fetching
 * them again, how many are current, and the files the server no longer has (never deleted). */
export function plan(local: Record<string, Local>, listings: Listing[]): Plan {
  const fetch: Fetch[] = [];
  const compress: Fetch[] = [];
  const seen = new Set<string>();
  let same = 0;
  for (const { source, files } of listings) {
    const names = new Set(files.map((f) => f.path.toLowerCase()));
    for (const file of files) {
      const listed = `${source}/${file.path}`;
      const key = `${source}/${storedAs(file.path, names)}`;
      seen.add(listed).add(key);
      const item = { key, listed, file, fresh: !local[key] && !local[listed] };
      if (current(local[key], file, key === listed)) same++;
      else if (key !== listed && current(local[listed], file)) compress.push(item);
      else fetch.push(item);
    }
  }
  const sources = new Set(listings.map((l) => l.source));
  const gone = Object.keys(local).filter((key) => sources.has(key.split("/")[0]) && !seen.has(key));
  // Smallest first: sheets and short takes are usable while the long recordings still come.
  const smallFirst = (a: Fetch, b: Fetch) => a.file.size - b.file.size;
  fetch.sort(smallFirst);
  compress.sort(smallFirst);
  return { fetch, compress, same, gone, bytes: fetch.reduce((sum, f) => sum + f.file.size, 0) };
}
