// Saved loops of a recording, their own section under a line: the heading with a name and Save loop, then
// the loops kept under a name to bring back (the loop turns on), ✕ to delete. Kept in the practice memory.

import { BookmarkPlus, X } from "lucide-react";
import { type FormEvent, useState } from "react";
import { clock } from "../../core/format";
import { deleteLoop, type Loop, practice, saveLoop, savedLoops } from "../../core/practice";
import { useStore } from "../../core/store";
import { m } from "../../paraglide/messages.js";
import { Muted } from "../kit/bits";
import { Button } from "../kit/Button";

type Props = { project: string; recording: string; loop: Loop | null; onUse: (loop: Loop) => void };

export function SavedLoops({ project, recording, loop, onUse }: Props) {
  useStore(practice);
  const list = savedLoops(project, recording);
  const [name, setName] = useState("");
  const fallback = m.loop_name_placeholder({ n: list.length + 1 });
  const same = (a: { start: number; end: number }) =>
    !!loop && Math.abs(a.start - loop.start) < 0.05 && Math.abs(a.end - loop.end) < 0.05;

  function save(event: FormEvent) {
    event.preventDefault();
    if (!loop) return;
    saveLoop(project, recording, { name: name.trim() || fallback, start: loop.start, end: loop.end });
    setName("");
  }

  return (
    <div className="space-y-2 border-t border-zinc-200 pt-3 dark:border-zinc-800">
      <form onSubmit={save} className="flex flex-wrap items-center gap-2">
        <span className="mr-auto text-sm font-semibold">{m.saved_loops()}</span>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={fallback}
          className="w-32 rounded-lg border border-zinc-300 bg-transparent px-2 py-1 text-sm dark:border-zinc-700"
        />
        <Button type="submit" disabled={!loop}>
          <BookmarkPlus size={16} /> {m.save_loop()}
        </Button>
      </form>
      <div className="flex flex-wrap items-center gap-2">
        {list.map((saved, index) => (
          <span key={index} className="inline-flex items-center">
            <Button
              active={same(saved)}
              className="!rounded-r-none !py-1"
              onClick={() => onUse({ start: saved.start, end: saved.end, on: true })}
              title={`${clock(saved.start, true)} – ${clock(saved.end, true)}`}
            >
              {saved.name}
            </Button>
            <Button
              className="!rounded-l-none border-l-0 !px-1.5 !py-1 text-zinc-500"
              onClick={() => deleteLoop(project, recording, index)}
              aria-label={m.delete_saved({ name: saved.name })}
              title={m.delete_saved({ name: saved.name })}
            >
              <X size={14} />
            </Button>
          </span>
        ))}
        {!list.length && <Muted>{m.no_saved()}</Muted>}
      </div>
    </div>
  );
}
