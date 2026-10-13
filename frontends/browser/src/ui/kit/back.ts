// The phone's Back (button or gesture) and the browser's Back close what is open on top: each open
// layer (Settings, a phone's song list or loop editor) adds a history step, and Back takes it away.
// Closed by the app instead (←, Esc, a pick), the layer takes its step out again, so Back never
// lands on a step that has nothing left to close.

import { useEffect, useRef } from "react";

const open: (() => void)[] = []; // the open layers' close functions, the top one last
let ours = 0; // Back steps the app took itself, not the user

window.addEventListener("popstate", () => {
  if (ours) ours--;
  else open.pop()?.();
});

export function useBackCloses(isOpen: boolean, close: () => void) {
  const latest = useRef(close);
  latest.current = close;
  useEffect(() => {
    if (!isOpen) return;
    const layer = () => latest.current();
    open.push(layer);
    history.pushState({ downtempoLayer: open.length }, "");
    return () => {
      const index = open.indexOf(layer);
      if (index < 0) return; // Back closed it: its step is gone already
      open.splice(index, 1);
      ours++;
      history.back();
    };
  }, [isOpen]);
}
