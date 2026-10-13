// Tailwind works: a real Vite build of the app (into a temp folder) must give CSS with the utilities
// the components use, the theme's accent colours, the class-based dark variant, breakpoints and the
// custom `range` utility, and none of the utilities nobody uses.
import { mkdtempSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { build } from "vite";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

let css = "";
const out = mkdtempSync(join(tmpdir(), "downtempo-css-"));

beforeAll(async () => {
  await build({ root: join(import.meta.dirname, ".."), logLevel: "silent", build: { outDir: out, emptyOutDir: true } });
  const assets = join(out, "assets");
  css = readdirSync(assets)
    .filter((name) => name.endsWith(".css"))
    .map((name) => readFileSync(join(assets, name), "utf8"))
    .join("\n");
}, 60_000);

afterAll(() => rmSync(out, { recursive: true, force: true }));

describe("tailwind", () => {
  it("emits the utilities the components use", () => {
    for (const selector of [".flex", ".rounded-full", ".bg-accent-600", ".tabular-nums", ".truncate", ".size-11"]) {
      expect(css).toContain(selector);
    }
  });

  it("has the theme's accent colours", () => {
    expect(css).toMatch(/--color-accent-600:\s*oklch\(/);
  });

  it("dark mode follows the .dark class", () => {
    expect(css).toMatch(/\.dark[\s,]/);
    expect(css).toMatch(/dark\\:bg-zinc-900/);
  });

  it("has breakpoints and the custom range utility", () => {
    expect(css).toMatch(/md\\:static/);
    expect(css).toMatch(/@media \(width>=48rem\)|@media \(min-width:\s*48rem\)/);
    expect(css).toContain(".range");
    expect(css).toMatch(/slider-thumb/);
  });

  it("leaves out unused utilities", () => {
    expect(css).not.toContain(".bg-pink-500");
  });
});
