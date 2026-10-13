// A visible Suomeksi / English pair for pages that have no ☰ menu (the first start).

import { Button } from "../kit/Button";
import { canSwitch, language, switchTo } from "../language";

const CHOICES = [
  ["fi", "Suomeksi"],
  ["en", "English"],
] as const;

/** Both languages always visible; the one in use is marked, the other is a click away. */
export function LanguageSwitch() {
  return (
    <div className="ml-auto flex gap-1" role="group" aria-label="Language / Kieli">
      {CHOICES.map(([code, label]) => (
        <Button
          key={code}
          kind="quiet"
          active={language() === code}
          disabled={!canSwitch()}
          lang={code}
          onClick={() => switchTo(code)}
        >
          {label}
        </Button>
      ))}
    </div>
  );
}

/** A small grey flag: the Union Jack for English (diagonals under a centred cross), the Nordic cross for Suomi. */
export function Flag({ nordic }: { nordic: boolean }) {
  return (
    <svg width="18" height="12" viewBox="0 0 18 12" aria-hidden className="shrink-0">
      <rect x="0.5" y="0.5" width="17" height="11" rx="1" fill="none" stroke="currentColor" />
      {nordic ? (
        <>
          <rect x="5" y="0.5" width="3" height="11" fill="currentColor" />
          <rect x="0.5" y="4.5" width="17" height="3" fill="currentColor" />
        </>
      ) : (
        <>
          <path d="M0.5 0.5 17.5 11.5 M17.5 0.5 0.5 11.5" stroke="currentColor" strokeWidth="1.6" opacity="0.55" />
          <rect x="7.25" y="0.5" width="3.5" height="11" fill="currentColor" />
          <rect x="0.5" y="4.25" width="17" height="3.5" fill="currentColor" />
        </>
      )}
    </svg>
  );
}
