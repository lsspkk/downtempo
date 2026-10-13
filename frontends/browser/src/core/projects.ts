// Projects: one per group the musician practises with. Each has its shared folders (sources) and a
// record of what is on this device; the current one is what the player shows. Kept in localStorage.

import { m } from "../paraglide/messages.js";
import { takes } from "./chosen";
import * as files from "./files";
import { forget } from "./practice";
import { stored, useStore } from "./store";

export type Source = {
  id: string;
  link: string;
  name: string; // the shared folder's, once listed
  folders?: string[]; // the chosen folders inside it; [] = all of it; missing = not chosen yet
  skip?: string[]; // folders inside the chosen ones that are left out
};
export type Local = { size: number; modified: string };
export type Project = {
  id: string;
  name: string;
  sources: Source[];
  files: Record<string, Local>; // "<source id>/<path on the server>" → the copy on this device
  checked: number | null; // when every source was last checked to the end
};
type State = { projects: Project[]; current: string | null };

export const projects = stored<State>("downtempo-projects", { projects: [], current: null });

export function useProjects() {
  const state = useStore(projects);
  return { all: state.projects, current: state.projects.find((p) => p.id === state.current) ?? null };
}

export const current = () => projects.get().projects.find((p) => p.id === projects.get().current) ?? null;
export const find = (id: string) => projects.get().projects.find((p) => p.id === id) ?? null;

const newId = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 6);

export function update(id: string, change: (p: Project) => Project) {
  projects.set((s) => ({ ...s, projects: s.projects.map((p) => (p.id === id ? change(p) : p)) }));
}

export function create(name: string, link: string): Project {
  const project: Project = {
    id: newId(),
    name: name.trim() || m.default_project_name(),
    sources: [],
    files: {},
    checked: null,
  };
  if (link) project.sources.push({ id: "s1", link: link.trim(), name: "" });
  projects.set((s) => ({ projects: [...s.projects, project], current: project.id }));
  return project;
}

export const use = (id: string) => projects.set((s) => ({ ...s, current: id }));

export const rename = (id: string, name: string) => update(id, (p) => ({ ...p, name: name.trim() || p.name }));

/** The whole project: out of the list, its files off the device, and all practice memory of it. */
export async function remove(id: string) {
  projects.set((s) => {
    const left = s.projects.filter((p) => p.id !== id);
    return { projects: left, current: s.current === id ? (left[0]?.id ?? null) : s.current };
  });
  forget(id);
  await files.removeProject(id);
}

/** Only the downloaded files, to free the space; the project, its folders and practice memory stay. */
export async function removeFiles(id: string) {
  update(id, (p) => ({ ...p, files: {}, checked: null }));
  await files.removeProject(id);
}

/** Adds the shared folder (its folders are chosen next) and returns its id. */
export function addSource(id: string, link: string): string {
  const taken = new Set(find(id)?.sources.map((s) => s.id));
  let n = taken.size + 1;
  while (taken.has(`s${n}`)) n++;
  const source = `s${n}`;
  update(id, (p) => ({ ...p, sources: [...p.sources, { id: source, link: link.trim(), name: "" }], checked: null }));
  return source;
}

/** The files on this device that choosing `folders` minus `skip` would leave out. */
export function leftOut(project: Project, source: string, folders: string[], skip: string[]): string[] {
  return Object.keys(project.files).filter((key) => {
    const [id, path] = splitKey(key);
    return id === source && !takes(folders, path, skip);
  });
}

/** Take only these folders of the shared folder, without the `skip` ones; files outside leave the device. */
export async function chooseFolders(id: string, source: string, folders: string[], skip: string[]) {
  const project = find(id);
  if (!project) return;
  const gone = leftOut(project, source, folders, skip);
  update(id, (p) => ({
    ...p,
    sources: p.sources.map((s) => (s.id === source ? { ...s, folders, skip } : s)),
    files: Object.fromEntries(Object.entries(p.files).filter(([key]) => !gone.includes(key))),
    checked: null,
  }));
  for (const key of gone) await files.remove(id, key);
}

/** The folder and its files leave the project and the device. */
export async function removeSource(id: string, source: string) {
  update(id, (p) => ({
    ...p,
    sources: p.sources.filter((s) => s.id !== source),
    files: Object.fromEntries(Object.entries(p.files).filter(([key]) => !key.startsWith(`${source}/`))),
  }));
  await files.remove(id, source);
}

/** The source's id and its path on the server, from a file key. */
export function splitKey(key: string): [string, string] {
  const slash = key.indexOf("/");
  return [key.slice(0, slash), key.slice(slash + 1)];
}
