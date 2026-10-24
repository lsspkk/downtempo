// One recording from this device, played by Stretch (stretch.ts): decoded into memory, tempo with the
// pitch kept, the A–B loop held inside the audio. Gives the player its state (ready, playing, time,
// duration), its actions, the waveform's peaks and `onTime`, which the waveforms follow at full speed.
// Each recording opens where it was left: the position is remembered on pause, on leaving it and when
// the page closes.

import { useEffect, useMemo, useRef, useState } from "react";
import * as files from "../../core/files";
import { type Loop, position, rememberPosition } from "../../core/practice";
import { m } from "../../paraglide/messages.js";
import { type Peaks, Stretch } from "./stretch";

export type AudioState = { ready: boolean; error: string; playing: boolean; time: number; duration: number };
type TimeListener = (time: number, playing: boolean) => void;

const SCREEN_MS = 100; // how often `state.time` (the clock text) is refreshed

/** `key`: the recording to load (none: nothing plays); a new key loads it, the old one is let go. */
export function useAudio(project: string, key: string | null, rate: number, loop: Loop | null) {
  const [state, setState] = useState<AudioState>({ ready: false, error: "", playing: false, time: 0, duration: 0 });
  const [peaks, setPeaks] = useState<Peaks | null>(null);
  const stretch = useRef<Stretch | null>(null);
  const listeners = useRef(new Set<TimeListener>());
  const loopRef = useRef(loop);
  loopRef.current = loop;
  const latest = useRef({ rate, loop });
  latest.current = { rate, loop };
  const where = useRef({ project, key });
  where.current = { project, key };
  /** Where a recording was left, for its next opening. */
  const remember = (project: string, key: string | null) => {
    const s = stretch.current;
    if (s && key) rememberPosition(project, key, s.time() < s.duration - 1 ? s.time() : 0);
  };

  useEffect(() => {
    let gone = false;
    let shown = 0;
    setState({ ready: false, error: "", playing: false, time: 0, duration: 0 });
    setPeaks(null);
    if (!key) return;
    const handlers = {
      onTime(time: number, playing: boolean) {
        listeners.current.forEach((listener) => listener(time, playing));
        const now = performance.now();
        if (playing && now - shown < SCREEN_MS) return;
        shown = now;
        setState((s) => ({ ...s, time, playing }));
      },
      onEnded: () => setState((s) => ({ ...s, playing: false })),
    };
    files
      .open(project, key)
      .then((file) => Stretch.open(file, handlers))
      .then((opened) => {
        if (gone) return opened.close();
        stretch.current = opened;
        opened.set(latest.current.rate, latest.current.loop);
        const left = position(project, key);
        if (left > 0 && left < opened.duration - 1) opened.seek(left);
        setPeaks(opened.peaks);
        setState((s) => ({ ...s, ready: true, duration: opened.duration, time: opened.time() }));
      })
      .catch((error: Error) => {
        if (gone) return;
        const text = error.name === "NotFoundError" ? m.file_gone() : m.cant_play_file();
        setState((s) => ({ ...s, error: text }));
      });
    const leave = () => remember(project, key); // this effect's recording, not the next one's
    window.addEventListener("pagehide", leave);
    return () => {
      gone = true;
      window.removeEventListener("pagehide", leave);
      leave();
      stretch.current?.close();
      stretch.current = null;
    };
  }, [project, key]);

  useEffect(() => {
    stretch.current?.set(rate, loop);
  }, [rate, loop?.on, loop?.start, loop?.end, state.ready]);

  const controls = useMemo(() => {
    const play = async () => {
      const s = stretch.current;
      if (!s) return;
      setState((st) => ({ ...st, error: "" }));
      const l = loopRef.current;
      if (l?.on && (s.time() < l.start || s.time() >= l.end)) s.seek(l.start);
      try {
        if (!(await s.play())) setState((st) => ({ ...st, error: m.click_first() }));
        else setState((st) => ({ ...st, playing: true }));
      } catch (error) {
        setState((st) => ({ ...st, error: m.cant_play({ reason: (error as Error).message }) }));
      }
    };
    const pause = () => {
      stretch.current?.pause();
      remember(where.current.project, where.current.key);
      setState((st) => ({ ...st, playing: false }));
    };
    return {
      play,
      pause,
      toggle: () => (stretch.current?.isPlaying() ? pause() : void play()),
      seek(time: number) {
        stretch.current?.seek(time);
        setState((st) => ({ ...st, time: stretch.current?.time() ?? 0 }));
      },
      now: () => stretch.current?.time() ?? 0,
      /** The waveforms' cursor: called with the time on every update; returns the way to stop. */
      onTime(listener: TimeListener) {
        listeners.current.add(listener);
        return () => void listeners.current.delete(listener);
      },
    };
  }, []);
  return { state, peaks, ...controls };
}
