import { describe, expect, it } from "vitest";
import { plan } from "./plan";

const remote = (path: string, size = 10, modified = "2026-01-02T00:00:00Z") => ({
  path,
  size,
  modified,
  drive: "d",
  id: path,
});

describe("plan", () => {
  it("new, changed, same and gone", () => {
    const local = {
      "s1/same.mp3": { size: 10, modified: "2026-01-02T00:00:00Z" },
      "s1/bigger.mp3": { size: 5, modified: "2026-01-02T00:00:00Z" },
      "s1/newer.pdf": { size: 10, modified: "2026-01-01T00:00:00Z" },
      "s1/gone.mp3": { size: 10, modified: "2026-01-01T00:00:00Z" },
      "s2/other source.mp3": { size: 10, modified: "2026-01-01T00:00:00Z" },
    };
    const result = plan(local, [
      { source: "s1", files: [remote("same.mp3"), remote("bigger.mp3"), remote("newer.pdf"), remote("new.wav", 7)] },
    ]);
    expect(result.fetch.map((f) => [f.key, f.fresh])).toEqual([
      ["s1/bigger.mp3", false],
      ["s1/newer.pdf", false],
      ["s1/new.wav", true],
    ]);
    expect(result.same).toBe(1);
    expect(result.gone).toEqual(["s1/gone.mp3"]);
    expect(result.bytes).toBe(27);
  });
});
