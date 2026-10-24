// The two languages have the same texts: every key in both files, with the same {parameters}.
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { m } from "./paraglide/messages.js";
import { getLocale } from "./paraglide/runtime.js";

const load = (lang: string) => JSON.parse(readFileSync(new URL(`../messages/${lang}.json`, import.meta.url), "utf8"));
const en = load("en");
const fi = load("fi");
const params = (text: unknown) => [...new Set(JSON.stringify(text).match(/\{\w+\}/g) ?? [])].sort();

describe("messages", () => {
  it("both languages have the same keys", () => {
    expect(Object.keys(fi).sort()).toEqual(Object.keys(en).sort());
  });
  it("each text has the same parameters in both", () => {
    for (const key of Object.keys(en)) expect([key, params(fi[key])]).toEqual([key, params(en[key])]);
  });
  it("no Finnish text is left in English", () => {
    const same = Object.keys(en).filter((k) => k !== "$schema" && JSON.stringify(en[k]) === JSON.stringify(fi[k]));
    expect(same.sort()).toEqual(["bpm_title", "ok", "tap", "tempo"]);
  });
  it("plurals pick the form by count", () => {
    expect(m.n_songs({ count: 1 }, { locale: "en" })).toBe("1 song");
    expect(m.n_songs({ count: 12 }, { locale: "en" })).toBe("12 songs");
    expect(m.n_songs({ count: 1 }, { locale: "fi" })).toBe("1 kappale");
    expect(m.n_songs({ count: 12 }, { locale: "fi" })).toBe("12 kappaletta");
  });
  it("without a browser the app speaks English", () => {
    expect(getLocale()).toBe("en");
  });
});
