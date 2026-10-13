// Is this a phone (below Tailwind's `sm`, 640 px)? Only the song page asks, to pick its layout
// (docs/browser-mobile.md); inside the parts the differences are CSS (`max-sm:` / `sm:`).

import { useEffect, useState } from "react";

const QUERY = "(max-width: 639px)";

export function usePhone() {
  const [phone, setPhone] = useState(() => window.matchMedia(QUERY).matches);
  useEffect(() => {
    const list = window.matchMedia(QUERY);
    const changed = () => setPhone(list.matches);
    list.addEventListener("change", changed);
    return () => list.removeEventListener("change", changed);
  }, []);
  return phone;
}
