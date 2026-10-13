// A project with nothing on this device yet: the first start's later steps (2 the link if it was
// skipped, 3 sign in, 4 choose the folders, each with its step count), then "about 12 songs from
// 31 files" → Download. Once the first file is in, the songs show instead.

import { useState } from "react";
import * as download from "../../core/download";
import { size } from "../../core/format";
import * as onedrive from "../../core/onedrive";
import * as projects from "../../core/projects";
import { useStore } from "../../core/store";
import { m } from "../../paraglide/messages.js";
import { FolderPicker } from "../folders/FolderPicker";
import { Muted, Progress, Step } from "../kit/bits";
import { Button } from "../kit/Button";
import { AddFolder } from "../folders/LinkInput";
import { signInThenCheck } from "../signin";

export function GetSongs({ project, onSettings }: { project: projects.Project; onSettings: () => void }) {
  const status = useStore(download.status);
  const signedIn = !!onedrive.signedIn();
  const [again, setAgain] = useState<string | null>(null); // a source whose folders are chosen again
  const choosing = project.sources.find((s) => s.id === again) ?? project.sources.find((s) => !s.folders);
  const mine =
    status.phase !== "idle" && (status.phase === "preview" ? status.preview.project : status.project) === project.id;

  let body;
  let step: number | null = null; // in the first start's steps (Welcome has 1 and 2)
  if (!project.sources.length) {
    step = 2;
    body = <AddFolder project={project} />;
  } else if (mine && status.phase === "listing") body = <Working text={status.text} />;
  else if (mine && status.phase === "downloading") {
    body = (
      <div className="space-y-2">
        <p>{m.downloading_file({ file: status.text })}</p>
        <Progress value={status.allBytes ? status.bytes / status.allBytes : 0} />
      </div>
    );
  } else if (mine && status.phase === "preview") {
    const { songs, files, plan } = status.preview;
    body = (
      <div className="space-y-4">
        <p className="text-lg">
          {m.about()} <strong>{m.n_songs({ count: songs })}</strong>{" "}
          {m.from_files({ count: files, size: size(plan.bytes) })}
        </p>
        <Muted>{m.saved_offline()}</Muted>
        <div className="flex gap-2">
          <Button kind="primary" onClick={() => download.download(status.preview)}>
            {m.download()}
          </Button>
          <Button
            kind="quiet"
            onClick={() => {
              download.dismiss();
              setAgain(project.sources[0].id);
            }}
          >
            {m.choose_other_folders()}
          </Button>
        </div>
      </div>
    );
  } else if (!signedIn || (mine && status.phase === "failed" && status.signIn)) {
    step = 3;
    body = (
      <div className="space-y-3">
        <p>{m.sign_in_once()}</p>
        <Muted>{m.only_reads()}</Muted>
        <Button kind="primary" onClick={() => signInThenCheck(project.id)}>
          {m.sign_in_onedrive()}
        </Button>
      </div>
    );
  } else if (choosing) {
    if (!choosing.folders) step = 4;
    body = (
      <FolderPicker
        key={choosing.id}
        project={project}
        source={choosing}
        okText={m.look_in_these()}
        onCancel={again && choosing.folders ? () => setAgain(null) : undefined}
        onDone={(folders, skip) => {
          setAgain(null);
          void projects.chooseFolders(project.id, choosing.id, folders, skip).then(() => download.check(project.id));
        }}
      />
    );
  } else {
    body = (
      <div className="space-y-3">
        {mine && status.phase === "failed" && <p className="text-red-700 dark:text-red-400">⚠ {status.text}</p>}
        <p>{m.look_hint()}</p>
        <div className="flex flex-wrap gap-2">
          <Button kind="primary" onClick={() => download.check(project.id)}>
            {m.look()}
          </Button>
          <Button onClick={() => setAgain(project.sources[0].id)}>{m.choose_folders()}</Button>
          <Button kind="quiet" onClick={onSettings}>
            {m.change_link()}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="m-auto w-full max-w-lg p-4">
      <section className="space-y-4 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-zinc-200 dark:bg-zinc-900 dark:ring-zinc-800">
        {step && <Step n={step} />}
        <h2 className="text-lg font-semibold">{m.get_songs_of({ project: project.name })}</h2>
        {body}
      </section>
    </div>
  );
}

function Working({ text }: { text: string }) {
  return (
    <p className="flex items-center gap-3">
      <span className="size-4 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" />
      {text}
    </p>
  );
}
