// The shared folder's link: a field that says when the text isn't a OneDrive link, and the
// "add a folder to this project" form built on it (first start, Get the songs, Settings).

import { type FormEvent, useState } from "react";
import * as onedrive from "../../core/onedrive";
import * as projects from "../../core/projects";
import { m } from "../../paraglide/messages.js";
import { Muted } from "../kit/bits";
import { Button } from "../kit/Button";

export const badLink = (link: string) => link.trim() !== "" && !onedrive.looksLikeLink(link);

export function LinkInput({
  value,
  onChange,
  hint,
  autoFocus,
}: {
  value: string;
  onChange: (v: string) => void;
  hint?: string;
  autoFocus?: boolean;
}) {
  return (
    <label className="block space-y-1">
      <span className="text-sm font-medium">{m.link_label()}</span>
      <input
        type="url"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="https://1drv.ms/f/…"
        autoFocus={autoFocus}
        className="w-full rounded-lg border border-zinc-300 bg-transparent px-3 py-2 dark:border-zinc-700"
      />
      {badLink(value) ? (
        <span className="text-sm text-red-600 dark:text-red-400">{m.link_bad()}</span>
      ) : (
        hint && <Muted>{hint}</Muted>
      )}
    </label>
  );
}

/** Adds the folder; the caller lets the musician choose its folders next. */
export function AddFolder({ project, onAdded }: { project: projects.Project; onAdded?: (source: string) => void }) {
  const [link, setLink] = useState("");
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!link.trim() || badLink(link)) return;
    const source = projects.addSource(project.id, link);
    setLink("");
    onAdded?.(source);
  }
  return (
    <form onSubmit={submit} className="space-y-2">
      <LinkInput value={link} onChange={setLink} />
      <Button type="submit" kind="primary" disabled={!link.trim() || badLink(link)}>
        {m.add_folder()}
      </Button>
    </form>
  );
}
