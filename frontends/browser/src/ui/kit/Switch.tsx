// An on / off switch with its label beside it (the Optimal switch, the Metronome): a track with a
// knob, indigo when on. A switch shows a state the user can flip; a disabled-looking one may still
// take a click (`muted`), so it can lead to where its value is set.

type Props = {
  on: boolean;
  onChange: (on: boolean) => void;
  label: string;
  title?: string;
  muted?: boolean; // grey: nothing to switch to yet
  disabled?: boolean;
  className?: string;
};

export function Switch({ on, onChange, label, title, muted = false, disabled = false, className = "" }: Props) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      disabled={disabled}
      title={title}
      onClick={() => onChange(!on)}
      className={`inline-flex shrink-0 items-center gap-1.5 rounded-lg px-1.5 py-1 text-sm whitespace-nowrap hover:bg-zinc-200/70 disabled:opacity-40 dark:hover:bg-zinc-800 ${muted ? "text-zinc-400 dark:text-zinc-500" : ""} ${className}`}
    >
      <span
        className={`relative h-4 w-7 shrink-0 rounded-full transition-colors ${on ? "bg-accent-600" : "bg-zinc-300 dark:bg-zinc-600"}`}
      >
        <span
          className={`absolute top-0.5 size-3 rounded-full bg-white shadow transition-[left] ${on ? "left-3.5" : "left-0.5"}`}
        />
      </span>
      {label}
    </button>
  );
}
