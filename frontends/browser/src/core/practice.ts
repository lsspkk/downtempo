// Practice memory per project: the last song, per song its tempo, optimal tempo, loop, recording and sheet,
// and per recording its saved loops (regions), its tempo in BPM (docs/tempo-goal.md) and where it was left.
// Kept in localStorage; keyed by song id, which comes from the title.

import { stored, useStore } from "./store";

export type Loop = { start: number; end: number; on: boolean };
export type SongMemory = {
  tempo?: number;
  goal?: number; // the optimal tempo, BPM
  playAt?: number; // the Play at switch is on: the % to go back to
  loop?: Loop | null;
  recording?: string;
  sheet?: string;
  zoom?: number; // the sheet's page width as a share of the view's
  fit?: "page" | null; // the sheet fits whole pages instead
};
export type SavedLoop = { name: string; start: number; end: number };
/** A recording's tempo at 100 % (an old memory's `estimate` flag is ignored: no estimated state now). */
export type RecordingTempo = { bpm: number };
type Memory = {
  last: Record<string, string>; // by project id
  songs: Record<string, SongMemory>; // by "project/song"
  saved: Record<string, SavedLoop[]>; // by "project/recording key"
  tempos: Record<string, RecordingTempo>; // by "project/recording key"
  positions: Record<string, number>; // seconds, by "project/recording key"
};

export const practice = stored<Memory>("downtempo-practice", {
  last: {},
  songs: {},
  saved: {},
  tempos: {},
  positions: {},
});

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

export const recordingTempo = (project: string, recording: string): RecordingTempo | null =>
  practice.get().tempos[`${project}/${recording}`] ?? null;

/** Redraws a component when any practice memory changes (a recording's tempo arrives by itself). */
export const useTempoMemory = () => useStore(practice).tempos;

export function rememberTempo(project: string, recording: string, tempo: RecordingTempo | null) {
  const key = `${project}/${recording}`;
  practice.set((m) => {
    const { [key]: _, ...rest } = m.tempos;
    return { ...m, tempos: tempo ? { ...rest, [key]: tempo } : rest };
  });
}

/** Where the recording was left (paused, another song or recording, the page closed). */
export const position = (project: string, recording: string) =>
  practice.get().positions[`${project}/${recording}`] ?? 0;

export const rememberPosition = (project: string, recording: string, seconds: number) =>
  practice.set((m) => ({
    ...m,
    positions: { ...m.positions, [`${project}/${recording}`]: Math.round(seconds * 10) / 10 },
  }));

/** A wav became an mp3 (core/download.ts): what was remembered under the old key follows it, in the
 * same step: the songs' chosen recording, the saved loops, the recording tempo, the position. */
export function moveRecording(project: string, from: string, to: string) {
  const move = <T>(all: Record<string, T>) => {
    const { [`${project}/${from}`]: value, ...rest } = all;
    return value === undefined ? all : { ...rest, [`${project}/${to}`]: value };
  };
  practice.set((m) => ({
    ...m,
    songs: Object.fromEntries(
      Object.entries(m.songs).map(([key, song]) => [
        key,
        key.startsWith(`${project}/`) && song.recording === from ? { ...song, recording: to } : song,
      ]),
    ),
    saved: move(m.saved),
    tempos: move(m.tempos),
    positions: move(m.positions),
  }));
}

/** How sheets are read on this device, for every song: the rotation (a laptop turned on the music
 * stand) and the margins trimmed from the pages (cm). */
export const sheetLook = stored<{ rotate: number; trim: number }>("downtempo-sheet", { rotate: 0, trim: 0 });

/** Everything remembered about a project: its last song, each song's tempo / loop / sheet, the regions,
 * the recordings' tempos. */
export function forget(project: string) {
  const mine = (key: string) => key.startsWith(`${project}/`);
  const keep = <T>(all: Record<string, T>) => Object.fromEntries(Object.entries(all).filter(([key]) => !mine(key)));
  practice.set((m) => ({
    last: Object.fromEntries(Object.entries(m.last).filter(([key]) => key !== project)),
    songs: keep(m.songs),
    saved: keep(m.saved),
    tempos: keep(m.tempos),
    positions: keep(m.positions),
  }));
}
