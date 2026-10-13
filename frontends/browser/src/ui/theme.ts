// Light, dark or as the system says: a class on <html> that Tailwind's dark variant follows.

import { useEffect } from "react";
import { stored, useStore } from "../core/store";

export type Theme = "system" | "light" | "dark";
export const look = stored<{ theme: Theme }>("downtempo-look", { theme: "system" });

export function useTheme() {
  const { theme } = useStore(look);
  useEffect(() => {
    const media = matchMedia("(prefers-color-scheme: dark)");
    const apply = () =>
      document.documentElement.classList.toggle("dark", theme === "dark" || (theme === "system" && media.matches));
    apply();
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, [theme]);
}
