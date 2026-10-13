// The ☰ menu: the projects (switch), New project…, Settings…, the other theme (Dark / Light theme),
// the other language (English ↔ Suomi) with a small grey flag, and About. The theme starts as the system's.

import { Info, Menu as MenuIcon, Moon, Sun } from "lucide-react";
import * as projects from "../../core/projects";
import { useStore } from "../../core/store";
import { m } from "../../paraglide/messages.js";
import { IconButton } from "../kit/Button";
import { DropDown, MenuItem, MenuLabel, MenuSeparator } from "../kit/DropDown";
import { canSwitch, LANGUAGES, language, switchTo } from "../language";
import { look } from "../theme";

type Props = { project: string; onSettings: () => void; onAbout: () => void; onNewProject: () => void };

export function MainMenu({ project, onSettings, onAbout, onNewProject }: Props) {
  const { all } = projects.useProjects();
  const { theme } = useStore(look);
  const dark = theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  const other = LANGUAGES.find(([code]) => code !== language()) ?? LANGUAGES[0]; // the menu offers the other one

  return (
    <DropDown
      trigger={(open, toggle) => (
        <IconButton label={m.menu()} active={open} aria-expanded={open} onClick={toggle}>
          <MenuIcon size={20} />
        </IconButton>
      )}
    >
      <MenuLabel>{m.projects()}</MenuLabel>
      {all.map((p) => (
        <MenuItem key={p.id} checked={p.id === project} onSelect={() => projects.use(p.id)}>
          <span className="block truncate">{p.name}</span>
        </MenuItem>
      ))}
      <MenuItem checked={false} onSelect={onNewProject}>
        {m.new_project_menu()}
      </MenuItem>
      <MenuSeparator />
      <MenuItem onSelect={onSettings}>{m.settings_menu()}</MenuItem>
      <MenuItem
        icon={dark ? <Sun size={16} /> : <Moon size={16} />}
        onSelect={() => look.set({ theme: dark ? "light" : "dark" })}
      >
        {dark ? m.light_theme() : m.dark_theme()}
      </MenuItem>
      <MenuItem
        icon={<Flag nordic={other[0] === "fi"} />}
        disabled={!canSwitch()}
        title={canSwitch() ? m.language_reloads() : m.language_wait()}
        onSelect={() => switchTo(other[0])}
      >
        {other[1]}
      </MenuItem>
      <MenuSeparator />
      <MenuItem icon={<Info size={16} />} onSelect={onAbout}>
        {m.about()}
      </MenuItem>
    </DropDown>
  );
}

/** A small grey flag: the Union Jack for English (diagonals under a centred cross), the Nordic cross for Suomi. */
function Flag({ nordic }: { nordic: boolean }) {
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
