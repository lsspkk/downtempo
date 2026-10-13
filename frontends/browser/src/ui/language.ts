// The app's language: English or Finnish, first from the browser, then as chosen (remembered).
// Switching reloads the page in the new language, so not while a download runs.

import * as download from "../core/download";
import { getLocale, type Locale, setLocale } from "../paraglide/runtime.js";

export const LANGUAGES: [Locale, string][] = [
  ["en", "English"],
  ["fi", "Suomi"],
];

export const language = getLocale;

export const canSwitch = () => !download.busy();

export function switchTo(locale: Locale) {
  if (locale !== getLocale() && canSwitch()) void setLocale(locale);
}
