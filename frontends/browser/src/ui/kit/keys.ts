// Keyboard shortcuts: each screen part registers its own keys; typing in a field never triggers them.

import { useEffect, useRef } from "react";

export type KeyMap = Record<string, (event: KeyboardEvent) => void>;

const typing = (target: EventTarget | null) =>
  target instanceof HTMLElement &&
  (target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName));

/** Keys by `event.key` ("ArrowLeft", " ", "a", "PageDown"); the latest map is used without re-subscribing. */
export function useKeys(map: KeyMap, enabled = true) {
  const latest = useRef(map);
  latest.current = map;
  useEffect(() => {
    if (!enabled) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey || event.altKey || typing(event.target)) return;
      if (document.querySelector("[role=dialog]")) return;
      const action = latest.current[event.key] ?? latest.current[event.key.toLowerCase()];
      if (!action) return;
      event.preventDefault();
      action(event);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [enabled]);
}
