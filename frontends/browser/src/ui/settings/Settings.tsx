// Settings as a page over the practice view (not a modal: it has too much to read, ux.md #12; the
// song keeps playing behind it); its own bar holds ☰, ← Back and its title, Esc goes back too. With
// room, each part is a card; on a phone plain sections with clear space between them, no borders.
// The important first (#15): the project (name, shared folders, and at its end deleting the files
// or the project), this device, the OneDrive sign-in, the keys.

import { type ReactNode, useEffect, useState } from "react";
import * as download from "../../core/download";
import * as files from "../../core/files";
import { size } from "../../core/format";
import * as onedrive from "../../core/onedrive";
import * as projects from "../../core/projects";
import { m } from "../../paraglide/messages.js";
import { Bar, BackTitle, BarStart } from "../bar/Bar";
import { FolderPicker } from "../folders/FolderPicker";
import { useBackCloses } from "../kit/back";
import { useKeys } from "../kit/keys";
import { language } from "../language";
import { AddFolder } from "../folders/LinkInput";
import { Muted } from "../kit/bits";
import { Button } from "../kit/Button";

type Props = { project: projects.Project; menu: ReactNode; onClose: () => void };

export function SettingsPage({ project, menu, onClose }: Props) {
  useKeys({ Escape: onClose });
  useBackCloses(true, onClose); // the phone's or browser's Back closes the page
  // Gutters on both edges keep the column centred like the title in the bar, scrollbar or not.
  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-zinc-50 dark:bg-zinc-950">
      <Bar>
        <div className="max-sm:hidden">
          <BarStart>{menu}</BarStart>
        </div>
        <BackTitle title={m.settings()} onBack={onClose} />
      </Bar>
      <div className="min-h-0 flex-1 overflow-y-auto [scrollbar-gutter:stable_both-edges]">
        <div className="mx-auto max-w-2xl space-y-10 px-4 py-5 sm:space-y-6 sm:py-6">
          <ProjectPart project={project} onClose={onClose} />
          <Storage />
          <SignIn />
          {/* Phones and tablets (a touch screen as the main pointer) have no keys to learn. */}
          <div className="pointer-coarse:hidden">
            <Keys />
          </div>
        </div>
      </div>
    </div>
  );
}

function Part({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-sm font-semibold">{title}</h2>
      <div className="space-y-3 sm:rounded-xl sm:bg-white sm:p-4 sm:ring-1 sm:ring-zinc-200 sm:dark:bg-zinc-900 sm:dark:ring-zinc-800">
        {children}
      </div>
    </section>
  );
}

function ProjectPart({ project, onClose }: { project: projects.Project; onClose: () => void }) {
  const [name, setName] = useState(project.name);
  const [adding, setAdding] = useState(false);
  const [picking, setPicking] = useState<string | null>(null); // the source whose folders are being chosen
  const count = (source: string) => Object.keys(project.files).filter((k) => k.startsWith(`${source}/`)).length;
  const taken = (source: projects.Source) => {
    if (!source.folders) return m.folders_not_chosen();
    const what = source.folders.length ? m.only_folders({ folders: source.folders.join(", ") }) : m.all_of_it();
    return source.skip?.length ? `${what}, ${m.without_folders({ folders: source.skip.join(", ") })}` : what;
  };

  return (
    <Part title={m.project()}>
      <label className="block space-y-1">
        <span className="text-sm font-medium">{m.name()}</span>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          onBlur={() => projects.rename(project.id, name)}
          onKeyDown={(e) => e.key === "Enter" && projects.rename(project.id, name)}
          className="block w-full max-w-sm rounded-lg border border-zinc-300 bg-transparent px-3 py-1.5 dark:border-zinc-700"
        />
      </label>
      <p className="pt-1 text-sm font-medium">{m.shared_folders()}</p>
      <ul className="divide-y divide-zinc-200 sm:rounded-lg sm:border sm:border-zinc-200 dark:divide-zinc-800 sm:dark:border-zinc-800">
        {project.sources.map((source) => (
          <li key={source.id} className="space-y-3 py-2 sm:px-3">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{source.name || m.not_opened()}</p>
                <p className="truncate text-xs text-zinc-500" title={taken(source)}>
                  {taken(source)} · {m.n_files({ count: count(source.id) })}
                </p>
                <p className="truncate text-xs text-zinc-500" title={source.link}>
                  {source.link}
                </p>
              </div>
              <Button
                className="!py-1"
                active={picking === source.id}
                onClick={() => setPicking(picking === source.id ? null : source.id)}
              >
                {m.folders_button()}
              </Button>
              <Button
                kind="danger"
                className="!py-1"
                onClick={() => {
                  if (confirm(m.confirm_remove_source({ name: source.name || source.link, count: count(source.id) }))) {
                    void projects.removeSource(project.id, source.id);
                  }
                }}
              >
                {m.remove()}
              </Button>
            </div>
            {picking === source.id && (
              <FolderPicker
                project={project}
                source={source}
                okText={m.use_these()}
                onCancel={() => setPicking(null)}
                onDone={(folders, skip) => {
                  const gone = projects.leftOut(project, source.id, folders, skip).length;
                  if (gone && !confirm(m.confirm_left_out({ count: gone }))) return;
                  setPicking(null);
                  void projects
                    .chooseFolders(project.id, source.id, folders, skip)
                    .then(() => download.check(project.id));
                }}
              />
            )}
          </li>
        ))}
        {!project.sources.length && <li className="px-3 py-2 text-sm text-zinc-500">{m.no_shared_folders()}</li>}
      </ul>
      {adding ? (
        <AddFolder
          project={project}
          onAdded={(source) => {
            setAdding(false);
            setPicking(source);
          }}
        />
      ) : (
        <Button onClick={() => setAdding(true)}>+ {m.add_folder()}</Button>
      )}
      <Deleting project={project} onClose={onClose} />
    </Part>
  );
}

function Storage() {
  const [use, setUse] = useState<files.Usage | null>(null);
  const refresh = () =>
    files
      .usage()
      .then(setUse)
      .catch(() => setUse(null));
  useEffect(() => void refresh(), []);

  return (
    <Part title={m.this_device()}>
      {use && <p className="text-sm">{m.device_all({ used: size(use.used), allowed: size(use.allowed) })}</p>}
      {use?.kept ? (
        <div className="space-y-1">
          <p className="text-sm">{m.kept()}</p>
          <Muted>{m.unkeep_hint()}</Muted>
        </div>
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Muted className="min-w-0 flex-1">{m.may_clear()}</Muted>
          <Button onClick={() => files.askToKeep().then(refresh)}>{m.keep_files()}</Button>
        </div>
      )}
    </Part>
  );
}

function SignIn() {
  const [tokens, setTokens] = useState(onedrive.signedIn);
  return (
    <Part title="OneDrive">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm">
          {tokens
            ? m.signed_in_since({ time: new Date(tokens.signedIn).toLocaleString(language()) })
            : m.not_signed_in()}
          <span className="block text-zinc-500">{m.asks_again()}</span>
        </p>
        {tokens ? (
          <Button
            onClick={() => {
              onedrive.signOut();
              setTokens(null);
            }}
          >
            {m.sign_out()}
          </Button>
        ) : (
          <Button kind="primary" onClick={() => onedrive.signIn()}>
            {m.sign_in()}
          </Button>
        )}
      </div>
    </Part>
  );
}

const KEYS: [string, () => string][] = [
  // the language is set before this module runs (switching reloads)
  [`${m.key_space()} / K`, m.key_play],
  ["← / →", m.key_tempo],
  [", / .", m.key_5s],
  ["J / L", m.key_10s],
  ["0, 1 … 9", m.key_jump],
  ["A / B", m.key_ab],
  ["R / C", m.key_loop],
  ["E", m.key_edit],
  ["T", m.key_recording],
  ["↑ / ↓", m.key_scroll],
  ["PgUp / PgDn", m.key_screen],
  ["Home / End", m.key_ends],
  ["+ / −", m.key_zoom],
  ["W / H", m.key_fit],
  ["O", m.key_rotate],
  ["F", m.key_full],
  ["N / P", m.key_song],
  ["Q, /", m.key_list],
];

function Keys() {
  return (
    <Part title={m.keyboard()}>
      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm sm:grid-cols-[auto_1fr_auto_1fr]">
        {KEYS.map(([key, what]) => (
          <div key={key} className="contents">
            <dt className="font-mono text-xs leading-5 text-zinc-600 dark:text-zinc-300">{key}</dt>
            <dd>{what()}</dd>
          </div>
        ))}
      </dl>
    </Part>
  );
}

/** The end of the Project part: free the device's space, or delete the whole project; both ask first. */
function Deleting({ project, onClose }: { project: projects.Project; onClose: () => void }) {
  const count = Object.keys(project.files).length;
  const bytes = size(Object.values(project.files).reduce((sum, f) => sum + f.size, 0));
  return (
    <div className="space-y-3 pt-4 sm:border-t sm:border-zinc-200 sm:pt-3 sm:dark:border-zinc-800">
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <Muted className="min-w-0 flex-1">{m.delete_files_hint({ size: bytes })}</Muted>
        <Button
          kind="danger"
          disabled={!count}
          onClick={() => {
            if (confirm(m.confirm_delete_files({ name: project.name, files: m.n_files({ count }), size: bytes })))
              void projects.removeFiles(project.id);
          }}
        >
          {m.delete_files()}
        </Button>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <Muted className="min-w-0 flex-1">{m.delete_project_hint()}</Muted>
        <Button
          kind="danger"
          onClick={() => {
            if (confirm(m.confirm_delete({ name: project.name }))) {
              onClose();
              void projects.remove(project.id);
            }
          }}
        >
          {m.delete_project()}
        </Button>
      </div>
    </div>
  );
}
