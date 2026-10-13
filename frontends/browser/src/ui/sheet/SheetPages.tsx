// The PDF's pages, drawn by pdf.js (most of the app's size: this module loads with the first sheet).
// It reports each page's size to the sheet (for fit page and trimming) and draws the pages at the
// sheet's width; with trimmed margins a page shows only its middle, in a box exactly that wide.

// The legacy build: pdf.js 6 itself uses 2026 JavaScript (Map.getOrInsertComputed) older browsers lack.
import * as pdfjs from "pdfjs-dist/legacy/build/pdf.mjs";
import type { PDFDocumentProxy } from "pdfjs-dist/legacy/build/pdf.mjs";
import workerUrl from "pdfjs-dist/legacy/build/pdf.worker.min.mjs?url";
import { useEffect, useRef, useState } from "react";
import * as files from "../../core/files";
import { m } from "../../paraglide/messages.js";
import { Muted } from "../kit/bits";
import type { Sheet } from "./useSheet";

pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;
// Fonts a PDF doesn't embed, character maps, and the decoders scanned sheets need (JBIG2, JPEG 2000);
// copied to public/pdfjs/ by `npm install` (scripts/copy-pdfjs.mjs).
const ASSETS = `${import.meta.env.BASE_URL}pdfjs/`;
const OPTIONS = {
  cMapUrl: `${ASSETS}cmaps/`,
  standardFontDataUrl: `${ASSETS}standard_fonts/`,
  wasmUrl: `${ASSETS}wasm/`,
  iccUrl: `${ASSETS}iccs/`,
};

export function SheetPages({ sheet }: { sheet: Sheet }) {
  const [doc, setDoc] = useState<PDFDocumentProxy | null>(null);
  const [error, setError] = useState("");
  const { project, setSizes } = sheet;
  const key = sheet.sheet?.key;

  useEffect(() => {
    if (!key) return;
    let gone = false;
    let task: ReturnType<typeof pdfjs.getDocument> | null = null;
    setDoc(null);
    setError("");
    files
      .open(project, key)
      .then(async (file) => {
        const data = new Uint8Array(await file.arrayBuffer());
        if (gone) return;
        task = pdfjs.getDocument({ data, ...OPTIONS });
        const loaded = await task.promise;
        const sizes = await Promise.all(
          Array.from({ length: loaded.numPages }, (_, i) =>
            loaded.getPage(i + 1).then((page) => {
              const { width, height } = page.getViewport({ scale: 1 });
              return { w: width, h: height };
            }),
          ),
        );
        if (gone) return;
        setSizes(sizes);
        setDoc(loaded);
      })
      .catch(
        (e) => !gone && setError(e.name === "NotFoundError" ? m.file_gone() : m.cant_open_pdf({ reason: e.message })),
      );
    return () => {
      gone = true;
      void task?.destroy();
    };
  }, [project, key, setSizes]);

  if (error) return <Muted className="p-6 text-center">⚠ {error}</Muted>;
  if (!doc || !sheet.ready) return null;
  return (
    <div
      ref={sheet.refs.pages}
      className="mx-auto flex flex-col items-center"
      style={{ width: sheet.contentWidth, padding: sheet.edge, gap: Math.max(2, sheet.edge) }}
    >
      {Array.from({ length: doc.numPages }, (_, i) => (
        <Page
          key={i}
          doc={doc}
          number={i + 1}
          width={sheet.contentWidth - 2 * sheet.edge}
          part={sheet.shown(sheet.sizes[i])}
        />
      ))}
    </div>
  );
}

/** One page: drawn whole at the scale that makes its shown part `width` wide, then cut to that part. */
function Page({
  doc,
  number,
  width,
  part,
}: {
  doc: PDFDocumentProxy;
  number: number;
  width: number;
  part: { w: number; h: number; cut: number };
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const scale = width / part.w;
  const offset = part.cut * scale;

  useEffect(() => {
    let task: ReturnType<Awaited<ReturnType<PDFDocumentProxy["getPage"]>>["render"]> | null = null;
    let gone = false;
    void doc.getPage(number).then((page) => {
      if (gone || !canvas.current) return;
      const ratio = window.devicePixelRatio || 1;
      const viewport = page.getViewport({ scale: scale * ratio });
      const element = canvas.current;
      element.width = Math.floor(viewport.width);
      element.height = Math.floor(viewport.height);
      element.style.width = `${viewport.width / ratio}px`;
      element.style.height = `${viewport.height / ratio}px`;
      task = page.render({ canvas: element, viewport });
      task.promise.catch(() => {}); // cancelled by a newer width
    });
    return () => {
      gone = true;
      task?.cancel();
    };
  }, [doc, number, scale]);

  return (
    <div
      className="relative shrink-0 overflow-hidden bg-white shadow-md max-sm:shadow-none"
      style={{ width, height: part.h * scale }}
    >
      <canvas ref={canvas} className="absolute max-w-none" style={{ left: -offset, top: -offset }} />
    </div>
  );
}
