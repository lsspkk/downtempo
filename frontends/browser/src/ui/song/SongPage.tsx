// One song: its choices (which recording, which PDF, the sheet's zoom; remembered per song), the
// player and the sheet as hooks, then the layout for this screen: DesktopSong or PhoneSong
// (docs/browser-mobile.md). The layouts only arrange the parts; nothing below here asks about phones.

import { type ReactNode, useState } from "react";
import type { Song, SongFile } from "../../core/grouping";
import { remember, songMemory } from "../../core/practice";
import { usePhone } from "../kit/phone";
import { usePlayer } from "../player/usePlayer";
import { type SheetView, useSheet } from "../sheet/useSheet";
import { DesktopSong } from "./DesktopSong";
import { PhoneSong } from "./PhoneSong";

export type LayoutProps = {
  song: Song;
  player: ReturnType<typeof usePlayer>;
  sheet: ReturnType<typeof useSheet>;
  menu: ReactNode; // the ☰ menu
  list: ReactNode; // the song list, when open
  listOpen: boolean;
  onToggleList: () => void;
};

type Props = Omit<LayoutProps, "player" | "sheet"> & { project: string };

// The chosen keys, not the files: a download may add files to the song while it shows.
const pick = (list: SongFile[], key?: string) => list.find((f) => f.key === key) ?? list[0] ?? null;

export function SongPage({ project, song, ...layout }: Props) {
  const memory = songMemory(project, song.id);
  const [recordingKey, setRecordingKey] = useState(memory.recording);
  const [sheetKey, setSheetKey] = useState(memory.sheet);
  const [view, setView] = useState<SheetView>({
    zoom: memory.zoom ?? 1,
    fit: memory.fit ?? null,
  });

  const player = usePlayer({
    project,
    song: song.id,
    recording: pick(song.audio, recordingKey),
    recordings: song.audio,
    pickRecording: (key) => {
      setRecordingKey(key);
      remember(project, song.id, { recording: key });
    },
  });
  const phone = usePhone();
  const sheet = useSheet({
    project,
    edge: phone ? 0 : 12, // a phone's sheet fills the width, no grey around it
    sheet: pick(song.sheets, sheetKey),
    sheets: song.sheets,
    pickSheet: (key) => {
      setSheetKey(key);
      remember(project, song.id, { sheet: key });
    },
    view,
    onView: (next) => {
      setView(next);
      remember(project, song.id, next);
    },
  });

  const Layout = phone ? PhoneSong : DesktopSong;
  return <Layout song={song} player={player} sheet={sheet} {...layout} />;
}
