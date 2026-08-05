import type { ReactNode } from "react";
import { cn } from "@/utils/cn";

export function Badge({
  children,
  tone = "default",
}: {
  children: ReactNode;
  tone?: "default" | "success" | "warning" | "danger" | "info";
}) {
  return (
    <span
      className={cn(
        "eds-badge",
        tone === "default" && "eds-badge--default",
        tone === "success" && "eds-badge--success",
        tone === "warning" && "eds-badge--warning",
        tone === "danger" && "eds-badge--danger",
        tone === "info" && "eds-badge--info",
      )}
    >
      {children}
    </span>
  );
}
