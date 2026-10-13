// Files → songs by their names: a lite port of the Python song grouping
// (src/downtempo/names.py, matching.py, suggesting.py, arranging.py; docs/song-grouping.md).
// Here every suggestion simply becomes a song: no sorting memory, no To sort screen. Pure.

import { m } from "../paraglide/messages.js";

const NOISE = new Set(
  (
    "chords soinnut sointu lyrics sanat sheet notes nuotit nuotti score partituuri melody melodia demo live mix " +
    "master rehearsal harjoitus harjoitukset treeni part parts stemma voice ääni bass basso guitar kitara fiddle " +
    "violin viulu accordion harmonikka piano drums rummut vocals laulu soprano sopraano alto altto tenor tenori " +
    "pohjat pohja taustat backing karaoke instrumental"
  ).split(" "),
);
const TYPES = new Set(
  (
    "audio mp3 wav pdf sheets nuotit notes scores old vanhat arkisto archive misc sekalaiset sekalaista uudet " +
    "muut other set setti keikka gig recordings äänitykset tallenteet"
  ).split(" "),
);
const JUNK = new Set("scan img image document untitled nimetön new recording tallenne track audio".split(" "));
const VERSION_WORDS = new Set(["final", "uusi", "new"]);
const TAKE_WORDS = new Set(["take", "otto", "ver", "version", "v"]);
const VERSION_FORM = /^(?:v|ver|version|take|otto)\d+$/;
const MUSICAL_KEY = /^[A-G][#b]?m?$/; // only counts when written with a capital
const SPECIAL =
  /(?<bracket>[(\[{][^)\]}]*[)\]}])|(?<iso>(?<!\d)\d{4}-\d{2}-\d{2}(?!\d))|(?<compact>(?<!\d)20\d{6}(?!\d))|(?<dmy>(?<![\d.])\d{1,2}\.\d{1,2}(?:\.(?:\d{4}|\d{2}))?(?!\d))/gu;
const SEPARATORS = /[\s_.\-+,;:]+/u;
const CAMEL = /(?<=[a-zåäö])(?=[A-ZÅÄÖ])/u;
const AUDIO = /\.(mp3|wav)$/i;

export type Cleaned = { key: string; title: string; extras: string[]; tags: string[]; date: string | null };
type Item = { kind: "word" | "tag" | "date" | "number" | "version"; text: string };

const fold = (text: string) => text.normalize("NFC").toLowerCase();

/** `clean("Harbour_Waltz - CHORDS 2026-01-15")` → key "harbour waltz", extras "CHORDS", "2026-01-15". */
export function clean(name: string): Cleaned {
  const text = name.normalize("NFC");
  const items: Item[] = [];
  let date: string | null = null;
  let position = 0;
  for (const match of text.matchAll(SPECIAL)) {
    const groups = match.groups ?? {};
    const when = readDate(groups);
    if (when === false) continue;
    addWords(items, text.slice(position, match.index));
    let inner = match[0];
    if (groups.bracket) inner = inner.slice(1, -1).trim();
    if (inner) items.push({ kind: groups.bracket ? "tag" : "date", text: inner });
    date ??= when;
    position = match.index + match[0].length;
  }
  addWords(items, text.slice(position));
  markAnywhere(items);
  stripTrailing(items);
  let kept = items.filter((i) => i.kind === "word").map((i) => i.text);
  if (kept.every((w) => JUNK.has(fold(w).replace(/\d+$/, "")))) kept = [];
  return {
    key: kept.map((w) => (w === "&" ? "and" : fold(w))).join(" "),
    title: kept.join(" "),
    extras: items.filter((i) => i.kind !== "word").map((i) => i.text),
    tags: items.filter((i) => i.kind === "tag").map((i) => i.text),
    date,
  };
}

/** A date-like match's ISO date, null for a bracket or a day without a year, false when not a date. */
function readDate(groups: Record<string, string | undefined>): string | null | false {
  const iso = (y: number, m: number, d: number) => {
    const day = new Date(Date.UTC(y, m - 1, d));
    return day.getUTCMonth() === m - 1 && day.getUTCDate() === d ? day.toISOString().slice(0, 10) : false;
  };
  if (groups.bracket) return null;
  if (groups.iso) {
    const [y, m, d] = groups.iso.split("-").map(Number);
    return iso(y, m, d);
  }
  if (groups.compact) {
    const t = groups.compact;
    return iso(+t.slice(0, 4), +t.slice(4, 6), +t.slice(6));
  }
  const [d, m, y] = (groups.dmy ?? "").split(".").map(Number);
  const when = iso(y === undefined ? 2000 : y < 100 ? y + 2000 : y, m, d);
  return when === false ? false : y === undefined ? null : when;
}

function addWords(items: Item[], text: string) {
  for (let raw of text.split(SEPARATORS)) {
    raw = raw.replace(/^['"!?]+|['"!?]+$/g, "");
    if (!raw) continue;
    for (const word of /^\p{L}+$/u.test(raw) ? raw.split(CAMEL) : [raw]) items.push({ kind: "word", text: word });
  }
}

function markAnywhere(items: Item[]) {
  items.forEach((item, i) => {
    if (item.kind !== "word") return;
    const folded = fold(item.text);
    const next = items[i + 1];
    if (NOISE.has(folded)) item.kind = "tag";
    else if (VERSION_FORM.test(folded)) item.kind = "version";
    else if (TAKE_WORDS.has(folded) && next?.kind === "word" && /^\d+$/.test(next.text)) {
      item.kind = next.kind = "version";
    }
  });
}

/** From the end: a number, `final` / `uusi` / `new`, a capital musical key (and its `in`). */
function stripTrailing(items: Item[]) {
  for (;;) {
    const words = items.filter((i) => i.kind === "word");
    const last = words[words.length - 1];
    if (!last) return;
    if (/^\d+$/.test(last.text)) last.kind = "number";
    else if (words.length > 1 && VERSION_WORDS.has(fold(last.text))) last.kind = "version";
    else if (words.length > 1 && MUSICAL_KEY.test(last.text)) {
      last.kind = "tag";
      const before = words[words.length - 2];
      if (words.length > 2 && fold(before.text) === "in") before.kind = "tag";
    } else return;
  }
}

const letters = (key: string) => key.replaceAll(" ", "");

/** How many letters may differ: 0 under 5 letters, 1 from 5, 2 from 10. */
export const tolerance = (count: number) => (count < 5 ? 0 : count < 10 ? 1 : 2);

/** Levenshtein distance, or `limit + 1` when it is more than `limit`. */
export function editDistance(a: string, b: string, limit: number): number {
  if (Math.abs(a.length - b.length) > limit) return limit + 1;
  let previous = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const current = [i];
    for (let j = 1; j <= b.length; j++) {
      current.push(Math.min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)));
    }
    if (Math.min(...current) > limit) return limit + 1;
    previous = current;
  }
  return Math.min(previous[b.length], limit + 1);
}

type Hit = { magnet: string; start: number; end: number; size: number; distance: number };

/** Every run of a magnet's words in `key`, and the whole key, within the tolerance; the longest magnet wins. */
function bestHits(key: string, magnets: string[]): Hit[] {
  const parts = key.split(" ").filter(Boolean);
  const hits: Hit[] = [];
  for (const magnet of magnets) {
    const size = magnet.split(" ").length;
    const limit = tolerance(letters(magnet).length);
    const spans = new Set([`0,${parts.length}`]);
    for (let i = 0; i + size <= parts.length; i++) spans.add(`${i},${i + size}`);
    for (const span of spans) {
      const [start, end] = span.split(",").map(Number);
      const distance = editDistance(parts.slice(start, end).join(""), letters(magnet), limit);
      if (distance <= limit) hits.push({ magnet, start, end, size: end - start, distance });
    }
  }
  const outer = hits.filter((h) => !hits.some((o) => o.start <= h.start && h.end <= o.end && o.size > h.size));
  return outer.filter((h) => !outer.some((o) => o.start === h.start && o.end === h.end && o.distance < h.distance));
}

/** One key contains the other (whole words, within the tolerance). */
export const related = (a: string, b: string) =>
  !!a && !!b && (bestHits(b, [a]).length > 0 || bestHits(a, [b]).length > 0);

const isTypeName = (key: string) => !!key && (TYPES.has(key) || key.split(" ").every((w) => TYPES.has(w)));

// Songs

export type FileIn = { key: string; modified: string }; // key: "<source id>/<path on the server>"
export type SongFile = { key: string; label: string };
export type Song = { id: string; title: string; audio: SongFile[]; sheets: SongFile[] };
export const OTHER = "other-files";

type Named = FileIn & { folder: string; stem: string; name: Cleaned; audio: boolean };
type Seed = { title: string; key: string; folder: string; files: Named[] };

const folderName = (folder: string) => folder.split("/").slice(1).pop() ?? "";

function named(file: FileIn): Named {
  const slash = file.key.lastIndexOf("/");
  const stem = file.key.slice(slash + 1).replace(/\.[^.]+$/, "");
  return { ...file, folder: file.key.slice(0, slash), stem, name: clean(stem), audio: AUDIO.test(file.key) };
}

/** The songs these files make, in title order; files whose name says nothing go to "Other files". */
export function group(input: FileIn[]): Song[] {
  const all = input.map(named).sort((a, b) => a.key.localeCompare(b.key));
  const seeds = songFolders(all);
  const taken = new Set(seeds.flatMap((s) => s.files.map((f) => f.key)));
  const byKey = new Map(seeds.map((s) => [s.key, s]));
  const loose: Named[] = [];
  const rest: Named[] = [];
  for (const file of all.filter((f) => !taken.has(f.key))) {
    if (!file.name.key) {
      loose.push(file);
      continue;
    }
    const found = [...new Set(bestHits(file.name.key, [...byKey.keys()]).map((h) => h.magnet))];
    if (found.length === 1) byKey.get(found[0])!.files.push(file);
    else if (found.length) loose.push(file);
    else rest.push(file);
  }
  const songs = [...seeds, ...groupByKey(rest)].sort((a, b) => a.title.localeCompare(b.title));
  if (loose.length) songs.push({ title: m.other_files(), key: "", folder: "", files: loose });
  const ids = new Set<string>();
  return songs.map((seed) => arrange(seed, uniqueId(seed.key ? slug(seed.title) : OTHER, ids)));
}

/** Folders with a meaningful name whose direct files mostly agree with it. */
function songFolders(files: Named[]): Seed[] {
  const byFolder = new Map<string, Named[]>();
  for (const file of files) byFolder.set(file.folder, [...(byFolder.get(file.folder) ?? []), file]);
  const seeds = new Map<string, Seed>();
  for (const [folder, members] of [...byFolder].sort(([a], [b]) => a.localeCompare(b))) {
    const name = folderName(folder);
    const cleaned = name ? clean(name) : null;
    if (!cleaned?.key || isTypeName(cleaned.key)) continue;
    const agree = members.filter((m) => !m.name.key || related(m.name.key, cleaned.key)).length;
    if (agree < members.length - agree) continue;
    const seed = seeds.get(cleaned.key) ?? { title: cleaned.title, key: cleaned.key, folder, files: [] };
    seed.files.push(...members);
    seeds.set(cleaned.key, seed);
  }
  return [...seeds.values()];
}

/** Same key within the tolerance → one song, titled with the most common spelling. */
function groupByKey(files: Named[]): Seed[] {
  const clusters: Seed[] = [];
  for (const file of [...files].sort((a, b) => a.name.key.localeCompare(b.name.key) || a.key.localeCompare(b.key))) {
    const cluster = clusters.find((c) => {
      const limit = tolerance(letters(c.key).length);
      return editDistance(letters(file.name.key), letters(c.key), limit) <= limit;
    });
    if (cluster) cluster.files.push(file);
    else clusters.push({ title: "", key: file.name.key, folder: "", files: [file] });
  }
  for (const cluster of clusters) {
    const counts = new Map<string, number>();
    for (const f of cluster.files) counts.set(f.name.title, (counts.get(f.name.title) ?? 0) + 1);
    cluster.title = [...counts].sort(([a, n], [b, m]) => m - n || a.localeCompare(b))[0][0];
  }
  return clusters;
}

function arrange(seed: Seed, id: string): Song {
  const own = (f: Named) => f.folder === seed.folder || (!!seed.key && clean(folderName(f.folder)).key === seed.key);
  const label = (f: Named) => {
    let folder = own(f) ? "" : folderName(f.folder);
    const cleaned = clean(folder);
    if (folder && (isTypeName(cleaned.key) || !(cleaned.key || cleaned.extras.length))) folder = "";
    return [folder, f.name.extras.join(" ")].filter(Boolean).join(" · ") || f.stem;
  };
  const when = (f: Named) => f.name.date ?? f.modified.slice(0, 10);
  const audio = seed.files
    .filter((f) => f.audio)
    .map((f) => ({
      f,
      rank: [f.name.key === seed.key && !f.name.extras.length ? 0 : 1, own(f) ? 0 : 1, f.name.extras.length],
    }))
    .sort(
      (a, b) =>
        a.rank[0] - b.rank[0] ||
        a.rank[1] - b.rank[1] ||
        a.rank[2] - b.rank[2] ||
        when(a.f).localeCompare(when(b.f)) ||
        a.f.key.localeCompare(b.f.key),
    )
    .map(({ f }) => ({ key: f.key, label: label(f) }));
  const sheets = seed.files
    .filter((f) => !f.audio)
    .sort((a, b) => when(b).localeCompare(when(a)) || a.key.localeCompare(b.key))
    .map((f) => ({ key: f.key, label: label(f) }));
  return { id, title: seed.title, audio, sheets };
}

export function slug(title: string): string {
  return (
    title
      .normalize("NFKD")
      .replace(/\p{M}/gu, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "") || "song"
  );
}

function uniqueId(base: string, ids: Set<string>): string {
  let id = base;
  for (let n = 2; ids.has(id); n++) id = `${base}-${n}`;
  ids.add(id);
  return id;
}
