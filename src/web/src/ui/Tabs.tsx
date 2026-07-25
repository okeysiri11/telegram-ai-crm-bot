import type { ReactNode } from "react";
import { cn } from "@/utils/cn";

type Tab = { id: string; label: string };
type Props = { tabs: Tab[]; active: string; onChange: (id: string) => void; children?: ReactNode };

export function Tabs({ tabs, active, onChange, children }: Props) {
  return (
    <div>
      <div className="mb-3 flex gap-2 border-b border-[var(--ew-border)]">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => onChange(t.id)}
            className={cn(
              "px-3 py-2 text-sm",
              active === t.id ? "border-b-2 border-[var(--ew-brand)] font-semibold" : "text-[var(--ew-muted)]",
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
