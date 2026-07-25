import type { InputHTMLAttributes } from "react";
import { cn } from "@/utils/cn";

export function Input({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-md border border-[var(--ew-border)] bg-[var(--ew-surface)] px-3 text-sm outline-none focus:ring-2 focus:ring-[var(--ew-brand)]",
        className,
      )}
      {...rest}
    />
  );
}
