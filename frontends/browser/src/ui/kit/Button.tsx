// Buttons: `Button` with text (primary, plain, quiet, danger), and `IconButton`, the round one of the
// top bars: 44 px on a phone (a thumb), 36 px with a pointer, a grey icon that turns indigo when on.

import type { ButtonHTMLAttributes } from "react";

type Kind = "primary" | "plain" | "quiet" | "danger";
const KINDS: Record<Kind, string> = {
  primary: "bg-accent-600 text-white hover:bg-accent-700 disabled:bg-zinc-300 dark:disabled:bg-zinc-700",
  plain:
    "border border-zinc-300 bg-white hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-900 dark:hover:bg-zinc-800",
  quiet: "hover:bg-zinc-200/70 dark:hover:bg-zinc-800",
  danger:
    "border border-red-300 text-red-700 hover:bg-red-50 dark:border-red-900 dark:text-red-400 dark:hover:bg-red-950",
};

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { kind?: Kind; active?: boolean };

export function Button({ kind = "plain", active = false, className = "", ...props }: Props) {
  const on = active
    ? "!bg-accent-100 !text-accent-900 ring-1 ring-accent-500 dark:!bg-accent-900 dark:!text-accent-50"
    : "";
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium whitespace-nowrap transition-colors disabled:opacity-50 ${KINDS[kind]} ${on} ${className}`}
      {...props}
    />
  );
}

/** A round button with only an icon; `label` is its tooltip and its name for screen readers. */
export function IconButton({
  label,
  active = false,
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { label: string; active?: boolean }) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      aria-pressed={props["aria-expanded"] === undefined ? active : undefined}
      className={`inline-flex size-11 shrink-0 items-center justify-center rounded-full transition-colors hover:bg-zinc-200/70 disabled:opacity-40 sm:size-9 dark:hover:bg-zinc-800 ${active ? "text-accent-600 dark:text-accent-400" : "text-zinc-600 dark:text-zinc-300"} ${className}`}
      {...props}
    />
  );
}
