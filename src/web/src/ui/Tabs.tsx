import type { ReactNode } from "react";
import { cn } from "@/utils/cn";

type Tab = { id: string; label: string };
type Props = { tabs: Tab[]; active: string; onChange: (id: string) => void; children?: ReactNode };

export function Tabs({ tabs, active, onChange, children }: Props) {
  return (
    <div>
      <div className="eds-toolbar mb-[var(--eds-space-3)] gap-0 border-b border-[var(--eds-border)]" role="tablist">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={active === t.id}
            onClick={() => onChange(t.id)}
            className={cn(
              "eds-focus-ring px-[var(--eds-space-3)] py-[var(--eds-space-2)] text-sm transition",
              active === t.id
                ? "border-b-2 border-[var(--eds-primary)] font-semibold text-[var(--eds-text)]"
                : "border-b-2 border-transparent text-[var(--eds-text-muted)] hover:text-[var(--eds-text)]",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>
      {children}
    </div>
  );
}
