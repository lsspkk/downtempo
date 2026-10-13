// Which recording plays. Two triggers for one menu: "♪ Audio 1/2" in small type (with a pointer) or
// a round ♪ (a phone, as the other buttons of its top line); the menu lists the song's recordings
// with their names and the dates they were uploaded. T steps through them too.

import { Music } from "lucide-react";
import { day } from "../../core/format";
import { m } from "../../paraglide/messages.js";
import { IconButton } from "../kit/Button";
import { DropDown, MenuItem } from "../kit/DropDown";
import type { Player } from "./usePlayer";

export function RecordingMenu({ player, round = false }: { player: Player; round?: boolean }) {
  const { recordings, recording, index } = player;
  const name = m.audio_n({ n: index + 1, count: recordings.length });
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
      {recordings.map((file, i) => {
        const date = player.uploaded(file.key);
        return (
          <MenuItem
            key={file.key}
            checked={file.key === recording?.key}
            onSelect={() => player.pickRecording(file.key)}
          >
            <span className="block truncate" title={file.label}>
              {i + 1}. {file.label}
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
