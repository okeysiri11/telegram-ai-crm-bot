import type { InputHTMLAttributes } from "react";
import { cn } from "@/utils/cn";

export function Radio({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input type="radio" className={cn("h-4 w-4 accent-[var(--eds-primary)]", className)} {...props} />
  );
}
