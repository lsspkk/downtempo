// A song on a phone (docs/browser-mobile.md): one top line of round buttons (☰, songs, ♪, tempo, loop,
// loop editor, and the sheet's menu at the right end), a line with the time, position, BPM and ▶, then
// the sheet. The song list, menus, the loop editor and the BPM strip (with the Optimal switch and Tap)
// open over the page.

import { m } from "../../paraglide/messages.js";
import { Bar, ListButton } from "../bar/Bar";
import { useBackCloses } from "../kit/back";
import { Muted } from "../kit/bits";
import { EditorButton, LoopButton, PlayButton, PlayerError, PlayTime } from "../player/controls";
import { LoopEditorPanel, Position } from "../player/lazy";
import { RecordingMenu } from "../player/RecordingMenu";
import { TempoButton } from "../player/Tempo";
import { BpmStrip } from "../tempo/BpmStrip";
import { TempoToast } from "../tempo/TempoToast";
import { BpmButton } from "../tempo/TempoBar";
import { SheetMenu } from "../sheet/SheetControls";
import { NoSheet, SheetFrame } from "../sheet/SheetFrame";
import type { LayoutProps } from "./SongPage";

export function PhoneSong({ player, sheet, menu, list, listOpen, onToggleList }: LayoutProps) {
  // The song list and the loop editor are pages of their own here: the phone's Back closes them.
  useBackCloses(listOpen, onToggleList);
  useBackCloses(player.editing, () => player.setEditing(false));
  useBackCloses(player.goal.open, () => player.goal.setOpen(false));
  return (
    <>
      <Bar>
        <div className="flex flex-1 items-center justify-between px-1">
          {menu}
          <ListButton phone open={listOpen} onClick={onToggleList} />
          {player.recording && (
            <>
              <RecordingMenu player={player} round />
              <TempoButton player={player} />
              <LoopButton player={player} />
              <EditorButton player={player} />
            </>
          )}
          {sheet.sheet && <SheetMenu sheet={sheet} />}
        </div>
      </Bar>
      {player.recording ? (
        <div className="flex h-12 shrink-0 items-center gap-2 border-b border-zinc-200 bg-white px-3 dark:border-zinc-800 dark:bg-zinc-900">
          <PlayTime player={player} />
          <Position player={player} />
          <BpmButton player={player} />
          <PlayButton player={player} className="size-10" />
        </div>
      ) : (
        <Muted className="border-b border-zinc-200 bg-white px-4 py-2 dark:border-zinc-800 dark:bg-zinc-900">
          {m.no_recording()}
        </Muted>
      )}
      <PlayerError player={player} />
      <div className="relative flex min-h-0 flex-1">
        {listOpen && list}
        <main className="flex min-w-0 flex-1 flex-col">
          <LoopEditorPanel player={player} />
          <BpmStrip player={player} />
          {sheet.sheet ? <SheetFrame sheet={sheet} /> : <NoSheet />}
          <TempoToast player={player} on={sheet.only} />
        </main>
      </div>
    </>
  );
}
