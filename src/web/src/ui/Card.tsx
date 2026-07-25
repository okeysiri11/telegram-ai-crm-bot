import type { ReactNode } from "react";
import { cn } from "@/utils/cn";

export function Card({ title, children, className }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <section className={cn("rounded-lg border border-[var(--ew-border)] bg-[var(--ew-surface)] p-4", className)}>
      {title ? <h3 className="mb-2 text-sm font-semibold tracking-wide text-[var(--ew-muted)]">{title}</h3> : null}
      {children}
    </section>
  );
}
