// Numbers as people read them: play times, file sizes, dates and "how long ago", in the app's language.

import { getLocale } from "../paraglide/runtime.js";

/** 75.4 → "1:15"; 3725 → "1:02:05"; with tenths 75.46 → "1:15.4" (Finnish "1:15,4"). */
export function clock(seconds: number, tenths = false, locale: string = getLocale()): string {
  if (!Number.isFinite(seconds) || seconds < 0) seconds = 0;
  const s = Math.floor(seconds);
  const [h, m, rest] = [Math.floor(s / 3600), Math.floor((s % 3600) / 60), s % 60];
  let tail = String(rest).padStart(2, "0");
  if (tenths) tail += (locale === "fi" ? "," : ".") + Math.floor((seconds - s) * 10 + 1e-6);
  return h ? `${h}:${String(m).padStart(2, "0")}:${tail}` : `${m}:${tail}`;
}

/** 1234567 → "1.2 MB" (Finnish "1,2 Mt"); 2.5e9 → "2.5 GB"; 10 → "1 kB". */
export function size(bytes: number, locale: string = getLocale()): string {
  const [value, unit] =
    bytes >= 1e9
      ? [bytes / 1e9, "gigabyte"]
      : bytes >= 1e6
        ? [bytes / 1e6, "megabyte"]
        : [Math.max(1, bytes / 1e3), "kilobyte"];
  const digits = unit === "kilobyte" ? 0 : 1;
  const format = { style: "unit", unit, minimumFractionDigits: digits, maximumFractionDigits: digits } as const;
  return new Intl.NumberFormat(locale, format).format(value);
}

/** "now", "3 min. ago", "3 hr. ago", "5 days ago" (Finnish "3 t sitten"). */
export function ago(time: number, now = Date.now(), locale: string = getLocale()): string {
  const format = new Intl.RelativeTimeFormat(locale, { style: "short", numeric: "auto" });
  const minutes = Math.round((now - time) / 60000);
  if (minutes < 1) return format.format(0, "second");
  if (minutes < 60) return format.format(-minutes, "minute");
  if (minutes < 60 * 36) return format.format(-Math.round(minutes / 60), "hour");
  return format.format(-Math.round(minutes / 1440), "day");
}

/** A file's date as the language writes it: "10/13/2026", Finnish "13.10.2026". */
export function day(iso: string, locale: string = getLocale()): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleDateString(locale);
}
