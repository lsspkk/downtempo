// The player's state and actions for one song: which recording, the sound (useAudio), tempo, loop,
// whether the loop editor is open, and the player's keys. Tempo and loop are remembered per song;
// a new song waits for Play. The parts (controls.tsx, Tempo, RecordingMenu, PositionWave, LoopEditor)
// take this object; the song page's layouts decide where they go.

import { useState } from "react";
import type { SongFile } from "../../core/grouping";
import { type Loop, remember, songMemory } from "../../core/practice";
import * as projects from "../../core/projects";
import { useKeys } from "../kit/keys";
import { useAudio } from "./audio";
import { clampTempo, TEMPO_STEP } from "./Tempo";

export type Player = ReturnType<typeof usePlayer>;

type Args = {
  project: string;
  song: string;
  recording: SongFile | null;
  recordings: SongFile[];
  pickRecording: (key: string) => void;
};

export function usePlayer({ project, song, recording, recordings, pickRecording }: Args) {
  const memory = songMemory(project, song);
  const [tempo, setTempoState] = useState(memory.tempo ?? 100);
  const [loop, setLoopState] = useState<Loop | null>(memory.loop ?? null);
  const [editing, setEditing] = useState(false);
  const audio = useAudio(project, recording?.key ?? null, tempo / 100, loop);
  const duration = audio.state.duration;

  const setTempo = (value: number | ((old: number) => number)) =>
    setTempoState((old) => {
      const next = clampTempo(typeof value === "function" ? value(old) : value);
      remember(project, song, { tempo: next });
      return next;
    });
  const setLoop = (next: Loop | null) => {
    setLoopState(next);
    remember(project, song, { loop: next });
  };

  // A at the play position (end stays if still after it), B likewise; a loop turns on once both make sense.
  const setStart = () => {
    const start = audio.now();
    const end = loop && loop.end > start + 0.2 ? loop.end : duration;
    setLoop({ start, end, on: loop?.on ?? false });
  };
  const setEnd = () => {
    const end = audio.now();
    const start = loop && loop.start < end - 0.2 ? loop.start : 0;
    setLoop({ start, end, on: true });
  };
  const toggleLoop = () => (loop ? setLoop({ ...loop, on: !loop.on }) : setEditing(true));
  /** The loop's last 2 s and the jump back to its start: the seam that most often needs a fix. */
  const hearEnd = () => {
    if (!loop) return;
    setLoop({ ...loop, on: true });
    audio.seek(Math.max(loop.start, loop.end - 2));
    audio.play();
  };
  const index = recordings.findIndex((r) => r.key === recording?.key);
  const stepRecording = (by: number) =>
    recordings.length > 1 && pickRecording(recordings[(index + by + recordings.length) % recordings.length].key);

  useKeys({
    " ": audio.toggle,
    k: audio.toggle,
    ArrowLeft: () => setTempo((t) => t - TEMPO_STEP),
    ArrowRight: () => setTempo((t) => t + TEMPO_STEP),
    ",": () => audio.seek(audio.now() - 5),
    ".": () => audio.seek(audio.now() + 5),
    j: () => audio.seek(audio.now() - 10),
    l: () => audio.seek(audio.now() + 10),
    "0": () => audio.seek(loop?.on ? loop.start : 0),
    ...Object.fromEntries([1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => [String(n), () => audio.seek((duration * n) / 10)])),
    a: setStart,
    b: setEnd,
    r: toggleLoop,
    c: () => setLoop(null),
    e: () => recording && setEditing((open) => !open),
    t: (event) => stepRecording(event.shiftKey ? -1 : 1),
  });

  return {
    project,
    recording,
    recordings,
    index,
    pickRecording,
    uploaded: (key: string) => projects.find(project)?.files[key]?.modified, // the server's change time
    audio,
    tempo,
    setTempo,
    loop,
    setLoop,
    toggleLoop,
    setStart,
    setEnd,
    hearEnd,
    editing,
    setEditing,
  };
}
