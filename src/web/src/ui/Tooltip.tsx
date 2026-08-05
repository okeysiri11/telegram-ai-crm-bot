import type { ReactNode } from "react";

export function Tooltip({ label, children }: { label: string; children: ReactNode }) {
  return (
    <span className="group relative inline-flex">
      {children}
      <span className="pointer-events-none absolute bottom-full left-1/2 z-[var(--eds-z-modal)] mb-[var(--eds-space-1)] hidden -translate-x-1/2 whitespace-nowrap rounded-[var(--eds-radius-md)] bg-[var(--eds-text)] px-[var(--eds-space-2)] py-[var(--eds-space-1)] text-xs text-[var(--eds-surface)] shadow-[var(--eds-shadow-md)] group-hover:block">
        {label}
      </span>
    </span>
  );
}
