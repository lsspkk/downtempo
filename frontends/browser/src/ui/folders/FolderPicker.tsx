// Choosing the folders to take from a shared folder: its tree, opened one level at a time, with a tick
// and the size of each folder. A ticked folder brings everything inside it (nothing ticked: the whole
// shared folder); a click on a folder inside a ticked one leaves it out (crossed out).

import { useEffect, useState } from "react";
import { tidy, tidySkip } from "../../core/chosen";
import { size } from "../../core/format";
import * as onedrive from "../../core/onedrive";
import type { Project, Source } from "../../core/projects";
import { m } from "../../paraglide/messages.js";
import { Muted } from "../kit/bits";
import { Button } from "../kit/Button";
import { signInThenCheck } from "../signin";

type Props = {
  project: Project;
  source: Source;
  okText: string;
  onDone: (folders: string[], skip: string[]) => void;
  onCancel?: () => void;
};
type Trouble = { text: string; signIn: boolean };

export function FolderPicker({ project, source, okText, onDone, onCancel }: Props) {
  const [share, setShare] = useState<onedrive.Share | null>(null);
  const [inside, setInside] = useState<Record<string, onedrive.Folder[] | "loading">>({}); // by folder path
  const [open, setOpen] = useState<Set<string>>(new Set());
  const [ticked, setTicked] = useState<string[]>(source.folders ?? []);
  const [skip, setSkip] = useState<string[]>(source.skip ?? []);
  const [trouble, setTrouble] = useState<Trouble | null>(null);

  const fail = (error: unknown) =>
    setTrouble({
      text: error instanceof Error ? error.message : String(error),
      signIn: error instanceof onedrive.SignInNeeded,
    });

  async function load(at: onedrive.Share, item: string, path: string) {
    setInside((all) => ({ ...all, [path]: "loading" }));
    try {
      const folders = await onedrive.subfolders(at, item, path);
      setInside((all) => ({ ...all, [path]: folders }));
    } catch (error) {
      setInside(({ [path]: _, ...rest }) => rest);
      fail(error);
    }
  }

  useEffect(() => {
    let gone = false;
    onedrive
      .openShare(source.link)
      .then((opened) => {
        if (gone) return;
        setShare(opened);
        void load(opened, opened.id, "");
      })
      .catch((error) => !gone && fail(error));
    return () => void (gone = true);
  }, [source.link]);

  function toggleOpen(folder: onedrive.Folder) {
    const next = new Set(open);
    if (next.has(folder.path)) next.delete(folder.path);
    else {
      next.add(folder.path);
      if (share && !inside[folder.path]) void load(share, folder.id, folder.path);
    }
    setOpen(next);
  }

  const under = (path: string, folder: string) => path.startsWith(`${folder}/`);
  // Inside a ticked folder a click leaves the folder out, or takes it back; elsewhere it ticks.
  function toggle(path: string) {
    if (ticked.some((t) => under(path, t)))
      setSkip((all) => (all.includes(path) ? all.filter((s) => s !== path) : tidySkip(ticked, [...all, path])));
    else {
      const next = ticked.includes(path) ? ticked.filter((t) => t !== path) : tidy([...ticked, path]);
      setTicked(next);
      setSkip((all) => tidySkip(next, all));
    }
  }

  function rows(path: string, depth: number) {
    const folders = inside[path];
    if (folders === "loading" || !folders) return <Loading depth={depth} />;
    if (!folders.length && depth)
      return (
        <li className="py-1 text-xs text-zinc-500" style={{ paddingLeft: `${depth * 1.25 + 2.25}rem` }}>
          {m.no_folders_inside()}
        </li>
      );
    return folders.map((folder) => {
      const covered = ticked.some((t) => under(folder.path, t));
      const left = skip.includes(folder.path);
      const inLeft = skip.some((s) => under(folder.path, s));
      const on = (covered || ticked.includes(folder.path)) && !left && !inLeft;
      const some = on
        ? skip.some((s) => under(s, folder.path))
        : !left && !inLeft && ticked.some((t) => under(t, folder.path));
      const isOpen = open.has(folder.path);
      return (
        <li key={folder.path}>
          <div className="flex items-center gap-1 py-0.5" style={{ paddingLeft: `${depth * 1.25}rem` }}>
            <button
              type="button"
              onClick={() => toggleOpen(folder)}
              disabled={!folder.items}
              aria-label={isOpen ? m.close_folder({ name: folder.name }) : m.open_folder({ name: folder.name })}
              className="size-7 shrink-0 rounded text-zinc-500 hover:bg-zinc-200 disabled:invisible dark:hover:bg-zinc-800"
            >
              {isOpen ? "▾" : "▸"}
            </button>
            <label
              className="flex min-w-0 flex-1 cursor-pointer items-center gap-2 rounded px-1 py-1 hover:bg-zinc-100 dark:hover:bg-zinc-800/60"
              title={covered ? (left ? m.take_back() : m.leave_out()) : undefined}
            >
              <input
                type="checkbox"
                checked={on}
                disabled={inLeft}
                ref={(box) => void (box && (box.indeterminate = some))}
                onChange={() => toggle(folder.path)}
                className="size-4 shrink-0 accent-accent-600"
              />
              <span className={`truncate ${left || inLeft ? "text-zinc-400 line-through dark:text-zinc-500" : ""}`}>
                📁 {folder.name}
              </span>
              <span className="ml-auto shrink-0 text-xs text-zinc-500 tabular-nums">
                {m.n_items({ count: folder.items })} · {size(folder.size)}
              </span>
            </label>
          </div>
          {isOpen && <ul>{rows(folder.path, depth + 1)}</ul>}
        </li>
      );
    });
  }

  if (trouble && !share) return <Problem trouble={trouble} project={project} onCancel={onCancel} />;

  const top = inside[""];
  const none = Array.isArray(top) && !top.length;
  return (
    <div className="space-y-3">
      <div>
        <p className="font-medium">{share ? m.which_folders_from({ name: share.name }) : m.which_folders()}</p>
        <Muted>{m.tick_hint()}</Muted>
      </div>
      {none ? (
        <Muted>{m.no_folders_top()}</Muted>
      ) : (
        <ul className="max-h-80 overflow-y-auto rounded-lg border border-zinc-200 p-1 text-sm dark:border-zinc-800">
          {share ? rows("", 0) : <Loading depth={0} />}
        </ul>
      )}
      {trouble && <p className="text-sm text-red-700 dark:text-red-400">⚠ {trouble.text}</p>}
      <p className="text-sm">
        {ticked.length ? (
          <>
            <strong>{m.n_folders({ count: ticked.length })}</strong>: {ticked.join(", ")}
            {skip.length > 0 && (
              <span className="block text-zinc-500">
                {m.n_left_out({ count: skip.length })}: {skip.join(", ")}
              </span>
            )}
          </>
        ) : (
          m.nothing_ticked()
        )}
      </p>
      <div className="flex flex-wrap gap-2">
        <Button kind="primary" disabled={!share} onClick={() => onDone(tidy(ticked), tidySkip(ticked, skip))}>
          {okText}
        </Button>
        {ticked.length > 0 && (
          <Button
            kind="quiet"
            onClick={() => {
              setTicked([]);
              setSkip([]);
            }}
          >
            {m.clear_ticks()}
          </Button>
        )}
        {onCancel && (
          <Button kind="quiet" onClick={onCancel}>
            {m.cancel()}
          </Button>
        )}
      </div>
    </div>
  );
}

function Loading({ depth }: { depth: number }) {
  return (
    <li className="flex items-center gap-2 py-1.5 text-zinc-500" style={{ paddingLeft: `${depth * 1.25 + 0.5}rem` }}>
      <span className="size-3.5 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" />
      {m.opening()}
    </li>
  );
}

function Problem({ trouble, project, onCancel }: { trouble: Trouble; project: Project; onCancel?: () => void }) {
  return (
    <div className="space-y-3">
      <p className="text-red-700 dark:text-red-400">⚠ {trouble.text}</p>
      <div className="flex gap-2">
        {trouble.signIn && (
          <Button kind="primary" onClick={() => signInThenCheck(project.id)}>
            {m.sign_in_onedrive()}
          </Button>
        )}
        {onCancel && (
          <Button kind="quiet" onClick={onCancel}>
            {m.cancel()}
          </Button>
        )}
      </div>
    </div>
  );
}
