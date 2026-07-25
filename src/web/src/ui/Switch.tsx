type Props = { checked: boolean; onChange: (v: boolean) => void; label?: string };

export function Switch({ checked, onChange, label }: Props) {
  return (
    <label className="inline-flex items-center gap-2 text-sm">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`h-6 w-11 rounded-full transition ${checked ? "bg-[var(--ew-brand)]" : "bg-[var(--ew-border)]"}`}
      >
        <span className={`block h-5 w-5 translate-y-0.5 rounded-full bg-white transition ${checked ? "translate-x-5" : "translate-x-0.5"}`} />
      </button>
      {label}
    </label>
  );
}
