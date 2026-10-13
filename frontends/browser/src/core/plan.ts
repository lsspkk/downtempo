// What a download has to do: compare the shared folders' listings with the files on this device. Pure.

import type { RemoteFile } from "./onedrive";
import type { Local } from "./projects";

export type Listing = { source: string; files: RemoteFile[] };
export type Fetch = { key: string; file: RemoteFile; fresh: boolean };
export type Plan = { fetch: Fetch[]; same: number; gone: string[]; bytes: number };

/** New and changed files to fetch (a copy counts as current when its size matches and it isn't older),
 * how many are current, and the files on this device the server no longer has (never deleted). */
export function plan(local: Record<string, Local>, listings: Listing[]): Plan {
  const fetch: Fetch[] = [];
  const seen = new Set<string>();
  let same = 0;
  for (const { source, files } of listings) {
    for (const file of files) {
      const key = `${source}/${file.path}`;
      seen.add(key);
      const copy = local[key];
      if (copy && copy.size === file.size && copy.modified >= file.modified) same++;
      else fetch.push({ key, file, fresh: !copy });
    }
  }
  const listed = new Set(listings.map((l) => l.source));
  const gone = Object.keys(local).filter((key) => listed.has(key.split("/")[0]) && !seen.has(key));
  return { fetch, same, gone, bytes: fetch.reduce((sum, f) => sum + f.file.size, 0) };
}
