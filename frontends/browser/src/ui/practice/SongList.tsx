// The song list: the project (⟳ and status) at its top, search, the songs with what each has
// (♪ recording, 𝄞 sheet), the current one marked. A column on wide screens, a drawer on small
// tablets, a full-screen page with ← on phones (the phone's Back closes it too).

import { ArrowLeft } from "lucide-react";
import { type RefObject, useState } from "react";
import type { Song } from "../../core/grouping";
import type { Project } from "../../core/projects";
import { m } from "../../paraglide/messages.js";
import { IconButton } from "../kit/Button";
import { ProjectPanel } from "./ProjectPanel";

type Props = {
  project: Project;
  songs: Song[];
  current: string | null;
  onPick: (id: string) => void;
  search: RefObject<HTMLInputElement | null>;
  onClose: () => void;
};

export function SongList({ project, songs, current, onPick, search, onClose }: Props) {
  const [query, setQuery] = useState("");
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  const shown = songs.filter((s) => words.every((w) => s.title.toLowerCase().includes(w)));

  return (
    <aside className="fixed inset-0 z-40 flex flex-col bg-white sm:absolute sm:inset-y-0 sm:right-auto sm:left-0 sm:z-20 sm:w-72 sm:max-w-[85vw] sm:border-r sm:border-zinc-200 sm:shadow-xl md:static md:w-64 md:shadow-none dark:bg-zinc-900 sm:dark:border-zinc-800">
      {/* On a phone the list is a page of its own: ← and its title, as any page (docs/browser-mobile.md). */}
      <div className="flex h-12 shrink-0 items-center gap-2 border-b border-zinc-200 px-1 sm:hidden dark:border-zinc-800">
        <IconButton label={m.back()} onClick={onClose}>
          <ArrowLeft size={22} />
        </IconButton>
        <h2 className="truncate font-semibold">{m.songs()}</h2>
      </div>
      <ProjectPanel project={project} />
      <div className="p-2">
        <input
          ref={search}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && shown[0]) onPick(shown[0].id);
            if (e.key === "Escape") {
              setQuery("");
              e.currentTarget.blur();
            }
          }}
          placeholder={m.search_songs({ count: songs.length })}
          className="w-full rounded-lg border border-zinc-300 bg-transparent px-3 py-1.5 text-sm dark:border-zinc-700"
        />
      </div>
      <ul className="min-h-0 flex-1 overflow-y-auto px-1 pb-2">
        {shown.map((song) => (
          <li key={song.id}>
            <button
              onClick={() => onPick(song.id)}
              aria-current={song.id === current}
              className="flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-left text-sm hover:bg-zinc-100 aria-[current=true]:bg-accent-100 aria-[current=true]:font-semibold aria-[current=true]:text-accent-900 dark:hover:bg-zinc-800 dark:aria-[current=true]:bg-accent-900 dark:aria-[current=true]:text-accent-50"
            >
              <span className="min-w-0 flex-1 truncate" title={song.title}>
                {song.title}
              </span>
              <span
                className="shrink-0 text-xs text-zinc-400"
                title={m.song_has({ audio: song.audio.length, sheets: song.sheets.length })}
              >
                {song.audio.length ? "♪" : ""}
                {song.sheets.length ? "𝄞" : ""}
              </span>
            </button>
          </li>
        ))}
        {!shown.length && <li className="px-3 py-2 text-sm text-zinc-500">{m.no_match({ query })}</li>}
      </ul>
    </aside>
  );
}
