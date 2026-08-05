type Props = { checked: boolean; onChange: (v: boolean) => void; label?: string };

export function Switch({ checked, onChange, label }: Props) {
  return (
    <label className="inline-flex items-center gap-[var(--eds-space-2)] text-sm text-[var(--eds-text)]">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`eds-focus-ring relative h-6 w-11 shrink-0 rounded-full transition ${
          checked ? "bg-[var(--eds-primary)]" : "bg-[var(--eds-border)]"
        }`}
      >
        <span
          className={`block h-5 w-5 rounded-full bg-white shadow-[var(--eds-shadow-sm)] transition ${
            checked ? "translate-x-5 translate-y-0.5" : "translate-x-0.5 translate-y-0.5"
          }`}
        />
      </button>
      {label}
    </label>
  );
}
