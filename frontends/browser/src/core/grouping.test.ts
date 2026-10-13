import { describe, expect, it } from "vitest";
import { clean, editDistance, group, related, slug } from "./grouping";

describe("clean", () => {
  it.each([
    ["Harbour_Waltz - CHORDS 2026-01-15", "harbour waltz", ["CHORDS", "2026-01-15"]],
    ["Harbour Waltz (live)", "harbour waltz", ["live"]],
    ["harbour waltz v2", "harbour waltz", ["v2"]],
    ["Harbour Waltz take 3", "harbour waltz", ["take", "3"]],
    ["Harbour Waltz in Bb", "harbour waltz", ["in", "Bb"]],
    ["HarbourWaltz", "harbour waltz", []],
    ["Rainy Polka 9.10.2026", "rainy polka", ["9.10.2026"]],
    ["Polkka soinnut", "polkka", ["soinnut"]],
    ["Scan 3", "", ["3"]],
  ])("%s → %s", (name, key, extras) => {
    const cleaned = clean(name);
    expect(cleaned.key).toBe(key);
    expect(cleaned.extras).toEqual(extras);
  });

  it("finds dates", () => {
    expect(clean("Song 2026-01-15").date).toBe("2026-01-15");
    expect(clean("Song 20260115").date).toBe("2026-01-15");
    expect(clean("Song 9.10.26").date).toBe("2026-10-09");
    expect(clean("Song 9.10").date).toBeNull();
    expect(clean("Song 31.02.2026")).toMatchObject({ key: "song", date: null }); // no such day: trailing numbers
  });
});

describe("matching helpers", () => {
  it("edit distance stops at the limit", () => {
    expect(editDistance("waltz", "walts", 1)).toBe(1);
    expect(editDistance("waltz", "polka", 1)).toBe(2);
  });
  it("related: whole words within the tolerance", () => {
    expect(related("harbour waltz reprise", "harbour waltz")).toBe(true);
    expect(related("harbour walts", "harbour waltz")).toBe(true);
    expect(related("vanhassa", "vanha")).toBe(false);
  });
  it("slug", () => {
    expect(slug("Äiti & Isä!")).toBe("aiti-isa");
    expect(slug("???")).toBe("song");
  });
});

const files = (...keys: string[]) => keys.map((key) => ({ key, modified: "2026-01-01T00:00:00Z" }));

describe("group", () => {
  it("one folder per song", () => {
    const songs = group(
      files(
        "s1/Harbour Waltz/Harbour Waltz.mp3",
        "s1/Harbour Waltz/hw take 3.wav",
        "s1/Harbour Waltz/Harbour Waltz chords.pdf",
        "s1/Rainy Polka/Rainy Polka.mp3",
      ),
    );
    expect(songs.map((s) => s.title)).toEqual(["Harbour Waltz", "Rainy Polka"]);
    expect(songs[0].audio.map((a) => a.key)).toEqual([
      "s1/Harbour Waltz/Harbour Waltz.mp3",
      "s1/Harbour Waltz/hw take 3.wav",
    ]);
    expect(songs[0].sheets).toHaveLength(1);
  });

  it("one big folder, matched by names across sources and typos", () => {
    const songs = group(
      files(
        "s1/All/Harbour Waltz.mp3",
        "s1/All/Harbour Waltz piano.mp3",
        "s1/All/harbour waltz - chords.pdf",
        "s2/Rehearsal 9.10/Harbour Walts 2.wav",
        "s1/All/Rainy Polka.mp3",
      ),
    );
    expect(songs.map((s) => s.title)).toEqual(["Harbour Waltz", "Rainy Polka"]);
    const waltz = songs[0];
    expect(waltz.audio.map((a) => a.label)).toEqual(["All", "All · piano", "Rehearsal 9.10 · 2"]);
    expect(waltz.sheets.map((s) => s.label)).toEqual(["All · chords"]);
  });

  it("sheets newest first, by the date in the name", () => {
    const [song] = group(files("s1/Waltz 2026-01-15.pdf", "s1/Waltz 2026-02-01.pdf", "s1/Waltz.mp3"));
    expect(song.sheets.map((s) => s.key)).toEqual(["s1/Waltz 2026-02-01.pdf", "s1/Waltz 2026-01-15.pdf"]);
  });

  it("names that say nothing go to Other files, last", () => {
    const songs = group(files("s1/Zebra.mp3", "s1/scan 3.pdf"));
    expect(songs.map((s) => [s.id, s.title])).toEqual([
      ["zebra", "Zebra"],
      ["other-files", "Other files"],
    ]);
  });

  it("ids are unique", () => {
    const songs = group(files("s1/A/Song.mp3", "s1/B/Song!.mp3", "s1/Song?.pdf"));
    expect(new Set(songs.map((s) => s.id)).size).toBe(songs.length);
  });
});
