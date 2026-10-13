// The sheet's controls, as the Python player's sheet pane: zoom − / % / +, fit width (W), fit page (H),
// Sheet only (F), trim margins (0.5 / 1 / 2 cm), rotate (O), open the PDF, and which PDF. SheetToolbar is a line over the sheet with
// a pointer; SheetMenu is one button for a phone's top line with all of it in its drop-down.

import {
  EllipsisVertical,
  ExternalLink,
  Fullscreen,
  RotateCcw,
  RotateCw,
  SlidersHorizontal,
  UnfoldHorizontal,
  UnfoldVertical,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { m } from "../../paraglide/messages.js";
import { Button, IconButton } from "../kit/Button";
import { DropDown, MenuItem, MenuLabel, MenuSeparator } from "../kit/DropDown";
import { type Sheet, TRIMS } from "./useSheet";

const ZoomRow = ({ sheet }: { sheet: Sheet }) => (
  <>
    <IconButton label={`${m.zoom_out()} (−)`} onClick={() => sheet.zoomStep(-1)}>
      <ZoomOut size={18} />
    </IconButton>
    <span className="w-12 text-center text-sm tabular-nums">{Math.round(sheet.zoom * 100)} %</span>
    <IconButton label={`${m.zoom_in()} (+)`} onClick={() => sheet.zoomStep(1)}>
      <ZoomIn size={18} />
    </IconButton>
  </>
);

const fitsWidth = (sheet: Sheet) => sheet.view.fit === null && sheet.view.zoom === 1;

const TRIM_NAMES: Record<number, () => string> = {
  0: m.trim_off,
  0.5: m.trim_small,
  1: m.trim_medium,
  2: m.trim_large,
};

/** Trim margins: cut 0.5, 1 or 2 cm from every side of the pages, so the notes get the room. */
const TrimItems = ({ sheet }: { sheet: Sheet }) => (
  <>
    <MenuLabel>{m.trim_margins()}</MenuLabel>
    {TRIMS.map((cm) => (
      <MenuItem key={cm} checked={(sheet.view.trim ?? 0) === cm} onSelect={() => sheet.setTrim(cm)}>
        {TRIM_NAMES[cm]()}
      </MenuItem>
    ))}
  </>
);

const RotateItems = ({ sheet }: { sheet: Sheet }) => (
  <>
    <TrimItems sheet={sheet} />
    <MenuSeparator />
    <MenuItem icon={<RotateCw size={16} />} stay onSelect={() => sheet.turn(90)}>
      {m.rotate_right()}
    </MenuItem>
    <MenuItem icon={<RotateCcw size={16} />} stay onSelect={() => sheet.turn(-90)}>
      {m.rotate_left()}
    </MenuItem>
    <MenuSeparator />
    <MenuItem icon={<ExternalLink size={16} />} onSelect={sheet.openPdf}>
      {m.open_pdf()}
    </MenuItem>
  </>
);

export function SheetToolbar({ sheet }: { sheet: Sheet }) {
  const { sheets, sheet: current } = sheet;
  return (
    <div className="flex shrink-0 items-center gap-1 border-b border-zinc-200 bg-white px-2 py-0.5 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex min-w-0 flex-1 items-center gap-1 overflow-x-auto">
        {sheets.length > 1 ? (
          sheets.map((s) => (
            <Button
              key={s.key}
              kind="quiet"
              active={s.key === current?.key}
              className="max-w-48 !py-1"
              onClick={() => sheet.pickSheet(s.key)}
              title={s.label}
            >
              <span className="truncate">{s.label}</span>
            </Button>
          ))
        ) : (
          <span className="truncate px-2 text-sm text-zinc-500" title={current?.label}>
            {current?.label}
          </span>
        )}
      </div>
      <div className="flex shrink-0 items-center">
        <ZoomRow sheet={sheet} />
        <IconButton label={m.fit_width()} active={fitsWidth(sheet)} onClick={sheet.fitWidth}>
          <UnfoldHorizontal size={18} />
        </IconButton>
        <IconButton label={m.fit_page()} active={sheet.view.fit === "page"} onClick={sheet.fitPage}>
          <UnfoldVertical size={18} />
        </IconButton>
        <IconButton label={m.full_screen()} onClick={() => sheet.sheetOnly(true)}>
          <Fullscreen size={18} />
        </IconButton>
        <DropDown
          align="right"
          trigger={(open, toggle) => (
            <IconButton label={m.sheet_more()} active={open} aria-expanded={open} onClick={toggle}>
              <EllipsisVertical size={18} />
            </IconButton>
          )}
        >
          <RotateItems sheet={sheet} />
        </DropDown>
      </div>
    </div>
  );
}

export function SheetMenu({ sheet }: { sheet: Sheet }) {
  const { sheets, sheet: current } = sheet;
  return (
    <DropDown
      align="right"
      title={m.sheet_title()}
      trigger={(open, toggle) => (
        <IconButton label={m.sheet_view()} active={open} aria-expanded={open} onClick={toggle}>
          <SlidersHorizontal size={20} />
        </IconButton>
      )}
    >
      <div className="flex items-center justify-between px-1 pb-1">
        <ZoomRow sheet={sheet} />
      </div>
      {sheets.length > 1 && (
        <>
          <MenuSeparator />
          {sheets.map((s) => (
            <MenuItem key={s.key} checked={s.key === current?.key} onSelect={() => sheet.pickSheet(s.key)}>
              <span className="block truncate">{s.label}</span>
            </MenuItem>
          ))}
        </>
      )}
      <MenuSeparator />
      <MenuItem icon={<UnfoldHorizontal size={16} />} checked={fitsWidth(sheet)} onSelect={sheet.fitWidth}>
        {m.fit_width()}
      </MenuItem>
      <MenuItem icon={<UnfoldVertical size={16} />} checked={sheet.view.fit === "page"} onSelect={sheet.fitPage}>
        {m.fit_page()}
      </MenuItem>
      <MenuItem icon={<Fullscreen size={16} />} onSelect={() => sheet.sheetOnly(true)}>
        {m.full_screen()}
      </MenuItem>
      <MenuSeparator />
      <RotateItems sheet={sheet} />
    </DropDown>
  );
}
