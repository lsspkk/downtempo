// The tempo in BPM for the open song (docs/tempo-goal.md#browser-app-t232), like the Python player's
// tempo_goal.py: the recording tempo (found by itself on first load, then just a number), the song's
// optimal tempo, the Play at switch (on, every recording of the song plays at the optimal tempo until the
// speed is changed by hand; remembered per song), Tap (from the 4th tap the speed
// follows, like a DAW's tap tempo) and the Metronome (a steady tick at the BPM now, playing or not).

import { useEffect, useRef, useState } from "react";
import { recordingTempo, remember, rememberTempo, songMemory, useTempoMemory } from "../../core/practice";
import type { useAudio } from "../player/audio";
import { TEMPO_MAX, TEMPO_MIN } from "../player/Tempo";
import { Click } from "./click";

const TAP_RESET = 2; // seconds without a tap start a new count
const TAP_KEEP = 8; // the BPM is the average over the last taps
const TAPS_TO_FOLLOW = 4;
const SHOW_TAPPED = 2000; // ms "108" stays on the Tap button

type Args = {
  project: string;
  song: string;
  recording: string | null;
  audio: ReturnType<typeof useAudio>;
  tempo: number; // %
  setTempo: (percent: number) => void; // exact, not rounded to the slider's steps
};

export type TempoGoal = ReturnType<typeof useTempoGoal>;

const bounded = (value: number) => Math.round(Math.min(400, Math.max(20, value)) * 10) / 10;

export function useTempoGoal({ project, song, recording, audio, tempo, setTempo }: Args) {
  useTempoMemory(); // redraw when a tempo is remembered
  const bpm = (recording && recordingTempo(project, recording)?.bpm) || null;
  const [optimal, setOptimalState] = useState<number | null>(songMemory(project, song).goal ?? null);
  const [finding, setFinding] = useState(false);
  const [failed, setFailed] = useState(false);
  const [back, setBack] = useState<number | null>(songMemory(project, song).playAt ?? null); // the % before Play at
  const [open, setOpen] = useState(false); // the BPM strip
  const [metronome, setMetronome] = useState(false);
  const [taps, setTaps] = useState<number[]>([]);
  const [tappedShown, setTappedShown] = useState(false);
  const click = useRef(new Click()).current;

  // First load of a recording without a tempo: find it in the background.
  const ready = audio.state.ready;
  useEffect(() => {
    setMetronome(false);
    setFailed(false);
    if (!recording || !ready || recordingTempo(project, recording)) return;
    let gone = false;
    setFinding(true);
    import("./estimate")
      .then(({ estimate }) => estimate(project, recording))
      .then((found) => {
        if (found && !recordingTempo(project, recording)) rememberTempo(project, recording, { bpm: found.bpm });
        if (!found && !gone) setFailed(true);
      })
      .catch(() => !gone && setFailed(true))
      .finally(() => !gone && setFinding(false));
    return () => {
      gone = true;
      setFinding(false);
    };
  }, [project, recording, ready]);

  const now = bpm ? bpm * (tempo / 100) : null;
  const ticking = metronome && !!now;
  useEffect(() => click.play(ticking ? now : null), [ticking, now]);
  useEffect(() => () => click.play(null), []);

  const optimalPercent = optimal && bpm ? (optimal / bpm) * 100 : null;
  const reachable = optimalPercent && Math.min(TEMPO_MAX, Math.max(TEMPO_MIN, Math.round(optimalPercent)));
  const atOptimal = back !== null && !!optimal;
  const setPlayAt = (value: number | null) => {
    setBack(value);
    remember(project, song, { playAt: value ?? undefined });
  };
  // While on: a new recording (or its BPM, or the optimal tempo) sets the speed; a change by hand turns
  // the switch off and the speed stays.
  const followed = useRef<number | null>(null);
  useEffect(() => {
    const changed = !!reachable && reachable !== followed.current;
    if (reachable) followed.current = reachable;
    if (!atOptimal || !reachable) return;
    if (changed) setTempo(reachable);
    else if (tempo !== reachable) setPlayAt(null);
  }, [tempo, reachable, atOptimal]);

  const setBpm = (value: number | null) =>
    recording && rememberTempo(project, recording, value ? { bpm: bounded(value) } : null);
  /** An empty field means no optimal tempo. */
  const setOptimal = (value: number | null) => {
    const next = value ? bounded(value) : null;
    setOptimalState(next);
    remember(project, song, { goal: next ?? undefined });
    if (!next) setPlayAt(null);
  };
  /** The Play at switch (X); without an optimal tempo it opens the strip, where it is set. */
  const toggleOptimal = () => {
    if (!recording) return;
    if (atOptimal) {
      setPlayAt(null);
      setTempo(back!);
    } else if (reachable) {
      setPlayAt(tempo);
      setTempo(reachable);
    } else setOpen(true);
  };

  const tap = () => {
    if (!recording) return;
    if (!bpm) return setOpen(true);
    const at = performance.now() / 1000;
    const next = [...(taps.length && at - taps[taps.length - 1] > TAP_RESET ? [] : taps), at].slice(-TAP_KEEP);
    setTaps(next);
    setTappedShown(true);
    const tapped = next.length > 1 ? (60 * (next.length - 1)) / (next[next.length - 1] - next[0]) : null;
    if (tapped && next.length >= TAPS_TO_FOLLOW) setTempo((tapped / bpm) * 100);
  };
  useEffect(() => {
    if (!tappedShown) return;
    const timer = setTimeout(() => setTappedShown(false), SHOW_TAPPED);
    return () => clearTimeout(timer);
  }, [taps, tappedShown]);
  const tapped = taps.length > 1 ? (60 * (taps.length - 1)) / (taps[taps.length - 1] - taps[0]) : null;

  return {
    bpm,
    now,
    optimal,
    optimalPercent,
    atOptimal,
    finding,
    failed,
    open,
    setOpen,
    setBpm,
    setOptimal,
    toggleOptimal,
    metronome: ticking,
    toggleMetronome: () => setMetronome(!ticking),
    tap,
    taps: tappedShown ? taps.length : 0,
    tapped: tappedShown ? tapped : null, // BPM as heard, while "108" is shown
  };
}
