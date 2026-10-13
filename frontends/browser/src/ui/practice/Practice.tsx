// A project's practice: its songs (grouped by name), the chosen one, the song list open or not; then
// the page that fits: Get the songs (nothing downloaded yet), the song (SongPage), or "No songs yet".
// Settings and About are pages over all of it, so a song keeps playing behind them.

import { useMemo, useRef, useState } from "react";
import { group } from "../../core/grouping";
import { lastSong, rememberLast } from "../../core/practice";
import type { Project } from "../../core/projects";
import { m } from "../../paraglide/messages.js";
import { Bar, BarStart, BarTitle } from "../bar/Bar";
import { MainMenu } from "../bar/MainMenu";
import { Muted } from "../kit/bits";
import { useKeys } from "../kit/keys";
import { AboutPage } from "../about/About";
import { SettingsPage } from "../settings/Settings";
import { SongPage } from "../song/SongPage";
import { GetSongs } from "./GetSongs";
import { SongList } from "./SongList";

const wide = () => window.innerWidth >= 768; // the list is a column (md); below it opens over the page

export function Practice({ project, onNewProject }: { project: Project; onNewProject: () => void }) {
  const songs = useMemo(
    () => group(Object.entries(project.files).map(([key, file]) => ({ key, modified: file.modified }))),
    [project.files],
  );
  const [chosen, setChosen] = useState(() => lastSong(project.id));
  const song = songs.find((s) => s.id === chosen) ?? songs[0] ?? null;
  const [listOpen, setListOpen] = useState(wide);
  const [settings, setSettings] = useState(false);
  const [about, setAbout] = useState(false);
  const search = useRef<HTMLInputElement>(null);

  function choose(id: string) {
    setChosen(id);
    rememberLast(project.id, id);
  }
  function pick(id: string) {
    choose(id);
    if (!wide()) setListOpen(false);
  }
  function step(by: number) {
    if (!songs.length) return;
    const index = song ? songs.indexOf(song) : -1;
    choose(songs[(index + by + songs.length) % songs.length].id);
  }

  useKeys({
    n: () => step(1),
    p: () => step(-1),
    q: () => setListOpen((open) => !open),
    "/": () => {
      setListOpen(true);
      setTimeout(() => search.current?.focus());
    },
  });

  const menu = (
    <MainMenu
      project={project.id}
      onSettings={() => setSettings(true)}
      onAbout={() => setAbout(true)}
      onNewProject={onNewProject}
    />
  );
  const list = (
    <>
      <div className="fixed inset-0 z-10 hidden bg-black/30 sm:block md:hidden" onClick={() => setListOpen(false)} />
      <SongList
        project={project}
        songs={songs}
        current={song?.id ?? null}
        onPick={pick}
        search={search}
        onClose={() => setListOpen(false)}
      />
    </>
  );
  const plain = (body: React.ReactNode) => (
    <>
      <Bar>
        <BarStart>{menu}</BarStart>
        <BarTitle>{project.name}</BarTitle>
      </Bar>
      <main className="flex min-h-0 flex-1 flex-col overflow-y-auto">{body}</main>
    </>
  );

  return (
    <div className="flex h-full flex-col">
      {!Object.keys(project.files).length ? (
        plain(<GetSongs project={project} onSettings={() => setSettings(true)} />)
      ) : song ? (
        <SongPage
          key={song.id}
          project={project.id}
          song={song}
          menu={menu}
          list={list}
          listOpen={listOpen}
          onToggleList={() => setListOpen((open) => !open)}
        />
      ) : (
        plain(<Muted className="m-auto">{m.no_songs()}</Muted>)
      )}
      {settings && <SettingsPage project={project} menu={menu} onClose={() => setSettings(false)} />}
      {about && <AboutPage menu={menu} onClose={() => setAbout(false)} />}
    </div>
  );
}
