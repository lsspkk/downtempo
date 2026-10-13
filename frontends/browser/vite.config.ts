/// <reference types="vitest/config" />
// Build and dev server. Dev runs on localhost:8000 at "/" and the build lives at /downtempo/ on
// GitHub Pages: both are redirect URIs in the Entra registration, so the paths must stay as they are.
import { paraglideVitePlugin } from "@inlang/paraglide-js";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig(({ command, isPreview }) => ({
  base: command === "build" || isPreview ? "/downtempo/" : "/",
  plugins: [
    react(),
    tailwindcss(),
    // messages/<language>.json → src/paraglide/ (generated): one typed function per text, m.download()
    paraglideVitePlugin({
      project: "./project.inlang",
      outdir: "./src/paraglide",
      strategy: ["localStorage", "preferredLanguage", "baseLocale"],
      localStorageKey: "downtempo-language",
      emitTsDeclarations: true,
    }),
  ],
  server: { port: 8000, strictPort: true },
  test: { include: ["src/**/*.test.ts"] },
}));
