// Screen width questions. Is this a phone (below Tailwind's `sm`, 640 px)? Only the song page asks, to
// pick its layout (docs/browser-mobile.md); inside the parts the differences are CSS (`max-sm:` / `sm:`).
// Is the window wide (a Full HD laptop at 125 % scaling, browser almost full)? The sheet then offers two pages side by side.

import { useEffect, useState } from "react";

function useMedia(query: string) {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const list = window.matchMedia(query);
    const changed = () => setMatches(list.matches);
    list.addEventListener("change", changed);
    return () => list.removeEventListener("change", changed);
  }, [query]);
  return matches;
}

export const usePhone = () => useMedia("(max-width: 639px)");
export const useWide = () => useMedia("(min-width: 1400px)");
