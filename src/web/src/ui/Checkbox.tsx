import type { InputHTMLAttributes } from "react";
import { cn } from "@/utils/cn";

export function Checkbox({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      type="checkbox"
      className={cn("h-4 w-4 rounded-[var(--eds-radius-sm)] accent-[var(--eds-primary)]", className)}
      {...props}
    />
  );
}
