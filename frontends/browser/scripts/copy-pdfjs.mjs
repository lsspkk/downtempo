// Copies pdf.js's data files (standard fonts, character maps, image decoders, colour profiles) to
// public/pdfjs/, where the sheet viewer fetches them in dev and Vite copies them into the build.
import { cpSync, rmSync } from "node:fs";

rmSync("public/pdfjs", { recursive: true, force: true });
for (const dir of ["cmaps", "standard_fonts", "wasm", "iccs"]) {
  cpSync(`node_modules/pdfjs-dist/${dir}`, `public/pdfjs/${dir}`, { recursive: true });
}
