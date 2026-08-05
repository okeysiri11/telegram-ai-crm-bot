import type { ReactNode } from "react";

export function StatusCard({
  title,
  value,
  subtitle,
  ok = true,
}: {
  title: string;
  value: ReactNode;
  subtitle?: string;
  ok?: boolean;
}) {
  return (
    <div className="glass fade-in rounded-2xl p-4 transition hover:border-sky-400/30">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">
          {title}
        </span>
        <span className={`status-dot ${ok ? "status-ok" : "status-err"}`} />
      </div>
      <div className="text-2xl font-semibold tracking-tight">{value}</div>
      {subtitle ? (
        <div className="mt-1 text-xs text-[var(--muted)]">{subtitle}</div>
      ) : null}
    </div>
  );
}
