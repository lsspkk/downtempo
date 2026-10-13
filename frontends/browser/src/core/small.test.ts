// The small pure helpers: share ids, link check, chosen folders, unsafe paths, formats.
import { describe, expect, it } from "vitest";
import { opens, takes, tidy, tidySkip } from "./chosen";
import { splitPath } from "./files";
import { ago, clock, size } from "./format";
import { looksLikeLink, shareId } from "./onedrive";

describe("onedrive", () => {
  it("share id is u! + unpadded base64url of the link", () => {
    expect(shareId("https://1drv.ms/f/s!abc")).toBe("u!aHR0cHM6Ly8xZHJ2Lm1zL2YvcyFhYmM");
  });
  it("a redeem link shares the URL inside it", () => {
    const inner = "https://1drv.ms/f/s!abc";
    const redeem = btoa(inner).replace(/=+$/, "");
    expect(shareId(`https://onedrive.live.com/redir?redeem=${redeem}`)).toBe(shareId(inner));
  });
  it("knows OneDrive links", () => {
    expect(looksLikeLink("https://1drv.ms/f/c/abc")).toBe(true);
    expect(looksLikeLink("https://contoso-my.sharepoint.com/:f:/g/x")).toBe(true);
    expect(looksLikeLink("https://drive.google.com/x")).toBe(false);
    expect(looksLikeLink("hello")).toBe(false);
  });
});

describe("files", () => {
  it("splits a path and refuses climbing out", () => {
    expect(splitPath("s1/a/b.mp3")).toEqual([["s1", "a"], "b.mp3"]);
    expect(() => splitPath("s1/../x.mp3")).toThrow();
  });
});

describe("format", () => {
  it("clock", () => {
    expect(clock(75.4)).toBe("1:15");
    expect(clock(3725)).toBe("1:02:05");
    expect(clock(NaN)).toBe("0:00");
    expect(clock(75.46, true, "en")).toBe("1:15.4");
    expect(clock(75.46, true, "fi")).toBe("1:15,4");
  });
  it("size, in each language", () => {
    expect(size(1_234_567, "en")).toBe("1.2 MB");
    expect(size(2.5e9, "en")).toBe("2.5 GB");
    expect(size(10, "en")).toBe("1 kB");
    expect(size(1_234_567, "fi")).toBe("1,2 Mt");
  });
  it("ago, in each language", () => {
    expect(ago(0, 20_000, "en")).toBe("now");
    expect(ago(0, 3 * 3600_000, "en")).toBe("3 hr. ago");
    expect(ago(0, 3 * 3600_000, "fi")).toBe("3 t sitten");
  });
});

describe("chosen folders", () => {
  const folders = ["Spring 2026", "Songbook/Waltzes"];
  it("takes files inside a chosen folder, any depth", () => {
    expect(takes(folders, "Spring 2026/a.mp3")).toBe(true);
    expect(takes(folders, "Songbook/Waltzes/x/b.pdf")).toBe(true);
    expect(takes(folders, "Songbook/c.pdf")).toBe(false);
    expect(takes(folders, "top.mp3")).toBe(false);
    expect(takes(folders, "Spring 2026 old/a.mp3")).toBe(false);
  });
  it("nothing chosen takes everything", () => {
    expect(takes([], "any/where.mp3")).toBe(true);
    expect(opens([], "any")).toBe(true);
  });
  it("opens only folders on the way to a chosen one", () => {
    expect(opens(folders, "Songbook")).toBe(true);
    expect(opens(folders, "Songbook/Waltzes/x")).toBe(true);
    expect(opens(folders, "Songbook/Tangos")).toBe(false);
    expect(opens(folders, "Archive")).toBe(false);
  });
  it("a left-out folder inside a chosen one is neither opened nor taken", () => {
    const skip = ["Spring 2026/Demos"];
    expect(takes(folders, "Spring 2026/a.mp3", skip)).toBe(true);
    expect(takes(folders, "Spring 2026/Demos/b.mp3", skip)).toBe(false);
    expect(takes(folders, "Spring 2026/Demos/old/c.mp3", skip)).toBe(false);
    expect(opens(folders, "Spring 2026/Demos", skip)).toBe(false);
    expect(opens(folders, "Spring 2026/Demos/old", skip)).toBe(false);
    expect(opens(folders, "Spring 2026", skip)).toBe(true);
    expect(takes([], "Archive/x.mp3", ["Archive"])).toBe(false);
  });
  it("left-out folders count only inside taken ones, outermost first", () => {
    expect(tidySkip(["A"], ["A/x", "B/y", "A/x/z", "A"])).toEqual(["A/x"]);
    expect(tidySkip([], ["Archive", "Archive/2019"])).toEqual(["Archive"]);
  });
  it("a ticked folder covers the ticks inside it", () => {
    expect(tidy(["B/x", "A", "B", "A/y", "A"])).toEqual(["A", "B"]);
    expect(tidy(["Ab", "A"])).toEqual(["A", "Ab"]);
  });
});
