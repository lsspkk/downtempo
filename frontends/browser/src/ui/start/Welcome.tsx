// First start and New project: one full page, not a wizard. First start: what Downtempo is, what
// it does and why a link is asked (left) beside one plain form (right): the project's name and the
// link to its shared folder. The link explanation is said once: in the intro, or folded in the form
// when there is no intro. Signing in and choosing folders follow on the Get the songs page.

import { ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import { type FormEvent, useState } from "react";
import * as projects from "../../core/projects";
import { m } from "../../paraglide/messages.js";
import { Bar, BarTitle } from "../bar/Bar";
import { LanguageSwitch } from "../bar/LanguageSwitch";
import { badLink, LinkInput } from "../folders/LinkInput";
import { Muted } from "../kit/bits";
import { Button } from "../kit/Button";

export const ONEDRIVE_SHARING_HELP =
  "https://support.microsoft.com/en-us/office/share-onedrive-files-and-folders-9fcc2f7d-de0c-4cec-93b0-a82024800c07";

const Bullets = ({ items }: { items: string[] }) => (
  <ul className="list-disc space-y-1 pl-5 text-sm">
    {items.map((t) => (
      <li key={t}>{t}</li>
    ))}
  </ul>
);

/** On a phone the details start hidden behind one button, so the form is the first thing to reach
 * (NN/g mobile accordions: condense, expand in place without scrolling away); on a desktop all shows. */
function About() {
  const [open, setOpen] = useState(false);
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">
          <span aria-hidden>🎻</span> Downtempo
        </h2>
        <p className="text-lg text-zinc-600 dark:text-zinc-300">{m.app_intro()}</p>
      </header>
      <Button className="w-full !justify-between md:hidden" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        {m.info_show()} {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </Button>
      <div className={`space-y-6 ${open ? "" : "max-md:hidden"}`}>
        <section className="space-y-2">
          <h2 className="font-semibold">{m.intro_how_title()}</h2>
          <Bullets items={[m.intro_how_1(), m.intro_how_2(), m.intro_how_3()]} />
        </section>
        <section className="space-y-2">
          <h2 className="font-semibold">{m.intro_trust_title()}</h2>
          <Bullets items={[m.intro_trust_1(), m.intro_trust_2(), m.intro_trust_3()]} />
        </section>
        <section className="space-y-2">
          <h2 className="font-semibold">{m.intro_storage_title()}</h2>
          <p className="text-sm">{m.intro_storage()}</p>
          <HelpLink href={OPFS_HELP}>{m.storage_help()}</HelpLink>
        </section>
        <section className="space-y-2">
          <h2 className="font-semibold">{m.link_why_title()}</h2>
          <LinkExplained />
        </section>
      </div>
    </div>
  );
}

const OPFS_HELP = "https://developer.mozilla.org/en-US/docs/Web/API/File_System_API/Origin_private_file_system";

const HelpLink = ({ href, children }: { href: string; children: string }) => (
  <a
    href={href}
    target="_blank"
    rel="noreferrer"
    className="inline-flex items-center gap-1.5 text-sm font-medium text-accent-600 hover:underline dark:text-accent-400"
  >
    <ExternalLink size={16} /> {children}
  </a>
);

function LinkExplained() {
  return (
    <div className="space-y-2 text-sm">
      <p>{m.link_why_what()}</p>
      <p>{m.link_why_who()}</p>
      <p>{m.link_why_how()}</p>
      <HelpLink href={ONEDRIVE_SHARING_HELP}>{m.link_help()}</HelpLink>
    </div>
  );
}

/** The same explanation folded away, for pages that don't show the intro. */
export function WhyLink() {
  return (
    <details className="rounded-lg bg-zinc-100 p-3 dark:bg-zinc-800/60">
      <summary className="cursor-pointer text-sm font-semibold">{m.link_why_title()}</summary>
      <div className="mt-2">
        <LinkExplained />
      </div>
    </details>
  );
}

export function Welcome({ first, onClose, onDone }: { first: boolean; onClose?: () => void; onDone: () => void }) {
  const [name, setName] = useState(first ? m.first_project_name() : "");
  const [link, setLink] = useState("");
  const bad = badLink(link);

  function create(withLink: string) {
    projects.create(name, withLink); // its folders are chosen next, on the Get the songs page
    onDone();
  }
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!bad && link.trim()) create(link);
  }

  return (
    <div className="flex h-full flex-col">
      <Bar>
        <BarTitle>{first ? "Downtempo" : m.new_project()}</BarTitle>
        <LanguageSwitch />
      </Bar>
      <main className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto grid max-w-5xl gap-8 px-4 py-8 md:grid-cols-2 md:gap-12 md:py-12">
          {first && <About />}
          <form onSubmit={submit} className="space-y-5">
            <h2 className="text-xl font-semibold">{m.create_project()}</h2>
            <label className="block space-y-1">
              <span className="text-sm font-medium">{m.project()}</span>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
                className="block w-full rounded-lg border border-zinc-300 bg-transparent px-3 py-2 dark:border-zinc-700"
              />
              <Muted>{m.project_is()}</Muted>
            </label>
            <LinkInput value={link} onChange={setLink} hint={m.link_hint()} />
            {!first && <WhyLink />}
            <div className="flex flex-wrap items-center gap-2">
              {onClose && (
                <Button kind="quiet" onClick={onClose}>
                  {m.cancel()}
                </Button>
              )}
              <span className="flex-1" />
              <Button type="submit" kind="primary" disabled={bad || !link.trim()}>
                {m.create_project()}
              </Button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
