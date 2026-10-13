// First start and New project, one question per step (ux.md #13): 1 the group's name, 2 the link to
// its shared folder (or later). Steps 3 (sign in) and 4 (folders) follow on the Get the songs page.

import { type FormEvent, useState } from "react";
import * as projects from "../../core/projects";
import { m } from "../../paraglide/messages.js";
import { badLink, LinkInput } from "../folders/LinkInput";
import { Muted, Step } from "../kit/bits";
import { Button } from "../kit/Button";

export function Welcome({ first, onClose, onDone }: { first: boolean; onClose?: () => void; onDone: () => void }) {
  const [step, setStep] = useState<1 | 2>(1);
  const [name, setName] = useState(first ? m.first_project_name() : "");
  const [link, setLink] = useState("");
  const bad = badLink(link);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (step === 1) return setStep(2);
    if (bad || !link.trim()) return;
    finish(link);
  }
  function finish(withLink: string) {
    projects.create(name, withLink); // its folders are chosen next, on the Get the songs page
    onDone();
  }

  return (
    <main className="flex min-h-full items-center justify-center p-4">
      <form
        onSubmit={submit}
        className="w-full max-w-lg space-y-5 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-zinc-200 sm:p-8 dark:bg-zinc-900 dark:ring-zinc-800"
      >
        {first && step === 1 && (
          <header className="space-y-2">
            <h1 className="text-2xl font-bold tracking-tight">
              <span aria-hidden>🎻</span> Downtempo
            </h1>
            <p className="text-zinc-600 dark:text-zinc-300">{m.app_intro()}</p>
          </header>
        )}
        {!first && step === 1 && <p className="text-sm font-medium text-zinc-500">{m.new_project()}</p>}

        <Step n={step} />
        {step === 1 ? (
          <label className="block space-y-2">
            <span className="block text-xl font-semibold">{m.ask_name()}</span>
            <Muted>{m.project_is()}</Muted>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
              className="block w-full rounded-lg border border-zinc-300 bg-transparent px-3 py-2 dark:border-zinc-700"
            />
          </label>
        ) : (
          <div className="space-y-2">
            <h2 className="text-xl font-semibold">{m.ask_link()}</h2>
            <LinkInput value={link} onChange={setLink} autoFocus hint={m.link_hint()} />
          </div>
        )}

        <div className="flex flex-wrap items-center gap-2">
          {step === 2 && (
            <Button kind="quiet" onClick={() => setStep(1)}>
              {m.back()}
            </Button>
          )}
          {step === 1 && onClose && (
            <Button kind="quiet" onClick={onClose}>
              {m.cancel()}
            </Button>
          )}
          <span className="flex-1" />
          {step === 2 && (
            <Button kind="quiet" onClick={() => finish("")}>
              {m.skip_link()}
            </Button>
          )}
          <Button type="submit" kind="primary" disabled={step === 2 && (bad || !link.trim())}>
            {m.next()}
          </Button>
        </div>
        {first && step === 1 && (
          <Muted className="border-t border-zinc-200 pt-4 dark:border-zinc-800">{m.stays_here()}</Muted>
        )}
      </form>
    </main>
  );
}
