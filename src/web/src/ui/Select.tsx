import type { SelectHTMLAttributes } from "react";
import { cn } from "@/utils/cn";

export function Select({ className, children, ...rest }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "h-10 w-full rounded-md border border-[var(--ew-border)] bg-[var(--ew-surface)] px-3 text-sm",
        className,
      )}
      {...rest}
    >
      {children}
    </select>
  );
}
