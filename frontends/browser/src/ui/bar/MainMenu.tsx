// The ☰ menu: the projects (switch), New project…, Settings…, the other theme (Dark / Light theme),
// the other language (English ↔ Suomi) with a small grey flag, and About. The theme starts as the system's.

import { Info, Menu as MenuIcon, Moon, Sun } from "lucide-react";
import * as projects from "../../core/projects";
import { useStore } from "../../core/store";
import { m } from "../../paraglide/messages.js";
import { IconButton } from "../kit/Button";
import { DropDown, MenuItem, MenuLabel, MenuSeparator } from "../kit/DropDown";
import { Flag } from "./LanguageSwitch";
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
