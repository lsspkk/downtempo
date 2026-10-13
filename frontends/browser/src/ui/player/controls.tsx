// The player's small parts, each taking the Player (usePlayer): play / pause, the time, loop on / off,
// the loop editor's button, and the player's problem line. The layouts place them.

import { Maximize2, Pause, Play, Repeat } from "lucide-react";
import { clock } from "../../core/format";
import { m } from "../../paraglide/messages.js";
import { IconButton } from "../kit/Button";
import type { Player } from "./usePlayer";

/** A filled indigo circle; the play triangle sits a little right of centre, so it looks centred. */
export function PlayButton({ player, className = "size-11 sm:size-9" }: { player: Player; className?: string }) {
  const playing = player.audio.state.playing;
  const label = playing ? m.pause() : m.play();
  return (
    <button
      type="button"
      onClick={player.audio.toggle}
      disabled={!player.audio.state.ready}
      title={`${label} (Space)`}
      aria-label={label}
      className={`inline-flex shrink-0 items-center justify-center rounded-full bg-accent-600 text-white transition-colors hover:bg-accent-700 disabled:bg-zinc-300 dark:disabled:bg-zinc-700 ${className}`}
    >
      {playing ? <Pause size={20} fill="currentColor" /> : <Play size={20} fill="currentColor" className="ml-0.5" />}
    </button>
  );
}

export const PlayTime = ({ player }: { player: Player }) => (
  <span className="shrink-0 text-xs text-zinc-500 tabular-nums">
    {clock(player.audio.state.time)} / {clock(player.audio.state.duration)}
  </span>
);

/** Repeat, amber when the loop is on; with no loop yet it opens the loop editor. */
export function LoopButton({ player }: { player: Player }) {
  const on = !!player.loop?.on;
  return (
    <IconButton
      label={m.loop_toggle()}
      active={on}
      onClick={player.toggleLoop}
      className={on ? "!text-amber-500" : "!text-zinc-400 dark:!text-zinc-500"}
    >
      <Repeat size={20} />
    </IconButton>
  );
}

export function EditorButton({ player }: { player: Player }) {
  return (
    <IconButton label={m.edit_loop()} active={player.editing} onClick={() => player.setEditing(!player.editing)}>
      <Maximize2 size={20} />
    </IconButton>
  );
}

export const PlayerError = ({ player }: { player: Player }) =>
  player.audio.state.error ? (
    <p className="shrink-0 bg-white px-3 py-1 text-sm text-red-700 dark:bg-zinc-900 dark:text-red-400">
      ⚠ {player.audio.state.error}
    </p>
  ) : null;
