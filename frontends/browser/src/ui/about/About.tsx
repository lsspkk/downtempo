// About ("Tietoja"), from the ☰ menu: what Downtempo is, that this online version is a demonstration
// (for regular use, run your own copy), and exactly what happens to the musician's account and files.
// A page over everything like Settings: ← Back, Esc and the phone's Back close it.

import { ExternalLink } from "lucide-react";
import type { ReactNode } from "react";
import { m } from "../../paraglide/messages.js";
import { Bar, BackTitle, BarStart } from "../bar/Bar";
import { useBackCloses } from "../kit/back";
import { useKeys } from "../kit/keys";

const REPOSITORY = "https://github.com/lsspkk/downtempo";

export function AboutPage({ menu, onClose }: { menu: ReactNode; onClose: () => void }) {
  useKeys({ Escape: onClose });
  useBackCloses(true, onClose);
  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-zinc-50 dark:bg-zinc-950">
      <Bar>
        <div className="max-sm:hidden">
          <BarStart>{menu}</BarStart>
        </div>
        <BackTitle title={m.about()} onBack={onClose} />
      </Bar>
      <div className="min-h-0 flex-1 overflow-y-auto [scrollbar-gutter:stable_both-edges]">
        <article className="mx-auto max-w-2xl space-y-8 px-4 py-6 leading-relaxed">
          <header className="space-y-2">
            <h2 className="text-2xl font-bold tracking-tight">
              <span aria-hidden>🎻</span> Downtempo
            </h2>
            <p className="text-zinc-600 dark:text-zinc-300">{m.about_intro()}</p>
          </header>

          <p className="rounded-lg border-l-4 border-amber-500 bg-amber-500/10 px-4 py-3 text-sm">{m.about_demo()}</p>

          <section className="space-y-3">
            <h3 className="font-semibold">{m.about_data_title()}</h3>
            <ul className="list-disc space-y-2 pl-5 text-sm">
              <li>{m.about_signin()}</li>
              <li>{m.about_kept()}</li>
              <li>{m.about_reads()}</li>
              <li>{m.about_copies()}</li>
              <li>{m.about_no_server()}</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h3 className="font-semibold">{m.about_remove_title()}</h3>
            <p className="text-sm">{m.about_remove()}</p>
          </section>

          <a
            href={REPOSITORY}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-accent-600 hover:underline dark:text-accent-400"
          >
            <ExternalLink size={16} /> {m.about_source()}
          </a>
        </article>
      </div>
    </div>
  );
}
