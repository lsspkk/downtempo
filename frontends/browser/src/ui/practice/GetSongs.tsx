// A project with nothing on this device yet, one full page: no folder yet (an empty state that
// asks for the link, never forced), then sign in, choose the folders (the progress list shows
// where we are), then "about 12 songs from
// 31 files" → Download. Once the first file is in, the songs show instead.

import { useState } from "react";
import * as download from "../../core/download";
import { size } from "../../core/format";
import * as onedrive from "../../core/onedrive";
import * as projects from "../../core/projects";
import { useStore } from "../../core/store";
import { m } from "../../paraglide/messages.js";
import { FolderPicker } from "../folders/FolderPicker";
import { Muted, Progress, Stages } from "../kit/bits";
import { Button } from "../kit/Button";
import { AddFolder } from "../folders/LinkInput";
import { signInThenCheck } from "../signin";
import { WhyLink } from "../start/Welcome";

export function GetSongs({ project, onSettings }: { project: projects.Project; onSettings: () => void }) {
  const status = useStore(download.status);
  const signedIn = !!onedrive.signedIn();
  const [again, setAgain] = useState<string | null>(null); // a source whose folders are chosen again
  const choosing = project.sources.find((s) => s.id === again) ?? project.sources.find((s) => !s.folders);
  const mine =
    status.phase !== "idle" && (status.phase === "preview" ? status.preview.project : status.project) === project.id;

  let body;
  let stage = 0; // 0-based place in Stages
  if (!project.sources.length) {
    return (
      <Page>
        <h2 className="text-xl font-semibold">{m.empty_title()}</h2>
        <p>{m.empty_why()}</p>
        <AddFolder project={project} />
        <WhyLink />
      </Page>
    );
  } else if (mine && status.phase === "listing") body = <Working text={status.text} />;
  else if (mine && status.phase === "downloading") {
    body = (
      <div className="space-y-2">
        <p>
          {status.compressing ? m.compressing_file({ file: status.text }) : m.downloading_file({ file: status.text })}
        </p>
        <Progress value={status.allBytes ? status.bytes / status.allBytes : 0} />
      </div>
    );
  } else if (mine && status.phase === "preview") {
    stage = 3;
    const { songs, files, plan } = status.preview;
    // a wav is kept as an mp3 (core/compress.ts): its key is the mp3's name
    const wavs = plan.fetch.filter((f) => f.key !== f.listed).length + plan.compress.length;
    body = (
      <div className="space-y-4">
        <p className="text-lg">
          {m.about()} <strong>{m.n_songs({ count: songs })}</strong>{" "}
          {m.from_files({ count: files, size: size(plan.bytes) })}
        </p>
        <Muted>
          {m.saved_offline()} {wavs > 0 && m.then_compressed({ count: wavs })}
        </Muted>
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
    stage = 1;
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
    stage = 2;
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
    <Page>
      <Stages current={stage} />
      <h2 className="text-xl font-semibold">{m.get_songs_of({ project: project.name })}</h2>
      {body}
    </Page>
  );
}

const Page = ({ children }: { children: React.ReactNode }) => (
  <div className="mx-auto w-full max-w-2xl space-y-4 px-4 py-8">{children}</div>
);

function Working({ text }: { text: string }) {
  return (
    <p className="flex items-center gap-3">
      <span className="size-4 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" />
      {text}
    </p>
  );
}
