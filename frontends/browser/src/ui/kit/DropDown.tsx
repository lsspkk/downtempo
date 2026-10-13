// A drop-down: a trigger and the panel it opens. With a pointer the panel hangs under the trigger
// (rounded, `width` wide); on a phone it is a sheet across the full width under the top bar. Only CSS
// tells the two apart, so the parts using it never ask which it is. On a phone its `title` heads the
// sheet, since the round button that opened it has no text. A pick, a click outside or Esc
// closes it. The menu parts: MenuItem (an action, maybe ✓), MenuLabel, MenuSeparator.

import { Check } from "lucide-react";
import { createContext, type ReactNode, useContext, useEffect, useRef, useState } from "react";

const Close = createContext<() => void>(() => {});

type Props = {
  trigger: (open: boolean, toggle: () => void) => ReactNode;
  children: ReactNode;
  align?: "left" | "right"; // with a pointer: which edge of the trigger the panel lines up with
  width?: string; // with a pointer, e.g. "sm:w-72"
  title?: string; // on a phone a heading on top of the sheet: which button opened it (the button has no text)
};

export function DropDown({ trigger, children, align = "left", width = "sm:w-64", title }: Props) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent | KeyboardEvent) => {
      if (event instanceof KeyboardEvent ? event.key === "Escape" : !box.current?.contains(event.target as Node))
        setOpen(false);
    };
    window.addEventListener("mousedown", close);
    window.addEventListener("keydown", close);
    return () => {
      window.removeEventListener("mousedown", close);
      window.removeEventListener("keydown", close);
    };
  }, [open]);

  return (
    <div ref={box} className="relative shrink-0">
      {trigger(open, () => setOpen(!open))}
      {open && (
        <div
          className={`z-40 border-zinc-200 bg-white p-1.5 shadow-lg dark:border-zinc-700 dark:bg-zinc-900 max-sm:fixed max-sm:inset-x-0 max-sm:top-12 max-sm:max-h-[calc(100dvh-3rem)] max-sm:overflow-y-auto max-sm:border-b sm:absolute sm:top-full sm:mt-1 sm:max-w-[90vw] sm:rounded-xl sm:border ${align === "right" ? "sm:right-0" : "sm:left-0"} ${width}`}
        >
          {title && (
            <p className="border-b border-zinc-200 px-3 pt-1 pb-2 mb-1 text-sm font-semibold sm:hidden dark:border-zinc-700">
              {title}
            </p>
          )}
          <Close.Provider value={() => setOpen(false)}>{children}</Close.Provider>
        </div>
      )}
    </div>
  );
}

type ItemProps = {
  onSelect: () => void;
  children: ReactNode;
  icon?: ReactNode;
  checked?: boolean; // shows ✓ (and keeps a ✓ column for its neighbours when false)
  stay?: boolean; // keeps the menu open (a toggle, a step)
  disabled?: boolean;
  title?: string;
};

export function MenuItem({ onSelect, children, icon, checked, stay = false, disabled, title }: ItemProps) {
  const close = useContext(Close);
  return (
    <button
      type="button"
      disabled={disabled}
      title={title}
      onClick={() => {
        onSelect();
        if (!stay) close();
      }}
      className="flex w-full items-center gap-2.5 rounded-md px-3 py-2.5 text-left text-sm hover:bg-zinc-100 disabled:opacity-50 sm:py-1.5 dark:hover:bg-zinc-800"
    >
      {checked !== undefined && (
        <span className="w-4 shrink-0 text-accent-600 dark:text-accent-400">{checked && <Check size={16} />}</span>
      )}
      {icon && <span className="flex w-5 shrink-0 justify-center text-zinc-500">{icon}</span>}
      <span className="min-w-0 flex-1">{children}</span>
    </button>
  );
}

export const MenuLabel = ({ children }: { children: ReactNode }) => (
  <p className="px-3 pt-1 pb-0.5 text-xs font-semibold tracking-wide text-zinc-500 uppercase">{children}</p>
);

export const MenuSeparator = () => <hr className="my-1.5 border-zinc-200 dark:border-zinc-700" />;
