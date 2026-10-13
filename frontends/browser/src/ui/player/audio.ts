// One recording from this device in an <audio> element: play, seek, tempo with the pitch kept
// (the browser's own playbackRate stretch), and the A–B loop held while playing.

import { useEffect, useMemo, useRef, useState } from "react";
import * as files from "../../core/files";
import type { Loop } from "../../core/practice";
import { m } from "../../paraglide/messages.js";

export type AudioState = { ready: boolean; error: string; playing: boolean; time: number; duration: number };

/** `key`: the recording to load (none: nothing plays); a new key loads it into the same <audio>. */
export function useAudio(project: string, key: string | null, rate: number, loop: Loop | null) {
  const audio = useMemo(() => new Audio(), []);
  const [state, setState] = useState<AudioState>({ ready: false, error: "", playing: false, time: 0, duration: 0 });
  const loopRef = useRef(loop);
  loopRef.current = loop;

  useEffect(() => {
    let url = "";
    let gone = false;
    setState({ ready: false, error: "", playing: false, time: 0, duration: 0 });
    if (!key) return;
    const update = () =>
      setState((s) => ({ ...s, playing: !audio.paused, time: audio.currentTime, duration: audio.duration || 0 }));
    const ready = () => setState((s) => ({ ...s, ready: true, duration: audio.duration || 0 }));
    const failed = () => setState((s) => ({ ...s, error: m.cant_play_file(), playing: false }));
    audio.addEventListener("loadedmetadata", ready);
    audio.addEventListener("play", update);
    audio.addEventListener("pause", update);
    audio.addEventListener("seeked", update);
    audio.addEventListener("error", failed);
    files
      .open(project, key)
      .then((file) => {
        if (gone) return;
        url = URL.createObjectURL(file);
        audio.src = url;
      })
      .catch(() => !gone && setState((s) => ({ ...s, error: m.file_gone() })));
    return () => {
      gone = true;
      audio.pause();
      audio.removeEventListener("loadedmetadata", ready);
      audio.removeEventListener("play", update);
      audio.removeEventListener("pause", update);
      audio.removeEventListener("seeked", update);
      audio.removeEventListener("error", failed);
      audio.removeAttribute("src");
      audio.load();
      if (url) URL.revokeObjectURL(url);
    };
  }, [audio, project, key]);

  // A new source resets playbackRate to defaultPlaybackRate, so both are set.
  useEffect(() => {
    audio.preservesPitch = true;
    audio.defaultPlaybackRate = rate;
    audio.playbackRate = rate;
  }, [audio, rate, state.ready]);

  // While playing: follow the time for the screen and jump back at the loop's end.
  useEffect(() => {
    if (!state.playing) return;
    let frame = 0;
    let shown = 0;
    const tick = (now: number) => {
      const l = loopRef.current;
      if (l?.on && audio.currentTime >= l.end) audio.currentTime = l.start;
      if (now - shown > 100) {
        shown = now;
        setState((s) => ({ ...s, time: audio.currentTime }));
      }
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [audio, state.playing]);

  const controls = useMemo(
    () => ({
      play() {
        const l = loopRef.current;
        if (l?.on && (audio.currentTime < l.start || audio.currentTime >= l.end)) audio.currentTime = l.start;
        setState((s) => ({ ...s, error: "" }));
        audio.play().catch((error: DOMException) => {
          const text = error.name === "NotAllowedError" ? m.click_first() : m.cant_play({ reason: error.message });
          setState((s) => ({ ...s, error: text }));
        });
      },
      pause: () => audio.pause(),
      seek(time: number) {
        audio.currentTime = Math.max(0, Math.min(time, audio.duration || 0));
        setState((s) => ({ ...s, time: audio.currentTime }));
      },
      now: () => audio.currentTime,
    }),
    [audio],
  );
  return { element: audio, state, ...controls, toggle: () => (audio.paused ? controls.play() : controls.pause()) };
}
