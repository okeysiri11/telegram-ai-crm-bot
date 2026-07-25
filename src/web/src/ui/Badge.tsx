import type { ReactNode } from "react";
import { cn } from "@/utils/cn";

export function Badge({ children, tone = "default" }: { children: ReactNode; tone?: "default" | "success" | "warning" | "danger" }) {
  return (
    <span
      className={cn(
        "inline-flex rounded px-2 py-0.5 text-xs font-medium",
        tone === "default" && "bg-[var(--ew-brand-soft)] text-[var(--ew-brand)]",
        tone === "success" && "bg-emerald-100 text-emerald-800",
        tone === "warning" && "bg-amber-100 text-amber-800",
        tone === "danger" && "bg-red-100 text-red-800",
      )}
    >
      {children}
    </span>
  );
}
