// The sheet's place: a size container whose scroll view turns as a whole with the rotation, the pages
// (pdf.js, loaded with the first sheet) inside. In Sheet only (docs/sheet-only.md) it covers the whole
// screen over the app's bars; taps on the sides turn, a tap in the middle shows a slim bar with ←.

import { ArrowLeft } from "lucide-react";
import { lazy, Suspense } from "react";
import { m } from "../../paraglide/messages.js";
import { Muted } from "../kit/bits";
import { IconButton } from "../kit/Button";
import { TURNS, type Sheet } from "./useSheet";

const SheetPages = lazy(() => import("./SheetPages").then((module) => ({ default: module.SheetPages })));

export function SheetFrame({ sheet }: { sheet: Sheet }) {
  return (
    <div
      ref={sheet.refs.frame}
      className={`overflow-hidden bg-zinc-200 dark:bg-zinc-800 ${sheet.only ? "fixed inset-0 z-[60]" : "relative min-h-0 flex-1"}`}
      style={{ containerType: "size" }}
      onClick={(event) => sheet.tap(event.clientX)}
    >
      <div
        ref={sheet.refs.scroller}
        className="absolute top-0 left-0 overflow-auto"
        style={TURNS[sheet.rotate] ?? TURNS[0]}
      >
        <Suspense fallback={<Muted className="p-6 text-center">{m.opening_sheet()}</Muted>}>
          <SheetPages sheet={sheet} />
        </Suspense>
      </div>
      {sheet.only && sheet.bar && <OnlyBar sheet={sheet} />}
    </div>
  );
}

/** The slim bar: ← to leave, the mode's name, and how the taps work. */
function OnlyBar({ sheet }: { sheet: Sheet }) {
  return (
    <div
      className="absolute inset-x-0 top-0 flex items-center gap-2 border-b border-zinc-200 bg-white/95 px-1 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/95"
      onClick={(event) => event.stopPropagation()}
    >
      <IconButton label={m.back()} onClick={() => sheet.sheetOnly(false)}>
        <ArrowLeft size={22} />
      </IconButton>
      <div className="min-w-0 flex-1 py-1">
        <p className="truncate text-sm font-semibold">{m.full_screen_title()}</p>
        <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">{m.sheet_only_hint()}</p>
      </div>
    </div>
  );
}

export const NoSheet = () => (
  <div className="flex flex-1 items-center justify-center bg-zinc-100 dark:bg-zinc-950">
    <Muted>{m.no_sheet()}</Muted>
  </div>
);
