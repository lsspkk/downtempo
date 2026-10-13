// The top bar's frame and its fixed pieces; each page puts its own buttons in it (the song page's
// two layouts, Get the songs, Settings). 48 px high everywhere: the phone's drop-down sheets open
// right under it (DropDown: top-12).

import { ArrowLeft, ListMusic, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import type { ReactNode } from "react";
import { m } from "../../paraglide/messages.js";
import { Button, IconButton } from "../kit/Button";

export const Bar = ({ children }: { children: ReactNode }) => (
  <header className="relative flex h-12 shrink-0 items-center border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
    {children}
  </header>
);

/** The bar's left end; over an open song list (md and up) as wide as the list, with the same edge. */
export const BarStart = ({ overList = false, children }: { overList?: boolean; children: ReactNode }) => (
  <div
    className={`flex h-full shrink-0 items-center gap-0.5 border-zinc-200 px-1 sm:gap-1 sm:px-2 dark:border-zinc-800 ${overList ? "md:w-64 md:border-r" : ""}`}
  >
    {children}
  </div>
);

export const BarTitle = ({ children }: { children: string }) => (
  <h1 className="ml-3 min-w-0 truncate font-semibold" title={children}>
    {children}
  </h1>
);

/** Shows or hides the song list: a side panel with a pointer, a page of its own on a phone. */
export function ListButton({ open, onClick, phone = false }: { open: boolean; onClick: () => void; phone?: boolean }) {
  const label = open ? m.hide_list() : m.show_list();
  return (
    <IconButton label={label} onClick={onClick}>
      {phone ? <ListMusic size={20} /> : open ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
    </IconButton>
  );
}

/** ← Back and the page's title (on a phone ← alone, as the standard page bar); on wide screens the
 * title stands where the page's column starts. */
export function BackTitle({ title, onBack }: { title: string; onBack: () => void }) {
  return (
    <div className="flex min-w-0 flex-1 items-center gap-2 px-1 sm:gap-8">
      <IconButton label={m.back()} onClick={onBack} className="sm:hidden">
        <ArrowLeft size={22} />
      </IconButton>
      <Button kind="quiet" onClick={onBack} title={`${m.back()} (Esc)`} className="max-sm:hidden">
        <ArrowLeft size={18} /> {m.back()}
      </Button>
      <h1 className="truncate text-lg font-semibold lg:pointer-events-none lg:absolute lg:inset-y-0 lg:left-1/2 lg:flex lg:w-full lg:max-w-2xl lg:-translate-x-1/2 lg:items-center lg:px-4">
        {title}
      </h1>
    </div>
  );
}
