// The top of the song list, as in the Python player: a "Project" caption with ⟳ (check the shared
// folders for new files; while it runs, stop), the project's name, and one status line that keeps its
// height ("Checked 2 h ago", "3 / 7 · 12 MB of 40 MB" with a thin bar, the result, or ⚠ the problem).

import { RefreshCw } from "lucide-react";
import * as download from "../../core/download";
import { ago, size } from "../../core/format";
import type { Project } from "../../core/projects";
import { useStore } from "../../core/store";
import { m } from "../../paraglide/messages.js";
import { Progress } from "../kit/bits";
import { Button } from "../kit/Button";
import { signInThenCheck } from "../signin";

export function ProjectPanel({ project }: { project: Project }) {
  const status = useStore(download.status);
  const mine =
    status.phase !== "idle" && (status.phase === "preview" ? status.preview.project : status.project) === project.id;
  const running = mine && (status.phase === "listing" || status.phase === "downloading");

  let text: string = project.checked ? m.checked_ago({ ago: ago(project.checked) }) : m.not_downloaded();
  let warn = false;
  let fraction = 0;
  if (mine) {
    switch (status.phase) {
      case "listing":
      case "done":
        text = status.text;
        break;
      case "downloading":
        text = m.progress({
          done: status.done + 1,
          total: status.total,
          bytes: size(status.bytes),
          all: size(status.allBytes),
        });
        fraction = status.allBytes ? status.bytes / status.allBytes : 0;
        break;
      case "failed":
        text = `⚠ ${status.text}`;
        warn = true;
        break;
      case "preview":
        text = m.ready_to_download();
        break;
    }
  }
  const signIn = mine && status.phase === "failed" && status.signIn;

  return (
    <div className="shrink-0 px-2 pt-1">
      <div className="flex items-center pl-2">
        <span className="text-xs tracking-wider text-zinc-500 uppercase">{m.project()}</span>
        <Button
          kind="quiet"
          className="ml-auto !rounded-full !p-1.5"
          disabled={!project.sources.length}
          onClick={() => (running ? download.stop() : download.check(project.id))}
          title={running ? m.stop_download() : m.update_title()}
          aria-label={running ? m.stop_download() : m.update_title()}
        >
          <RefreshCw size={16} className={running ? "animate-spin" : ""} />
        </Button>
      </div>
      <p className="truncate px-2 leading-tight font-medium" title={project.name}>
        {project.name}
      </p>
      <button
        type="button"
        disabled={!signIn}
        onClick={() => signInThenCheck(project.id)}
        className={`block h-5 w-full truncate px-2 text-left text-xs leading-5 ${warn ? "text-red-700 dark:text-red-400" : "text-zinc-500 dark:text-zinc-400"} ${signIn ? "underline" : ""}`}
        title={signIn ? `${text} · ${m.sign_in()}` : text}
      >
        {text}
      </button>
      <div className={`mx-2 ${running && fraction ? "" : "invisible"}`}>
        <Progress value={fraction} />
      </div>
    </div>
  );
}
