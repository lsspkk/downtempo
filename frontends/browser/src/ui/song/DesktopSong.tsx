// A song with a pointer and a keyboard (a laptop, a tablet): one bar with ☰ and the list toggle over
// the song list, the title, then ♪ Audio, ▶, time, position, tempo, loop, loop editor; under it the
// song list beside the loop editor and the sheet with its toolbar.

import { m } from "../../paraglide/messages.js";
import { Bar, BarStart, BarTitle, ListButton } from "../bar/Bar";
import { Muted } from "../kit/bits";
import { EditorButton, LoopButton, PlayButton, PlayerError, PlayTime } from "../player/controls";
import { LoopEditorPanel, Position } from "../player/lazy";
import { RecordingMenu } from "../player/RecordingMenu";
import { TempoSlider } from "../player/Tempo";
import { SheetToolbar } from "../sheet/SheetControls";
import { NoSheet, SheetFrame } from "../sheet/SheetFrame";
import type { LayoutProps } from "./SongPage";

export function DesktopSong({ song, player, sheet, menu, list, listOpen, onToggleList }: LayoutProps) {
  return (
    <>
      <Bar>
        <BarStart overList={listOpen}>
          {menu}
          <ListButton open={listOpen} onClick={onToggleList} />
        </BarStart>
        <div className="max-w-56 min-w-0 shrink">
          <BarTitle>{song.title}</BarTitle>
        </div>
        {player.recording ? (
          <div className="flex min-w-0 flex-1 items-center gap-2 pr-3 pl-3">
            <RecordingMenu player={player} />
            <PlayButton player={player} />
            <PlayTime player={player} />
            <Position player={player} />
            <TempoSlider player={player} />
            <LoopButton player={player} />
            <EditorButton player={player} />
          </div>
        ) : (
          <Muted className="ml-auto pr-3">{m.no_recording()}</Muted>
        )}
      </Bar>
      <div className="relative flex min-h-0 flex-1">
        {listOpen && list}
        <main className="flex min-w-0 flex-1 flex-col">
          <PlayerError player={player} />
          <LoopEditorPanel player={player} />
          {sheet.sheet ? (
            <>
              <SheetToolbar sheet={sheet} />
              <SheetFrame sheet={sheet} />
            </>
          ) : (
            <NoSheet />
          )}
        </main>
      </div>
    </>
  );
}
