// The sheet's state and actions for one song, without pdf.js (that loads with SheetPages): which PDF,
// the view's size, zoom or fit page, rotation (one per device), Sheet only, the scroll keys. The
// parts (SheetFrame, SheetToolbar, SheetMenu) take this object; the song page's layouts place them.

import { type CSSProperties, useEffect, useRef, useState } from "react";
import * as files from "../../core/files";
import type { SongFile } from "../../core/grouping";
import { sheetLook } from "../../core/practice";
import { useStore } from "../../core/store";
import { useBackCloses } from "../kit/back";
import { useKeys } from "../kit/keys";

// zoom: page width as a share of the view's; trim: cm cut from every side of the page (0, 0.5, 1, 2)
export type SheetView = { zoom: number; fit: "page" | null; trim: number };
export type PageSize = { w: number; h: number }; // in PDF points (1/72 inch)
export const TRIMS = [0, 0.5, 1, 2];
const POINTS_PER_CM = 72 / 2.54;
export type Sheet = ReturnType<typeof useSheet>;

const ZOOMS = [0.5, 0.67, 0.8, 0.9, 1, 1.25, 1.5, 2, 3];
// The view turns as a whole, so its scrollbar, the wheel and the scroll keys follow the page; the
// frame is a size container, 100cqw / 100cqh its width / height (as the Python player's sheet pane).
export const TURNS: Record<number, CSSProperties> = {
  0: { width: "100%", height: "100%" },
  90: { width: "100cqh", height: "100cqw", transformOrigin: "0 0", transform: "translateX(100cqw) rotate(90deg)" },
  180: { width: "100%", height: "100%", transform: "rotate(180deg)" },
  270: { width: "100cqh", height: "100cqw", transformOrigin: "0 0", transform: "translateY(100cqh) rotate(-90deg)" },
};

type Args = {
  project: string;
  sheet: SongFile | null;
  sheets: SongFile[];
  pickSheet: (key: string) => void;
  view: SheetView;
  onView: (view: SheetView) => void;
  edge: number; // the grey margin around and between the pages: 12 px with room, 0 on a phone (the page fills the width)
};

export function useSheet({ project, sheet, sheets, pickSheet, view, onView, edge }: Args) {
  const [sizes, setSizes] = useState<PageSize[]>([]); // each page's size, from SheetPages
  const [size, setSize] = useState({ w: 0, h: 0 }); // the view's own (turned) size
  const [only, setOnly] = useState(false); // Sheet only: the app's bars and menus hidden (docs/sheet-only.md)
  const [bar, setBar] = useState(false); // in Sheet only: the slim bar with ← shown
  const barTimer = useRef(0);
  const { rotate } = useStore(sheetLook);
  const frame = useRef<HTMLDivElement>(null);
  const scroller = useRef<HTMLDivElement>(null);
  const pages = useRef<HTMLDivElement>(null);
  const fitAt = useRef(0); // the page fit page fits
  const target = useRef<number | null>(null); // where a smooth scroll is going
  const settle = useRef(0);

  // Pages are redrawn for a new size only after resizing pauses.
  useEffect(() => {
    const element = scroller.current;
    if (!element) return;
    let timer = 0;
    const observer = new ResizeObserver(([entry]) => {
      clearTimeout(timer);
      const next = { w: Math.floor(entry.contentRect.width), h: Math.floor(entry.contentRect.height) };
      timer = window.setTimeout(() => setSize(next), size.w ? 150 : 0);
    });
    observer.observe(element);
    return () => {
      observer.disconnect();
      clearTimeout(timer);
    };
  }, [size.w, sheet]);

  // Sheet only: the phone's Back leaves it; the screen stays on while it lasts (where the browser can).
  useBackCloses(only, () => setOnly(false));
  useEffect(() => {
    if (!only || !("wakeLock" in navigator)) return;
    let lock: WakeLockSentinel | null = null;
    let gone = false;
    const take = () =>
      navigator.wakeLock
        .request("screen")
        .then((got) => (gone ? void got.release() : (lock = got)))
        .catch(() => {}); // refused (battery saver, no permission): the screen may dim, nothing more
    const back = () => document.visibilityState === "visible" && void take(); // a hidden page loses its lock
    void take();
    document.addEventListener("visibilitychange", back);
    return () => {
      gone = true;
      document.removeEventListener("visibilitychange", back);
      void lock?.release();
    };
  }, [only]);

  // Fit page: the page whole in the view, never wider than fit width.
  // Trim margins: what shows of a page is its size less the trim on every side (at most a quarter each way).
  const trim = (view.trim ?? 0) * POINTS_PER_CM;
  const shown = (size: PageSize | undefined) => {
    const page = size ?? { w: 595, h: 842 }; // A4 until the PDF says
    const cut = Math.min(trim, page.w / 4, page.h / 4);
    return { w: page.w - 2 * cut, h: page.h - 2 * cut, cut };
  };
  const fitZoom = () => {
    const part = shown(sizes[fitAt.current] ?? sizes[0]);
    const shape = part.h / part.w;
    return Math.min(1, ((size.h - 2 * edge) / shape + 2 * edge) / Math.max(1, size.w));
  };
  const zoom = view.fit === "page" ? fitZoom() : view.zoom;

  const pageAtTop = () => {
    const el = scroller.current;
    const children = [...(pages.current?.children ?? [])] as HTMLElement[];
    if (!el || !children.length) return 0;
    return Math.max(
      0,
      children.findLastIndex((c) => c.offsetTop - 16 <= el.scrollTop + 24),
    );
  };
  const toPage = (index: number) =>
    requestAnimationFrame(() =>
      requestAnimationFrame(() => {
        const child = pages.current?.children[index] as HTMLElement | undefined;
        if (child && scroller.current) scroller.current.scrollTo({ top: child.offsetTop - edge });
      }),
    );

  // A press during a smooth scroll goes on from where that one is going: a quick double tap on a
  // footswitch moves two steps.
  const scrollTo = (top: number) => {
    const el = scroller.current;
    if (!el) return;
    top = Math.max(0, Math.min(top, el.scrollHeight - el.clientHeight));
    target.current = top;
    clearTimeout(settle.current);
    settle.current = window.setTimeout(() => (target.current = null), 600);
    el.scrollTo({ top, behavior: "smooth" });
  };
  const scrollBy = (share: number) => {
    const el = scroller.current;
    if (el) scrollTo((target.current ?? el.scrollTop) + el.clientHeight * share);
  };

  const zoomStep = (by: number) => {
    const index = ZOOMS.findIndex((z) => z >= zoom - 0.001);
    const next = ZOOMS[Math.min(ZOOMS.length - 1, Math.max(0, (index < 0 ? ZOOMS.length - 1 : index) + by))];
    onView({ ...view, zoom: next, fit: null });
  };
  const fitWidth = () => onView({ ...view, zoom: 1, fit: null });
  const fitPage = () => {
    fitAt.current = pageAtTop();
    onView({ ...view, fit: "page" });
    toPage(fitAt.current);
  };
  const setTrim = (cm: number) => {
    fitAt.current = pageAtTop();
    onView({ ...view, trim: cm });
    toPage(fitAt.current);
  };
  const turn = (by: number) => sheetLook.set({ rotate: (rotate + by + 360) % 360 });
  const showBar = (on: boolean, forAMoment = false) => {
    clearTimeout(barTimer.current);
    setBar(on);
    if (on && forAMoment) barTimer.current = window.setTimeout(() => setBar(false), 3000);
  };
  const sheetOnly = (on: boolean) => {
    setOnly(on);
    showBar(on, true); // on entering: the bar and its hint for a moment
  };
  /** In Sheet only a tap's place decides: the left third a screen back, the right third on, the middle the bar. */
  const tap = (x: number) => {
    const box = frame.current?.getBoundingClientRect();
    if (!only || !box) return;
    const at = (x - box.left) / box.width;
    if (at < 1 / 3) scrollBy(-0.85);
    else if (at > 2 / 3) scrollBy(0.85);
    else showBar(!bar);
  };
  const openPdf = () => {
    if (!sheet) return;
    void files.open(project, sheet.key).then((file) => {
      const url = URL.createObjectURL(file);
      window.open(url, "_blank");
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    });
  };

  const on = (action: () => void) => () => sheet && action();
  useKeys({
    ArrowDown: on(() => scrollBy(0.2)),
    ArrowUp: on(() => scrollBy(-0.2)),
    PageDown: on(() => scrollBy(0.85)),
    PageUp: on(() => scrollBy(-0.85)),
    Home: on(() => scrollTo(0)),
    End: on(() => scrollTo(Number.MAX_SAFE_INTEGER)),
    "+": on(() => zoomStep(1)),
    "=": on(() => zoomStep(1)),
    "-": on(() => zoomStep(-1)),
    w: on(fitWidth),
    h: on(fitPage),
    o: on(() => turn(90)),
    f: on(() => sheetOnly(!only)),
    Escape: () => only && sheetOnly(false),
  });

  return {
    project,
    sheet,
    sheets,
    pickSheet,
    view,
    zoom,
    contentWidth: Math.max(size.w * zoom, 200),
    edge,
    ready: size.w > 0,
    rotate,
    only,
    bar,
    sheetOnly,
    tap,
    sizes,
    setSizes,
    shown, // a page's size less the trimmed margins, and how much is cut
    setTrim,
    refs: { frame, scroller, pages },
    zoomStep,
    fitWidth,
    fitPage,
    turn,
    openPdf,
  };
}
