// Which part of a shared folder a project takes: the folders the musician ticked (paths from the
// shared folder's top), or all of it when none are ticked, minus the folders left out (`skip`),
// which lie inside the taken ones. Pure.

const under = (path: string, folder: string) => path.startsWith(`${folder}/`);
const at = (path: string, folder: string) => path === folder || under(path, folder);

/** A file is taken when it lies in a chosen folder (any depth) and not in a left-out one. */
export const takes = (folders: string[], file: string, skip: string[] = []) =>
  (!folders.length || folders.some((f) => under(file, f))) && !skip.some((s) => under(file, s));

/** A folder is worth opening when it is chosen, lies in a chosen one, or leads to one; never when left out. */
export const opens = (folders: string[], folder: string, skip: string[] = []) =>
  !skip.some((s) => at(folder, s)) &&
  (!folders.length || folders.some((f) => f === folder || under(folder, f) || under(f, folder)));

/** Ticking a folder covers what is inside it, so those ticks go; sorted for showing. */
export function tidy(folders: string[]): string[] {
  const unique = [...new Set(folders)];
  return unique.filter((f) => !unique.some((other) => under(f, other))).sort();
}

/** Left-out folders that still mean something: inside a taken folder, not inside another left-out one. */
export function tidySkip(folders: string[], skip: string[]): string[] {
  const inside = [...new Set(skip)].filter((s) => !folders.length || folders.some((f) => under(s, f)));
  return inside.filter((s) => !inside.some((other) => under(s, other))).sort();
}
