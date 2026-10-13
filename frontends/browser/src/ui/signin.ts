// Sign-in leaves the page; what to do when it comes back (look in a project's folders, unless its
// folders are still to be chosen) waits in the tab.

import * as download from "../core/download";
import * as onedrive from "../core/onedrive";
import * as projects from "../core/projects";

const AFTER = "downtempo-after-sign-in";

export function signInThenCheck(projectId: string) {
  sessionStorage.setItem(AFTER, projectId);
  void onedrive.signIn();
}

/** On page load: finish a sign-in that came back, then run what waited for it. */
export async function finishSignIn(): Promise<void> {
  const after = sessionStorage.getItem(AFTER);
  sessionStorage.removeItem(AFTER);
  if (!(await onedrive.finishSignIn()) || !after) return;
  const project = projects.find(after);
  const choosing = project && !Object.keys(project.files).length && project.sources.some((s) => !s.folders);
  if (!choosing) await download.check(after);
}
