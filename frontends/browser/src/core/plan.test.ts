import { describe, expect, it } from "vitest";
import { storedAs } from "./compress";
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
      { source: "s1", files: [remote("same.mp3"), remote("bigger.mp3"), remote("newer.pdf"), remote("new.pdf", 7)] },
    ]);
    expect(result.fetch.map((f) => [f.key, f.fresh])).toEqual([
      ["s1/bigger.mp3", false],
      ["s1/newer.pdf", false],
      ["s1/new.pdf", true],
    ]);
    expect(result.same).toBe(1);
    expect(result.gone).toEqual(["s1/gone.mp3"]);
    expect(result.bytes).toBe(27);
  });

  it("wavs are kept as mp3: new ones fetched, old ones compressed on the device", () => {
    const local = {
      "s1/kept.mp3": { size: 3, modified: "2026-01-02T00:00:00Z" }, // made from the wav: time only
      "s1/old.wav": { size: 10, modified: "2026-01-02T00:00:00Z" }, // downloaded before compression
      "s1/stale.wav": { size: 10, modified: "2026-01-01T00:00:00Z" }, // the server's is newer
    };
    const result = plan(local, [
      {
        source: "s1",
        files: [
          remote("kept.wav"),
          remote("old.wav"),
          remote("stale.wav"),
          remote("new.WAV"),
          remote("both.wav"),
          remote("both.mp3"),
        ],
      },
    ]);
    expect(result.same).toBe(1);
    expect(result.compress.map((f) => [f.listed, f.key])).toEqual([["s1/old.wav", "s1/old.mp3"]]);
    expect(result.fetch.map((f) => [f.listed, f.key, f.fresh])).toEqual([
      ["s1/stale.wav", "s1/stale.mp3", false],
      ["s1/new.WAV", "s1/new.mp3", true],
      ["s1/both.wav", "s1/both.wav", true],
      ["s1/both.mp3", "s1/both.mp3", true],
    ]);
    expect(result.gone).toEqual([]);
  });
});

describe("storedAs", () => {
  it("a wav is an mp3 unless the server has that mp3 too", () => {
    expect(storedAs("a/Song.wav", new Set())).toBe("a/Song.mp3");
    expect(storedAs("a/Song.WAV", new Set(["a/song.mp3"]))).toBe("a/Song.WAV");
    expect(storedAs("a/Song.pdf", new Set())).toBe("a/Song.pdf");
  });
});
