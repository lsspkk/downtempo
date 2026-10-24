// Which recording plays. Two triggers for one menu: "♪ Recording 1/2" in small type (with a pointer) or
// a round ♪ (a phone, as the other buttons of its top line); the menu, headed "Recording", has a row per
// recording: ✓ on the current one, its name, its recording tempo and the date it was uploaded. With a
// pointer, a single recording is plain text. T steps through them too.

import { Music } from "lucide-react";
import { day } from "../../core/format";
import { recordingTempo, useTempoMemory } from "../../core/practice";
import { m } from "../../paraglide/messages.js";
import { IconButton } from "../kit/Button";
import { DropDown, MenuItem, MenuLabel } from "../kit/DropDown";
import type { Player } from "./usePlayer";

export function RecordingMenu({ player, round = false }: { player: Player; round?: boolean }) {
  useTempoMemory(); // a recording tempo found meanwhile shows in the rows
  const { recordings, recording, index } = player;
  const name = m.audio_n({ n: index + 1, count: recordings.length });
  if (!round && recordings.length === 1)
    return (
      <span
        className="flex max-w-40 min-w-0 shrink items-center gap-0.5 text-[11px] text-zinc-500 dark:text-zinc-400"
        title={recording?.label}
      >
        <Music size={14} className="shrink-0" />
        <span className="truncate">{recording?.label}</span>
      </span>
    );
  return (
    <DropDown
      width="sm:w-80"
      title={m.recordings_title()}
      trigger={(open, toggle) =>
        round ? (
          <IconButton label={name} active={open} aria-expanded={open} onClick={toggle}>
            <Music size={20} />
          </IconButton>
        ) : (
          <button
            type="button"
            onClick={toggle}
            aria-expanded={open}
            title={m.recordings()}
            className="flex items-center gap-0.5 rounded-md px-1 py-1 text-[11px] whitespace-nowrap text-zinc-500 tabular-nums hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
          >
            <Music size={14} />
            {name}
          </button>
        )
      }
    >
      <span className="max-sm:hidden">
        <MenuLabel>{m.recordings_title()}</MenuLabel>
      </span>
      {recordings.map((file) => {
        const date = player.uploaded(file.key);
        const bpm = recordingTempo(player.project, file.key)?.bpm;
        return (
          <MenuItem
            key={file.key}
            checked={file.key === recording?.key}
            onSelect={() => player.pickRecording(file.key)}
          >
            <span className="flex items-baseline gap-2">
              <span className="min-w-0 flex-1 truncate" title={file.label}>
                {file.label}
              </span>
              {bpm && <span className="shrink-0 text-xs text-zinc-500 tabular-nums">{Math.round(bpm)} BPM</span>}
            </span>
            {date && (
              <span className="block text-xs text-zinc-500 dark:text-zinc-400">{m.uploaded({ date: day(date) })}</span>
            )}
          </MenuItem>
        );
      })}
    </DropDown>
  );
}
