// Practice memory per project: the last song, per song its tempo, loop, recording and sheet, and per
// recording its saved loops (regions).
// Kept in localStorage; keyed by song id, which comes from the title.

import { stored } from "./store";

export type Loop = { start: number; end: number; on: boolean };
export type SongMemory = {
  tempo?: number;
  loop?: Loop | null;
  recording?: string;
  sheet?: string;
  zoom?: number; // the sheet's page width as a share of the view's
  fit?: "page" | null; // the sheet fits whole pages instead
  trim?: number; // cm cut from every side of the sheet's pages
};
export type SavedLoop = { name: string; start: number; end: number };
type Memory = {
  last: Record<string, string>; // by project id
  songs: Record<string, SongMemory>; // by "project/song"
  saved: Record<string, SavedLoop[]>; // by "project/recording key"
};

export const practice = stored<Memory>("downtempo-practice", { last: {}, songs: {}, saved: {} });

export const songMemory = (project: string, song: string): SongMemory =>
  practice.get().songs[`${project}/${song}`] ?? {};

export function remember(project: string, song: string, change: Partial<SongMemory>) {
  practice.set((m) => {
    const key = `${project}/${song}`;
    return { ...m, songs: { ...m.songs, [key]: { ...m.songs[key], ...change } } };
  });
}

export const lastSong = (project: string) => practice.get().last[project] ?? null;

export const rememberLast = (project: string, song: string) =>
  practice.set((m) => ({ ...m, last: { ...m.last, [project]: song } }));

export const savedLoops = (project: string, recording: string) => practice.get().saved[`${project}/${recording}`] ?? [];

function changeSaved(project: string, recording: string, change: (list: SavedLoop[]) => SavedLoop[]) {
  const key = `${project}/${recording}`;
  practice.set((m) => ({ ...m, saved: { ...m.saved, [key]: change(m.saved[key] ?? []) } }));
}

export const saveLoop = (project: string, recording: string, loop: SavedLoop) =>
  changeSaved(project, recording, (list) => [...list, loop]);

export const deleteLoop = (project: string, recording: string, index: number) =>
  changeSaved(project, recording, (list) => list.filter((_, i) => i !== index));

/** The sheet's rotation on this device (a laptop turned on the music stand), for every song. */
export const sheetLook = stored<{ rotate: number }>("downtempo-sheet", { rotate: 0 });

/** Everything remembered about a project: its last song, each song's tempo / loop / sheet, the regions. */
export function forget(project: string) {
  const mine = (key: string) => key.startsWith(`${project}/`);
  const keep = <T>(all: Record<string, T>) => Object.fromEntries(Object.entries(all).filter(([key]) => !mine(key)));
  practice.set((m) => ({
    last: Object.fromEntries(Object.entries(m.last).filter(([key]) => key !== project)),
    songs: keep(m.songs),
    saved: keep(m.saved),
  }));
}
